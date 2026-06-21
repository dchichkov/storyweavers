#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/varsity_lesson_learned_twist_fairy_tale.py
=====================================================================

A standalone storyworld for a fairy-tale sports story with a lesson and a twist:
a child hurries toward the royal varsity games, meets a humble stranger beside an
obstacle, and learns that kindness matters more than showing off.

The world is intentionally small and constraint-checked:

* A helper belongs with one obstacle type. The story refuses mismatched pairs.
* The hero can choose to help or rush.
* In the twist, the shabby helper is revealed to be the secret royal judge of the
  varsity games.
* Helping leads to the strongest ending; rushing leads to a gentler, humbled ending.
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

# Make the shared result containers importable when this script is run directly:
# add the package dir (storyworlds/) to sys.path from this nested world folder.
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "princess", "woman"}
        male = {"boy", "father", "king", "prince", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Realm:
    id: str
    meadow: str
    lane: str
    opening: str
    ending: str


@dataclass
class HelperCfg:
    id: str
    label: str
    type: str
    first_seen: str
    need: str
    small_task: str
    magic_help: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObstacleCfg:
    id: str
    label: str
    block: str
    stumble: str
    helper_id: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PrizeCfg:
    id: str
    label: str
    phrase: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    realm: str
    helper: str
    obstacle: str
    choice: str
    prize: str
    hero_name: str
    hero_gender: str
    teammate_name: str
    teammate_gender: str
    crown: str
    trait: str
    seed: Optional[int] = None


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


def _r_kindness_opens_help(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    obstacle = world.get("obstacle")
    if hero.memes["kindness"] < THRESHOLD:
        return []
    sig = ("opened", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["opened"] += 1
    helper.memes["trust"] += 1
    return []


def _r_pride_causes_delay(world: World) -> list[str]:
    hero = world.get("hero")
    obstacle = world.get("obstacle")
    if hero.memes["pride"] < THRESHOLD:
        return []
    sig = ("delayed", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["delay"] += 1
    hero.memes["worry"] += 1
    obstacle.meters["still_blocked"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="kindness_opens_help", tag="social", apply=_r_kindness_opens_help),
    Rule(name="pride_causes_delay", tag="social", apply=_r_pride_causes_delay),
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
        for sent in produced:
            world.say(sent)
    return produced


REALMS = {
    "moonmeadow": Realm(
        id="moonmeadow",
        meadow="Moonmeadow",
        lane="the silver running lane beside the reeds",
        opening="where dew shone like little stars",
        ending="under lantern-light and a soft white moon",
    ),
    "rosefield": Realm(
        id="rosefield",
        meadow="Rosefield",
        lane="the red-clay track curling around the rose hedge",
        opening="where bees hummed over the blossoms",
        ending="beneath banners that fluttered like petals",
    ),
    "thistledown": Realm(
        id="thistledown",
        meadow="Thistledown Green",
        lane="the springy grass path near the old willow",
        opening="where dandelion fluff drifted in the breeze",
        ending="while gold light lay warm on the grass",
    ),
}

HELPERS = {
    "frog": HelperCfg(
        id="frog",
        label="a mossy frog",
        type="frog",
        first_seen="on a flat stone by the brook",
        need="armfuls of rushes had blown out of place",
        small_task="set the rushes back in a neat little raft",
        magic_help="croaked a bright spell and made lily pads leap into a swift green bridge",
        reveal="the frog shook off a ragged leaf-cloak and stood tall as the royal bridge judge",
        tags={"frog", "bridge", "kindness"},
    ),
    "owl": HelperCfg(
        id="owl",
        label="a dusty owl",
        type="owl",
        first_seen="beneath a bent goal-post of ash wood",
        need="the scoreboard ribbons had snarled in the wind",
        small_task="untangle the ribbons and tie them straight",
        magic_help="beat wide wings and turned the ribbons into a shining wind-road",
        reveal="the owl lifted a plain hood and showed the moon-badge of the royal score judge",
        tags={"owl", "ribbons", "kindness"},
    ),
    "mole": HelperCfg(
        id="mole",
        label="a little mole",
        type="mole",
        first_seen="half out of a hill of soft brown earth",
        need="heavy marker stones had rolled across the way",
        small_task="heave the marker stones back into a proper line",
        magic_help="patted the ground and opened a smooth tunnel path straight to the field",
        reveal="the mole brushed off the dirt and bowed as the royal course judge",
        tags={"mole", "path", "kindness"},
    ),
}

OBSTACLES = {
    "brook": ObstacleCfg(
        id="brook",
        label="the brook",
        block="a brook that had nibbled the stepping-stones away",
        stumble="the bank was slick, and the team lost precious moments skidding in the mud",
        helper_id="frog",
        tags={"water", "bridge"},
    ),
    "windgate": ObstacleCfg(
        id="windgate",
        label="the windy gate",
        block="a windy gate whose streamers had wrapped themselves into a knot",
        stumble="the gate slapped and tangled around their ankles until they had to stop",
        helper_id="owl",
        tags={"wind", "ribbons"},
    ),
    "stonepath": ObstacleCfg(
        id="stonepath",
        label="the stone path",
        block="a stone path choked with marker rocks",
        stumble="the stones rolled underfoot, and the team had to pick their way step by step",
        helper_id="mole",
        tags={"stones", "path"},
    ),
}

PRIZES = {
    "ribbon": PrizeCfg(
        id="ribbon",
        label="blue varsity ribbon",
        phrase="a blue varsity ribbon sewn with tiny silver stars",
        ending_image="the ribbon shone on the hero's chest like a bit of morning sky",
        tags={"ribbon", "varsity"},
    ),
    "sash": PrizeCfg(
        id="sash",
        label="scarlet varsity sash",
        phrase="a scarlet varsity sash with a golden acorn clasp",
        ending_image="the sash lay across the hero's shoulder in a bright, brave stripe",
        tags={"sash", "varsity"},
    ),
    "bell": PrizeCfg(
        id="bell",
        label="varsity bell medal",
        phrase="a varsity bell medal on a braided green cord",
        ending_image="the medal chimed softly each time the hero laughed",
        tags={"bell", "varsity"},
    ),
}

CHOICES = ["help", "rush"]
CROWNS = ["queen", "king"]
TRAITS = ["eager", "swift", "proud", "hopeful", "spirited", "bold"]
GIRL_NAMES = ["Lila", "Mira", "Nora", "Elsa", "Poppy", "Tessa", "Wren"]
BOY_NAMES = ["Finn", "Owen", "Theo", "Milo", "Rowan", "Jasper", "Hugo"]


def valid_pair(helper_id: str, obstacle_id: str) -> bool:
    return helper_id in HELPERS and obstacle_id in OBSTACLES and OBSTACLES[obstacle_id].helper_id == helper_id


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for helper_id in sorted(HELPERS):
        for obstacle_id in sorted(OBSTACLES):
            if valid_pair(helper_id, obstacle_id):
                combos.append((helper_id, obstacle_id))
    return combos


def explain_rejection(helper_id: str, obstacle_id: str) -> str:
    if helper_id not in HELPERS:
        return f"(No story: unknown helper '{helper_id}'.)"
    if obstacle_id not in OBSTACLES:
        return f"(No story: unknown obstacle '{obstacle_id}'.)"
    expected = OBSTACLES[obstacle_id].helper_id
    return (
        f"(No story: {HELPERS[helper_id].label} does not fit {OBSTACLES[obstacle_id].label}. "
        f"That obstacle belongs with {HELPERS[expected].label}, whose task and magic can really solve it.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "champion" if params.choice == "help" else "humbled"


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def setup_story(world: World, realm: Realm, prize: PrizeCfg, crown: str, hero: Entity, teammate: Entity) -> None:
    hero.memes["hope"] += 1
    teammate.memes["hope"] += 1
    world.say(
        f"In the little kingdom by {realm.meadow}, where children trained {realm.opening}, "
        f"there was a grand day called the Royal Varsity Run."
    )
    world.say(
        f"{hero.id}, a {next(iter([t for t in hero.attrs.get('traits', []) if t != 'little']), hero.type)} {hero.type}, "
        f"longed to win {prize.phrase} from the {crown}."
    )
    world.say(
        f"At sunrise, {hero.id} and {teammate.id} set off for {realm.lane}, carrying their team baton and bright racing hopes."
    )


def boast(world: World, hero: Entity, teammate: Entity) -> None:
    hero.memes["pride"] += 0.5
    world.say(
        f'"If my feet are fast enough," {hero.id} said, "we shall fly past everyone before the trumpets finish blowing."'
    )
    world.say(
        f"{teammate.id} smiled, but {teammate.pronoun()} held the baton carefully, as if a team should move with more than speed."
    )


def meet_obstacle(world: World, obstacle: ObstacleCfg, helper: HelperCfg) -> None:
    world.say(
        f"But before they reached the field, they found {obstacle.block}. "
        f"There sat {helper.label} {helper.first_seen}."
    )
    world.say(
        f'The stranger blinked and said, "I would be grateful for help. {helper.need}. '
        f'Will you {helper.small_task}?"'
    )


def choose_help(world: World, hero: Entity, teammate: Entity, helper: HelperCfg, obstacle_ent: Entity) -> None:
    hero.memes["kindness"] += 1
    teammate.memes["trust"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} looked at the waiting field, then at the small, troubled stranger. "
        f"At last {hero.pronoun()} knelt and helped {helper.small_task}."
    )
    world.say(
        f"{teammate.id} joined in at once, and soon the work was done with muddy hands and cheerful breaths."
    )
    if obstacle_ent.meters["opened"] >= THRESHOLD:
        world.say(
            f"Then the stranger {helper.magic_help}. In one blink, the blocked way opened before them."
        )


def choose_rush(world: World, hero: Entity, teammate: Entity, obstacle: ObstacleCfg) -> None:
    hero.memes["pride"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} clutched the baton and answered, "I cannot stop for little chores. The varsity ribbon waits for no one."'
    )
    world.say(
        f"{hero.id} tugged {teammate.id} onward, but {obstacle.stumble}"
    )


def reveal_twist(world: World, helper: HelperCfg, crown: str) -> None:
    helper_ent = world.get("helper")
    helper_ent.memes["revealed"] += 1
    world.say(
        f"Just then, a laugh as soft as a bell rang out. {helper.reveal}."
    )
    world.say(
        f'"I was sent by the {crown} to watch who was ready for the varsity honor," the judge said.'
    )


def reward_help(world: World, hero: Entity, teammate: Entity, prize: PrizeCfg) -> None:
    hero.meters["won"] += 1
    hero.memes["joy"] += 1
    hero.memes["lesson"] += 1
    teammate.memes["joy"] += 1
    world.say(
        f"The judge guided them by the secret way, and they reached the field just as the silver horn sounded."
    )
    world.say(
        f"{hero.id} ran swiftly, but now {hero.pronoun()} matched steps with {teammate.id}, and together they crossed the line first."
    )
    world.say(
        f"Before all the meadow, the judge placed the {prize.label} upon {hero.id}. {prize.ending_image}."
    )
    world.say(
        f"From that day on, {hero.id} remembered that the truest varsity heart is quick to help, not only quick to race."
    )


def reward_rush(world: World, hero: Entity, teammate: Entity, prize: PrizeCfg) -> None:
    hero.meters["late"] += 1
    hero.memes["shame"] += 1
    hero.memes["lesson"] += 1
    teammate.memes["worry"] += 1
    world.say(
        f'The judge tapped the ground, and the path finally opened, but by the time they reached the field, the first race had already begun.'
    )
    world.say(
        f"{hero.id} lowered {hero.pronoun('possessive')} head. The prize was close enough to see, yet too late to win."
    )
    world.say(
        f'Still, the judge pinned a small practice rosette on the team baton and said, "Speed without kindness runs crooked."'
    )
    world.say(
        f"{hero.id} thanked the judge, turned to {teammate.id}, and promised never again to hurry past someone in need. "
        f"That promise was the lesson {hero.pronoun()} carried home."
    )


def tell(
    realm: Realm,
    helper_cfg: HelperCfg,
    obstacle_cfg: ObstacleCfg,
    prize_cfg: PrizeCfg,
    choice: str,
    hero_name: str,
    hero_gender: str,
    teammate_name: str,
    teammate_gender: str,
    crown: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            attrs={"traits": ["little", trait]},
        )
    )
    teammate = world.add(
        Entity(
            id="teammate",
            kind="character",
            type=teammate_gender,
            label=teammate_name,
            role="teammate",
            attrs={"traits": ["steady"]},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_cfg.type,
            label=helper_cfg.label,
            role="helper",
            tags=set(helper_cfg.tags),
        )
    )
    obstacle = world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type="obstacle",
            label=obstacle_cfg.label,
            role="obstacle",
            tags=set(obstacle_cfg.tags),
        )
    )

    setup_story(world, realm, prize_cfg, crown, hero, teammate)
    boast(world, hero, teammate)

    world.para()
    meet_obstacle(world, obstacle_cfg, helper_cfg)

    if choice == "help":
        choose_help(world, hero, teammate, helper_cfg, obstacle)
    else:
        choose_rush(world, hero, teammate, obstacle_cfg)

    world.para()
    reveal_twist(world, helper_cfg, crown)

    if choice == "help":
        reward_help(world, hero, teammate, prize_cfg)
    else:
        reward_rush(world, hero, teammate, prize_cfg)

    world.facts.update(
        realm=realm,
        helper_cfg=helper_cfg,
        obstacle_cfg=obstacle_cfg,
        prize_cfg=prize_cfg,
        choice=choice,
        crown=crown,
        hero=hero,
        teammate=teammate,
        helper=helper,
        obstacle=obstacle,
        outcome="champion" if choice == "help" else "humbled",
        twist_revealed=helper.memes["revealed"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "varsity": [
        (
            "What does varsity mean?",
            "Varsity means a school or team group chosen to represent the group in a sport or big game. In this fairy tale, it means the honored team everyone hopes to join."
        )
    ],
    "kindness": [
        (
            "Why can kindness matter in a race story?",
            "Kindness matters because being a good teammate is not only about being fast. It shows that you care about other people, and that can change what happens next."
        )
    ],
    "twist": [
        (
            "What is a twist in a story?",
            "A twist is a surprise turn that changes how you understand what was happening. It can make a plain stranger turn out to be someone important."
        )
    ],
    "frog": [
        (
            "Why are frogs often near brooks in stories?",
            "Frogs like wet places, so brooks and ponds feel like their natural homes. That makes them good fairy-tale guides near water."
        )
    ],
    "owl": [
        (
            "Why do stories use owls as wise characters?",
            "Owls are often shown as watchful and thoughtful because they see quietly from high places. In stories, that makes them feel like judges or helpers."
        )
    ],
    "mole": [
        (
            "Why can a mole help underground paths?",
            "Moles dig through soft earth, so they fit stories about hidden tunnels and secret ways. A mole helper feels believable when the path is blocked by dirt or stones."
        )
    ],
    "bridge": [
        (
            "Why is a bridge useful in a race?",
            "A bridge lets runners cross water quickly and safely. Without one, they may slip, slow down, or have to turn back."
        )
    ],
    "ribbons": [
        (
            "Why can loose ribbons cause trouble on a track?",
            "Loose ribbons can flap, knot, and catch around feet or posts. That makes a gate messy and hard to pass through."
        )
    ],
    "path": [
        (
            "Why do stories use blocked paths?",
            "A blocked path forces a character to choose what kind of person to be. The obstacle is not only in the road but also in the heart."
        )
    ],
}
KNOWLEDGE_ORDER = ["varsity", "kindness", "twist", "frog", "owl", "mole", "bridge", "ribbons", "path"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    teammate = f["teammate"]
    helper_cfg = f["helper_cfg"]
    obstacle_cfg = f["obstacle_cfg"]
    prize_cfg = f["prize_cfg"]
    choice = f["choice"]
    if choice == "help":
        return [
            'Write a fairy tale for a 3-to-5-year-old that includes the word "varsity" and ends with a lesson about kindness.',
            f"Tell a fairy-tale sports story where {hero.label} stops on the way to a race to help {helper_cfg.label} at {obstacle_cfg.label}, and the helper turns out to be the secret judge.",
            f"Write a gentle twist story in which a child wins {prize_cfg.phrase} only after learning that helping a teammate and a stranger matters more than bragging.",
        ]
    return [
        'Write a fairy tale for a 3-to-5-year-old that includes the word "varsity" and contains a twist and a lesson learned.',
        f"Tell a fairy-tale race story where {hero.label} hurries past {helper_cfg.label}, learns the stranger was the royal judge, and understands why kindness matters.",
        f"Write a simple story with a twist in which {hero.label} and {teammate.label} nearly miss a varsity prize because pride gets in the way of helping.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    teammate = f["teammate"]
    helper_cfg = f["helper_cfg"]
    obstacle_cfg = f["obstacle_cfg"]
    prize_cfg = f["prize_cfg"]
    choice = f["choice"]
    crown = f["crown"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, {teammate.label}, and {helper_cfg.label} beside {obstacle_cfg.label}. They meet on the way to the royal varsity games."
        ),
        (
            "What did the hero want?",
            f"{hero.label} wanted to win {prize_cfg.phrase}. That wish made the race feel very important from the beginning."
        ),
        (
            "What problem stopped the team on the way?",
            f"They found {obstacle_cfg.block}. The blocked way is what forced them to choose between hurrying and helping."
        ),
    ]
    if choice == "help":
        qa.extend(
            [
                (
                    f"Why did {hero.label} stop to help?",
                    f"{hero.label} saw that the stranger truly needed help and chose kindness over bragging rights. That choice changed the obstacle itself, because the helper opened a magic way after being helped."
                ),
                (
                    "What was the twist?",
                    f"The shabby stranger was not ordinary at all. {helper_cfg.reveal}, and the judge said the {crown} had sent {helper_cfg.type if helper_cfg.type else 'the judge'} to see who was ready for varsity honor."
                ),
                (
                    f"How did {hero.label} win the prize?",
                    f"{hero.label} won after helping first and then running as a good teammate beside {teammate.label}. The story shows that the prize came from character as well as speed."
                ),
                (
                    "What lesson did the hero learn?",
                    f"{hero.label} learned that the truest varsity heart helps others. Being fast mattered, but kindness is what opened the right path."
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    f"Why did {hero.label} get delayed?",
                    f"{hero.label} was too proud to stop and help, so the obstacle stayed difficult. Because the team rushed ahead anyway, they lost time struggling with the blocked way."
                ),
                (
                    "What was the twist?",
                    f"The plain stranger turned out to be the royal judge. That surprise mattered because the hero had shown pride to the very person watching for good sportsmanship."
                ),
                (
                    f"Did {hero.label} win {prize_cfg.label}?",
                    f"No. {hero.label} arrived too late to win it, because pride caused the delay before the race."
                ),
                (
                    "What lesson did the hero learn?",
                    f"{hero.label} learned that speed without kindness runs crooked. The loss hurt, but it taught a better way to act next time."
                ),
            ]
        )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"varsity", "kindness", "twist"}
    tags |= set(f["helper_cfg"].tags)
    tags |= set(f["obstacle_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        realm="moonmeadow",
        helper="frog",
        obstacle="brook",
        choice="help",
        prize="ribbon",
        hero_name="Lila",
        hero_gender="girl",
        teammate_name="Finn",
        teammate_gender="boy",
        crown="queen",
        trait="eager",
    ),
    StoryParams(
        realm="rosefield",
        helper="owl",
        obstacle="windgate",
        choice="rush",
        prize="sash",
        hero_name="Theo",
        hero_gender="boy",
        teammate_name="Mira",
        teammate_gender="girl",
        crown="king",
        trait="proud",
    ),
    StoryParams(
        realm="thistledown",
        helper="mole",
        obstacle="stonepath",
        choice="help",
        prize="bell",
        hero_name="Poppy",
        hero_gender="girl",
        teammate_name="Owen",
        teammate_gender="boy",
        crown="queen",
        trait="hopeful",
    ),
    StoryParams(
        realm="moonmeadow",
        helper="frog",
        obstacle="brook",
        choice="rush",
        prize="bell",
        hero_name="Jasper",
        hero_gender="boy",
        teammate_name="Nora",
        teammate_gender="girl",
        crown="king",
        trait="bold",
    ),
]


ASP_RULES = r"""
valid(H, O) :- helper(H), obstacle(O), solves(H, O).

outcome(champion) :- chosen_choice(help).
outcome(humbled)  :- chosen_choice(rush).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for realm_id in sorted(REALMS):
        lines.append(asp.fact("realm", realm_id))
    for helper_id in sorted(HELPERS):
        lines.append(asp.fact("helper", helper_id))
    for obstacle_id, obstacle in sorted(OBSTACLES.items()):
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("solves", obstacle.helper_id, obstacle_id))
    for prize_id in sorted(PRIZES):
        lines.append(asp.fact("prize", prize_id))
    lines.append(asp.fact("choice", "help"))
    lines.append(asp.fact("choice", "rush"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_choice", params.choice)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid helper/obstacle pairs:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story in smoke test.")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale varsity storyworld with a lesson and a twist. "
        "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--realm", choices=sorted(REALMS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--crown", choices=CROWNS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list helper/obstacle pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and args.obstacle and not valid_pair(args.helper, args.obstacle):
        raise StoryError(explain_rejection(args.helper, args.obstacle))

    combos = [
        combo
        for combo in valid_combos()
        if (args.helper is None or combo[0] == args.helper)
        and (args.obstacle is None or combo[1] == args.obstacle)
    ]
    if not combos:
        raise StoryError("(No valid helper and obstacle combination matches the given options.)")

    helper_id, obstacle_id = rng.choice(sorted(combos))
    realm = args.realm or rng.choice(sorted(REALMS))
    choice = args.choice or rng.choice(CHOICES)
    prize = args.prize or rng.choice(sorted(PRIZES))
    hero_name, hero_gender = _pick_child(rng)
    teammate_name, teammate_gender = _pick_child(rng, avoid=hero_name)
    crown = args.crown or rng.choice(CROWNS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        realm=realm,
        helper=helper_id,
        obstacle=obstacle_id,
        choice=choice,
        prize=prize,
        hero_name=hero_name,
        hero_gender=hero_gender,
        teammate_name=teammate_name,
        teammate_gender=teammate_gender,
        crown=crown,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.realm not in REALMS:
        raise StoryError(f"(No story: unknown realm '{params.realm}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(No story: unknown obstacle '{params.obstacle}'.)")
    if params.choice not in CHOICES:
        raise StoryError(f"(No story: unknown choice '{params.choice}'.)")
    if params.prize not in PRIZES:
        raise StoryError(f"(No story: unknown prize '{params.prize}'.)")
    if params.crown not in CROWNS:
        raise StoryError(f"(No story: unknown crown '{params.crown}'.)")
    if not valid_pair(params.helper, params.obstacle):
        raise StoryError(explain_rejection(params.helper, params.obstacle))

    world = tell(
        realm=REALMS[params.realm],
        helper_cfg=HELPERS[params.helper],
        obstacle_cfg=OBSTACLES[params.obstacle],
        prize_cfg=PRIZES[params.prize],
        choice=params.choice,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        teammate_name=params.teammate_name,
        teammate_gender=params.teammate_gender,
        crown=params.crown,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_combos()
        print(f"{len(pairs)} compatible (helper, obstacle) pairs:\n")
        for helper_id, obstacle_id in pairs:
            print(f"  {helper_id:6} {obstacle_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero_name} at {p.realm}: {p.helper} / {p.obstacle} / "
                f"{p.choice} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
