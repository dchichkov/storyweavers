#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rutabaga_wit_dialogue_bravery_tall_tale.py
=====================================================================

A standalone storyworld for a tall-tale flavored TinyStories domain: a brave
child faces an oversized rutabaga problem and solves it with wit instead of
force alone.

The world model tracks physical meters (weight, stuckness, loosenedness) and
emotional memes (worry, bravery, pride, trust). State drives the turn of the
story: a giant rutabaga causes a practical problem, people try ordinary help,
the hero speaks cleverly, and a surprising but grounded trick resolves the jam.

Run it
------
    python storyworlds/worlds/gpt-5.4/rutabaga_wit_dialogue_bravery_tall_tale.py
    python storyworlds/worlds/gpt-5.4/rutabaga_wit_dialogue_bravery_tall_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/rutabaga_wit_dialogue_bravery_tall_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/rutabaga_wit_dialogue_bravery_tall_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/rutabaga_wit_dialogue_bravery_tall_tale.py --verify
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
# This file lives in storyworlds/worlds/gpt-5.4/, so the package dir is three
# levels up from here.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    path_word: str
    crowd: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    problem: str
    size_text: str
    boast: str
    loosen_phrase: str
    ending_line: str
    heaviness: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    arrive_text: str
    effort_text: str
    fail_text: str
    strength: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Trick:
    id: str
    label: str
    setup_text: str
    action_text: str
    success_text: str
    reason_text: str
    wit: int
    sense: int
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


