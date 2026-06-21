#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/savings_bustle_friendship_moral_value_kindness_heartwarming.py
==========================================================================================

A standalone story world about a child bringing hard-earned savings into a busy,
bustling little market or fair, then choosing kindness when a friend suddenly
needs help. The world model tracks coins, needs, and feelings, then renders a
heartwarming story whose turn comes from the simulated state: sometimes the hero
can help a friend and still buy the planned treat, and sometimes the hero gives
up the treat and discovers that friendship feels warmer than keeping every coin.

Run it
------
    python storyworlds/worlds/gpt-5.4/savings_bustle_friendship_moral_value_kindness_heartwarming.py
    python storyworlds/worlds/gpt-5.4/savings_bustle_friendship_moral_value_kindness_heartwarming.py --setting market_square --need notebook
    python storyworlds/worlds/gpt-5.4/savings_bustle_friendship_moral_value_kindness_heartwarming.py --savings button_tin --wish pinwheel
    python storyworlds/worlds/gpt-5.4/savings_bustle_friendship_moral_value_kindness_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/savings_bustle_friendship_moral_value_kindness_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4/savings_bustle_friendship_moral_value_kindness_heartwarming.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    bustle: str
    afford_wishes: set[str] = field(default_factory=set)
    afford_needs: set[str] = field(default_factory=set)
    gift: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class SavingsPlan:
    id: str
    phrase: str
    coins: int
    source: str
    container: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Wish:
    id: str
    label: str
    phrase: str
    cost: int
    delight: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    label: str
    phrase: str
    cost: int
    shortage: int
    reason: str
    consequence: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

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
        clone.history = list(self.history)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_need_met(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    need = world.get("need")
    if need.meters["bought"] >= THRESHOLD and ("need_met",) not in world.fired:
        world.fired.add(("need_met",))
        friend.memes["relief"] += 1
        friend.memes["included"] += 1
        hero.memes["kindness"] += 1
        hero.memes["warmth"] += 1
        out.append("__need_met__")
    return out


def _r_kindness_bond(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["kindness"] >= THRESHOLD and ("bond",) not in world.fired:
        world.fired.add(("bond",))
        hero.memes["friendship"] += 1
        friend.memes["friendship"] += 1
        friend.memes["gratitude"] += 1
        out.append("__bond__")
    return out


def _r_skipped_wish(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    wish = world.get("wish")
    if hero.meters["coins"] < wish.attrs["cost"] and wish.meters["bought"] < THRESHOLD:
        if ("skip",) not in world.fired:
            world.fired.add(("skip",))
            hero.memes["disappointment"] += 1
            out.append("__skip__")
    return out


CAUSAL_RULES = [
    Rule("need_met", "social", _r_need_met),
    Rule("kindness_bond", "social", _r_kindness_bond),
    Rule("skipped_wish", "emotional", _r_skipped_wish),
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


def sold_here(setting: Setting, wish: Wish, need: Need) -> bool:
    return wish.id in setting.afford_wishes and need.id in setting.afford_needs


def can_help(plan: SavingsPlan, need: Need) -> bool:
    return plan.coins >= need.cost


def can_really_want(plan: SavingsPlan, wish: Wish) -> bool:
    return plan.coins >= wish.cost


def valid_choice(setting: Setting, plan: SavingsPlan, wish: Wish, need: Need) -> bool:
    return sold_here(setting, wish, need) and can_help(plan, need) and can_really_want(plan, wish)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for pid, plan in SAVINGS.items():
            for wid, wish in WISHES.items():
                for nid, need in NEEDS.items():
                    if valid_choice(setting, plan, wish, need):
                        combos.append((sid, pid, wid, nid))
    return combos


def need_text(text: str, friend: Entity) -> str:
    return text.format(friend=friend.id, poss=friend.pronoun("possessive"))


def outcome_of(params: "StoryParams") -> str:
    plan = SAVINGS[params.savings]
    wish = WISHES[params.wish]
    need = NEEDS[params.need]
    if plan.coins >= wish.cost + need.cost:
        return "both"
    return "friend_first"


def predict_without_help(world: World) -> dict:
    sim = world.copy()
    friend = sim.get("friend")
    need = sim.get("need")
    if need.meters["bought"] < THRESHOLD:
        friend.memes["worry"] += 1
        friend.memes["left_out"] += 1
    return {
        "left_out": friend.memes["left_out"] >= THRESHOLD,
        "worry": friend.memes["worry"],
    }


def introduce(world: World, hero: Entity, friend: Entity, parent: Entity, plan: SavingsPlan) -> None:
    world.say(
        f"{hero.id} and {friend.id} walked with {hero.pronoun('possessive')} {parent.label_word} into {world.setting.place}. "
        f"The whole place hummed with bustle as {world.setting.bustle}."
    )
    world.say(
        f"In {hero.pronoun('possessive')} pocket, {hero.id} carried {plan.phrase}. "
        f"{hero.pronoun().capitalize()} had built those savings {plan.source}, and each coin felt important."
    )
    hero.meters["coins"] = float(plan.coins)
    hero.memes["pride"] += 1
    world.history.append("hero_arrived_with_savings")


def desire(world: World, hero: Entity, wish: Wish) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"Near one bright stall, {hero.id} spotted {wish.phrase}. "
        f"{hero.pronoun().capitalize()} had been hoping for it because {wish.delight}."
    )
    world.say(f"{hero.id} quietly counted the coins again and smiled.")
    world.history.append("hero_wanted_wish")


def friend_problem(world: World, friend: Entity, need: Need) -> None:
    friend.memes["worry"] += 1
    world.say(
        f"Then {friend.id} stopped at another table and looked down at {need.phrase}. "
        f"{friend.pronoun().capitalize()} whispered that {need_text(need.reason, friend)}."
    )
    world.say(
        f"But {friend.pronoun('possessive')} hand only held part of the price, and {friend.pronoun()} was short by {need.shortage} coin"
        f"{'' if need.shortage == 1 else 's'}."
    )
    world.history.append("friend_was_short")


def warning_beat(world: World, hero: Entity, friend: Entity, need: Need) -> None:
    pred = predict_without_help(world)
    world.facts["predicted_left_out"] = pred["left_out"]
    hero.memes["concern"] += 1
    if pred["left_out"]:
        world.say(
            f"{hero.id} looked at {friend.id}'s face and could almost see what would happen next: {need_text(need.consequence, friend)}."
        )
    else:
        world.say(f"{hero.id} could tell that {friend.id} was worried.")
    world.history.append("hero_predicted_loss")


def choose_kindness(world: World, hero: Entity, friend: Entity, wish: Wish, need: Entity, need_cfg: Need) -> None:
    world.say(
        f"{hero.id} curled {hero.pronoun('possessive')} fingers around the savings for a moment. "
        f"{hero.pronoun().capitalize()} still wanted {wish.label}, but friendship tugged harder."
    )
    gift = need_cfg.cost
    hero.meters["coins"] -= float(gift)
    friend.meters["coins"] += float(gift)
    need.meters["bought"] += 1
    hero.memes["kindness"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Here," {hero.id} said, tipping the coins into {friend.id}\'s palm. '
        f'"You can use my savings today."'
    )
    world.say(
        f"{friend.id}'s shoulders softened at once. Together they paid for {need_cfg.phrase}."
    )
    world.history.append("hero_shared_savings")


def buy_wish(world: World, hero: Entity, wish: Entity, wish_cfg: Wish) -> None:
    hero.meters["coins"] -= float(wish_cfg.cost)
    wish.meters["bought"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"There were still enough coins left, so {hero.id} also bought {wish_cfg.phrase}. "
        f"{hero.pronoun().capitalize()} held it carefully, smiling even wider now."
    )
    world.history.append("hero_bought_wish")


def skip_wish(world: World, hero: Entity, friend: Entity, wish: Wish) -> None:
    propagate(world, narrate=False)
    world.say(
        f"When {hero.id} looked back at the stall with {wish.phrase}, the coins left were not enough."
    )
    if hero.memes["disappointment"] >= THRESHOLD:
        world.say(
            f"For one small moment, {hero.pronoun('possessive')} heart pinched. Then {hero.id} saw {friend.id} holding {world.get('need').label} with a relieved smile, and the pinch turned warm."
        )
    world.history.append("hero_skipped_wish")


def ending_both(world: World, hero: Entity, friend: Entity, wish: Wish, need: Need) -> None:
    friend.memes["joy"] += 1
    hero.memes["contentment"] += 1
    world.say(
        f"Soon the two friends were walking through the bustle side by side, {friend.id} carrying {need.phrase} and {hero.id} carrying {wish.phrase}."
    )
    world.say(
        f"{friend.id} bumped shoulders with {hero.id} and said that kind friends make busy places feel gentle. {hero.id} knew the savings had done something better than buy a thing all by themselves."
    )
    world.history.append("ending_both")


def ending_friend_first(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["contentment"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"The stallkeeper had seen everything. With a soft smile, {friend.id} was given {setting.gift} to share, just because kindness had brightened the table."
    )
    world.say(
        f"So the friends walked back into the bustle together, sharing {setting.gift} and talking closely. {hero.id} had fewer coins than before, but a fuller heart."
    )
    world.history.append("ending_friend_first")


def tell(
    setting: Setting,
    plan: SavingsPlan,
    wish: Wish,
    need: Need,
    hero_name: str = "Mia",
    hero_type: str = "girl",
    friend_name: str = "Ben",
    friend_type: str = "boy",
    parent_type: str = "mother",
    friend_trait: str = "gentle",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend", traits=[friend_trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    wish_ent = world.add(Entity(id="wish", type="wish", label=wish.label, phrase=wish.phrase, attrs={"cost": wish.cost}))
    need_ent = world.add(Entity(id="need", type="need", label=need.label, phrase=need.phrase, attrs={"cost": need.cost}))

    introduce(world, hero, friend, parent, plan)
    desire(world, hero, wish)

    world.para()
    friend_problem(world, friend, need)
    warning_beat(world, hero, friend, need)

    world.para()
    choose_kindness(world, hero, friend, wish, need_ent, need)
    if plan.coins >= wish.cost + need.cost:
        buy_wish(world, hero, wish_ent, wish)
        world.para()
        ending_both(world, hero, friend, wish, need)
        outcome = "both"
    else:
        skip_wish(world, hero, friend, wish)
        world.para()
        ending_friend_first(world, hero, friend, setting)
        outcome = "friend_first"

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        plan=plan,
        wish_cfg=wish,
        need_cfg=need,
        setting=setting,
        outcome=outcome,
        shared_amount=need.cost,
        remaining_coins=int(hero.meters["coins"]),
        bought_need=True,
        bought_wish=world.get("wish").meters["bought"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "market_square": Setting(
        "market_square",
        "the market square",
        "bakers calling out, baskets rustling, and little shoes pattering between flower buckets",
        afford_wishes={"pinwheel", "honey_cake", "ribbon"},
        afford_needs={"notebook", "seed_packet", "muffin_ticket"},
        gift="a warm paper cup of apple cider",
        tags={"market", "bustle"},
    ),
    "school_fair": Setting(
        "school_fair",
        "the school fair",
        "parents chatting, raffle bells chiming, and paper flags fluttering above the game tables",
        afford_wishes={"sticker_book", "honey_cake", "ribbon"},
        afford_needs={"notebook", "muffin_ticket"},
        gift="a gold star cookie",
        tags={"fair", "bustle"},
    ),
    "garden_sale": Setting(
        "garden_sale",
        "the church garden sale",
        "watering cans clinking, neighbors laughing, and bees bobbing around herb pots",
        afford_wishes={"pinwheel", "ribbon"},
        afford_needs={"seed_packet", "muffin_ticket"},
        gift="a little paper posy tied with string",
        tags={"garden", "bustle"},
    ),
}

SAVINGS = {
    "button_tin": SavingsPlan(
        "button_tin",
        "a button tin with 4 bright coins",
        4,
        "by helping fold towels and putting away blocks",
        "button tin",
        tags={"savings"},
    ),
    "blue_jar": SavingsPlan(
        "blue_jar",
        "a blue jar with 5 bright coins",
        5,
        "one careful chore at a time",
        "blue jar",
        tags={"savings"},
    ),
    "striped_pouch": SavingsPlan(
        "striped_pouch",
        "a striped pouch with 6 bright coins",
        6,
        "over many patient Saturdays",
        "striped pouch",
        tags={"savings"},
    ),
    "paper_envelope": SavingsPlan(
        "paper_envelope",
        "a paper envelope with 7 bright coins",
        7,
        "by saving tiny bits instead of spending them right away",
        "paper envelope",
        tags={"savings"},
    ),
}

WISHES = {
    "pinwheel": Wish(
        "pinwheel",
        "a pinwheel",
        "a rainbow pinwheel",
        4,
        "it would spin like a small happy windmill in the air",
        tags={"toy"},
    ),
    "honey_cake": Wish(
        "honey_cake",
        "a honey cake",
        "a small honey cake",
        3,
        "it smelled sweet and warm enough to make the whole day feel golden",
        tags={"treat"},
    ),
    "ribbon": Wish(
        "ribbon",
        "a ribbon wand",
        "a ribbon wand",
        5,
        "the long ribbon would dance behind every skip",
        tags={"toy"},
    ),
    "sticker_book": Wish(
        "sticker_book",
        "a sticker book",
        "a tiny sticker book",
        4,
        "each shiny page looked like a pocketful of celebration",
        tags={"book"},
    ),
}

NEEDS = {
    "notebook": Need(
        "notebook",
        "a notebook",
        "a plain notebook",
        3,
        2,
        "the class writing table had opened, but without a notebook there would be nowhere to keep the pages",
        "{friend} would have to stand aside and watch the writing table instead of joining in",
        tags={"school"},
    ),
    "seed_packet": Need(
        "seed_packet",
        "a seed packet",
        "a packet of sunflower seeds",
        4,
        1,
        "{friend} had promised to bring seeds for the shared planting tray",
        "{friend} would have an empty space in the planting tray while everyone else pressed seeds into the soil",
        tags={"garden"},
    ),
    "muffin_ticket": Need(
        "muffin_ticket",
        "a muffin ticket",
        "a blueberry muffin ticket",
        2,
        1,
        "{friend}'s coin had rolled under a stall, and snack time was almost there",
        "{friend} would have to sit at snack time with empty hands while the others nibbled and chatted",
        tags={"food"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Ella", "Zoe", "Lucy", "Anna"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Finn", "Noah", "Jack", "Theo"]
TRAITS = ["gentle", "cheerful", "patient", "thoughtful", "sunny"]


@dataclass
class StoryParams:
    setting: str
    savings: str
    wish: str
    need: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
    friend_trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "savings": [
        (
            "What are savings?",
            "Savings are coins or money you keep and do not spend right away. You save them little by little for something you may need or want later."
        )
    ],
    "bustle": [
        (
            "What does bustle mean?",
            "Bustle means a place is busy and full of moving, talking, and little sounds. A bustling market or fair feels lively because many people are doing things at once."
        )
    ],
    "market": [
        (
            "What is a market?",
            "A market is a place where people sell things like food, flowers, and small goods. It can feel colorful and busy because many stalls are close together."
        )
    ],
    "fair": [
        (
            "What is a fair?",
            "A fair is a cheerful event with tables, games, food, or things to buy. Families and friends often visit fairs together."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help or comfort someone. Sometimes it means giving up a small thing of your own to make someone else's day better."
        )
    ],
    "friendship": [
        (
            "Why does kindness help friendship grow?",
            "Kindness helps friendship grow because it shows you care about how your friend feels. When people help each other, trust and warmth get stronger."
        )
    ],
    "notebook": [
        (
            "What is a notebook for?",
            "A notebook is for keeping writing or drawings together on pages. It helps you save your ideas in one place."
        )
    ],
    "seed_packet": [
        (
            "What is a seed packet?",
            "A seed packet holds little seeds that can be planted in soil. With water and sunlight, the seeds may grow into plants."
        )
    ],
    "muffin_ticket": [
        (
            "What is a snack ticket?",
            "A snack ticket is a small paper ticket you trade for food at an event. It helps the seller know what has been paid for."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "savings",
    "bustle",
    "market",
    "fair",
    "kindness",
    "friendship",
    "notebook",
    "seed_packet",
    "muffin_ticket",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    wish = f["wish_cfg"]
    need = f["need_cfg"]
    setting = f["setting"]
    if f["outcome"] == "both":
        return [
            f'Write a heartwarming story for a 3-to-5-year-old that includes the words "savings" and "bustle". Set it at {setting.place}, where {hero.id} uses savings to help a friend and still buys {wish.phrase}.',
            f"Tell a gentle friendship story where {hero.id} wants {wish.phrase}, but first shares money so {friend.id} can get {need.phrase}.",
            f'Write a story about kindness and moral value in a busy place, ending with two friends walking happily together through the bustle.'
        ]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words "savings" and "bustle". Set it at {setting.place}, where {hero.id} gives up {wish.phrase} to help {friend.id}.',
        f"Tell a friendship story where {hero.id} has just enough savings for one special thing, then chooses kindness when {friend.id} needs {need.phrase}.",
        f'Write a simple moral story showing that a full heart can matter more than full pockets.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    plan = f["plan"]
    wish = f["wish_cfg"]
    need = f["need_cfg"]
    outcome = f["outcome"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two friends at {f['setting'].place}, and {hero.id}'s {pw}. The story follows what {hero.id} does with {hero.pronoun('possessive')} savings."
        ),
        (
            f"What had {hero.id} been saving?",
            f"{hero.id} had been carrying {plan.phrase}. Those savings mattered because {hero.pronoun()} had built them slowly {plan.source}."
        ),
        (
            f"What did {hero.id} want at first?",
            f"{hero.id} wanted {wish.phrase}. {hero.pronoun().capitalize()} had been hoping for it because {wish.delight}."
        ),
        (
            f"Why was {friend.id} worried?",
            f"{friend.id} was worried because {need_text(need.reason, friend)}. {friend.pronoun().capitalize()} was short by {need.shortage} coin{'' if need.shortage == 1 else 's'}, so getting {need.label} suddenly felt hard."
        ),
        (
            f"Why did {hero.id} decide to share the savings?",
            f"{hero.id} could see that without help, {need_text(need.consequence, friend)}. That is why friendship tugged harder than buying {wish.label} first."
        ),
    ]
    if outcome == "both":
        qa.append(
            (
                f"What happened after {hero.id} helped {friend.id}?",
                f"There were still enough coins left, so {hero.id} also bought {wish.phrase}. The ending shows kindness did not shrink the day; it made the day bigger for both friends."
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.id} still buy {wish.label}?",
                f"No. After helping {friend.id}, there were not enough coins left for {wish.phrase}. For a moment that felt hard, but seeing {friend.id}'s relieved smile made the choice feel warm and right."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The stallkeeper noticed the kind choice and gave the friends {f['setting'].gift} to share. The ending proves that kindness can leave a heart fuller even when a pocket is lighter."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"savings", "bustle", "kindness", "friendship"}
    setting = world.facts["setting"]
    if "market" in setting.tags:
        tags.add("market")
    if "fair" in setting.tags:
        tags.add("fair")
    tags.add(world.facts["need_cfg"].id)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  history: {world.history}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("market_square", "button_tin", "pinwheel", "muffin_ticket", "Mia", "girl", "Ben", "boy", "mother", "gentle"),
    StoryParams("market_square", "paper_envelope", "honey_cake", "seed_packet", "Leo", "boy", "Nora", "girl", "father", "thoughtful"),
    StoryParams("school_fair", "blue_jar", "sticker_book", "notebook", "Ava", "girl", "Sam", "boy", "mother", "patient"),
    StoryParams("garden_sale", "striped_pouch", "ribbon", "seed_packet", "Finn", "boy", "Ella", "girl", "father", "cheerful"),
]


def explain_rejection(setting: Setting, plan: SavingsPlan, wish: Wish, need: Need) -> str:
    if wish.id not in setting.afford_wishes:
        return (
            f"(No story: {wish.phrase} is not sold at {setting.place}. Pick a wish that belongs in this setting.)"
        )
    if need.id not in setting.afford_needs:
        return (
            f"(No story: {need.phrase} is not the kind of need this setting supports. Pick a need that fits {setting.place}.)"
        )
    if plan.coins < need.cost:
        return (
            f"(No story: {plan.phrase} does not hold enough coins to help with {need.phrase}. The world insists that the kindness choice must actually be possible.)"
        )
    if plan.coins < wish.cost:
        return (
            f"(No story: {plan.phrase} is not enough to buy {wish.phrase} in the first place, so there is no honest temptation between self and kindness.)"
        )
    return "(No story: this combination is not reasonable in the world model.)"


ASP_RULES = r"""
sold_here(S, W, N) :- setting(S), wish(W), need(N), sells_wish(S, W), supports_need(S, N).
can_help(P, N) :- savings(P), need(N), coins(P, C), need_cost(N, K), C >= K.
can_really_want(P, W) :- savings(P), wish(W), coins(P, C), wish_cost(W, K), C >= K.

valid(S, P, W, N) :- sold_here(S, W, N), can_help(P, N), can_really_want(P, W).

outcome(both) :- chosen_setting(S), chosen_plan(P), chosen_wish(W), chosen_need(N),
                 valid(S, P, W, N),
                 coins(P, C), wish_cost(W, WC), need_cost(N, NC), C >= WC + NC.
outcome(friend_first) :- chosen_setting(S), chosen_plan(P), chosen_wish(W), chosen_need(N),
                         valid(S, P, W, N),
                         coins(P, C), wish_cost(W, WC), need_cost(N, NC), C < WC + NC.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for wid in sorted(setting.afford_wishes):
            lines.append(asp.fact("sells_wish", sid, wid))
        for nid in sorted(setting.afford_needs):
            lines.append(asp.fact("supports_need", sid, nid))
    for pid, plan in SAVINGS.items():
        lines.append(asp.fact("savings", pid))
        lines.append(asp.fact("coins", pid, plan.coins))
    for wid, wish in WISHES.items():
        lines.append(asp.fact("wish", wid))
        lines.append(asp.fact("wish_cost", wid, wish.cost))
    for nid, need in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("need_cost", nid, need.cost))
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
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_plan", params.savings),
            asp.fact("chosen_wish", params.wish),
            asp.fact("chosen_need", params.need),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for s in range(100):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming story world: savings, bustle, and kindness between friends."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--savings", choices=SAVINGS)
    ap.add_argument("--wish", choices=WISHES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.savings and args.wish and args.need:
        if not valid_choice(SETTINGS[args.setting], SAVINGS[args.savings], WISHES[args.wish], NEEDS[args.need]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], SAVINGS[args.savings], WISHES[args.wish], NEEDS[args.need]))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.savings is None or c[1] == args.savings)
        and (args.wish is None or c[2] == args.wish)
        and (args.need is None or c[3] == args.need)
    ]
    if not combos:
        if args.setting and args.savings and args.wish and args.need:
            raise StoryError(explain_rejection(SETTINGS[args.setting], SAVINGS[args.savings], WISHES[args.wish], NEEDS[args.need]))
        raise StoryError("(No valid combination matches the given options.)")

    setting, savings, wish, need = rng.choice(sorted(combos))
    hero, hero_gender = _pick_name(rng)
    friend, friend_gender = _pick_name(rng, avoid=hero)
    parent = args.parent or rng.choice(["mother", "father"])
    friend_trait = rng.choice(TRAITS)
    return StoryParams(setting, savings, wish, need, hero, hero_gender, friend, friend_gender, parent, friend_trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        SAVINGS[params.savings],
        WISHES[params.wish],
        NEEDS[params.need],
        params.hero,
        params.hero_gender,
        params.friend,
        params.friend_gender,
        params.parent,
        params.friend_trait,
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
        print(f"{len(combos)} compatible (setting, savings, wish, need) combos:\n")
        for setting, savings, wish, need in combos:
            outcome = outcome_of(StoryParams(setting, savings, wish, need, "Mia", "girl", "Ben", "boy", "mother", "gentle"))
            print(f"  {setting:13} {savings:14} {wish:12} {need:13} -> {outcome}")
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
            header = f"### {p.hero} & {p.friend}: {p.savings} at {p.setting} ({p.wish} / {p.need}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
