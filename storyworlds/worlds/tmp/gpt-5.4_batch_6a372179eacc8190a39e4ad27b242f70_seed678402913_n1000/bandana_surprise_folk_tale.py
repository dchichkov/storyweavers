#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bandana_surprise_folk_tale.py
========================================================

A standalone story world for a small folk-tale domain built around a bandana,
an act of kindness, and a surprise return of help.

Premise
-------
A child sets out on a simple errand wearing a bright bandana. On the path, the
child meets a small creature in trouble and uses the bandana to help. Later, a
different danger rises on the road. The earlier kindness changes the world:
the helped creature returns, often with friends, and solves the harder problem
in a surprising but grounded folk-tale way. The child reaches home wiser, and
the ending image proves the bandana has become a sign of kindness rather than
just a cloth.

The world model keeps two axes:
- physical meters: hurt, wrapped, stuck, lost, crossed, delivered
- emotional memes: kindness, worry, trust, relief, gratitude

The reasonableness gate is simple and explicit:
- the chosen creature must be the kind of creature a bandana can plausibly help
- that creature must also plausibly solve the later road trouble

Run it
------
python storyworlds/worlds/gpt-5.4/bandana_surprise_folk_tale.py
python storyworlds/worlds/gpt-5.4/bandana_surprise_folk_tale.py --helper sparrow --trouble fog
python storyworlds/worlds/gpt-5.4/bandana_surprise_folk_tale.py --helper tortoise --trouble river
python storyworlds/worlds/gpt-5.4/bandana_surprise_folk_tale.py --all
python storyworlds/worlds/gpt-5.4/bandana_surprise_folk_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/bandana_surprise_folk_tale.py --verify
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
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }
        return mapping.get(self.type, self.label or self.type)


@dataclass
class Errand:
    id: str
    start: str
    destination: str
    gift: str
    container: str
    elder: str
    opening: str
    closing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    label: str
    phrase: str
    hurt: str
    wrap_text: str
    return_text: str
    solves: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    rise_text: str
    fear_text: str
    solved_texts: dict[str, str] = field(default_factory=dict)
    ending_image: str = ""
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