def _r_notice_jam(world: World) -> list[str]:
    root = world.get("rutabaga")
    path = world.get("path")
    if root.meters["stuck"] < THRESHOLD:
        return []
    sig = ("jam", root.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    path.meters["blocked"] += 1
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["worry"] += 1
    return []


def _r_loosen_clears_block(world: World) -> list[str]:
    root = world.get("rutabaga")
    path = world.get("path")
    if root.meters["loosened"] < THRESHOLD:
        return []
    sig = ("clear", root.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    root.meters["stuck"] = 0.0
    path.meters["blocked"] = 0.0
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["relief"] += 1
            ent.memes["worry"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="notice_jam", tag="physical", apply=_r_notice_jam),
    Rule(name="loosen_clears_block", tag="physical", apply=_r_loosen_clears_block),
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


PLACES = {
    "lane": Place(
        id="lane",
        label="the pumpkin lane",
        path_word="lane",
        crowd="wagons and wheelbarrows",
        ending_image="After that, the lane shone open from fence to fence again",
        tags={"road", "harvest"},
    ),
    "bridge": Place(
        id="bridge",
        label="the little wooden bridge",
        path_word="bridge",
        crowd="carts and boots",
        ending_image="After that, the bridge rang with footsteps instead of worried sighs",
        tags={"bridge", "road"},
    ),
    "market": Place(
        id="market",
        label="the market gate",
        path_word="gate",
        crowd="baskets and ponies",
        ending_image="After that, the gate stood wide as a grin and the market hummed again",
        tags={"market", "road"},
    ),
}

OBSTACLES = {
    "field_root": Obstacle(
        id="field_root",
        label="rutabaga",
        phrase="a rutabaga so big it looked like a yellow moon with dirt on it",
        problem="had burst up from the field and rolled right across the way",
        size_text="Its shoulders were as broad as a washtub and its roots curled like sleepy ropes",
        boast='the biggest rutabaga for fifty farms in every direction',
        loosen_phrase="wiggled a finger-deep crack around the rutabaga's roots",
        ending_line="The giant rutabaga rested beside the fence like a tamed hill",
        heaviness=3,
        tags={"rutabaga", "vegetable"},
    ),
    "cellar_root": Obstacle(
        id="cellar_root",
        label="rutabaga",
        phrase="a rutabaga so large it seemed to have grown while listening to thunder",
        problem="had wedged itself halfway out of the cellar door and stuck there stubbornly",
        size_text="Its round back was bigger than a rain barrel and its roots were knotted like a ship's rope",
        boast='a rutabaga with more opinions than a town meeting',
        loosen_phrase="made the dirt under the rutabaga tremble loose",
        ending_line="The huge rutabaga sat in the yard, dusty and harmless as a sleepy pony",
        heaviness=2,
        tags={"rutabaga", "vegetable"},
    ),
    "wagon_root": Obstacle(
        id="wagon_root",
        label="rutabaga",
        phrase="a rutabaga so hefty it made the wagon groan before anyone even touched it",
        problem="had slid from a wagon and planted itself in the middle of the path",
        size_text="It was round as a kettle drum and heavy enough to make the pebbles complain",
        boast='a rutabaga fit for a giant's stewpot',
        loosen_phrase="left a neat little trail where the rutabaga finally began to budge",
        ending_line="The enormous rutabaga ended up under an oak tree, looking proud but no longer troublesome",
        heaviness=2,
        tags={"rutabaga", "vegetable"},
    ),
}

HELPERS = {
    "farmer": Helper(
        id="farmer",
        label="farmer",
        arrive_text="Old Farmer Reed came first, tugging off one glove and squinting at the trouble",
        effort_text='He grunted, "Well now, I have pulled stumps from spring mud."',
        fail_text="He pulled until his hat slid over one ear, but the rutabaga only gave a rude little creak",
        strength=1,
        tags={"farmer"},
    ),
    "blacksmith": Helper(
        id="blacksmith",
        label="blacksmith",
        arrive_text="Then the blacksmith strode over with arms like gate posts",
        effort_text='She snorted, "If iron listens to me, this root should too."',
        fail_text="She leaned in hard enough to make her boots bite the ground, but the rutabaga stayed put",
        strength=2,
        tags={"blacksmith"},
    ),
    "miller": Helper(
        id="miller",
        label="miller",
        arrive_text="Soon the miller hurried up, dusted white with flour and full of advice",
        effort_text='He huffed, "I can move sacks all day; surely I can roll one vegetable."',
        fail_text="He shoved until flour puffed off his sleeves like smoke, but the giant root barely twitched",
        strength=1,
        tags={"miller"},
    ),
}

TRICKS = {
    "praise_pull": Trick(
        id="praise_pull",
        label="praise and promise",
        setup_text='The child put both hands on hips and called, "You grand old rutabaga, everyone can see how mighty you are."',
        action_text='Then the child added, "A truly mighty rutabaga would never block little feet. Show us your good manners and slide this way."',
        success_text="The townsfolk pulled at that exact moment, and the rutabaga rocked loose as if it liked being praised",
        reason_text="The clever talk made everyone pull together at the same moment, and the new tug found the weak spot in the dirt",
        wit=2,
        sense=2,
        tags={"wit", "dialogue"},
    ),
    "tickle_root": Trick(
        id="tickle_root",
        label="feather tickle",
        setup_text='The child knelt, found a goose feather, and whispered, "Even a proud rutabaga must have a ticklish root somewhere."',
        action_text='With a grin, the child tickled the little root hairs while saying, "Out you come, sleepy lump, before I make you laugh yourself loose."',
        success_text="The fine roots shook dust into the air, the big rutabaga gave a sudden hop, and everyone gasped",
        reason_text="The feather cleared dirt from the tiniest roots, and that small looseness let the heavy root start moving",
        wit=3,
        sense=3,
        tags={"wit", "dialogue", "feather"},
    ),
    "song_step": Trick(
        id="song_step",
        label="counting song",
        setup_text='The child clapped a rhythm and cried, "No more random yanking. This rutabaga needs a marching song."',
        action_text='Then the child sang, "One stomp, two stomp, three and pull!" until the whole crowd joined in.',
        success_text="On the third grand pull, the rutabaga lurched free and rolled aside in a shower of crumbs and pebbles",
        reason_text="The song gave the helpers one brave shared timing, so their strength landed together instead of separately",
        wit=1,
        sense=2,
        tags={"wit", "dialogue", "song"},
    ),
}


def valid_combo(place_id: str, obstacle_id: str, helper_id: str, trick_id: str) -> bool:
    obstacle = OBSTACLES[obstacle_id]
    helper = HELPERS[helper_id]
    trick = TRICKS[trick_id]
    if trick.sense < SENSE_MIN:
        return False
    return helper.strength + trick.wit >= obstacle.heaviness


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for obstacle_id in OBSTACLES:
            for helper_id in HELPERS:
                for trick_id in TRICKS:
                    if valid_combo(place_id, obstacle_id, helper_id, trick_id):
                        combos.append((place_id, obstacle_id, helper_id, trick_id))
    return combos


def explain_rejection(obstacle_id: str, helper_id: str, trick_id: str) -> str:
    obstacle = OBSTACLES[obstacle_id]
    helper = HELPERS[helper_id]
    trick = TRICKS[trick_id]
    if trick.sense < SENSE_MIN:
        return (
            f"(No story: the trick '{trick_id}' scores below the common-sense floor "
            f"for this world, so it is refused.)"
        )
    need = obstacle.heaviness
    have = helper.strength + trick.wit
    return (
        f"(No story: {helper.label} plus the '{trick.label}' trick are not enough "
        f"to move this {obstacle.label}. The obstacle needs combined power {need}, "
        f"but this pair only reaches {have}.)"
    )


def predict_outcome(obstacle_id: str, helper_id: str, trick_id: str) -> str:
    return "cleared" if valid_combo("lane", obstacle_id, helper_id, trick_id) else "stuck"


def introduce(world: World, hero: Entity, place: Place, obstacle: Obstacle, grownup: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"In a town where cabbages were said to cast afternoon shade, {hero.id} was the bravest little "
        f"{hero.type} on {place.label}."
    )
    world.say(
        f"One harvest morning, {hero.id} and {grownup.label_word} stopped short. "
        f"There in front of them lay {obstacle.phrase} that {obstacle.problem}."
    )
    world.say(obstacle.size_text + ".")


def set_problem(world: World, place: Place, obstacle: Obstacle, hero: Entity, grownup: Entity) -> None:
    root = world.get("rutabaga")
    root.meters["stuck"] += 1
    root.meters["weight"] = float(obstacle.heaviness)
    propagate(world, narrate=False)
    world.say(
        f"{place.crowd.capitalize()} piled up on both sides, and everybody began talking at once."
    )
    world.say(
        f'"Mercy," said {grownup.label_word}, "that is {obstacle.boast}."'
    )
    world.say(
        f'{hero.id} lifted {hero.pronoun("possessive")} chin. "Big is not the same as unbeatable," '
        f'{hero.pronoun()} said.'
    )


def summon_helper(world: World, helper: Helper, helper_ent: Entity) -> None:
    helper_ent.memes["confidence"] += 1
    world.say(helper.arrive_text + ".")
    world.say(helper.effort_text)
    world.say(helper.fail_text + ".")


def deepen_tension(world: World, hero: Entity, place: Place) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"The line of waiting {place.crowd} grew longer. Some people frowned, but {hero.id} did not back up one inch."
    )
    world.say(
        f'"If shoving were enough, it would be gone already," {hero.id} said. "This calls for wit."'
    )


def perform_trick(world: World, hero: Entity, trick: Trick, obstacle: Obstacle) -> None:
    hero.memes["wit"] += float(trick.wit)
    hero.memes["bravery"] += 1
    world.say(trick.setup_text)
    world.say(trick.action_text)
    root = world.get("rutabaga")
    root.meters["loosened"] += 1
    root.meters["moved"] += 1
    propagate(world, narrate=False)
    world.say(trick.success_text + ".")
    world.say(
        f"{obstacle.loosen_phrase.capitalize()}, and the great root finally rolled clear."
    )


def celebrate(world: World, hero: Entity, grownup: Entity, place: Place, obstacle: Obstacle, helper: Helper, trick: Trick) -> None:
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    grownup.memes["love"] += 1
    helper_ent = world.get("helper")
    helper_ent.memes["respect"] += 1
    world.say(
        f'"Well I never," said the {helper.label}, brushing off tired hands. '
        f'"That was not just brave. That was sharp."'
    )
    world.say(
        f'{grownup.label_word.capitalize()} laughed and hugged {hero.id}. '
        f'"You used both courage and wit," {grownup.pronoun()} said.'
    )
    world.say(
        f"{place.ending_image}, while {obstacle.ending_line.lower()}."
    )
    world.say(
        f"By supper, half the town was repeating {hero.id}'s words and swearing they had seen the rutabaga mind its manners."
    )
    world.facts["lesson"] = trick.reason_text


def tell(place: Place, obstacle: Obstacle, helper: Helper, trick: Trick,
         hero_name: str = "Mara", hero_type: str = "girl",
         grownup_type: str = "father") -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        role="hero",
        label=hero_name,
        traits=["brave", "quick"],
        tags={"hero"},
    ))
    grownup = world.add(Entity(
        id="Grownup",
        kind="character",
        type=grownup_type,
        role="grownup",
        label="the grown-up",
        traits=["steady"],
        tags={"parent"},
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="character",
        type="person",
        role="helper",
        label=helper.label,
        traits=["strong"],
        tags=set(helper.tags),
    ))
    world.add(Entity(
        id="rutabaga",
        kind="thing",
        type="vegetable",
        label="rutabaga",
        phrase=obstacle.phrase,
        tags=set(obstacle.tags),
    ))
    world.add(Entity(
        id="path",
        kind="thing",
        type="path",
        label=place.path_word,
        phrase=place.label,
        tags=set(place.tags),
    ))

    introduce(world, hero, place, obstacle, grownup)
    world.para()
    set_problem(world, place, obstacle, hero, grownup)
    summon_helper(world, helper, helper_ent)
    world.para()
    deepen_tension(world, hero, place)
    perform_trick(world, hero, trick, obstacle)
    world.para()
    celebrate(world, hero, grownup, place, obstacle, helper, trick)

    root = world.get("rutabaga")
    path = world.get("path")
    world.facts.update(
        hero=hero,
        grownup=grownup,
        helper=helper_ent,
        helper_cfg=helper,
        place=place,
        obstacle=obstacle,
        trick=trick,
        root=root,
        path=path,
        outcome="cleared" if path.meters["blocked"] < THRESHOLD and root.meters["loosened"] >= THRESHOLD else "stuck",
        brave=hero.memes["bravery"] >= THRESHOLD,
        witty=hero.memes["wit"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    obstacle: str
    helper: str
    trick: str
    hero_name: str
    hero_type: str
    grownup_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="bridge",
        obstacle="field_root",
        helper="blacksmith",
        trick="tickle_root",
        hero_name="Mara",
        hero_type="girl",
        grownup_type="father",
    ),
    StoryParams(
        place="lane",
        obstacle="cellar_root",
        helper="farmer",
        trick="praise_pull",
        hero_name="Eli",
        hero_type="boy",
        grownup_type="mother",
    ),
    StoryParams(
        place="market",
        obstacle="wagon_root",
        helper="miller",
        trick="song_step",
        hero_name="June",
        hero_type="girl",
        grownup_type="mother",
    ),
    StoryParams(
        place="lane",
        obstacle="field_root",
        helper="blacksmith",
        trick="song_step",
        hero_name="Ned",
        hero_type="boy",
        grownup_type="father",
    ),
]


