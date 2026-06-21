#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/semantic_money_happy_ending_repetition_mystery_to.py
==============================================================================

A standalone story world about a small space mystery: two children save money
for a treat at a moon market, then discover that some of it seems to be missing.
They solve the mystery by following clues and repeating a gentle search routine,
and the ending is always happy: the money is found, the true cause is understood,
and the children still get their prize.

Seed requirements carried into the world:
- words: "semantic", "money"
- features: Happy Ending, Repetition, Mystery to Solve
- style: Space Adventure

Run it
------
    python storyworlds/worlds/gpt-5.4/semantic_money_happy_ending_repetition_mystery_to.py
    python storyworlds/worlds/gpt-5.4/semantic_money_happy_ending_repetition_mystery_to.py --cause rumble --spot boot
    python storyworlds/worlds/gpt-5.4/semantic_money_happy_ending_repetition_mystery_to.py --cause pet --spot drawer
    python storyworlds/worlds/gpt-5.4/semantic_money_happy_ending_repetition_mystery_to.py --all
    python storyworlds/worlds/gpt-5.4/semantic_money_happy_ending_repetition_mystery_to.py --qa
    python storyworlds/worlds/gpt-5.4/semantic_money_happy_ending_repetition_mystery_to.py --verify
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
class Setting:
    id: str
    place: str
    craft: str
    view: str
    market: str
    helper_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MoneyKind:
    id: str
    label: str
    plural: str
    container: str
    shine: str
    count_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    use_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    clue: str
    explanation: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    found_line: str
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