def _r_wrapped_helper(world: World) -> list[str]:
    out: list[str] = []
    if "helper" not in world.entities:
        return out
    helper = world.get("helper")
    if helper.meters["wrapped"] < THRESHOLD:
        return out
    sig = ("wrapped_helper", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.meters["hurt"] = 0.0
    helper.memes["trust"] += 1
    helper.memes["gratitude"] += 1
    world.get("hero").memes["kindness"] += 1
    out.append("__kindness__")
    return out


def _r_lost_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["lost"] < THRESHOLD:
        return out
    sig = ("lost_worry", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    out.append("__worry__")
    return out


def _r_stuck_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["stuck"] < THRESHOLD:
        return out
    sig = ("stuck_worry", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    out.append("__worry__")
    return out


CAUSAL_RULES = [
    Rule(name="wrapped_helper", tag="social", apply=_r_wrapped_helper),
    Rule(name="lost_worry", tag="emotion", apply=_r_lost_worry),
    Rule(name="stuck_worry", tag="emotion", apply=_r_stuck_worry),
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
            if not sent.startswith("__"):
                world.say(sent)
    return produced


def helper_can_solve(helper: HelperKind, trouble: Trouble) -> bool:
    return trouble.id in helper.solves


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for helper_id, helper in HELPERS.items():
        for trouble_id, trouble in TROUBLES.items():
            if helper_can_solve(helper, trouble):
                combos.append((helper_id, trouble_id))
    return combos


def predict_rescue(world: World, trouble_id: str) -> dict:
    sim = world.copy()
    trouble = TROUBLES[trouble_id]
    hero = sim.get("hero")
    if trouble_id == "fog":
        hero.meters["lost"] += 1
    elif trouble_id == "river":
        hero.meters["stuck"] += 1
    elif trouble_id == "thorn_gate":
        hero.meters["stuck"] += 1
    propagate(sim, narrate=False)
    helper = sim.get("helper")
    return {
        "worry": hero.memes["worry"],
        "can_rescue": helper_can_solve(HELPERS[helper.attrs["kind_id"]], trouble),
    }


def introduce(world: World, hero: Entity, bandana_color: str, errand: Errand) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"In the days when the footpaths still remembered the songs of travelers, "
        f"there lived a child named {hero.id} in {errand.start}. "
        f"A {bandana_color} bandana rested around {hero.pronoun('possessive')} neck like a little flag of morning."
    )
    world.say(errand.opening)


def send_off(world: World, hero: Entity, elder: Entity, errand: Errand) -> None:
    world.say(
        f"One day, {hero.id} set out for {errand.destination} with {errand.container} of {errand.gift} for "
        f"{hero.pronoun('possessive')} {elder.label_word}. "
        f"{hero.pronoun().capitalize()} walked carefully, for the road was simple only to those who were kind."
    )


def meet_helper(world: World, hero: Entity, helper: Entity, helper_cfg: HelperKind) -> None:
    helper.meters["hurt"] += 1
    world.say(
        f"Before {hero.id} had gone far, {hero.pronoun()} heard a small cry near the ditch. "
        f"There lay {helper_cfg.phrase}, {helper_cfg.hurt}."
    )
    world.say(
        f"{hero.id} knelt at once. Though the bandana was {hero.pronoun('possessive')} brightest thing, "
        f"{hero.pronoun()} did not think of keeping it clean."
    )


def wrap_bandana(world: World, hero: Entity, helper: Entity, helper_cfg: HelperKind) -> None:
    helper.meters["wrapped"] += 1
    hero.meters["bandana_given"] += 1
    world.get("bandana").meters["used_for_help"] += 1
    propagate(world, narrate=False)
    world.say(helper_cfg.wrap_text.format(hero=hero.id))
    world.say(
        f"{helper_cfg.return_text} Then it slipped away, carrying {hero.pronoun('possessive')} bandana with it."
    )


def raise_trouble(world: World, hero: Entity, trouble: Trouble) -> None:
    if trouble.id == "fog":
        hero.meters["lost"] += 1
    else:
        hero.meters["stuck"] += 1
    propagate(world, narrate=False)
    world.say(trouble.rise_text.format(hero=hero.id))
    world.say(trouble.fear_text.format(hero=hero.id))


def surprise_rescue(world: World, hero: Entity, helper: Entity, helper_cfg: HelperKind,
                    trouble: Trouble, errand: Errand) -> None:
    hero.meters["safe"] += 1
    hero.meters["delivered"] += 1
    hero.memes["relief"] += 1
    hero.memes["wonder"] += 1
    helper.memes["gratitude"] += 1
    world.get("bandana").meters["returned"] += 1
    solve = trouble.solved_texts[helper_cfg.id]
    world.say(
        f"Just when the road seemed ready to swallow {hero.id} whole, there came a surprise."
    )
    world.say(
        solve.format(hero=hero.id)
    )
    world.say(
        f"Bound neatly where {hero.pronoun('possessive')} lost cloth should have been fluttered the same bandana, "
        f"now carrying the smell of clean wind and wild thyme."
    )
    world.say(
        f"So {hero.id} reached {errand.destination}, placed {errand.container} of {errand.gift} in "
        f"{hero.pronoun('possessive')} {errand.elder}'s hands, and told what had happened."
    )


def closing(world: World, hero: Entity, elder: Entity, trouble: Trouble, errand: Errand) -> None:
    elder.memes["pride"] += 1
    world.say(
        f"{elder.label_word.capitalize()} smiled the old smile of people who know how stories grow. "
        f'"A cloth tied for kindness never stays lost," {elder.pronoun()} said.'
    )
    world.say(
        f"From that day on, whenever folk in {errand.start} saw {hero.id}'s bandana, they remembered "
        f"that a small gift may come home as a great surprise. {trouble.ending_image}"
    )
    world.say(errand.closing)


def tell(errand: Errand, helper_cfg: HelperKind, trouble: Trouble,
         hero_name: str = "Mira", hero_type: str = "girl",
         elder_type: str = "grandmother", bandana_color: str = "red") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name, role="hero"))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label=errand.elder,
        role="elder",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="animal",
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        role="helper",
        attrs={"kind_id": helper_cfg.id},
        tags=set(helper_cfg.tags),
    ))
    bandana = world.add(Entity(
        id="bandana",
        kind="thing",
        type="cloth",
        label="bandana",
        phrase=f"a {bandana_color} bandana",
        role="bandana",
        tags={"bandana"},
    ))

    introduce(world, hero, bandana_color, errand)
    send_off(world, hero, elder, errand)

    world.para()
    meet_helper(world, hero, helper, helper_cfg)
    wrap_bandana(world, hero, helper, helper_cfg)

    world.para()
    pred = predict_rescue(world, trouble.id)
    world.facts["predicted_worry"] = pred["worry"]
    raise_trouble(world, hero, trouble)

    world.para()
    surprise_rescue(world, hero, helper, helper_cfg, trouble, errand)
    closing(world, hero, elder, trouble, errand)

    world.facts.update(
        hero=hero,
        elder=elder,
        helper=helper,
        helper_cfg=helper_cfg,
        trouble=trouble,
        errand=errand,
        bandana=bandana,
        rescued=True,
        delivered=hero.meters["delivered"] >= THRESHOLD,
        kindness=hero.memes["kindness"] >= THRESHOLD,
    )
    return world