KNOWLEDGE = {
    "rutabaga": [
        (
            "What is a rutabaga?",
            "A rutabaga is a round root vegetable that grows in the ground. It is bigger and tougher than many little garden roots."
        )
    ],
    "wit": [
        (
            "What does wit mean?",
            "Wit means using quick, clever thinking. A person with wit can notice a smart idea faster than other people."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when a problem looks big or scary. It does not mean pretending you are never afraid."
        )
    ],
    "bridge": [
        (
            "Why is a blocked bridge a problem?",
            "A blocked bridge stops people, carts, and animals from getting across. That can keep everyone waiting until the way is clear."
        )
    ],
    "market": [
        (
            "Why do people need a market gate to stay open?",
            "People use a market gate to carry food and goods in and out. If the gate is blocked, the whole market slows down."
        )
    ],
    "timing": [
        (
            "Why does pulling together work better than pulling one by one?",
            "When everyone pulls together at the same time, their strength adds up in one strong push. Random little tugs waste effort."
        )
    ],
    "roots": [
        (
            "Why can roots get stuck in dirt?",
            "Roots press into soil and wrap around little stones and clumps. That makes them hard to move until the dirt loosens."
        )
    ],
    "feather": [
        (
            "How can a feather help with a stuck thing?",
            "A feather cannot lift something heavy by itself. But it can brush dirt out of a tiny crack, and that small change can help a larger pull start working."
        )
    ],
    "song": [
        (
            "Why can a song help workers move together?",
            "A song gives everyone one beat to follow. That shared rhythm helps people act at the same moment."
        )
    ],
}
KNOWLEDGE_ORDER = ["rutabaga", "wit", "bravery", "bridge", "market", "roots", "timing", "feather", "song"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    trick = f["trick"]
    obstacle = f["obstacle"]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the word "rutabaga" and the word "wit".',
        f"Tell a playful exaggeration where a brave {hero.type} named {hero.id} uses clever dialogue to move an enormous {obstacle.label} blocking {place.label}.",
        f"Write a story in a tall-tale style where the problem looks too big for grown-ups, but a child solves it with bravery, timing, and {trick.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    grownup = f["grownup"]
    helper = f["helper_cfg"]
    place = f["place"]
    obstacle = f["obstacle"]
    trick = f["trick"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a brave little {hero.type}, and the giant rutabaga that blocked {place.label}. A grown-up and {helper.label} were there too, but {hero.id} found the winning idea."
        ),
        (
            "What was the problem in the story?",
            f"The problem was that {obstacle.phrase} {obstacle.problem}. It blocked the way and made a crowd pile up on both sides."
        ),
        (
            f"What did the {helper.label} do first?",
            f"The {helper.label} tried to move the rutabaga with plain strength. That failed, which showed the problem needed more than hard pulling."
        ),
        (
            f"How did {hero.id} show bravery?",
            f"{hero.id} stayed near the huge rutabaga when other people were only grumbling and waiting. {hero.pronoun().capitalize()} also spoke up in front of grown-ups and offered a new plan instead of giving up."
        ),
        (
            f"How did {hero.id} use wit?",
            f"{hero.id} used wit by choosing {trick.label} instead of another shove. {trick.reason_text[0].upper()}{trick.reason_text[1:]}."
        ),
        (
            "How did the story end?",
            f"The rutabaga rolled clear, the way opened again, and the town started telling the tale before supper. The ending proves that quick thinking changed the whole day."
        ),
    ]
    if f["outcome"] == "cleared":
        qa.append(
            (
                f"Why did the trick work?",
                f"It worked because {trick.reason_text}. The trick changed the crowd from a bunch of separate helpers into one useful pull."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"rutabaga", "wit", "bravery", "roots", "timing"}
    if f["place"].id == "bridge":
        tags.add("bridge")
    if f["place"].id == "market":
        tags.add("market")
    if f["trick"].id == "tickle_root":
        tags.add("feather")
    if f["trick"].id == "song_step":
        tags.add("song")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Pl, Ob, He, Tr) :- place(Pl), obstacle(Ob), helper(He), trick(Tr),
                         sense(Tr, S), sense_min(M), S >= M,
                         heaviness(Ob, H), strength(He, P), wit(Tr, W),
                         P + W >= H.

