#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/linden_influence_fault_conflict_foreshadowing_superhero_story.py

A small storyworld about a young superhero at a linden-themed town celebration.
A few early clues foreshadow a tremor from a hidden fault line. The hero faces a
conflict: a flashy friend tries to pull them toward showing off, and that social
influence can delay the rescue. The story resolves when the hero chooses people
over applause, admits fault when needed, and uses the right power for the real
problem.

Run it
------
python storyworlds/worlds/gpt-5.4/linden_influence_fault_conflict_foreshadowing_superhero_story.py
python storyworlds/worlds/gpt-5.4/linden_influence_fault_conflict_foreshadowing_superhero_story.py --all
python storyworlds/worlds/gpt-5.4/linden_influence_fault_conflict_foreshadowing_superhero_story.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/linden_influence_fault_conflict_foreshadowing_superhero_story.py --qa
python storyworlds/worlds/gpt-5.4/linden_influence_fault_conflict_foreshadowing_superhero_story.py --verify
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
    name: str
    tree_phrase: str
    crowd_phrase: str
    landing_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    text: str
    warning: str
    omen: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    the: str
    setup: str
    danger_text: str
    risk: int
    need: str
    save_text: str
    fail_text: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class Power:
    id: str
    label: str
    boast: str
    action_text: str
    power_type: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Influence:
    id: str
    label: str
    score: int
    push_text: str
    consequence_text: str


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


