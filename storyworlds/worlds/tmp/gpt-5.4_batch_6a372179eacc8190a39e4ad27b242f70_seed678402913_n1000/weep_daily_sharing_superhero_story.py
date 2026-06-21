#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/weep_daily_sharing_superhero_story.py
===============================================================

A standalone story world about a child superhero who learns that the strongest
kind of heroism can be sharing, every day.

The domain is small on purpose: a child brings a special item to a place where a
friend has none. The hero first wants to keep the whole item, then notices the
friend's sadness, shares in a practical way, and ends with a repeated daily
habit. The story uses typed entities with physical meters and emotional memes,
state-driven prose, grounded QA, and an inline ASP twin for the reasonableness
gate.

Run it
------
    python storyworlds/worlds/gpt-5.4/weep_daily_sharing_superhero_story.py
    python storyworlds/worlds/gpt-5.4/weep_daily_sharing_superhero_story.py --hero-item apple --friend-need snack
    python storyworlds/worlds/gpt-5.4/weep_daily_sharing_superhero_story.py --hero-item cape
    python storyworlds/worlds/gpt-5.4/weep_daily_sharing_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/weep_daily_sharing_superhero_story.py --qa
    python storyworlds/worlds/gpt-5.4/weep_daily_sharing_superhero_story.py --verify