outcome(Ob, He, Tr, cleared) :- valid(_, Ob, He, Tr).
outcome(Ob, He, Tr, stuck)   :- obstacle(Ob), helper(He), trick(Tr),
                                not outcome(Ob, He, Tr, cleared).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("heaviness", obstacle_id, obstacle.heaviness))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("strength", helper_id, helper.strength))
    for trick_id, trick in TRICKS.items():
        lines.append(asp.fact("trick", trick_id))
        lines.append(asp.fact("wit", trick_id, trick.wit))
        lines.append(asp.fact("sense", trick_id, trick.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(obstacle_id: str, helper_id: str, trick_id: str) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_obstacle", obstacle_id),
        asp.fact("chosen_helper", helper_id),
        asp.fact("chosen_trick", trick_id),
        "selected_outcome(O) :- outcome(Ob, He, Tr, O), chosen_obstacle(Ob), chosen_helper(He), chosen_trick(Tr).",
    ])
    model = asp.one_model(asp_program(extra, "#show selected_outcome/1."))
    outs = asp.atoms(model, "selected_outcome")
    return outs[0][0] if outs else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "rutabaga" not in sample.story.lower():
        raise StoryError("(Smoke test failed: story generation produced empty or malformed output.)")


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

    checked = 0
    mismatches = 0
    for obstacle_id in OBSTACLES:
        for helper_id in HELPERS:
            for trick_id in TRICKS:
                py = predict_outcome(obstacle_id, helper_id, trick_id)
                asp_out = asp_outcome(obstacle_id, helper_id, trick_id)
                checked += 1
                if py != asp_out:
                    mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {checked} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{checked} outcome scenarios differ.")

    try:
        _smoke_test()
        print("OK: smoke test story generation passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


GIRL_NAMES = ["Mara", "June", "Nell", "Dora", "Ivy", "Ruth"]
BOY_NAMES = ["Eli", "Ned", "Toby", "Finn", "Abe", "Cal"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a giant rutabaga blocks the way, and a brave child uses wit to clear it."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--trick", choices=sorted(TRICKS))
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--grownup-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.helper and args.trick:
        if not valid_combo(args.place or "lane", args.obstacle, args.helper, args.trick):
            raise StoryError(explain_rejection(args.obstacle, args.helper, args.trick))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.helper is None or combo[2] == args.helper)
        and (args.trick is None or combo[3] == args.trick)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, helper_id, trick_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    grownup_type = args.grownup_type or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        obstacle=obstacle_id,
        helper=helper_id,
        trick=trick_id,
        hero_name=hero_name,
        hero_type=hero_type,
        grownup_type=grownup_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Invalid obstacle: {params.obstacle})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")
    if params.trick not in TRICKS:
        raise StoryError(f"(Invalid trick: {params.trick})")
    if params.hero_type not in {"girl", "boy"}:
        raise StoryError(f"(Invalid hero type: {params.hero_type})")
    if params.grownup_type not in {"mother", "father"}:
        raise StoryError(f"(Invalid grown-up type: {params.grownup_type})")
    if not valid_combo(params.place, params.obstacle, params.helper, params.trick):
        raise StoryError(explain_rejection(params.obstacle, params.helper, params.trick))

    world = tell(
        place=PLACES[params.place],
        obstacle=OBSTACLES[params.obstacle],
        helper=HELPERS[params.helper],
        trick=TRICKS[params.trick],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        grownup_type=params.grownup_type,
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
        print(asp_program("", "#show valid/4.\n#show outcome/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, obstacle, helper, trick) combos:\n")
        for place_id, obstacle_id, helper_id, trick_id in combos:
            print(f"  {place_id:8} {obstacle_id:12} {helper_id:10} {trick_id}")
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
            header = f"### {p.hero_name}: {p.obstacle} at {p.place} with {p.helper} + {p.trick}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