ERRANDS = {
    "cakes": Errand(
        id="cakes",
        start="Willow Hollow",
        destination="the far mill",
        gift="honey cakes",
        container="a willow basket",
        elder="grandmother",
        opening="The child was known for listening to creaking gates, old trees, and quiet advice.",
        closing="And that is why, in Willow Hollow, people still knot bright cloth before they travel.",
        tags={"cakes", "journey"},
    ),
    "plums": Errand(
        id="plums",
        start="Reed Village",
        destination="the hill cottage",
        gift="summer plums",
        container="a small reed basket",
        elder="grandfather",
        opening="Some said the child's steps were so light that even dust did not mind being stirred.",
        closing="And so the road to the hill cottage became known as the Kind Path.",
        tags={"plums", "journey"},
    ),
    "bread": Errand(
        id="bread",
        start="Ash Lane",
        destination="the old orchard house",
        gift="warm bread",
        container="a round lidded basket",
        elder="grandmother",
        opening="The old people said that roads test the heart before they test the feet.",
        closing="To this day, the orchard folk call a helpful child rich, even with empty pockets.",
        tags={"bread", "journey"},
    ),
}

HELPERS = {
    "sparrow": HelperKind(
        id="sparrow",
        label="sparrow",
        phrase="a brown sparrow",
        hurt="with one wing drooping in the dust",
        wrap_text="{hero} untied the bandana, tore a gentle strip from its edge, and bound the little wing so it could rest close and still.",
        return_text='The sparrow dipped its head as if bowing. "Kind hands are never forgotten," it seemed to say.',
        solves={"fog", "thorn_gate"},
        tags={"bird", "bandage"},
    ),
    "goat_kid": HelperKind(
        id="goat_kid",
        label="goat kid",
        phrase="a white goat kid",
        hurt="with one leg trembling between two roots",
        wrap_text="{hero} folded the bandana into a soft sling and tied the sore leg snugly, then lifted the kid free from the roots.",
        return_text="The little goat stamped once, lively again, and looked back with bright thankful eyes.",
        solves={"river", "thorn_gate"},
        tags={"goat", "bandage"},
    ),
    "tortoise": HelperKind(
        id="tortoise",
        label="tortoise",
        phrase="a mossy tortoise",
        hurt="turned on its side against a stone, unable to right itself",
        wrap_text="{hero} laid the bandana under the tortoise, made a broad cradle, and rolled it gently back onto its feet so its shell would not scrape.",
        return_text="The tortoise blinked slowly, as if sealing a promise older than the road.",
        solves={"river", "fog"},
        tags={"tortoise", "care"},
    ),
}