def _r_missing_creates_mystery(world: World) -> list[str]:
    bank = world.entities.get("bank")
    if not bank or bank.meters["missing"] < THRESHOLD:
        return []
    sig = ("mystery",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("hero", "friend"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
            world.get(eid).memes["curiosity"] += 1
    return ["__mystery__"]


def _r_found_brings_relief(world: World) -> list[str]:
    bank = world.entities.get("bank")
    if not bank or bank.meters["found"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bank.meters["missing"] = 0.0
    for eid in ("hero", "friend"):
        if eid in world.entities:
            world.get(eid).memes["worry"] = 0.0
            world.get(eid).memes["relief"] += 1
            world.get(eid).memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_creates_mystery", tag="social", apply=_r_missing_creates_mystery),
    Rule(name="found_brings_relief", tag="social", apply=_r_found_brings_relief),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "station": Setting(
        id="station",
        place="the little ring station",
        craft="their bright shuttle",
        view="blue planets turning outside the window",
        market="the moon market",
        helper_phrase="a round ship robot with blinking teal eyes",
        tags={"station", "space", "robot"},
    ),
    "rocket": Setting(
        id="rocket",
        place="the long silver rocket",
        craft="their silver rocket",
        view="a stripe of stars slipping past the glass",
        market="the crater market",
        helper_phrase="a tidy cargo robot with soft wheel-feet",
        tags={"rocket", "space", "robot"},
    ),
    "orbiter": Setting(
        id="orbiter",
        place="the small moon orbiter",
        craft="their moon orbiter",
        view="dusty moons glowing below",
        market="the star dock market",
        helper_phrase="a helper bot with a humming map light",
        tags={"orbiter", "space", "robot"},
    ),
}

MONEY = {
    "coins": MoneyKind(
        id="coins",
        label="star coin",
        plural="star coins",
        container="clear magnet jar",
        shine="small gold circles that winked in the cabin light",
        count_line='"One star coin, two star coins, three star coins," they sang.',
        tags={"money", "coins"},
    ),
    "tokens": MoneyKind(
        id="tokens",
        label="moon token",
        plural="moon tokens",
        container="blue click-box",
        shine="flat silver tokens that flashed like tiny moons",
        count_line='"One moon token, two moon tokens, three moon tokens," they sang.',
        tags={"money", "tokens"},
    ),
    "credits": MoneyKind(
        id="credits",
        label="comet credit",
        plural="comet credits",
        container="tiny latch tin",
        shine="bright stamped credits that glittered with icy tails",
        count_line='"One comet credit, two comet credits, three comet credits," they sang.',
        tags={"money", "credits"},
    ),
}

PRIZES = {
    "kite": Prize(
        id="kite",
        label="comet kite",
        phrase="a comet kite with a silver tail",
        use_text="They took turns flying the comet kite in the station breeze tunnel.",
        tags={"kite", "market"},
    ),
    "seeds": Prize(
        id="seeds",
        label="moonberry seeds",
        phrase="a packet of moonberry seeds for the ship garden",
        use_text="They planted the moonberry seeds in a warm tray and imagined the first green curl.",
        tags={"garden", "market"},
    ),
    "lantern": Prize(
        id="lantern",
        label="star lantern",
        phrase="a star lantern that glowed like honey",
        use_text="That night the star lantern glowed beside their bunks like a friendly little sun.",
        tags={"light", "market"},
    ),
}

CAUSES = {
    "rumble": Cause(
        id="rumble",
        label="a docking rumble",
        clue="A soft clink came from somewhere low after the morning docking bump.",
        explanation="Nobody had taken the money. A gentle rumble had tipped the container and sent the pieces sliding.",
        supports={"boot", "grate"},
        tags={"clue", "sound"},
    ),
    "robot": Cause(
        id="robot",
        label="a helpful robot tidy-up",
        clue="The helper bot said it had sorted one loose pile by meaning after reading the ship's semantic labels.",
        explanation="Nobody had taken the money. The robot had tried to be useful and had put the pieces where their label made sense.",
        supports={"drawer", "tray"},
        tags={"semantic", "robot", "clue"},
    ),
    "pet": Cause(
        id="pet",
        label="a curious starmouse",
        clue="A trail of sparkle dust led away in tiny hops because the starmouse loved shiny things.",
        explanation="Nobody had taken the money. The little starmouse had carried the shiny pieces away one by one.",
        supports={"nest", "cup"},
        tags={"pet", "clue"},
    ),
}

SPOTS = {
    "boot": Spot(
        id="boot",
        label="space boot",
        phrase="inside a puffy space boot by the bunk",
        found_line="There, tucked in the toe, lay the missing money with a sleepy little clink.",
        tags={"low"},
    ),
    "grate": Spot(
        id="grate",
        label="floor grate",
        phrase="behind the warm floor grate",
        found_line="Behind the grate the missing money shone like trapped stars.",
        tags={"low"},
    ),
    "drawer": Spot(
        id="drawer",
        label="drawer",
        phrase='in the drawer marked "round things"',
        found_line='In the drawer marked "round things" sat the missing money in a neat little stack.',
        tags={"semantic"},
    ),
    "tray": Spot(
        id="tray",
        label="parts tray",
        phrase="on the sorting tray beside the map screen",
        found_line="On the sorting tray the missing money waited in a perfect shiny row.",
        tags={"semantic"},
    ),
    "nest": Spot(
        id="nest",
        label="nest",
        phrase="inside the starmouse nest behind the heater",
        found_line="Inside the soft nest gleamed the missing money, mixed with ribbons and foil stars.",
        tags={"pet"},
    ),
    "cup": Spot(
        id="cup",
        label="teacup",
        phrase="in a tiny teacup near the pet hammock",
        found_line="In the tiny teacup rested the missing money, bright as little moons.",
        tags={"pet"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Zee", "Ava", "Tali"]
BOY_NAMES = ["Jax", "Milo", "Finn", "Leo", "Oren", "Tao"]
TRAITS = ["careful", "curious", "brave", "patient", "clever", "gentle"]


@dataclass
class StoryParams:
    setting: str
    money: str
    prize: str
    cause: str
    spot: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def cause_fits_spot(cause: Cause, spot: Spot) -> bool:
    return spot.id in cause.supports


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id in SETTINGS:
        for money_id in MONEY:
            for prize_id in PRIZES:
                for cause_id, cause in CAUSES.items():
                    for spot_id, spot in SPOTS.items():
                        if cause_fits_spot(cause, spot):
                            combos.append((setting_id, money_id, prize_id, cause_id, spot_id))
    return combos


def explain_rejection(cause: Cause, spot: Spot) -> str:
    good = ", ".join(sorted(cause.supports))
    return (
        f"(No story: {cause.label} would not reasonably hide the money at {spot.phrase}. "
        f"Try one of: {good}.)"
    )


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options), gender


def introduce(world: World, setting: Setting, hero: Entity, friend: Entity, helper: Entity) -> None:
    world.say(
        f"On {setting.place}, {hero.id} and {friend.id} pressed their noses to the window and watched "
        f"{setting.view}. Near them rolled {helper.phrase}."
    )
    world.say(
        f"They were saving money for a trip to {setting.market}, and the whole cabin felt full of small space plans."
    )


def semantic_setup(world: World, setting: Setting, hero: Entity, friend: Entity, money: MoneyKind) -> None:
    bank = world.get("bank")
    bank.meters["saved"] = 3
    hero.memes["hope"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"Their {money.container} sat on the table, full of {money.shine}. Beside it glowed a semantic chart, "
        f"a smart little board that matched labels to meanings so every tool and snack had the right place."
    )
    world.say(money.count_line)
    world.say(
        f"Every night they counted again. {money.count_line} Counting made the trip to {setting.market} feel closer."
    )


def discover_missing(world: World, hero: Entity, friend: Entity, money: MoneyKind) -> None:
    bank = world.get("bank")
    bank.meters["missing"] = 1
    propagate(world, narrate=False)
    world.say(
        f"But on market morning, {hero.id} opened the {money.container} and blinked. Some of the {money.plural} were gone."
    )
    world.say(
        f'{friend.id} whispered, "That is a mystery." {hero.id} felt a small pinch of worry in {hero.pronoun("possessive")} chest.'
    )


def search_ritual(world: World, hero: Entity, friend: Entity) -> None:
    chant = '"Look low, listen close, check the labels," they said.'
    world.say(
        f"They did not shout. Instead, {hero.id} and {friend.id} used their ship-search rhyme. {chant}"
    )
    world.say(chant)
    world.facts["chant"] = "Look low, listen close, check the labels."


def clue_beat(world: World, cause: Cause, helper: Entity) -> None:
    helper.memes["helpfulness"] += 1
    world.say(cause.clue)
    if cause.id == "robot":
        world.say(
            f'{helper.id} blinked and said, "I read the semantic signs and tried to sort things by meaning."'
        )
    elif cause.id == "rumble":
        world.say(
            f"{helper.id} tipped its round head toward the floor and played back the sound it had heard: clink, clink."
        )
    else:
        world.say(
            f"{helper.id} pointed one glowing beam at the sparkle dust and followed the tiny hopping trail."
        )


def solve(world: World, hero: Entity, friend: Entity, cause: Cause, spot: Spot, money: MoneyKind) -> None:
    bank = world.get("bank")
    bank.meters["found"] = 1
    bank.meters["saved"] = 3
    world.facts["found_phrase"] = spot.phrase
    propagate(world, narrate=False)
    world.say(
        f"Once more they whispered, {world.facts['chant'].lower()}."
    )
    world.say(
        f"They searched {spot.phrase}. {spot.found_line}"
    )
    world.say(cause.explanation)
    world.say(
        f"{hero.id} laughed first, and then {friend.id} laughed too. The mystery was solved, and nobody had been unkind."
    )
    world.facts["cause_explanation"] = cause.explanation
    world.facts["stolen"] = False


def happy_end(world: World, setting: Setting, hero: Entity, friend: Entity, parent: Entity,
              money: MoneyKind, prize: Prize) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{parent.label_word.capitalize()} helped them slide the {money.plural} back into the {money.container}, and together they counted one last time."
    )
    world.say(money.count_line)
    world.say(
        f"At {setting.market}, the children bought {prize.phrase}. {prize.use_text}"
    )
    world.say(
        f"After that, they kept their money in the same place every night and checked the semantic chart before bed, just in case a new little mystery tried to begin."
    )


def tell(setting: Setting, money: MoneyKind, prize: Prize, cause: Cause, spot: Spot,
         hero_name: str, hero_gender: str, friend_name: str, friend_gender: str,
         parent_type: str, trait: str) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero",
                            attrs={"name": hero_name, "trait": trait}))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend",
                              attrs={"name": friend_name}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    helper = world.add(Entity(id="helper", kind="thing", type="robot", label="helper robot",
                              phrase=setting.helper_phrase, role="helper"))
    world.add(Entity(id="bank", kind="thing", type="container", label=money.container, role="bank"))
    world.facts.update(
        setting=setting,
        money=money,
        prize=prize,
        cause=cause,
        spot=spot,
        hero=hero,
        friend=friend,
        parent=parent,
        helper=helper,
        hero_name=hero_name,
        friend_name=friend_name,
        parent_word=parent.label_word,
    )

    introduce(world, setting, hero, friend, helper)
    semantic_setup(world, setting, hero, friend, money)

    world.para()
    discover_missing(world, hero, friend, money)
    search_ritual(world, hero, friend)
    clue_beat(world, cause, helper)

    world.para()
    solve(world, hero, friend, cause, spot, money)

    world.para()
    happy_end(world, setting, hero, friend, parent, money, prize)
    world.facts["resolved"] = True
    world.facts["happy"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero_name = f["hero_name"]
    friend_name = f["friend_name"]
    setting = f["setting"]
    prize = f["prize"]
    money = f["money"]
    return [
        f'Write a short space adventure for a 3-to-5-year-old that includes the words "semantic" and "money".',
        f"Tell a gentle mystery story where {hero_name} and {friend_name} lose track of some {money.plural} on {setting.place} and solve the puzzle by repeating a careful search rhyme.",
        f"Write a happy-ending story set near {setting.market} where children save money for {prize.phrase}, find the missing money, and end with a clear image of what changed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero_name = f["hero_name"]
    friend_name = f["friend_name"]
    setting = f["setting"]
    prize = f["prize"]
    money = f["money"]
    cause = f["cause"]
    spot = f["spot"]
    parent_word = f["parent_word"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {hero_name} and {friend_name}, two children on {setting.place} who were saving money for a treat at {setting.market}. A helper robot and their {parent_word} also help once the mystery begins.",
        ),
        (
            "What was the mystery?",
            f"Some of the {money.plural} seemed to be missing from the {money.container}. That worried the children because they had been counting the money over and over for their market trip.",
        ),
        (
            "What did they repeat while they searched?",
            f'They repeated, "{f["chant"]}." The rhyme helped them stay calm and look for real clues instead of guessing wildly.',
        ),
        (
            "How did they solve the mystery?",
            f"They followed the clue from {cause.label} and searched {spot.phrase}. That is where they found the missing money, so they learned it had not really been stolen at all.",
        ),
        (
            "Why was the semantic chart important?",
            "The semantic chart matched labels to meanings, so it helped the children think about where things belonged. It turned the search into a smart puzzle instead of a frightened scramble.",
        ),
        (
            "How did the story end?",
            f"They put the money back, counted it again, and went to {setting.market} for {prize.phrase}. The ending feels happy because the mystery is solved, nobody was mean, and the children still get the thing they saved for.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "money": [
        (
            "What is money?",
            "Money is something people save and use to buy things they need or want. It can be coins, tokens, or credits, depending on the place.",
        )
    ],
    "semantic": [
        (
            "What does semantic mean?",
            "Semantic means connected to meaning. A semantic label helps you understand what a word is really for or what group it belongs in.",
        )
    ],
    "robot": [
        (
            "What does a helper robot do?",
            "A helper robot does small jobs like sorting, carrying, or noticing clues. It can help people, but it still needs clear instructions.",
        )
    ],
    "market": [
        (
            "What is a market?",
            "A market is a place where people buy and sell things. In a story, it can be full of food, lights, toys, or other treats.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you solve a mystery. It might be a sound, a mark, a trail, or something that seems out of place.",
        )
    ],
    "coins": [
        (
            "Why do coins make a clink sound?",
            "Coins are hard pieces of metal, so when they bump each other they make a small ringing or clinking sound. That sound can help you find them.",
        )
    ],
    "pet": [
        (
            "Why do little pets carry shiny things?",
            "Some little animals like bright things because they catch the eye. A pet may pick them up out of curiosity, not because it understands they are important.",
        )
    ],
}
KNOWLEDGE_ORDER = ["money", "semantic", "robot", "market", "clue", "coins", "pet"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"money", "semantic", "market", "clue", "robot"}
    money = world.facts["money"]
    cause = world.facts["cause"]
    tags |= set(money.tags)
    tags |= set(cause.tags)
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
        if ent.label:
            bits.append(f"label={ent.label}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="station",
        money="coins",
        prize="kite",
        cause="robot",
        spot="drawer",
        hero="Lina",
        hero_gender="girl",
        friend="Milo",
        friend_gender="boy",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        setting="rocket",
        money="tokens",
        prize="lantern",
        cause="rumble",
        spot="grate",
        hero="Finn",
        hero_gender="boy",
        friend="Mira",
        friend_gender="girl",
        parent="father",
        trait="curious",
    ),
    StoryParams(
        setting="orbiter",
        money="credits",
        prize="seeds",
        cause="pet",
        spot="nest",
        hero="Nora",
        hero_gender="girl",
        friend="Jax",
        friend_gender="boy",
        parent="mother",
        trait="gentle",
    ),
]


ASP_RULES = r"""
compatible(C, S) :- cause(C), spot(S), supports(C, S).
valid(St, M, P, C, S) :- setting(St), money(M), prize(P), compatible(C, S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MONEY:
        lines.append(asp.fact("money", mid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        for spot_id in sorted(cause.supports):
            lines.append(asp.fact("supports", cid, spot_id))
    for sid in SPOTS:
        lines.append(asp.fact("spot", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "semantic" not in sample.story.lower() or "money" not in sample.story.lower():
            raise StoryError("Smoke test story is missing required seed words or story text.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(7))
        sample = generate(params)
        if not sample.story:
            raise StoryError("Random smoke test produced empty story.")
        print("OK: random resolve_params() + generate() succeeded.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"RANDOM SMOKE FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A space-adventure story world about missing money, a semantic clue system, and a happy mystery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--money", choices=MONEY)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from the inline ASP twin")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.spot:
        cause = CAUSES[args.cause]
        spot = SPOTS[args.spot]
        if not cause_fits_spot(cause, spot):
            raise StoryError(explain_rejection(cause, spot))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.money is None or c[1] == args.money)
        and (args.prize is None or c[2] == args.prize)
        and (args.cause is None or c[3] == args.cause)
        and (args.spot is None or c[4] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, money_id, prize_id, cause_id, spot_id = rng.choice(sorted(combos))
    hero_name, hero_gender = _pick_child(rng)
    friend_name, friend_gender = _pick_child(rng, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        money=money_id,
        prize=prize_id,
        cause=cause_id,
        spot=spot_id,
        hero=hero_name,
        hero_gender=hero_gender,
        friend=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.money not in MONEY:
        raise StoryError(f"(Invalid money kind: {params.money})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Invalid prize: {params.prize})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Invalid cause: {params.cause})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Invalid spot: {params.spot})")

    cause = CAUSES[params.cause]
    spot = SPOTS[params.spot]
    if not cause_fits_spot(cause, spot):
        raise StoryError(explain_rejection(cause, spot))

    world = tell(
        setting=SETTINGS[params.setting],
        money=MONEY[params.money],
        prize=PRIZES[params.prize],
        cause=cause,
        spot=spot,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        trait=params.trait,
    )
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )
    return sample


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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, money, prize, cause, spot) combos:\n")
        for setting_id, money_id, prize_id, cause_id, spot_id in combos:
            print(f"  {setting_id:8} {money_id:7} {prize_id:8} {cause_id:7} {spot_id}")
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
            header = f"### {p.hero} & {p.friend}: {p.cause} -> {p.spot} ({p.setting}, {p.money}, {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
