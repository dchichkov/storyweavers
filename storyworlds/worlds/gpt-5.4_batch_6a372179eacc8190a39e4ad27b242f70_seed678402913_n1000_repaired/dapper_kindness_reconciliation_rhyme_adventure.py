#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dapper_kindness_reconciliation_rhyme_adventure.py
==============================================================================

A standalone storyworld for a small adventure tale about a quarrel, a kind
repair, and a rhyming reconciliation.

Premise
-------
Two children set out on a tiny adventure to follow a clue and find a prize.
One child comes dressed in a dapper explorer outfit. The other child makes an
unkind remark, the dapper child walks ahead with hurt feelings, and an obstacle
blocks the path. The only way the adventure can truly continue is if the first
child helps in a sensible physical way *and* offers a gentle rhyming apology.
That combination restores trust, lets the children reconcile, and leads to a
final shared discovery.

The world model tracks:
- physical state: blocked path, gear use, progress, possession
- emotional state: hurt, worry, kindness, trust, reconciliation

Reasonableness constraint
-------------------------
Not every tool fits every obstacle. A lantern does not bridge a stream, and a
plank does not light a dark tunnel. This world only generates stories where the
chosen gear can honestly solve the obstacle.

Run it
------
    python storyworlds/worlds/gpt-5.4/dapper_kindness_reconciliation_rhyme_adventure.py
    python storyworlds/worlds/gpt-5.4/dapper_kindness_reconciliation_rhyme_adventure.py --setting garden --obstacle stream
    python storyworlds/worlds/gpt-5.4/dapper_kindness_reconciliation_rhyme_adventure.py --gear lantern --obstacle stream
    python storyworlds/worlds/gpt-5.4/dapper_kindness_reconciliation_rhyme_adventure.py --all
    python storyworlds/worlds/gpt-5.4/dapper_kindness_reconciliation_rhyme_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/dapper_kindness_reconciliation_rhyme_adventure.py --verify
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


@dataclass
class Setting:
    id: str
    place: str
    trail: str
    clue_place: str
    prize: str
    opening: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    sentence: str
    need: str
    failure: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    solves: set[str] = field(default_factory=set)
    use_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ApologyStyle:
    id: str
    sense: int
    kind: bool
    rhyme_line1: str
    rhyme_line2: str
    qa_text: str
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