TROUBLES = {
    "fog": Trouble(
        id="fog",
        label="fog",
        rise_text="By noon a white fog spilled out of the low fields and wrapped the path until even {hero}'s own footsteps sounded far away.",
        fear_text="{hero} stopped under a thorn tree, for every lane looked like every other lane, and the basket felt very small in the world.",
        solved_texts={
            "sparrow": "From the fog came the sparrow, circling ahead and singing from post to post, leading {hero} by sound until the mill wheel thumped through the mist.",
            "tortoise": "Out of the whitening air came the tortoise, tapping the true road with its shell against the stones. {hero} followed that steady little knock until the cottage chimney rose from the mist.",
        },
        ending_image="At sunset the cloth shone on the windowsill like a piece of brave sky.",
        tags={"fog"},
    ),
    "river": Trouble(
        id="river",
        label="river",
        rise_text="At the crossing, the shallow stream of morning had grown bold and brown, licking over the stepping stones so that {hero} could not tell safe rock from rushing water.",
        fear_text="{hero} hugged the basket to {hero}'s chest and dared not step, for one slip would send both child and gift into the cold current.",
        solved_texts={
            "goat_kid": "Then there was the patter of quick hooves. The goat kid bounded back with its mother, and together they stood firm among the stones, showing {hero} where to place each foot until the crossing was done.",
            "tortoise": "Then the tortoise appeared at the bank where the water curled slowest. It edged from stone to stone, and where it placed its patient feet, {hero} stepped too, crossing safely through the gentler stream.",
        },
        ending_image="That evening the bandana dried by the hearth, bright as a berry after rain.",
        tags={"river"},
    ),
    "thorn_gate": Trouble(
        id="thorn_gate",
        label="thorn gate",
        rise_text="Near the last bend, a fallen hedge of thorn branches blocked the lane, hooked and tangled so tightly that even a hare would think twice.",
        fear_text="{hero} could not climb through without tearing the basket cloth and scattering the gift into the dust.",
        solved_texts={
            "sparrow": "All at once the sparrow returned with a cloud of small birds. They tugged at the finest twigs and showed {hero} a narrow clean gap hidden behind the hedge.",
            "goat_kid": "Then the goat kid came dancing back. It nibbled and worried the tender thorn shoots while its mother shoved the heavier branches aside, opening a crooked but safe way for {hero}.",
        },
        ending_image="Long after supper, children traced little bird-feet and goat-hoof prints in the dust outside the door.",
        tags={"thorns"},
    ),
}

GIRL_NAMES = ["Mira", "Toma", "Lina", "Anya", "Rosa", "Suri", "Nella", "Pia"]
BOY_NAMES = ["Ivo", "Milo", "Tarin", "Bram", "Niko", "Rian", "Pavel", "Luca"]
BANDANA_COLORS = ["red", "blue", "golden", "green"]
ELDERS = ["grandmother", "grandfather"]


@dataclass
class StoryParams:
    errand: str
    helper: str
    trouble: str
    hero_name: str
    hero_type: str
    elder_type: str
    bandana_color: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        errand="cakes",
        helper="sparrow",
        trouble="fog",
        hero_name="Mira",
        hero_type="girl",
        elder_type="grandmother",
        bandana_color="red",
    ),
    StoryParams(
        errand="plums",
        helper="goat_kid",
        trouble="river",
        hero_name="Milo",
        hero_type="boy",
        elder_type="grandfather",
        bandana_color="blue",
    ),
    StoryParams(
        errand="bread",
        helper="tortoise",
        trouble="fog",
        hero_name="Anya",
        hero_type="girl",
        elder_type="grandmother",
        bandana_color="golden",
    ),
    StoryParams(
        errand="cakes",
        helper="goat_kid",
        trouble="thorn_gate",
        hero_name="Bram",
        hero_type="boy",
        elder_type="grandmother",
        bandana_color="green",
    ),
]