"""

from __future__ import annotations

import argparse
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
    shareable: bool = False
    snack_like: bool = False
    school_like: bool = False
    divisible: bool = False
    carryable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HeroItem:
    id: str
    label: str
    phrase: str
    kind: str
    shareable: bool
    snack_like: bool
    school_like: bool
    divisible: bool
    method: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    label: str
    phrase: str
    wants_snack_like: bool
    wants_school_like: bool
    reason: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero_item: str
    friend_need: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    adult_type: str
    costume_color: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.events: list[str] = []

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

    def log(self, event: str) -> None:
        self.events.append(event)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_sadness(world: World) -> list[str]:
    out: list[str] = []
    friend = world.get("friend")
    if friend.meters["without"] >= THRESHOLD:
        sig = ("sadness", "friend")
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["sad"] += 1
            friend.memes["about_to_weep"] += 1
            out.append("__sadness__")
    return out


def _r_sharing_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.meters["shared_amount"] >= THRESHOLD:
        sig = ("relief", "pair")
        if sig not in world.fired:
            world.fired.add(sig)
            friend.meters["without"] = 0.0
            friend.memes["sad"] = 0.0
            friend.memes["about_to_weep"] = 0.0
            friend.memes["relief"] += 1
            hero.memes["pride"] += 1
            hero.memes["kindness"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="sadness", tag="social", apply=_r_sadness),
    Rule(name="sharing_relief", tag="social", apply=_r_sharing_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "schoolyard": Place(
        id="schoolyard",
        label="schoolyard",
        phrase="the sunny schoolyard beside the swings",
        tags={"school"},
    ),
    "classroom": Place(
        id="classroom",
        label="classroom",
        phrase="the bright classroom with paper stars on the wall",
        tags={"school"},
    ),
    "library": Place(
        id="library",
        label="library",
        phrase="the quiet library corner with a hero rug",
        tags={"books"},
    ),
}

HERO_ITEMS = {
    "apple": HeroItem(
        id="apple",
        label="apple",
        phrase="a shiny red apple",
        kind="food",
        shareable=True,
        snack_like=True,
        school_like=False,
        divisible=True,
        method="broke the apple in two even pieces",
        ending_image="two children crunching apple slices like a tiny hero picnic",
        tags={"food", "sharing", "snack"},
    ),
    "sandwich": HeroItem(
        id="sandwich",
        label="sandwich",
        phrase="a cheese sandwich cut into neat triangles",
        kind="food",
        shareable=True,
        snack_like=True,
        school_like=False,
        divisible=True,
        method="offered one triangle, then another, until they both had enough",
        ending_image="two small caped heroes sitting knee to knee with sandwich crumbs and smiles",
        tags={"food", "sharing", "snack"},
    ),
    "crayons": HeroItem(
        id="crayons",
        label="crayons",
        phrase="a small box of bright crayons",
        kind="tool",
        shareable=True,
        snack_like=False,
        school_like=True,
        divisible=False,
        method="opened the box and slid half the colors across the table",
        ending_image="two superhero drawings glowing with the same brave colors",
        tags={"school", "sharing", "art"},
    ),
    "stickers": HeroItem(
        id="stickers",
        label="stickers",
        phrase="a sheet of star stickers",
        kind="tool",
        shareable=True,
        snack_like=False,
        school_like=True,
        divisible=True,
        method="peeled off some star stickers and shared them one by one",
        ending_image="two papers sparkling with silver stars",
        tags={"school", "sharing", "stars"},
    ),
    "cape": HeroItem(
        id="cape",
        label="cape",
        phrase="a swoopy superhero cape",
        kind="costume",
        shareable=False,
        snack_like=False,
        school_like=False,
        divisible=False,
        method="",
        ending_image="",
        tags={"costume"},
    ),
}

NEEDS = {
    "snack": Need(
        id="snack",
        label="snack",
        phrase="no snack at all",
        wants_snack_like=True,
        wants_school_like=False,
        reason="forgot to bring a snack",
        tags={"food", "care"},
    ),
    "lunchbox_spill": Need(
        id="lunchbox_spill",
        label="snack",
        phrase="a lunchbox that had spilled and left no bite to eat",
        wants_snack_like=True,
        wants_school_like=False,
        reason="the lunchbox had tipped over and the food was ruined",
        tags={"food", "care"},
    ),
    "drawing": Need(
        id="drawing",
        label="colors",
        phrase="plain paper and no colors for the hero picture",
        wants_snack_like=False,
        wants_school_like=True,
        reason="could not find any colors for drawing time",
        tags={"school", "art"},
    ),
    "project": Need(
        id="stickers",
        label="stickers",
        phrase="a project page with no stickers to finish it",
        wants_snack_like=False,
        wants_school_like=True,
        reason="needed something bright for the class project",
        tags={"school", "art"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli"]
COLORS = ["red", "blue", "gold", "purple"]
TRAITS = ["brave", "kind", "quick", "thoughtful", "cheerful"]


def item_matches_need(item: HeroItem, need: Need) -> bool:
    return item.shareable and (
        (item.snack_like and need.wants_snack_like)
        or (item.school_like and need.wants_school_like)
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for item_id, item in HERO_ITEMS.items():
            for need_id, need in NEEDS.items():
                if item_matches_need(item, need):
                    combos.append((place_id, item_id, need_id))
    return combos


def explain_rejection(item: HeroItem, need: Need) -> str:
    if not item.shareable:
        return (
            f"(No story: {item.phrase} is not a practical sharing solution for a friend who has "
            f"{need.phrase}. Pick something that can truly be shared.)"
        )
    return (
        f"(No story: {item.label} does not meet this need. A good sharing story needs the shared "
        f"item to actually help with the friend's problem.)"
    )


def choose_names(rng: random.Random) -> tuple[str, str, str, str]:
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    hero_name = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    pool = [n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != hero_name]
    friend_name = rng.choice(pool)
    return hero_name, hero_gender, friend_name, friend_gender


def introduce(world: World, hero: Entity, place: Place, color: str, trait: str) -> None:
    hero.memes["joy"] += 1
    hero.memes["heroic"] += 1
    world.say(
        f"Every morning, {hero.id} liked to pull on {hero.pronoun('possessive')} {color} backpack "
        f"and imagine it was a hero pack. At {place.phrase}, {hero.pronoun()} was known as "
        f"Captain {hero.id}, the {trait} little superhero."
    )
    world.say(
        f"{hero.pronoun().capitalize()} did not fight dragons or robots. {hero.pronoun().capitalize()} "
        f"looked for small troubles that appeared in ordinary places."
    )
    world.log("hero_introduced")


def bring_item(world: World, hero: Entity, item_cfg: HeroItem) -> None:
    item = world.get("item")
    item.meters["whole"] = 1
    hero.meters["has_item"] = 1
    world.say(
        f"That day, Captain {hero.id} carried {item_cfg.phrase} in {hero.pronoun('possessive')} bag. "
        f"To {hero.pronoun('object')}, it felt like special hero equipment."
    )
    world.log("item_brought")


def reveal_need(world: World, friend: Entity, need_cfg: Need) -> None:
    friend.meters["without"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Near the play table, {friend.id} looked down at {need_cfg.phrase}. "
        f"{friend.pronoun().capitalize()} had {need_cfg.reason}."
    )
    if friend.memes["about_to_weep"] >= THRESHOLD:
        world.say(
            f"{friend.id}'s eyes grew shiny, and {friend.pronoun()} looked ready to weep."
        )
    world.log("need_revealed")


def hesitate(world: World, hero: Entity, item_cfg: HeroItem, friend: Entity) -> None:
    hero.memes["selfish_pull"] += 1
    world.say(
        f"For one quiet moment, Captain {hero.id} held onto the {item_cfg.label}. "
        f"{hero.pronoun().capitalize()} had wanted it all for {hero.pronoun('object')}self."
    )
    world.say(
        f"But heroes notice faces, and {hero.pronoun()} noticed {friend.id}'s trembling lip."
    )
    world.log("hero_hesitated")


def share(world: World, hero: Entity, friend: Entity, item_cfg: HeroItem, need_cfg: Need) -> None:
    hero.meters["shared_amount"] += 1
    friend.meters["received"] += 1
    propagate(world, narrate=False)
    if item_cfg.divisible:
        detail = item_cfg.method
    else:
        detail = item_cfg.method
    world.say(
        f"Then Captain {hero.id} made a better choice. {hero.pronoun().capitalize()} {detail}."
    )
    if need_cfg.wants_snack_like:
        world.say(
            f'"Here," {hero.pronoun()} said. "A superhero never lets a friend stay hungry alone."'
        )
    else:
        world.say(
            f'"Here," {hero.pronoun()} said. "A superhero makes room at the table and shares the bright parts."'
        )
    world.log("shared")


def comfort(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["care"] += 1
    friend.memes["gratitude"] += 1
    world.say(
        f"{friend.id} did not weep after all. The worry slid out of {friend.pronoun('possessive')} face, "
        f"and a smile came back instead."
    )
    world.say(
        f"Soon the two children sat shoulder to shoulder, and the room felt lighter because "
        f"one small act had changed it."
    )
    world.log("comforted")


def adult_notice(world: World, adult: Entity, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{adult.label_word.capitalize()} saw what had happened and smiled. "
        f'"That is real superhero work," {adult.pronoun()} said. "You used what you had to help."'
    )
    hero.memes["seen"] += 1
    world.log("adult_noticed")


def daily_resolution(world: World, hero: Entity, item_cfg: HeroItem) -> None:
    hero.memes["habit"] += 1
    world.say(
        f"On the way home, Captain {hero.id} decided something new. {hero.pronoun().capitalize()} would look, "
        f"every daily school morning, for one person who might need a hand."
    )
    world.say(
        f"After that, sharing became part of {hero.pronoun('possessive')} secret hero code. "
        f"Sometimes the mission was half a snack, sometimes a few colors, but it always began with noticing."
    )
    world.say(
        f"And the next day, {item_cfg.ending_image}."
    )
    world.log("daily_vow")


def tell(
    place_cfg: Place,
    item_cfg: HeroItem,
    need_cfg: Need,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    adult_type: str,
    costume_color: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label="the adult", role="adult"))
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type=item_cfg.kind,
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            shareable=item_cfg.shareable,
            snack_like=item_cfg.snack_like,
            school_like=item_cfg.school_like,
            divisible=item_cfg.divisible,
            tags=set(item_cfg.tags),
        )
    )

    world.facts.update(
        place_cfg=place_cfg,
        item_cfg=item_cfg,
        need_cfg=need_cfg,
        costume_color=costume_color,
        trait=trait,
    )

    introduce(world, hero, place_cfg, costume_color, trait)
    bring_item(world, hero, item_cfg)

    world.para()
    reveal_need(world, friend, need_cfg)
    hesitate(world, hero, item_cfg, friend)

    world.para()
    share(world, hero, friend, item_cfg, need_cfg)
    comfort(world, hero, friend)
    adult_notice(world, adult, hero, friend)

    world.para()
    daily_resolution(world, hero, item_cfg)

    world.facts.update(
        hero=hero,
        friend=friend,
        adult=adult,
        item=item,
        shared=hero.meters["shared_amount"] >= THRESHOLD,
        friend_wept=friend.memes["about_to_weep"] >= THRESHOLD and friend.meters["received"] < THRESHOLD,
        friend_almost_wept="need_revealed" in world.events,
        daily_habit=hero.memes["habit"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting someone else use or have part of something you have. It is a kind way to help when another person needs some too."
        )
    ],
    "superhero": [
        (
            "Does a superhero always need powers?",
            "No. A superhero can also be someone who notices trouble and helps bravely. Kind choices can be heroic even without flying or lasers."
        )
    ],
    "weep": [
        (
            "What does weep mean?",
            "To weep means to cry, especially when someone feels very sad. In a gentle story, it can also mean someone is close to crying."
        )
    ],
    "daily": [
        (
            "What does daily mean?",
            "Daily means something happens every day, as part of a regular habit. A daily kindness is one you try to do again and again."
        )
    ],
    "snack": [
        (
            "Why can sharing food help?",
            "Sharing food can help when someone is hungry and has none. It can make their body feel better and also help them feel cared for."
        )
    ],
    "crayons": [
        (
            "Why can sharing crayons be helpful?",
            "Sharing crayons helps another child join a drawing activity. It lets both children make pictures instead of one child being left out."
        )
    ],
    "stickers": [
        (
            "Why do children like stickers?",
            "Stickers are bright little decorations children can put on paper or cards. Sharing them can make a project feel fun and finished."
        )
    ],
}

KNOWLEDGE_ORDER = ["sharing", "superhero", "weep", "daily", "snack", "crayons", "stickers"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item_cfg = f["item_cfg"]
    need_cfg = f["need_cfg"]
    place_cfg = f["place_cfg"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the words "weep" and "daily" and centers on sharing.',
        f"Tell a gentle story where {hero.label} imagines being a superhero at {place_cfg.label}, sees that {friend.label} has {need_cfg.phrase}, and shares {item_cfg.label}.",
        f'Write a child-friendly story in which the greatest superpower is kindness, and the ending turns one shared {item_cfg.label} into a daily habit of helping.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    adult = f["adult"]
    item_cfg = f["item_cfg"]
    need_cfg = f["need_cfg"]
    place_cfg = f["place_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who imagined being a little superhero, and {friend.label}, who needed help at {place_cfg.label}. The grown-up also noticed the kind choice at the end."
        ),
        (
            f"Why did {friend.label} look ready to weep?",
            f"{friend.label} had {need_cfg.phrase} because {need_cfg.reason}. That made {friend.pronoun('object')} feel left out and close to crying."
        ),
        (
            f"Why did {hero.label} hesitate before sharing?",
            f"{hero.label} first wanted to keep the whole {item_cfg.label}. Then {hero.pronoun()} noticed {friend.label}'s face and understood that being heroic meant helping, not holding on."
        ),
        (
            f"How did {hero.label} help {friend.label}?",
            f"{hero.pronoun().capitalize()} shared the {item_cfg.label} in a way that actually fit the problem. Because the shared thing met {friend.label}'s need, the sadness lifted right away."
        ),
        (
            "What made this a superhero story?",
            f"The hero did not use magic beams or punches. The brave act was noticing a problem and using kindness to change what happened."
        ),
    ]
    if f.get("daily_habit"):
        qa.append(
            (
                f"What did {hero.label} decide to do daily?",
                f"{hero.pronoun().capitalize()} decided to look every day for one person who might need help. The story ends by turning one sharing moment into a daily hero habit."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sharing", "superhero", "weep", "daily"}
    item_cfg = f["item_cfg"]
    if item_cfg.snack_like:
        tags.add("snack")
    if item_cfg.id == "crayons":
        tags.add("crayons")
    if item_cfg.id == "stickers":
        tags.add("stickers")
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
    for ent in world.entities.values():
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
        flags = []
        if ent.shareable:
            flags.append("shareable")
        if ent.snack_like:
            flags.append("snack_like")
        if ent.school_like:
            flags.append("school_like")
        if ent.divisible:
            flags.append("divisible")
        if flags:
            bits.append(f"flags={flags}")
        shown = ent.label or ent.id
        lines.append(f"  {shown:12} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  events: {world.events}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
share_fit(I, N) :- shareable(I), snack_like(I), need_snack(N).
share_fit(I, N) :- shareable(I), school_like(I), need_school(N).
valid(P, I, N)  :- place(P), item(I), need(N), share_fit(I, N).

sad(friend)     :- chosen_need(N), need(N), valid_need(N).
valid_need(N)   :- need(N).

shared          :- chosen_item(I), chosen_need(N), share_fit(I, N).
daily_habit     :- shared.
story_ok        :- chosen_place(P), chosen_item(I), chosen_need(N), valid(P, I, N), shared, daily_habit.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, item in HERO_ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.shareable:
            lines.append(asp.fact("shareable", iid))
        if item.snack_like:
            lines.append(asp.fact("snack_like", iid))
        if item.school_like:
            lines.append(asp.fact("school_like", iid))
    for nid, need in NEEDS.items():
        lines.append(asp.fact("need", nid))
        if need.wants_snack_like:
            lines.append(asp.fact("need_snack", nid))
        if need.wants_school_like:
            lines.append(asp.fact("need_school", nid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_story_ok(params: StoryParams) -> bool:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_item", params.hero_item),
        asp.fact("chosen_need", params.friend_need),
    ])
    model = asp.one_model(asp_program(extra, "#show story_ok/0."))
    return bool(asp.atoms(model, "story_ok"))


CURATED = [
    StoryParams(
        place="schoolyard",
        hero_item="apple",
        friend_need="snack",
        hero_name="Lily",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        adult_type="teacher",
        costume_color="red",
        trait="brave",
    ),
    StoryParams(
        place="classroom",
        hero_item="crayons",
        friend_need="drawing",
        hero_name="Max",
        hero_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        adult_type="teacher",
        costume_color="blue",
        trait="thoughtful",
    ),
    StoryParams(
        place="library",
        hero_item="stickers",
        friend_need="project",
        hero_name="Ava",
        hero_gender="girl",
        friend_name="Noah",
        friend_gender="boy",
        adult_type="teacher",
        costume_color="gold",
        trait="kind",
    ),
    StoryParams(
        place="schoolyard",
        hero_item="sandwich",
        friend_need="lunchbox_spill",
        hero_name="Sam",
        hero_gender="boy",
        friend_name="Ella",
        friend_gender="girl",
        adult_type="teacher",
        costume_color="purple",
        trait="quick",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a little superhero learns that sharing can be daily hero work."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-item", choices=HERO_ITEMS)
    ap.add_argument("--friend-need", choices=NEEDS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--adult-type", choices=["mother", "father", "teacher"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hero_item and args.friend_need:
        item = HERO_ITEMS[args.hero_item]
        need = NEEDS[args.friend_need]
        if not item_matches_need(item, need):
            raise StoryError(explain_rejection(item, need))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.hero_item is None or combo[1] == args.hero_item)
        and (args.friend_need is None or combo[2] == args.friend_need)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, hero_item, friend_need = rng.choice(sorted(combos))
    hero_name, hero_gender, friend_name, friend_gender = choose_names(rng)

    if args.hero_gender is not None:
        hero_gender = args.hero_gender
        hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elif args.hero_name is not None:
        hero_name = args.hero_name

    if args.friend_gender is not None:
        friend_gender = args.friend_gender
        pool = [n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != hero_name]
        friend_name = args.friend_name or rng.choice(pool)
    elif args.friend_name is not None:
        friend_name = args.friend_name

    if friend_name == hero_name:
        pool = [n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != hero_name]
        if not pool:
            raise StoryError("(No valid distinct friend name available.)")
        friend_name = rng.choice(pool)

    adult_type = args.adult_type or "teacher"
    costume_color = rng.choice(COLORS)
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place,
        hero_item=hero_item,
        friend_need=friend_need,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        adult_type=adult_type,
        costume_color=costume_color,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.hero_item not in HERO_ITEMS:
        raise StoryError(f"(Unknown hero item: {params.hero_item})")
    if params.friend_need not in NEEDS:
        raise StoryError(f"(Unknown friend need: {params.friend_need})")
    item_cfg = HERO_ITEMS[params.hero_item]
    need_cfg = NEEDS[params.friend_need]
    if not item_matches_need(item_cfg, need_cfg):
        raise StoryError(explain_rejection(item_cfg, need_cfg))

    world = tell(
        place_cfg=PLACES[params.place],
        item_cfg=item_cfg,
        need_cfg=need_cfg,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        adult_type=params.adult_type,
        costume_color=params.costume_color,
        trait=params.trait,
    )
    story = world.render().replace("hero", "hero")
    return StorySample(
        params=params,
        story=story,
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

    for params in CURATED:
        try:
            ok = asp_story_ok(params)
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if not ok:
                raise StoryError("ASP story_ok failed on curated params")
        except Exception as exc:
            rc = 1
            print(f"SMOKE TEST FAILED for curated sample {params}: {exc}")
            break
    else:
        print(f"OK: smoke-tested generation on {len(CURATED)} curated stories.")

    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(7))
        default_params.seed = 7
        sample = generate(default_params)
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: default random generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, hero_item, friend_need) combos:\n")
        for place, item, need in combos:
            print(f"  {place:10} {item:10} {need}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.hero_name}: {p.hero_item} for {p.friend_need} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