def _r_hurt_distance(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["hurt"] >= THRESHOLD:
        sig = ("distance", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["ahead"] += 1
            friend.memes["worry"] += 1
            out.append("__distance__")
    return out


def _r_help_progress(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.meters["blocked"] >= THRESHOLD and friend.meters["helping"] >= THRESHOLD:
        sig = ("progress", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["blocked"] = 0.0
            hero.meters["progress"] += 1
            friend.meters["progress"] += 1
            hero.memes["relief"] += 1
            friend.memes["kindness"] += 1
            out.append("__helped__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if friend.memes["apologized"] >= THRESHOLD and friend.meters["helping"] >= THRESHOLD:
        sig = ("reconcile", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["hurt"] = 0.0
            hero.memes["trust"] += 1
            friend.memes["trust"] += 1
            hero.memes["reconciled"] += 1
            friend.memes["reconciled"] += 1
            out.append("__reconciled__")
    return out


CAUSAL_RULES = [
    Rule(name="hurt_distance", tag="social", apply=_r_hurt_distance),
    Rule(name="help_progress", tag="physical", apply=_r_help_progress),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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


def gear_fits(obstacle: Obstacle, gear: Gear) -> bool:
    return obstacle.id in gear.solves


def sensible_apologies() -> list[ApologyStyle]:
    return [a for a in APOLOGIES.values() if a.sense >= SENSE_MIN and a.kind]


def explain_rejection(obstacle: Obstacle, gear: Gear) -> str:
    return (
        f"(No story: {gear.phrase} does not solve {obstacle.label}. "
        f"{obstacle.need.capitalize()}, so pick gear that truly fits the obstacle.)"
    )


def explain_apology(aid: str) -> str:
    ap = APOLOGIES[aid]
    better = ", ".join(sorted(a.id for a in sensible_apologies()))
    return (
        f"(Refusing apology '{aid}': it is not kind enough for reconciliation "
        f"(sense={ap.sense} < {SENSE_MIN} or kind={ap.kind}). Try: {better}.)"
    )


def introduce(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    world.say(
        f"One bright afternoon, {hero.id} and {friend.id} set out on an adventure in "
        f"{setting.place}. {setting.opening}"
    )
    world.say(
        f"{hero.id} wore a dapper {hero.attrs['outfit']}, with a little bow at the neck, "
        f"and held the clue card as if it were a captain's map."
    )
    world.say(
        f"Together they hurried along {setting.trail}, looking for the hidden {setting.prize}."
    )


def first_clue(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"At {setting.clue_place}, they found the first clue tucked under a stone: "
        f'"Take the brave path, take the bright time, and listen well for a friendly rhyme."'
    )


def tease(world: World, friend: Entity, hero: Entity) -> None:
    friend.memes["boast"] += 1
    hero.memes["hurt"] += 1
    world.say(
        f'{friend.id} laughed a little too loudly and said, '
        f'"That dapper {hero.attrs["outfit_noun"]} looks made for a parade, not a quest."'
    )
    world.say(
        f"The words landed with a thud. {hero.id}'s smile folded up, and {hero.pronoun()} walked ahead without answering."
    )
    propagate(world, narrate=False)


def obstacle_strikes(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.meters["blocked"] += 1
    world.say(
        f"A moment later, the path changed. {obstacle.sentence}"
    )
    world.say(
        f"{hero.id} stopped short, clutching the clue card. {obstacle.failure}"
    )


def regret(world: World, friend: Entity, hero: Entity, obstacle: Obstacle) -> None:
    friend.memes["regret"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"Seeing {hero.id} stuck and silent, {friend.id} felt the unkind joke turn heavy inside {friend.pronoun('object')}."
    )
    world.say(
        f"{friend.pronoun().capitalize()} understood that the real trouble was not only {obstacle.label}; it was the hurt {friend.pronoun()} had caused."
    )


def use_gear(world: World, friend: Entity, hero: Entity, gear: Gear) -> None:
    friend.meters["helping"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{friend.id} hurried forward with {gear.phrase} and {gear.use_text}"
    )
    world.say(
        f'"Here," {friend.pronoun()} said, "let me help you first."'
    )


def apologize(world: World, friend: Entity, apology: ApologyStyle) -> None:
    if apology.kind and apology.sense >= SENSE_MIN:
        friend.memes["apologized"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {friend.id} took a breath and spoke in a soft rhyme:"
    )
    world.say(
        f'"{apology.rhyme_line1}"'
    )
    world.say(
        f'"{apology.rhyme_line2}"'
    )


def reconcile(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    world.say(
        f"{hero.id} looked at {friend.id}, then at the steady helping hand. The hurt in {hero.pronoun('possessive')} face eased."
    )
    world.say(
        f'"Thank you for helping, and thank you for saying it kindly," {hero.pronoun()} said.'
    )
    world.say(
        f"They walked side by side again, and the adventure felt wide and bright once more."
    )
    world.say(
        f"Behind the next bend they found the hidden {setting.prize}, shining as if it had been waiting for friends who stayed friends."
    )
    world.say(
        '"Kind and brave, kind and brave," they chanted together, "that is how we find our way."'
    )


def tell(
    setting: Setting,
    obstacle: Obstacle,
    gear: Gear,
    apology: ApologyStyle,
    hero_name: str = "Milo",
    hero_gender: str = "boy",
    friend_name: str = "Nia",
    friend_gender: str = "girl",
    outfit: str = "velvet explorer jacket",
    outfit_noun: str = "jacket",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            attrs={"outfit": outfit, "outfit_noun": outfit_noun},
            tags={"dapper"},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="friend",
        )
    )
    world.add(Entity(id="gear", type="tool", label=gear.label, phrase=gear.phrase, tags=set(gear.tags)))
    world.add(Entity(id="obstacle", type="obstacle", label=obstacle.label, tags=set(obstacle.tags)))

    hero.memes["trust"] = 1.0
    friend.memes["trust"] = 1.0

    introduce(world, hero, friend, setting)
    first_clue(world, hero, friend, setting)

    world.para()
    tease(world, friend, hero)
    obstacle_strikes(world, hero, obstacle)
    regret(world, friend, hero, obstacle)

    world.para()
    use_gear(world, friend, hero, gear)
    apologize(world, friend, apology)
    reconcile(world, hero, friend, setting)

    world.facts.update(
        hero=hero,
        friend=friend,
        setting=setting,
        obstacle=obstacle,
        gear=gear,
        apology=apology,
        outcome="reconciled" if hero.memes["reconciled"] >= THRESHOLD else "stuck",
        prize_found=hero.memes["reconciled"] >= THRESHOLD and hero.meters["blocked"] < THRESHOLD,
    )
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the old garden behind the house",
        trail="the mossy stepping path",
        clue_place="the crooked birdbath",
        prize="silver acorn",
        opening="A row of tall beans leaned like jungle trees, and every leaf seemed to hide a secret.",
        tags={"garden", "adventure"},
    ),
    "attic": Setting(
        id="attic",
        place="the attic under the sloping roof",
        trail="the narrow trail between trunks and quilts",
        clue_place="the brass telescope by the window",
        prize="star badge",
        opening="Dusty trunks rose like cliffs, and old blankets draped down like cave curtains.",
        tags={"attic", "adventure"},
    ),
    "shore": Setting(
        id="shore",
        place="the windy shore by the dunes",
        trail="the shell-marked path between the grasses",
        clue_place="the weathered driftwood log",
        prize="shell key",
        opening="The dunes stood like golden hills, and the sea kept whispering as if it knew the answer already.",
        tags={"shore", "adventure"},
    ),
}

OBSTACLES = {
    "thorns": Obstacle(
        id="thorns",
        label="a thorn patch",
        sentence="A patch of brambles scratched across the trail, all hooks and twigs.",
        need="something thick to press the thorns aside",
        failure="The brambles snagged at the path and would not let the way open.",
        tags={"thorns", "careful"},
    ),
    "stream": Obstacle(
        id="stream",
        label="a little stream",
        sentence="A little stream cut across the trail, chuckling over slick stones.",
        need="a bridge or steady way across",
        failure="The stones were too slippery to trust with the clue card in hand.",
        tags={"stream", "water"},
    ),
    "dark": Obstacle(
        id="dark",
        label="a dark tunnel of leaves",
        sentence="A tunnel of tangled leaves swallowed the light ahead until the path looked like evening.",
        need="a light to see the way",
        failure="The shadows were so deep that even the clue card seemed to disappear.",
        tags={"dark", "light"},
    ),
}

GEAR = {
    "cloak": Gear(
        id="cloak",
        label="cloak",
        phrase="a little adventure cloak",
        solves={"thorns"},
        use_text="spread it over the brambles so the thorns bent down and made a safe gap.",
        tags={"cloak", "help"},
    ),
    "gloves": Gear(
        id="gloves",
        label="gloves",
        phrase="a pair of sturdy garden gloves",
        solves={"thorns"},
        use_text="pulled them on and gently bent the thorny branches back until the trail opened.",
        tags={"gloves", "help"},
    ),
    "plank": Gear(
        id="plank",
        label="plank",
        phrase="a smooth old plank",
        solves={"stream"},
        use_text="laid it from one bank to the other so the stream suddenly had a tiny bridge.",
        tags={"bridge", "help"},
    ),
    "lantern": Gear(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        solves={"dark"},
        use_text="clicked it on, and a warm circle of light rolled down the tunnel of leaves.",
        tags={"lantern", "light", "help"},
    ),
    "glowjar": Gear(
        id="glowjar",
        label="glow jar",
        phrase="a glow jar full of firefly-like lights",
        solves={"dark"},
        use_text="lifted it high, and the path ahead woke up in a soft green shimmer.",
        tags={"glow", "light", "help"},
    ),
}

APOLOGIES = {
    "rhyme": ApologyStyle(
        id="rhyme",
        sense=3,
        kind=True,
        rhyme_line1="I teased your style, and that was wrong; a friend should help your heart stay strong.",
        rhyme_line2="Your dapper coat is brave and bright; please let me make our quarrel right.",
        qa_text="gave a gentle rhyming apology and admitted the teasing was wrong",
        tags={"rhyme", "kindness", "apology"},
    ),
    "short_rhyme": ApologyStyle(
        id="short_rhyme",
        sense=2,
        kind=True,
        rhyme_line1="I was mean, and that was wrong; friends are kinder, brave, and strong.",
        rhyme_line2="Will you walk this quest with me, side by side, from clue to key?",
        qa_text="used a short kind rhyme to say sorry and ask to be friends again",
        tags={"rhyme", "kindness", "apology"},
    ),
    "shrug": ApologyStyle(
        id="shrug",
        sense=0,
        kind=False,
        rhyme_line1="Well, the path was rough today.",
        rhyme_line2="Let's just go. No more to say.",
        qa_text="mumbled without really saying sorry",
        tags={"unkind"},
    ),
}

GIRL_NAMES = ["Nia", "Lila", "Zoe", "Ava", "Mira", "Ruby", "Tess", "Nora"]
BOY_NAMES = ["Milo", "Ben", "Leo", "Arlo", "Finn", "Theo", "Jude", "Max"]
OUTFITS = [
    ("velvet explorer jacket", "jacket"),
    ("striped adventure coat", "coat"),
    ("smart little cape", "cape"),
]


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    gear: str
    apology: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    outfit: str
    outfit_noun: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for oid, obstacle in OBSTACLES.items():
            for gid, gear in GEAR.items():
                if gear_fits(obstacle, gear):
                    combos.append((sid, oid, gid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    setting = f["setting"]
    obstacle = f["obstacle"]
    gear = f["gear"]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the word "dapper" and ends with reconciliation.',
        f"Tell a gentle adventure where {friend.id} hurts {hero.id}'s feelings, then helps {hero.pronoun('object')} across {obstacle.label} with {gear.phrase} and says sorry in rhyme.",
        f"Write a child-facing quest in {setting.place} where kindness repairs a quarrel and helps two friends keep going together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    setting = f["setting"]
    obstacle = f["obstacle"]
    gear = f["gear"]
    apology = f["apology"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two young adventurers, {hero.id} and {friend.id}. They set out together in {setting.place} to look for the hidden {setting.prize}.",
        ),
        (
            f"What made {hero.id} look dapper?",
            f"{hero.id} wore a dapper {hero.attrs['outfit']}. The neat outfit made {hero.pronoun('object')} look ready for a grand little quest.",
        ),
        (
            f"Why did {hero.id}'s feelings get hurt?",
            f"{friend.id} laughed at {hero.id}'s outfit and said it looked better for a parade than an adventure. That unkind joke made {hero.id} go quiet and walk ahead with hurt feelings.",
        ),
        (
            f"What problem stopped the adventure?",
            f"The children ran into {obstacle.label}. {obstacle.failure[0].upper()}{obstacle.failure[1:]}",
        ),
        (
            f"How did {friend.id} help?",
            f"{friend.id} used {gear.phrase} to solve the obstacle. That practical help showed kindness with actions, not only words.",
        ),
        (
            f"How did {friend.id} make peace with {hero.id}?",
            f"{friend.id} {apology.qa_text}. The apology mattered because it named the wrong and came with real help at the same time.",
        ),
        (
            "How did the story end?",
            f"The children reconciled, walked side by side again, and found the hidden {setting.prize}. The ending shows that kindness helped both the friendship and the adventure move forward.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words have matching end sounds, like 'bright' and 'light.' Rhymes can make words feel musical and easy to remember.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing words or actions that help someone feel safe, cared for, or included. It can be as small as helping, listening, or saying sorry.",
        )
    ],
    "reconciliation": [
        (
            "What does reconciliation mean?",
            "Reconciliation means people make peace after a hurt or quarrel. They listen, repair the hurt, and become friendly again.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern makes light so you can see in dim places. It helps people move safely when the path is dark.",
        )
    ],
    "bridge": [
        (
            "Why do people use a bridge or plank over water?",
            "A bridge or plank gives you a steady way to cross from one side to the other. It keeps your feet out of the water and helps you avoid slipping.",
        )
    ],
    "thorns": [
        (
            "Why are thorns tricky on a path?",
            "Thorns are sharp, so they can scratch skin or catch clothes. That is why people move carefully and use something sturdy to help.",
        )
    ],
    "dapper": [
        (
            "What does dapper mean?",
            "Dapper means neat, tidy, and a little dressy. Someone who looks dapper seems especially smart and well put together.",
        )
    ],
}
KNOWLEDGE_ORDER = ["dapper", "kindness", "reconciliation", "rhyme", "lantern", "bridge", "thorns"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"dapper", "kindness", "reconciliation", "rhyme"}
    obstacle = world.facts["obstacle"]
    gear = world.facts["gear"]
    tags |= set(obstacle.tags) | set(gear.tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        obstacle="thorns",
        gear="cloak",
        apology="rhyme",
        hero_name="Milo",
        hero_gender="boy",
        friend_name="Nia",
        friend_gender="girl",
        outfit="velvet explorer jacket",
        outfit_noun="jacket",
    ),
    StoryParams(
        setting="attic",
        obstacle="dark",
        gear="lantern",
        apology="short_rhyme",
        hero_name="Ruby",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        outfit="striped adventure coat",
        outfit_noun="coat",
    ),
    StoryParams(
        setting="shore",
        obstacle="stream",
        gear="plank",
        apology="rhyme",
        hero_name="Theo",
        hero_gender="boy",
        friend_name="Lila",
        friend_gender="girl",
        outfit="smart little cape",
        outfit_noun="cape",
    ),
]


ASP_RULES = r"""
fits(O, G) :- obstacle(O), gear(G), solves(G, O).
sensible(A) :- apology(A), sense(A, S), sense_min(M), S >= M, kind(A).
valid(S, O, G) :- setting(S), obstacle(O), gear(G), fits(O, G).

reconciled :- chosen_gear(G), chosen_obstacle(O), fits(O, G),
              chosen_apology(A), sensible(A).
outcome(reconciled) :- reconciled.
outcome(stuck) :- not reconciled.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for oid in sorted(gear.solves):
            lines.append(asp.fact("solves", gid, oid))
    for aid, apology in APOLOGIES.items():
        lines.append(asp.fact("apology", aid))
        lines.append(asp.fact("sense", aid, apology.sense))
        if apology.kind:
            lines.append(asp.fact("kind", aid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_gear", params.gear),
            asp.fact("chosen_apology", params.apology),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    gear = GEAR[params.gear]
    apology = APOLOGIES[params.apology]
    ok = gear_fits(obstacle, gear) and apology.sense >= SENSE_MIN and apology.kind
    return "reconciled" if ok else "stuck"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sensible = set(asp_sensible())
    python_sensible = {a.id for a in sensible_apologies()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible apologies match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible apologies: clingo={sorted(clingo_sensible)} "
            f"python={sorted(python_sensible)}"
        )

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a dapper adventure, a quarrel, a kind repair, and a rhyme."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--apology", choices=APOLOGIES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.gear:
        obstacle = OBSTACLES[args.obstacle]
        gear = GEAR[args.gear]
        if not gear_fits(obstacle, gear):
            raise StoryError(explain_rejection(obstacle, gear))
    if args.apology and args.apology in APOLOGIES and APOLOGIES[args.apology].sense < SENSE_MIN:
        raise StoryError(explain_apology(args.apology))
    if args.apology and args.apology in APOLOGIES and not APOLOGIES[args.apology].kind:
        raise StoryError(explain_apology(args.apology))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.gear is None or combo[2] == args.gear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, obstacle_id, gear_id = rng.choice(sorted(combos))
    apology_id = args.apology or rng.choice(sorted(a.id for a in sensible_apologies()))
    hero_name, hero_gender = _pick_name(rng)
    friend_name, friend_gender = _pick_name(rng, avoid=hero_name)
    outfit, outfit_noun = rng.choice(OUTFITS)

    return StoryParams(
        setting=setting_id,
        obstacle=obstacle_id,
        gear=gear_id,
        apology=apology_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        outfit=outfit,
        outfit_noun=outfit_noun,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.gear not in GEAR:
        raise StoryError(f"(Unknown gear: {params.gear})")
    if params.apology not in APOLOGIES:
        raise StoryError(f"(Unknown apology: {params.apology})")

    obstacle = OBSTACLES[params.obstacle]
    gear = GEAR[params.gear]
    apology = APOLOGIES[params.apology]
    if not gear_fits(obstacle, gear):
        raise StoryError(explain_rejection(obstacle, gear))
    if apology.sense < SENSE_MIN or not apology.kind:
        raise StoryError(explain_apology(params.apology))

    world = tell(
        setting=SETTINGS[params.setting],
        obstacle=obstacle,
        gear=gear,
        apology=apology,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        outfit=params.outfit,
        outfit_noun=params.outfit_noun,
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
        combos = asp_valid_combos()
        print(f"sensible apologies: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (setting, obstacle, gear) combos:\n")
        for setting_id, obstacle_id, gear_id in combos:
            print(f"  {setting_id:8} {obstacle_id:8} {gear_id}")
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
            header = f"### {p.hero_name} & {p.friend_name}: {p.setting}, {p.obstacle}, {p.gear}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