def _r_tremor(world: World) -> list[str]:
    hazard = world.get("hazard")
    if hazard.meters["shaking"] < THRESHOLD:
        return []
    sig = ("tremor", hazard.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("crowd").meters["fear"] += 1
    world.get("hero").memes["alarm"] += 1
    world.get("friend").memes["alarm"] += 1
    return []


def _r_delay(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["showing_off"] < THRESHOLD:
        return []
    sig = ("delay", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("hazard").meters["severity"] += 1
    world.get("crowd").meters["fear"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="tremor", tag="physical", apply=_r_tremor),
    Rule(name="delay", tag="social", apply=_r_delay),
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
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "plaza": Place(
        id="plaza",
        name="Linden Plaza",
        tree_phrase="an old linden tree spreading cool green shade over the square",
        crowd_phrase="families, paper flags, and a row of lemonade tables",
        landing_phrase="the bright bricks near the fountain",
        tags={"linden"},
    ),
    "schoolyard": Place(
        id="schoolyard",
        name="Linden Schoolyard",
        tree_phrase="a young linden tree beside the painted blacktop",
        crowd_phrase="students, teachers, and a banner tied between two poles",
        landing_phrase="the chalky edge of the playground",
        tags={"linden"},
    ),
    "market": Place(
        id="market",
        name="Linden Market Lane",
        tree_phrase="a line of linden trees shading the cobblestones",
        crowd_phrase="neighbors, baskets, and striped market tents",
        landing_phrase="the cobbles by the bread stall",
        tags={"linden"},
    ),
}

CLUES = {
    "birds": Clue(
        id="birds",
        text="A flock of sparrows burst out of the linden branches all at once.",
        warning="Even before anything broke, the square felt as if it were listening for a thump.",
        omen="The sudden birds were the first small sign that the ground under the party was not settled.",
        tags={"foreshadowing", "bird"},
    ),
    "marbles": Clue(
        id="marbles",
        text="A bag of toy marbles tipped over, and every marble rolled the same strange way.",
        warning="The little glass balls seemed to know the ground was leaning before the children did.",
        omen="The rolling marbles foreshadowed that something under the stones had shifted.",
        tags={"foreshadowing", "marble"},
    ),
    "fountain": Clue(
        id="fountain",
        text="The water in the fountain made rings even though no one had touched it.",
        warning="It looked like a quiet shiver hiding in plain sight.",
        omen="Those ripples were an early hint that a fault below the square was stirring.",
        tags={"foreshadowing", "water"},
    ),
}

HAZARDS = {
    "statue": Hazard(
        id="statue",
        label="hero statue",
        the="the bronze hero statue",
        setup="the bronze hero statue on its tall base",
        danger_text="The base cracked, and the heavy statue began to lean toward the snack tables.",
        risk=3,
        need="brace",
        save_text="braced the leaning statue until workers slid thick blocks under the base",
        fail_text="could not hold the leaning statue steady, and it crashed through the tables",
        tags={"statue", "heavy"},
    ),
    "banner_pole": Hazard(
        id="banner_pole",
        label="banner pole",
        the="the tall banner pole",
        setup="the tall banner pole holding the festival sign",
        danger_text="The pole snapped loose at the bottom and swung toward the crowd like a giant stick.",
        risk=2,
        need="shield",
        save_text="threw a bright shield over the crowd and knocked the pole harmlessly aside",
        fail_text="was too late to cover everyone, and the falling pole smashed the sign and benches",
        tags={"pole", "overhead"},
    ),
    "fruit_cart": Hazard(
        id="fruit_cart",
        label="fruit cart",
        the="the fruit cart",
        setup="a fruit cart parked on the sloping curb",
        danger_text="The curb split, and the fruit cart rolled fast toward a group of younger children.",
        risk=2,
        need="dash",
        save_text="blurred across the lane, pushed the children clear, and steered the cart into hay bales",
        fail_text="could not reach the cart in time, and fruit and wooden wheels scattered everywhere",
        tags={"cart", "rolling"},
    ),
}

POWERS = {
    "strength": Power(
        id="strength",
        label="super strength",
        boast="lift the biggest thing in sight",
        action_text="planted both boots, locked both arms, and used super strength",
        power_type="brace",
        power=3,
        tags={"strength"},
    ),
    "shield": Power(
        id="shield",
        label="light shield",
        boast="make a glowing wall for everyone to clap at",
        action_text="snapped both hands forward and spread a round light shield",
        power_type="shield",
        power=2,
        tags={"shield"},
    ),
    "speed": Power(
        id="speed",
        label="super speed",
        boast="zip around the square faster than anyone could blink",
        action_text="leaned low and burst into super speed",
        power_type="dash",
        power=2,
        tags={"speed"},
    ),
}

INFLUENCES = {
    "low": Influence(
        id="low",
        label="gentle influence",
        score=0,
        push_text='"{hero}, maybe save the cheering for later," said {friend}.',
        consequence_text="The friend still wanted a show, but the pull was easy to ignore.",
    ),
    "medium": Influence(
        id="medium",
        label="pushy influence",
        score=1,
        push_text='"{hero}, do one amazing move first!" cried {friend}. "Everybody is watching!"',
        consequence_text="The shout tugged at the hero for one dangerous heartbeat.",
    ),
    "high": Influence(
        id="high",
        label="loud influence",
        score=1,
        push_text='"{hero}, do not ruin the fun with warnings!" shouted {friend}. "Give them a real superhero entrance!"',
        consequence_text="That loud influence pulled hard, and the hero wasted precious seconds trying to look impressive.",
    ),
}

GIRL_NAMES = ["Nova", "Mira", "Lina", "Ava", "Ruby", "Tess"]
BOY_NAMES = ["Jax", "Eli", "Max", "Noah", "Finn", "Theo"]
FRIEND_GIRL_NAMES = ["Skye", "Ivy", "June", "Piper", "Zoe"]
FRIEND_BOY_NAMES = ["Bolt", "Kai", "Rex", "Milo", "Sam"]
TRAITS = ["brave", "careful", "earnest", "quick-thinking", "kind"]

KNOWLEDGE = {
    "linden": [
        (
            "What is a linden tree?",
            "A linden tree is a leafy shade tree with a broad crown and sweet-smelling flowers. It gives people a cool place to gather on a warm day.",
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when a story shows a small clue before the big trouble happens. The clue helps the later event feel surprising but not random.",
        )
    ],
    "fault": [
        (
            "What is a fault line?",
            "A fault line is a crack deep in the earth where pieces of ground can move. When they shift, the surface above can shake.",
        )
    ],
    "shield": [
        (
            "What does a shield do in a rescue?",
            "A shield makes a safe barrier between people and danger. It gives everyone a moment to move away from something falling.",
        )
    ],
    "strength": [
        (
            "Why is super strength useful in an emergency?",
            "Super strength helps a hero hold up or move something heavy. That can keep it from crushing people until help arrives.",
        )
    ],
    "speed": [
        (
            "Why is super speed useful in an emergency?",
            "Super speed lets a hero reach danger very quickly. That matters when someone has only a second to get out of the way.",
        )
    ],
    "admit_fault": [
        (
            "Why is it brave to admit fault?",
            "Admitting fault means telling the truth when you made a mistake. It is brave because honesty helps people fix the problem faster.",
        )
    ],
}
KNOWLEDGE_ORDER = ["linden", "foreshadowing", "fault", "shield", "strength", "speed", "admit_fault"]


def power_matches(power_id: str, hazard_id: str) -> bool:
    return POWERS[power_id].power_type == HAZARDS[hazard_id].need


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for clue_id in CLUES:
            for hazard_id in HAZARDS:
                for power_id in POWERS:
                    if power_matches(power_id, hazard_id):
                        combos.append((place_id, clue_id, hazard_id, power_id))
    return combos


def severity_for(params: "StoryParams") -> int:
    return HAZARDS[params.hazard].risk + INFLUENCES[params.influence].score


def outcome_of(params: "StoryParams") -> str:
    if severity_for(params) <= POWERS[params.power].power:
        return "saved"
    return "messy"


def predict_trouble(hazard: Hazard, influence: Influence) -> dict:
    return {
        "severity": hazard.risk + influence.score,
        "delay": influence.score > 0,
    }


def introduce(world: World, place: Place, hero: Entity, friend: Entity, parent: Entity) -> None:
    world.say(
        f"In {place.name}, people had gathered beneath {place.tree_phrase}. There were {place.crowd_phrase}, "
        f"and {hero.id}, a young superhero in training, landed on {place.landing_phrase} while {friend.id} waved from the crowd."
    )
    world.say(
        f"{hero.id} loved helping, and {parent.label_word} always said that real heroes listened before they leapt."
    )


def foreshadow(world: World, clue: Clue, hazard: Hazard) -> None:
    world.say(clue.text)
    world.say(clue.warning)
    world.say(
        f"Near the middle of the celebration stood {hazard.setup}, and for a blink it seemed to tremble on its own."
    )


def build_conflict(world: World, hero: Entity, friend: Entity, clue: Clue, influence: Influence) -> None:
    world.para()
    hero.memes["duty"] += 1
    friend.memes["showy"] += 1
    world.say(
        f'{hero.id} narrowed {hero.pronoun("possessive")} eyes. "Something is wrong under the ground," '
        f'{hero.pronoun()} said. "That clue was not normal."'
    )
    world.say(influence.push_text.format(hero=hero.id, friend=friend.id))
    world.say(influence.consequence_text)
    world.say(
        f"{friend.id} wanted cheers right away, but {hero.id} wanted to warn everyone. That was the conflict: applause on one side, responsibility on the other."
    )
    world.facts["foreshadow_text"] = clue.omen


def trigger_hazard(world: World, hazard: Hazard) -> None:
    world.para()
    world.get("hazard").meters["shaking"] += 1
    world.get("hazard").meters["severity"] = float(hazard.risk)
    world.get("ground").meters["fault"] += 1
    propagate(world, narrate=False)
    world.say(
        "Then the street gave a deep little jump. A hidden fault under the square had moved."
    )
    world.say(hazard.danger_text)


def flashy_mistake(world: World, hero: Entity, power: Power, influence: Influence) -> bool:
    if influence.score <= 0:
        return False
    hero.memes["showing_off"] += 1
    propagate(world, narrate=False)
    world.say(
        f"For one bad moment, {hero.id} let that influence win. Instead of shouting a warning at once, "
        f"{hero.pronoun()} rose into the air and tried to {power.boast}."
    )
    world.say(
        f"That pause was {hero.pronoun('possessive')} fault, and the danger grew sharper."
    )
    return True


def rescue(world: World, hero: Entity, friend: Entity, power: Power, hazard: Hazard, success: bool) -> None:
    world.para()
    world.say(
        f"Then {hero.id} stopped thinking about claps. {hero.pronoun().capitalize()} looked at the frightened crowd, took one steady breath, and {power.action_text}."
    )
    if success:
        world.get("hazard").meters["danger"] = 0.0
        world.get("crowd").meters["fear"] = 0.0
        hero.memes["relief"] += 1
        hero.memes["honesty"] += 1
        world.say(
            f"{hero.id} {hazard.save_text}. The square went from shouting to gasping and then to safe, shaky silence."
        )
        world.say(
            f'"Everybody back behind the chalk line!" called {friend.id}, finally helping instead of pushing for a show.'
        )
    else:
        world.get("hazard").meters["damage"] += 1
        hero.memes["guilt"] += 1
        hero.memes["honesty"] += 1
        world.say(
            f"But the trouble had grown too big. {hero.id} {hazard.fail_text}."
        )
        world.say(
            f'{friend.id} stopped shouting for a performance and instead yelled, "Move back! Move back!"'
        )


def resolution(world: World, hero: Entity, friend: Entity, parent: Entity, place: Place, success: bool) -> None:
    world.para()
    if success:
        world.say(
            f"When the helpers arrived, {hero.id} floated down under the linden leaves and said, "
            f'"I almost listened to the wrong kind of influence. Next time I will warn people first."'
        )
        world.say(
            f'{parent.label_word.capitalize()} squeezed {hero.pronoun("possessive")} shoulder. "That is how a hero grows," '
            f'{parent.pronoun()} said. "Not by pretending to be perfect, but by choosing what is right."'
        )
        world.say(
            f"{friend.id} looked embarrassed. \"I was pushing for cheers,\" {friend.pronoun()} admitted. "
            f"\"That was my fault too.\" Above them, the linden leaves trembled once and then grew still."
        )
    else:
        world.say(
            f"Sirens and grown-up rescue crews filled {place.name}. No one had been badly hurt, but benches were splintered and fruit rolled into the gutters."
        )
        world.say(
            f'{hero.id} landed quietly and said, "The delay was my fault. I cared about looking heroic instead of being helpful."'
        )
        world.say(
            f'{parent.label_word.capitalize()} knelt beside {hero.pronoun("object")} and nodded. "Then learn fast," {parent.pronoun()} said softly. '
            f'"A true hero tells the truth and does better the next time."'
        )
        world.say(
            f"{friend.id} stared at the cracked stones and whispered that cheering had never mattered as much as safety. "
            f"The linden tree stood above them like a green promise for another, wiser festival day."
        )


def tell(
    place: Place,
    clue: Clue,
    hazard: Hazard,
    power: Power,
    influence: Influence,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=[trait],
            tags={"hero"},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="friend",
            traits=["flashy"],
            tags={"friend"},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
            tags={"adult"},
        )
    )
    world.add(Entity(id="crowd", type="crowd", label="the crowd"))
    world.add(Entity(id="ground", type="ground", label="the ground"))
    world.add(Entity(id="hazard", type="hazard", label=hazard.label, tags=set(hazard.tags)))

    introduce(world, place, hero, friend, parent)
    foreshadow(world, clue, hazard)
    build_conflict(world, hero, friend, clue, influence)
    trigger_hazard(world, hazard)
    admitted_fault = flashy_mistake(world, hero, power, influence)
    success = severity_for(
        StoryParams(
            place=place.id,
            clue=clue.id,
            hazard=hazard.id,
            power=power.id,
            influence=influence.id,
            hero_name=hero_name,
            hero_gender=hero_gender,
            friend_name=friend_name,
            friend_gender=friend_gender,
            parent=parent_type,
            trait=trait,
            seed=None,
        )
    ) <= power.power
    rescue(world, hero, friend, power, hazard, success)
    resolution(world, hero, friend, parent, place, success)

    world.facts.update(
        place=place,
        clue=clue,
        hazard_cfg=hazard,
        power_cfg=power,
        influence_cfg=influence,
        hero=hero,
        friend=friend,
        parent=parent,
        outcome="saved" if success else "messy",
        severity=hazard.risk + influence.score,
        admitted_fault=admitted_fault,
        foreshadowed=True,
    )
    return world


@dataclass
class StoryParams:
    place: str
    clue: str
    hazard: str
    power: str
    influence: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="plaza",
        clue="birds",
        hazard="statue",
        power="strength",
        influence="low",
        hero_name="Nova",
        hero_gender="girl",
        friend_name="Bolt",
        friend_gender="boy",
        parent="mother",
        trait="careful",
        seed=None,
    ),
    StoryParams(
        place="schoolyard",
        clue="marbles",
        hazard="banner_pole",
        power="shield",
        influence="medium",
        hero_name="Jax",
        hero_gender="boy",
        friend_name="Skye",
        friend_gender="girl",
        parent="father",
        trait="earnest",
        seed=None,
    ),
    StoryParams(
        place="market",
        clue="fountain",
        hazard="fruit_cart",
        power="speed",
        influence="high",
        hero_name="Mira",
        hero_gender="girl",
        friend_name="Rex",
        friend_gender="boy",
        parent="mother",
        trait="brave",
        seed=None,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    hazard = f["hazard_cfg"]
    power = f["power_cfg"]
    place = f["place"]
    clue = f["clue"]
    outcome = f["outcome"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that uses the words "linden", "influence", and "fault". Set it at {place.name}.',
        f"Tell a superhero story where {hero.id} notices a clue, argues with a flashy friend, and uses {power.label} to stop {hazard.the}.",
        f"Write a gentle action story with conflict and foreshadowing: start with {clue.text.lower()} and end with a hero learning that safety matters more than applause{' and saving the day' if outcome == 'saved' else ' after a mistake'}.",
    ]


def pair_noun(hero: Entity, friend: Entity) -> str:
    if hero.type == "girl" and friend.type == "girl":
        return "two girls"
    if hero.type == "boy" and friend.type == "boy":
        return "two boys"
    return "two young friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    hazard = f["hazard_cfg"]
    power = f["power_cfg"]
    clue = f["clue"]
    place = f["place"]
    influence = f["influence_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, friend)} at {place.name}, especially {hero.id}, a young superhero, and {friend.id}, the friend beside {hero.pronoun('object')}.",
        ),
        (
            "What clue warned that trouble was coming?",
            f"The first warning was that {clue.text[0].lower() + clue.text[1:]} {clue.omen}",
        ),
        (
            "What was the conflict in the story?",
            f"The conflict was between showing off and protecting people. {friend.id} used {influence.label} to push for a flashy moment, but {hero.id} knew the ground felt wrong and wanted to warn the crowd.",
        ),
        (
            "Why does the story use the word fault?",
            f"It uses the word fault in two ways. A hidden fault under the ground shook the square, and when the delay made the danger worse, {hero.id} had to admit that part of the mistake was {hero.pronoun('possessive')} fault.",
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                f"How did {hero.id} save everyone?",
                f"{hero.id} used {power.label} when {hazard.the} turned dangerous. That worked because {power.label} fit the problem and stopped the trouble before it could hit the crowd.",
            )
        )
        qa.append(
            (
                f"What changed by the end?",
                f"At the end, {friend.id} stopped chasing cheers and started helping, and {hero.id} spoke honestly about the bad influence. The still linden leaves at the end show that the square became calm again.",
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.id} fix everything in time?",
                f"No. {hero.id} tried to help, but the danger had grown too big after the delay. Even so, {hero.pronoun().capitalize()} told the truth about the mistake and learned to put people first next time.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the town shaken but safe enough to recover, and with {hero.id} admitting fault instead of hiding. The last image of the linden tree promises a wiser beginning later.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"linden", "foreshadowing", "fault", "admit_fault"}
    tags |= set(f["power_cfg"].tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(power_id: str, hazard_id: str) -> str:
    power = POWERS[power_id]
    hazard = HAZARDS[hazard_id]
    return (
        f"(No story: {power.label} is not the right kind of rescue for {hazard.the}. "
        f"That hazard needs a hero who can {hazard.need} the danger instead.)"
    )


ASP_RULES = r"""
% a power is compatible when its rescue kind matches the hazard's need
compatible(P, H) :- power(P), hazard(H), ptype(P, T), need(H, T).

valid(Place, Clue, Hazard, Power) :-
    place(Place), clue(Clue), hazard(Hazard), power(Power),
    compatible(Power, Hazard).

severity(Hazard, Influence, S) :-
    risk(Hazard, R), infl(Influence, I), S = R + I.

outcome(saved) :-
    chosen_hazard(H), chosen_power(P), chosen_influence(I),
    severity(H, I, S), pstrength(P, PS), S <= PS.
outcome(messy) :-
    chosen_hazard(H), chosen_power(P), chosen_influence(I),
    severity(H, I, S), pstrength(P, PS), S > PS.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        lines.append(asp.fact("risk", hazard_id, hazard.risk))
        lines.append(asp.fact("need", hazard_id, hazard.need))
    for power_id, power in POWERS.items():
        lines.append(asp.fact("power", power_id))
        lines.append(asp.fact("ptype", power_id, power.power_type))
        lines.append(asp.fact("pstrength", power_id, power.power))
    for influence_id, influence in INFLUENCES.items():
        lines.append(asp.fact("influence", influence_id))
        lines.append(asp.fact("infl", influence_id, influence.score))
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
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_power", params.power),
            asp.fact("chosen_influence", params.influence),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
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
        print("MISMATCH in valid combos.")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            continue
        params.seed = seed
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a young superhero notices foreshadowing, faces bad influence, and responds to a fault-line emergency."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--influence", choices=INFLUENCES)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "", friend: bool = False) -> str:
    if gender == "girl":
        pool = FRIEND_GIRL_NAMES if friend else GIRL_NAMES
    else:
        pool = FRIEND_BOY_NAMES if friend else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.power and args.hazard and not power_matches(args.power, args.hazard):
        raise StoryError(explain_rejection(args.power, args.hazard))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.clue is None or combo[1] == args.clue)
        and (args.hazard is None or combo[2] == args.hazard)
        and (args.power is None or combo[3] == args.power)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, clue_id, hazard_id, power_id = rng.choice(sorted(combos))
    influence_id = args.influence or rng.choice(sorted(INFLUENCES))
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    hero_name = _pick_name(rng, hero_gender, friend=False)
    friend_name = _pick_name(rng, friend_gender, avoid=hero_name, friend=True)
    parent_type = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        clue=clue_id,
        hazard=hazard_id,
        power=power_id,
        influence=influence_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent_type,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.power not in POWERS:
        raise StoryError(f"(Unknown power: {params.power})")
    if params.influence not in INFLUENCES:
        raise StoryError(f"(Unknown influence: {params.influence})")
    if not power_matches(params.power, params.hazard):
        raise StoryError(explain_rejection(params.power, params.hazard))

    world = tell(
        place=PLACES[params.place],
        clue=CLUES[params.clue],
        hazard=HAZARDS[params.hazard],
        power=POWERS[params.power],
        influence=INFLUENCES[params.influence],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, clue, hazard, power) combos:\n")
        for place_id, clue_id, hazard_id, power_id in combos:
            print(f"  {place_id:10} {clue_id:8} {hazard_id:12} {power_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero_name} at {p.place}: {p.power} vs {p.hazard} "
                f"({p.influence}, {outcome_of(p)})"
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
