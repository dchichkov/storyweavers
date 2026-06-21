#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/defend_dopey_transformation_humor_folk_tale.py
========================================================================

A small storyworld for a humorous folk-tale pattern:

A child in a village finds a creature everyone calls dopey. The child chooses
to defend the creature instead of laughing at it. Because the child's kindness
matches the creature's hidden nature, the creature transforms and fixes a real
village trouble.

This world prefers tight, plausible variants over broad coverage:
- the offered gift must suit the creature;
- the transformed creature's magic must fit the village's need.

Run it
------
    python storyworlds/worlds/gpt-5.4/defend_dopey_transformation_humor_folk_tale.py
    python storyworlds/worlds/gpt-5.4/defend_dopey_transformation_humor_folk_tale.py --creature goose --need garden
    python storyworlds/worlds/gpt-5.4/defend_dopey_transformation_humor_folk_tale.py --creature frog --gift barley
    python storyworlds/worlds/gpt-5.4/defend_dopey_transformation_humor_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/defend_dopey_transformation_humor_folk_tale.py --qa
    python storyworlds/worlds/gpt-5.4/defend_dopey_transformation_humor_folk_tale.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so the package dir is
# three levels up from here.
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
        female = {"girl", "woman", "mother", "witch"}
        male = {"boy", "man", "father", "miller", "baker", "headman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Need:
    id: str
    place: str
    trouble: str
    image: str
    request: str
    fixed: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CreatureCfg:
    id: str
    label: str
    phrase: str
    comic: str
    insult: str
    likes: str
    true_form: str
    reveal: str
    boon_need: str
    boon_text: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    suits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MockerCfg:
    id: str
    type: str
    label: str
    phrase: str
    scold: str
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


def _r_mocking_hurts(world: World) -> list[str]:
    out: list[str] = []
    creature = world.entities.get("creature")
    hero = world.entities.get("hero")
    if creature is None or hero is None:
        return out
    if creature.memes["mocked"] < THRESHOLD:
        return out
    sig = ("mocking_hurts", creature.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.memes["shame"] += 1
    hero.memes["protective"] += 1
    out.append("__hurt__")
    return out


def _r_kindness_builds_trust(world: World) -> list[str]:
    out: list[str] = []
    creature = world.entities.get("creature")
    hero = world.entities.get("hero")
    gift = world.entities.get("gift")
    if creature is None or hero is None or gift is None:
        return out
    if hero.memes["defended"] < THRESHOLD or creature.meters["fed"] < THRESHOLD:
        return out
    sig = ("kindness", creature.id, gift.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.memes["trust"] += 1
    hero.memes["kindness"] += 1
    out.append("__trust__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    creature = world.entities.get("creature")
    if creature is None:
        return out
    if creature.memes["trust"] < THRESHOLD:
        return out
    if creature.attrs.get("gift_ok") is not True:
        return out
    if creature.attrs.get("need_ok") is not True:
        return out
    sig = ("transform", creature.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.meters["disguise"] = 0.0
    creature.meters["transformed"] += 1
    creature.memes["joy"] += 1
    out.append("__transform__")
    return out


def _r_help_need(world: World) -> list[str]:
    out: list[str] = []
    creature = world.entities.get("creature")
    need = world.entities.get("need")
    village = world.entities.get("village")
    if creature is None or need is None or village is None:
        return out
    if creature.meters["transformed"] < THRESHOLD:
        return out
    sig = ("help_need", need.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    need.meters["solved"] += 1
    village.meters["peace"] += 1
    out.append("__help__")
    return out


CAUSAL_RULES = [
    Rule(name="mocking_hurts", tag="social", apply=_r_mocking_hurts),
    Rule(name="kindness_builds_trust", tag="social", apply=_r_kindness_builds_trust),
    Rule(name="transform", tag="magic", apply=_r_transform),
    Rule(name="help_need", tag="physical", apply=_r_help_need),
]


def propagate(world: World, narrate: bool = False) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    return produced


def gift_suits(creature: CreatureCfg, gift: Gift) -> bool:
    return creature.id in gift.suits


def can_solve(creature: CreatureCfg, need: Need) -> bool:
    return creature.boon_need == need.id


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for need_id, need in NEEDS.items():
        for creature_id, creature in CREATURES.items():
            for gift_id, gift in GIFTS.items():
                if gift_suits(creature, gift) and can_solve(creature, need):
                    combos.append((need_id, creature_id, gift_id))
    return sorted(combos)


def explain_rejection(creature: CreatureCfg, need: Need, gift: Gift) -> str:
    if not gift_suits(creature, gift):
        return (
            f"(No story: {gift.label} does not suit the {creature.label}. "
            f"In this tale, the creature only trusts someone who offers what it can really use.)"
        )
    if not can_solve(creature, need):
        return (
            f"(No story: a transformed {creature.label} cannot honestly fix the trouble at "
            f"{need.place}. Pick a creature whose hidden magic matches that village need.)"
        )
    return "(No story: this combination does not fit the world.)"


def predict_transformation(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    creature = sim.get("creature")
    hero.memes["defended"] += 1
    creature.meters["fed"] += 1
    propagate(sim, narrate=False)
    return {
        "transforms": creature.meters["transformed"] >= THRESHOLD,
        "need_solved": sim.get("need").meters["solved"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, need: Need) -> None:
    world.say(
        f"In a village beside {need.place}, there lived {hero.id}, a child who listened "
        f"hard when grown-ups muttered about trouble."
    )
    world.say(need.image)


def arrive_creature(world: World, creature: Entity, creature_cfg: CreatureCfg) -> None:
    creature.meters["disguise"] = 1.0
    creature.meters["hunger"] = 1.0
    world.say(
        f"One morning {creature_cfg.phrase} wandered into the square. {creature_cfg.comic}"
    )


def mock(world: World, mocker: Entity, creature: Entity, creature_cfg: CreatureCfg) -> None:
    creature.memes["mocked"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Shoo!" cried {mocker.phrase}. "{creature_cfg.insult}" '
        f"{mocker.scold}"
    )


def defend_creature(world: World, hero: Entity, mocker: Entity, creature_cfg: CreatureCfg) -> None:
    hero.memes["courage"] += 1
    hero.memes["defended"] += 1
    world.say(
        f'But {hero.id} stepped between them and lifted a small hand. '
        f'"No," {hero.pronoun()} said. "I will defend this dopey {creature_cfg.label}. '
        f'It has done nothing worse than make us laugh."'
    )


def offer_gift(world: World, hero: Entity, creature: Entity, gift: Gift) -> None:
    creature.meters["fed"] += 1
    world.say(
        f"Then {hero.id} set down {gift.phrase}. The creature stopped blinking, "
        f"sniffed once, and took it with surprising manners."
    )
    propagate(world, narrate=False)


def reveal(world: World, hero: Entity, creature_cfg: CreatureCfg, need: Need) -> None:
    world.say(
        f"At once the creature shook itself. Feathers, fur, or damp skin flashed like "
        f"coins in sunlight, and in their place stood {creature_cfg.reveal}."
    )
    world.say(
        f'"You defended me when others laughed," it said. "Now I will answer the village\'s need."'
    )
    world.say(creature_cfg.boon_text.format(place=need.place, fixed=need.fixed))


def celebrate(world: World, hero: Entity, mocker: Entity, creature_cfg: CreatureCfg, need: Need) -> None:
    hero.memes["joy"] += 1
    mocker.memes["embarrassed"] += 1
    world.say(
        f"Soon {need.fixed}. Even {mocker.phrase} stared as if a dumpling had begun to sing."
    )
    world.say(
        f"From that day on, nobody hurried to laugh at odd little visitors, and {hero.id} "
        f"was known as the child who could spot a hidden wonder under a foolish face."
    )
    world.say(creature_cfg.ending_image)


NEEDS = {
    "garden": Need(
        id="garden",
        place="the bean garden",
        trouble="the bean rows had turned pale and thirsty",
        image="The bean rows drooped like tired old fingers, and every bucket came up light.",
        request="water for the bean garden",
        fixed="the bean leaves stood up fresh and green again",
        tags={"garden", "rain"},
    ),
    "path": Need(
        id="path",
        place="the mill path",
        trouble="the path to the mill was choked with thorny brambles",
        image="The mill path was so snarled with thorns that even the cat walked around it.",
        request="a clear path to the mill",
        fixed="the mill path lay open and soft under many feet",
        tags={"path", "bramble"},
    ),
    "well": Need(
        id="well",
        place="the old stone well",
        trouble="the village well had gone stingy and low",
        image="At the old stone well, the rope creaked longer and longer before it touched water.",
        request="water in the well",
        fixed="the old well brimmed cold and bright to the top",
        tags={"well", "water"},
    ),
}

CREATURES = {
    "goose": CreatureCfg(
        id="goose",
        label="goose",
        phrase="a speckled goose with one feather sticking up like a flag",
        comic="It slid through a cabbage basket, stole a ribbon, and sat in the mayor's lap as if that were the proper seat for a bird.",
        insult="That bird is a dopey goose",
        likes="barley",
        true_form="a cloud-sprite with silver wings",
        reveal="a small cloud-sprite with silver wings and a laugh like rain on a roof",
        boon_need="garden",
        boon_text="The sprite beat its bright wings over {place}, and a soft rain fell exactly where it was needed most.",
        ending_image="At supper, the beans were glossy, the goose-ribbon hung over the chimney, and children laughed for a kinder reason.",
        tags={"goose", "rain", "bird"},
    ),
    "goat": CreatureCfg(
        id="goat",
        label="goat",
        phrase="a knock-kneed goat with a bell tied on backward",
        comic="It climbed onto a flour barrel, sneezed into the dust, and looked pleased to come out wearing a white mustache.",
        insult="That beast is a dopey goat",
        likes="cabbage",
        true_form="a hill-sprite with curling green horns",
        reveal="a nimble hill-sprite with curling green horns and laughing eyes",
        boon_need="path",
        boon_text="The sprite skipped toward {place}, and every hungry thorn bent down for it as if apologizing. By noon, the way was clear.",
        ending_image="Before long, carts rolled easily down the path, and people said even brambles had better manners after meeting that goat.",
        tags={"goat", "path", "bramble"},
    ),
    "frog": CreatureCfg(
        id="frog",
        label="frog",
        phrase="a round green frog wearing a crown of duckweed",
        comic="It leaped into a bread bowl, sat there like a pudding with eyes, and croaked at anyone who complained.",
        insult="That creature is a dopey frog",
        likes="water",
        true_form="a well-spirit in a green coat",
        reveal="a bright-eyed well-spirit in a green coat stitched with drops of light",
        boon_need="well",
        boon_text="The spirit touched the stones of {place}, and clear water came singing up from the dark as if it had only been waiting for a polite invitation.",
        ending_image="That evening the well shone with stars, and the frog's duckweed crown floated on top like a joke the whole village treasured.",
        tags={"frog", "well", "water"},
    ),
}

GIFTS = {
    "barley": Gift(
        id="barley",
        label="barley",
        phrase="a little wooden scoop of barley",
        suits={"goose"},
        tags={"grain", "barley"},
    ),
    "cabbage": Gift(
        id="cabbage",
        label="cabbage leaf",
        phrase="a crisp cabbage leaf",
        suits={"goat"},
        tags={"cabbage", "leaf"},
    ),
    "water": Gift(
        id="water",
        label="bowl of water",
        phrase="a blue bowl of cool water",
        suits={"frog"},
        tags={"water"},
    ),
}

MOCKERS = {
    "baker": MockerCfg(
        id="baker",
        type="baker",
        label="baker",
        phrase="the baker",
        scold="It will upset my baskets before noon.",
        tags={"baker"},
    ),
    "miller": MockerCfg(
        id="miller",
        type="miller",
        label="miller",
        phrase="the miller",
        scold="It has more foolishness than sense.",
        tags={"miller"},
    ),
    "headwoman": MockerCfg(
        id="headwoman",
        type="woman",
        label="headwoman",
        phrase="the headwoman",
        scold="A village has enough trouble without a foolish animal adding more.",
        tags={"headwoman"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nell", "Anya", "Pia", "Rosa", "Mila"]
BOY_NAMES = ["Tobin", "Nico", "Pavel", "Jori", "Marten", "Ivo", "Sami", "Oren"]
TRAITS = ["brave", "kind", "quick-eyed", "cheerful", "steady", "gentle"]


@dataclass
class StoryParams:
    need: str
    creature: str
    gift: str
    mocker: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def pair_registry_lookup(name: str, table: dict, kind: str):
    if name not in table:
        raise StoryError(f"(Unknown {kind}: {name})")
    return table[name]


def tell(
    need_cfg: Need,
    creature_cfg: CreatureCfg,
    gift_cfg: Gift,
    mocker_cfg: MockerCfg,
    hero_name: str,
    hero_gender: str,
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
            label=hero_name,
        )
    )
    mocker = world.add(
        Entity(
            id="Mocker",
            kind="character",
            type=mocker_cfg.type,
            role="mocker",
            label=mocker_cfg.label,
            phrase=mocker_cfg.phrase,
            tags=set(mocker_cfg.tags),
        )
    )
    creature = world.add(
        Entity(
            id="creature",
            kind="thing",
            type="creature",
            role="creature",
            label=creature_cfg.label,
            phrase=creature_cfg.phrase,
            attrs={
                "gift_ok": gift_suits(creature_cfg, gift_cfg),
                "need_ok": can_solve(creature_cfg, need_cfg),
                "true_form": creature_cfg.true_form,
            },
            tags=set(creature_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="gift",
            kind="thing",
            type="gift",
            role="gift",
            label=gift_cfg.label,
            phrase=gift_cfg.phrase,
            tags=set(gift_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="need",
            kind="thing",
            type="need",
            role="need",
            label=need_cfg.place,
            phrase=need_cfg.trouble,
            tags=set(need_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="village",
            kind="thing",
            type="place",
            role="village",
            label="village",
        )
    )

    introduce(world, hero, need_cfg)
    arrive_creature(world, creature, creature_cfg)

    world.para()
    mock(world, mocker, creature, creature_cfg)
    defend_creature(world, hero, mocker, creature_cfg)
    offer_gift(world, hero, creature, gift_cfg)

    prediction = predict_transformation(world)
    world.facts["predicted_transforms"] = prediction["transforms"]
    world.facts["predicted_need_solved"] = prediction["need_solved"]

    world.para()
    if creature.meters["transformed"] >= THRESHOLD:
        reveal(world, hero, creature_cfg, need_cfg)
        celebrate(world, hero, mocker, creature_cfg, need_cfg)

    world.facts.update(
        hero=hero,
        mocker=mocker,
        creature=creature,
        need_cfg=need_cfg,
        creature_cfg=creature_cfg,
        gift_cfg=gift_cfg,
        mocker_cfg=mocker_cfg,
        transformed=creature.meters["transformed"] >= THRESHOLD,
        solved=world.get("need").meters["solved"] >= THRESHOLD,
        defended=hero.memes["defended"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    need = f["need_cfg"]
    creature = f["creature_cfg"]
    gift = f["gift_cfg"]
    return [
        'Write a short folk tale for a 3-to-5-year-old that includes the words "defend" and "dopey".',
        f"Tell a humorous transformation tale where {hero.id} chooses to defend a dopey {creature.label} and offers {gift.phrase}, and the odd creature turns out to be magical.",
        f"Write a village folk tale where a child protects a foolish-looking animal from mockery, and that kindness fixes the trouble at {need.place}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mocker = f["mocker_cfg"]
    creature = f["creature_cfg"]
    need = f["need_cfg"]
    gift = f["gift_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a {next(iter(hero.traits), 'kind')} child in a village, and a strange {creature.label} that others laughed at. The tale turns on {hero.id}'s choice to defend it instead.",
        ),
        (
            f"Why did people think the {creature.label} was dopey?",
            f"They thought it was dopey because it behaved in a silly, funny way in the village square. Its clownish tricks made people laugh before they knew what it really was.",
        ),
        (
            f"What did {hero.id} do when {mocker.phrase} wanted to drive the creature away?",
            f"{hero.id} stepped forward and said {hero.pronoun()} would defend the dopey {creature.label}. Then {hero.pronoun()} offered {gift.phrase}, which showed real kindness instead of mockery.",
        ),
    ]
    if f.get("transformed"):
        qa.append(
            (
                f"Why did the creature transform?",
                f"It transformed because {hero.id} defended it when others laughed and gave it the right gift. In this world, kindness that truly suits the creature breaks the disguise.",
            )
        )
        qa.append(
            (
                f"How did the transformed creature help the village?",
                f"After changing into {creature.reveal}, it fixed the trouble at {need.place}. That proved the funny-looking visitor had been a hidden helper all along.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the village changed for the better: {need.fixed}. The last image shows that a foolish face can hide a gift.",
            )
        )
    return qa


KNOWLEDGE = {
    "folk_tale": [
        (
            "What is a folk tale?",
            "A folk tale is a story told and retold by many people. It often has a simple lesson, strange luck, and a bit of wonder.",
        )
    ],
    "transform": [
        (
            "What is a transformation in a story?",
            "A transformation is when someone or something changes into a different form. In stories, that change often reveals what was hidden before.",
        )
    ],
    "defend": [
        (
            "What does it mean to defend someone?",
            "To defend someone means to stand up for them and try to keep them safe from harm or unfair treatment. You use your words or actions to protect them.",
        )
    ],
    "goose": [
        (
            "Why do geese seem funny sometimes?",
            "Geese can honk, flap, and march in a bossy way that makes people laugh. Their funny movements can look silly even when the goose is serious.",
        )
    ],
    "goat": [
        (
            "Why are goats in many funny stories?",
            "Goats climb where they should not climb and nibble things they should not nibble. That makes them good for playful, silly scenes in stories.",
        )
    ],
    "frog": [
        (
            "Why do frogs belong in magical stories?",
            "Frogs live near water and vanish with a splash, so they feel mysterious. Many old tales use frogs to hint that magic is close by.",
        )
    ],
    "well": [
        (
            "Why was a village well important?",
            "A village well gave people water for drinking and cooking. If the well ran low, daily life became hard very quickly.",
        )
    ],
    "rain": [
        (
            "Why is rain important for a garden?",
            "Rain helps plants drink through their roots and keep growing. Without enough water, leaves droop and crops suffer.",
        )
    ],
    "path": [
        (
            "Why does a clear path matter in a village?",
            "A clear path lets people walk, carry food, and visit neighbors safely. When a path is blocked, the whole village slows down.",
        )
    ],
}
KNOWLEDGE_ORDER = ["folk_tale", "transform", "defend", "goose", "goat", "frog", "well", "rain", "path"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"folk_tale", "transform", "defend", f["creature_cfg"].id}
    if f["need_cfg"].id == "garden":
        tags.add("rain")
    if f["need_cfg"].id == "path":
        tags.add("path")
    if f["need_cfg"].id == "well":
        tags.add("well")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v not in ("", None, False)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        need="garden",
        creature="goose",
        gift="barley",
        mocker="baker",
        name="Lina",
        gender="girl",
        trait="brave",
    ),
    StoryParams(
        need="path",
        creature="goat",
        gift="cabbage",
        mocker="miller",
        name="Tobin",
        gender="boy",
        trait="steady",
    ),
    StoryParams(
        need="well",
        creature="frog",
        gift="water",
        mocker="headwoman",
        name="Mira",
        gender="girl",
        trait="gentle",
    ),
]


ASP_RULES = r"""
suitable(C, G) :- gift_suits(G, C).
can_help(C, N) :- helps_need(C, N).
valid(N, C, G) :- need(N), creature(C), gift(G), suitable(C, G), can_help(C, N).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for need_id in NEEDS:
        lines.append(asp.fact("need", need_id))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        lines.append(asp.fact("helps_need", creature_id, creature.boon_need))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        for creature_id in sorted(gift.suits):
            lines.append(asp.fact("gift_suits", gift_id, creature_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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

    smoke_cases = list(CURATED)
    for seed in range(5):
        rng = random.Random(seed)
        args = build_parser().parse_args([])
        try:
            params = resolve_params(args, rng)
        except StoryError as err:
            rc = 1
            print(f"SMOKE resolve failed: {err}")
            continue
        smoke_cases.append(params)

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if "defend" not in sample.story.lower():
                raise StoryError("story missing required word 'defend'")
            if "dopey" not in sample.story.lower():
                raise StoryError("story missing required word 'dopey'")
        except Exception as err:  # pragma: no cover - verify path
            rc = 1
            print(f"SMOKE generate failed for {params}: {err}")

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale storyworld about defending a dopey creature whose kindness-triggered transformation helps a village."
    )
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--mocker", choices=MOCKERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.creature is not None:
        pair_registry_lookup(args.creature, CREATURES, "creature")
    if args.need is not None:
        pair_registry_lookup(args.need, NEEDS, "need")
    if args.gift is not None:
        pair_registry_lookup(args.gift, GIFTS, "gift")
    if args.mocker is not None:
        pair_registry_lookup(args.mocker, MOCKERS, "mocker")

    if args.creature and args.need and args.gift:
        creature = CREATURES[args.creature]
        need = NEEDS[args.need]
        gift = GIFTS[args.gift]
        if not (gift_suits(creature, gift) and can_solve(creature, need)):
            raise StoryError(explain_rejection(creature, need, gift))

    combos = [
        c for c in valid_combos()
        if (args.need is None or c[0] == args.need)
        and (args.creature is None or c[1] == args.creature)
        and (args.gift is None or c[2] == args.gift)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    need_id, creature_id, gift_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mocker_id = args.mocker or rng.choice(sorted(MOCKERS))
    trait = rng.choice(TRAITS)
    return StoryParams(
        need=need_id,
        creature=creature_id,
        gift=gift_id,
        mocker=mocker_id,
        name=name,
        gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    need_cfg = pair_registry_lookup(params.need, NEEDS, "need")
    creature_cfg = pair_registry_lookup(params.creature, CREATURES, "creature")
    gift_cfg = pair_registry_lookup(params.gift, GIFTS, "gift")
    mocker_cfg = pair_registry_lookup(params.mocker, MOCKERS, "mocker")

    if not gift_suits(creature_cfg, gift_cfg) or not can_solve(creature_cfg, need_cfg):
        raise StoryError(explain_rejection(creature_cfg, need_cfg, gift_cfg))

    world = tell(
        need_cfg=need_cfg,
        creature_cfg=creature_cfg,
        gift_cfg=gift_cfg,
        mocker_cfg=mocker_cfg,
        hero_name=params.name,
        hero_gender=params.gender,
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
        print(f"{len(combos)} compatible (need, creature, gift) combos:\n")
        for need_id, creature_id, gift_id in combos:
            print(f"  {need_id:8} {creature_id:8} {gift_id}")
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
            header = f"### {p.name}: {p.creature} for {p.need} with {p.gift}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