KNOWLEDGE = {
    "bandana": [
        (
            "What is a bandana?",
            "A bandana is a square piece of cloth people can tie around the head, neck, or wrist. It is light, soft, and useful for carrying or wrapping small things.",
        )
    ],
    "fog": [
        (
            "What is fog?",
            "Fog is a cloud close to the ground. It makes it hard to see far away because tiny drops of water fill the air.",
        )
    ],
    "river": [
        (
            "Why can crossing a river be dangerous?",
            "A river can move fast and hide slippery stones under the water. That is why people must cross carefully where the water is shallow and safe.",
        )
    ],
    "thorns": [
        (
            "What are thorns?",
            "Thorns are sharp points that grow on some plants. They help protect the plant, but they can scratch skin and cloth.",
        )
    ],
    "bird": [
        (
            "How can a bird help someone find the way?",
            "A bird can fly ahead and call from the right path. Even when the road is hard to see, a clear sound can help a traveler follow safely.",
        )
    ],
    "goat": [
        (
            "Why are goats good on rocky places?",
            "Goats are sure-footed animals. They are very good at stepping on uneven ground without slipping.",
        )
    ],
    "tortoise": [
        (
            "Why is a tortoise a symbol of patience in stories?",
            "A tortoise moves slowly and steadily. In many stories, that makes it a sign that careful steps can beat hurry.",
        )
    ],
    "bandage": [
        (
            "What does a bandage do?",
            "A bandage wraps around a hurt place to protect it and hold it still. It can help a small injury rest while it heals.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bandana", "fog", "river", "thorns", "bird", "goat", "tortoise", "bandage"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper_cfg"]
    trouble = f["trouble"]
    errand = f["errand"]
    return [
        'Write a short folk tale for a young child that includes the word "bandana" and a surprise return of kindness.',
        f"Tell a folk tale about {hero.id}, who wears a bandana, helps a {helper.label} on the road, and later faces {trouble.label} while carrying {errand.gift}.",
        f"Write a gentle journey story in a folk-tale voice where a small act of kindness turns into a surprising rescue before {hero.id} reaches {errand.destination}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper_cfg"]
    trouble = f["trouble"]
    errand = f["errand"]
    elder = f["elder"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child on the road to {errand.destination}. {hero.pronoun().capitalize()} wore a {world.get('bandana').phrase.split(' ', 1)[1]} and carried {errand.gift} for {hero.pronoun('possessive')} {elder.label_word}.",
        ),
        (
            "Why did the child take off the bandana?",
            f"{hero.id} saw {helper.phrase} in trouble and used the bandana to help. That choice mattered because the cloth became a real sign of kindness, not just something pretty to wear.",
        ),
        (
            f"What problem came later on the road?",
            f"The later trouble was {trouble.label}. It frightened {hero.id} because {trouble.fear_text.format(hero=hero.id)}",
        ),
        (
            "What was the surprise in the story?",
            f"The surprise was that the helped {helper.label} came back when {hero.id} needed help most. The earlier kindness changed the road, so help returned in an unexpected way.",
        ),
        (
            "How did the story end?",
            f"{hero.id} reached {errand.destination} safely and delivered the {errand.gift}. In the end, the bandana came back carrying the memory of the good deed, which is the folk-tale proof that kindness returns.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"bandana", "bandage"} | set(world.facts["helper_cfg"].tags) | set(world.facts["trouble"].tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(helper: HelperKind, trouble: Trouble) -> str:
    return (
        f"(No story: a {helper.label} can be helped by the bandana here, but it is not a good folk-tale answer to {trouble.label}. "
        f"The later rescue must grow naturally from the earlier kindness.)"
    )


ASP_RULES = r"""
rescues(H, T) :- helper(H), trouble(T), can_solve(H, T).
valid(H, T) :- helper(H), trouble(T), rescues(H, T).

outcome(help_returns) :- chosen_helper(H), chosen_trouble(T), rescues(H, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for errand_id in ERRANDS:
        lines.append(asp.fact("errand", errand_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for trouble_id in sorted(helper.solves):
            lines.append(asp.fact("can_solve", helper_id, trouble_id))
    for trouble_id in TROUBLES:
        lines.append(asp.fact("trouble", trouble_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_trouble", params.trouble),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bandana, a kind deed, and a folk-tale surprise."
    )
    ap.add_argument("--errand", choices=ERRANDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=ELDERS)
    ap.add_argument("--bandana-color", choices=BANDANA_COLORS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible helper/trouble combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and args.trouble:
        helper = HELPERS[args.helper]
        trouble = TROUBLES[args.trouble]
        if not helper_can_solve(helper, trouble):
            raise StoryError(explain_rejection(helper, trouble))

    combos = [
        combo for combo in valid_combos()
        if (args.helper is None or combo[0] == args.helper)
        and (args.trouble is None or combo[1] == args.trouble)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    helper_id, trouble_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(ELDERS)
    errand = args.errand or rng.choice(sorted(ERRANDS))
    bandana_color = args.bandana_color or rng.choice(BANDANA_COLORS)
    return StoryParams(
        errand=errand,
        helper=helper_id,
        trouble=trouble_id,
        hero_name=hero_name,
        hero_type=hero_type,
        elder_type=elder_type,
        bandana_color=bandana_color,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        errand = ERRANDS[params.errand]
        helper = HELPERS[params.helper]
        trouble = TROUBLES[params.trouble]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter: {exc.args[0]!r} is not in this world.)") from exc

    if not helper_can_solve(helper, trouble):
        raise StoryError(explain_rejection(helper, trouble))

    world = tell(
        errand=errand,
        helper_cfg=helper,
        trouble=trouble,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        elder_type=params.elder_type,
        bandana_color=params.bandana_color,
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

    cases = list(CURATED)
    for s in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != "help_returns":
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generated a story.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (helper, trouble) combos:\n")
        for helper_id, trouble_id in combos:
            print(f"  {helper_id:10} {trouble_id}")
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
            header = f"### {p.hero_name}: {p.helper} and {p.trouble} ({p.errand})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
