#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/swear_coin_flashback_folk_tale.py
===========================================================

A small folk-tale storyworld about a child, a treasured coin, and a hot word
that almost leaps out. The world models a child who is tempted to swear after a
small wrong or hurt, then feels the old coin in a pocket and falls into a brief
flashback of an elder's lesson. Depending on the child's temper, the trigger,
and the helper nearby, the story ends in either a gentle repair or a rueful
lesson.

Run it
------
    python storyworlds/worlds/gpt-5.4/swear_coin_flashback_folk_tale.py
    python storyworlds/worlds/gpt-5.4/swear_coin_flashback_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/swear_coin_flashback_folk_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/swear_coin_flashback_folk_tale.py --qa
    python storyworlds/worlds/gpt-5.4/swear_coin_flashback_folk_tale.py --verify
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
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.label or self.type)


@dataclass
class Setting:
    id: str
    place: str
    path_detail: str
    errand: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Trigger:
    id: str
    mishap: str
    sting: str
    need: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class CoinLesson:
    id: str
    coin_phrase: str
    gleam: str
    elder_type: str
    lesson: str
    proverb: str
    virtue: str
    power: int
    memory_place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    type: str
    aid: str
    repair_text: str
    thanks: str
    offers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    trigger: str
    coin: str
    helper: str
    child_name: str
    child_gender: str
    temper: int
    seed: Optional[int] = None


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


def _r_hot_tongue(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["anger"] < THRESHOLD:
        return []
    sig = ("hot_tongue",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["hot_tongue"] += 1
    return ["__heat__"]


def _r_coin_memory(world: World) -> list[str]:
    child = world.get("child")
    coin = world.get("coin")
    if child.meters["hot_tongue"] < THRESHOLD or coin.meters["touched"] < THRESHOLD:
        return []
    sig = ("coin_memory",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["remembering"] += 1
    child.memes["restraint"] += coin.attrs.get("power", 0)
    return ["__flashback__"]


def _r_kind_speech(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["restraint"] < child.meters["anger"]:
        return []
    sig = ("kind_speech",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["kind_speech"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="hot_tongue", tag="emotional", apply=_r_hot_tongue),
    Rule(name="coin_memory", tag="memory", apply=_r_coin_memory),
    Rule(name="kind_speech", tag="social", apply=_r_kind_speech),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if not bit.startswith("__"):
                world.say(bit)
    return produced


SETTINGS = {
    "market": Setting(
        id="market",
        place="the market lane",
        path_detail="where bright awnings fluttered like little flags",
        errand="to trade eggs for flour",
        affords={"baker", "weaver"},
    ),
    "bridge": Setting(
        id="bridge",
        place="the old bridge over the reed river",
        path_detail="where the planks hummed under passing carts",
        errand="to carry a basket of apples to an aunt across the water",
        affords={"ferryman", "weaver"},
    ),
    "mill": Setting(
        id="mill",
        place="the mill path",
        path_detail="where white dust drifted from the turning wheel",
        errand="to bring grain for grinding",
        affords={"miller", "baker"},
    ),
}

TRIGGERS = {
    "spilled_flour": Trigger(
        id="spilled_flour",
        mishap="A hasty donkey cart clipped the basket and sent a white puff of flour over everything.",
        sting="The loss felt unfair, and the child's mouth opened with a hot, sharp word.",
        need="cleanup",
        severity=2,
        tags={"cleanup", "flour"},
    ),
    "lost_apple": Trigger(
        id="lost_apple",
        mishap="One red apple rolled through the slats and plopped into the river below.",
        sting="The sound of the splash made the child's heart leap with angry grief.",
        need="replacement",
        severity=2,
        tags={"replacement", "apple"},
    ),
    "stubbed_toe": Trigger(
        id="stubbed_toe",
        mishap="A stone hid in the dust, and the child struck a toe against it hard enough to make tears jump.",
        sting="Pain rushed up like fire, and an ugly swear pushed at the child's teeth.",
        need="comfort",
        severity=1,
        tags={"comfort", "pain"},
    ),
    "torn_basket": Trigger(
        id="torn_basket",
        mishap="The old basket snagged on a nail and split, and eggs began to wobble toward the ground.",
        sting="For one fierce instant, blame and fright rose together in the child's throat.",
        need="mending",
        severity=3,
        tags={"mending", "basket"},
    ),
}

COINS = {
    "copper_patience": CoinLesson(
        id="copper_patience",
        coin_phrase="a smooth copper coin",
        gleam="warm as bread crust in the sun",
        elder_type="grandmother",
        lesson="patience",
        proverb='“A slow tongue keeps a whole heart.”',
        virtue="comfort",
        power=2,
        memory_place="by the cottage hearth",
        tags={"coin", "patience"},
    ),
    "silver_honesty": CoinLesson(
        id="silver_honesty",
        coin_phrase="a small silver coin",
        gleam="bright as river light",
        elder_type="grandfather",
        lesson="honesty",
        proverb='“Let your first word be true, and your second word be gentle.”',
        virtue="replacement",
        power=2,
        memory_place="on a fishing stool by the reeds",
        tags={"coin", "honesty"},
    ),
    "star_mercy": CoinLesson(
        id="star_mercy",
        coin_phrase="a star-stamped coin",
        gleam="soft as moonlight on a pail",
        elder_type="grandmother",
        lesson="mercy",
        proverb='“A mouth that spares others often finds help.”',
        virtue="cleanup",
        power=2,
        memory_place="under the elder tree behind the house",
        tags={"coin", "mercy"},
    ),
    "iron_steady": CoinLesson(
        id="iron_steady",
        coin_phrase="an old iron coin",
        gleam="dark, but steady in the hand",
        elder_type="grandfather",
        lesson="steadiness",
        proverb='“When your hands shake, speak as if you carry water.”',
        virtue="mending",
        power=3,
        memory_place="in the shed where nets and ropes were kept",
        tags={"coin", "steadiness"},
    ),
}

HELPERS = {
    "baker": Helper(
        id="baker",
        label="the baker",
        type="woman",
        aid="cleanup",
        repair_text="the baker shook the flour from her apron, brought out a fresh scoop, and helped fill the sack again",
        thanks="The baker said the lane was kinder when children chose clean words.",
        offers={"cleanup", "replacement"},
        tags={"baker", "help"},
    ),
    "ferryman": Helper(
        id="ferryman",
        label="the ferryman",
        type="man",
        aid="replacement",
        repair_text="the ferryman hooked the drifting apple with his long pole and drew it safely back to shore",
        thanks="The ferryman laughed softly and said a calm voice crosses many waters.",
        offers={"replacement", "comfort"},
        tags={"ferryman", "help"},
    ),
    "miller": Helper(
        id="miller",
        label="the miller",
        type="man",
        aid="mending",
        repair_text="the miller fetched cord from the wheel-house and tied the basket tighter than before",
        thanks="The miller nodded and said steady words make steady hands.",
        offers={"mending", "cleanup"},
        tags={"miller", "help"},
    ),
    "weaver": Helper(
        id="weaver",
        label="the weaver",
        type="woman",
        aid="comfort",
        repair_text="the weaver sat the child on a bench, washed the dusty toe, and wrapped it with a strip of soft cloth",
        thanks="The weaver said pain need not be answered with a hard tongue.",
        offers={"comfort", "mending"},
        tags={"weaver", "help"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Elsa", "Nella", "Tessa", "Rosa"]
BOY_NAMES = ["Ivo", "Marek", "Tobin", "Jory", "Pavel", "Nico"]


def valid_combo(setting_id: str, trigger_id: str, coin_id: str, helper_id: str) -> bool:
    setting = SETTINGS[setting_id]
    trigger = TRIGGERS[trigger_id]
    coin = COINS[coin_id]
    helper = HELPERS[helper_id]
    return helper_id in setting.affords and trigger.need in helper.offers and trigger.need == coin.virtue


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for trigger_id in TRIGGERS:
            for coin_id in COINS:
                for helper_id in HELPERS:
                    if valid_combo(setting_id, trigger_id, coin_id, helper_id):
                        out.append((setting_id, trigger_id, coin_id, helper_id))
    return out


def outcome_of(params: StoryParams) -> str:
    trigger = TRIGGERS[params.trigger]
    coin = COINS[params.coin]
    helper = HELPERS[params.helper]
    restraint = coin.power + (1 if trigger.need in helper.offers else 0)
    anger = trigger.severity + params.temper
    return "repaired" if restraint >= anger else "regret"


def explain_rejection(setting_id: str, trigger_id: str, coin_id: str, helper_id: str) -> str:
    setting = SETTINGS[setting_id]
    trigger = TRIGGERS[trigger_id]
    coin = COINS[coin_id]
    helper = HELPERS[helper_id]
    if helper_id not in setting.affords:
        return (
            f"(No story: {helper.label} does not belong in {setting.place}, "
            f"so that helper cannot witness the trouble there.)"
        )
    if trigger.need not in helper.offers:
        return (
            f"(No story: {helper.label} cannot reasonably solve a problem of {trigger.need}, "
            f"so the ending would feel unearned.)"
        )
    if trigger.need != coin.virtue:
        return (
            f"(No story: {coin.coin_phrase} teaches {coin.lesson}, but this mishap needs "
            f"{trigger.need}. The flashback should fit the problem it helps solve.)"
        )
    return "(No story: that combination is unreasonable in this world.)"


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS or params.trigger not in TRIGGERS or params.coin not in COINS or params.helper not in HELPERS:
        raise StoryError("(Invalid params: unknown setting, trigger, coin, or helper.)")
    if not valid_combo(params.setting, params.trigger, params.coin, params.helper):
        raise StoryError(explain_rejection(params.setting, params.trigger, params.coin, params.helper))

    setting = SETTINGS[params.setting]
    trigger = TRIGGERS[params.trigger]
    coin_cfg = COINS[params.coin]
    helper_cfg = HELPERS[params.helper]

    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name, role="child"))
    elder = world.add(Entity(id="elder", kind="character", type=coin_cfg.elder_type, label=f"the {coin_cfg.elder_type}", role="elder"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg.type, label=helper_cfg.label, role="helper"))
    coin = world.add(Entity(
        id="coin",
        kind="thing",
        type="coin",
        label="coin",
        phrase=coin_cfg.coin_phrase,
        attrs={"lesson": coin_cfg.lesson, "proverb": coin_cfg.proverb, "power": coin_cfg.power},
        tags=set(coin_cfg.tags),
    ))

    child.memes["temper"] = float(params.temper)
    world.facts.update(
        setting=setting,
        trigger=trigger,
        coin_cfg=coin_cfg,
        helper_cfg=helper_cfg,
        child=child,
        elder=elder,
        helper=helper,
        coin=coin,
    )

    world.say(
        f"In a small village where stories were traded as often as bread, {params.child_name} set out toward {setting.place}, "
        f"{setting.path_detail}, {setting.errand}."
    )
    world.say(
        f"In a pocket rested {coin_cfg.coin_phrase}, {coin_cfg.gleam}. {params.child_name} kept it not for spending, "
        f"but because {child.pronoun('possessive')} {coin_cfg.elder_type} had once pressed it into {child.pronoun('possessive')} hand."
    )

    world.para()
    world.say(trigger.mishap)
    world.say(trigger.sting)
    child.meters["anger"] = float(trigger.severity + params.temper)
    propagate(world, narrate=False)

    world.say(
        f"{params.child_name} curled small fingers around the coin. The hard edge bit the palm, and the busy road fell away."
    )

    world.para()
    coin.meters["touched"] += 1
    propagate(world, narrate=False)
    world.say("Then came a flashback, clear as bell metal.")
    world.say(
        f"{params.child_name} was small again, standing {coin_cfg.memory_place}. {coin_cfg.elder_type.capitalize()} had laid the coin in "
        f"{child.pronoun('possessive')} hand and said, {coin_cfg.proverb}"
    )
    world.say(
        f'"If ever you wish to swear," the old one had added, "close your fist first, and let the coin remember for you."'
    )

    anger = int(child.meters["anger"])
    restraint = coin_cfg.power + (1 if trigger.need in helper_cfg.offers else 0)
    child.memes["restraint"] = float(restraint)

    world.para()
    if restraint >= anger:
        child.memes["kind_speech"] = 1.0
        world.say(
            f"The sharp swear melted before it could fly. {params.child_name} drew one breath, then another, and spoke to {helper_cfg.label} in a voice that trembled but did not bite."
        )
        world.say(
            f"{helper_cfg.label.capitalize()} saw the trouble plainly and {helper_cfg.repair_text}."
        )
        world.say(helper_cfg.thanks)
        child.memes["relief"] += 1
        child.memes["lesson"] += 1
        world.facts["outcome"] = "repaired"
        world.facts["repair_done"] = True
        world.facts["swore"] = False

        world.para()
        world.say(
            f"When the errand was mended, {params.child_name} slipped the coin back into the pocket. It felt no heavier than before, yet the road ahead seemed easier to walk."
        )
        world.say(
            f"And so the village children later said that a coin may be small, but a remembered word can be worth more than silver."
        )
    else:
        child.memes["regret"] += 1
        child.meters["swore"] += 1
        world.say(
            f"But the anger was too quick. One rough swear burst out and hung in the air like a crow's wing."
        )
        world.say(
            f"{helper_cfg.label.capitalize()} did not scold, yet the kind help came slowly after that, and {params.child_name} felt the heat of shame more than the first hurt."
        )
        world.say(
            f"In the end, {helper_cfg.label} still offered a little help, but only after {params.child_name} bowed {child.pronoun('possessive')} head and asked forgiveness with plain, careful words."
        )
        child.memes["lesson"] += 1
        child.memes["humility"] += 1
        world.facts["outcome"] = "regret"
        world.facts["repair_done"] = True
        world.facts["swore"] = True

        world.para()
        world.say(
            f"That night, {params.child_name} rubbed the coin with a thumb and remembered the flashback more sharply than the mishap itself."
        )
        world.say(
            f"From then on, whenever a hard word tried to climb out, {child.pronoun()} touched the coin first, for even a folk-tale child learns that the tongue must be taught twice."
        )

    world.facts["anger"] = anger
    world.facts["restraint"] = restraint
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    setting = world.facts["setting"]
    trigger = world.facts["trigger"]
    coin_cfg = world.facts["coin_cfg"]
    outcome = world.facts["outcome"]
    end = "gentle repair" if outcome == "repaired" else "rueful lesson"
    return [
        'Write a short folk tale for a young child that includes the words "swear" and "coin" and uses a flashback.',
        f"Tell a folk-tale story where {child.label} goes to {setting.place}, suffers a small mishap, reaches for {coin_cfg.coin_phrase}, and remembers an elder's lesson in a flashback.",
        f"Write a village tale with a {end}: the mishap is {trigger.id.replace('_', ' ')}, and the coin's teaching guides what the child says next.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    trigger = world.facts["trigger"]
    coin_cfg = world.facts["coin_cfg"]
    helper_cfg = world.facts["helper_cfg"]
    setting = world.facts["setting"]
    outcome = world.facts["outcome"]
    elder = world.facts["elder"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a child in a village, and the old coin {child.pronoun()} carried. The coin mattered because it held a lesson from {elder.label_word}.",
        ),
        (
            "What went wrong on the errand?",
            f"{trigger.mishap} That is what made anger rise and almost made {child.label} swear.",
        ),
        (
            "What happened in the flashback?",
            f"In the flashback, {child.label} remembered standing {coin_cfg.memory_place} while {elder.label_word} gave {child.pronoun('object')} the coin. The elder taught this proverb: {coin_cfg.proverb}",
        ),
    ]
    if outcome == "repaired":
        qa.append(
            (
                f"Why did {child.label} not swear in the end?",
                f"{child.label} felt the coin, remembered the elder's words, and that memory gave enough calm to hold the hard word back. Because {helper_cfg.label} was nearby and could truly help, the child could ask for help instead of speaking harshly.",
            )
        )
        qa.append(
            (
                f"How was the problem solved at {setting.place}?",
                f"{helper_cfg.label.capitalize()} {helper_cfg.repair_text}. The repair proves the gentle words changed what happened next.",
            )
        )
    else:
        qa.append(
            (
                f"Did {child.label} swear, and what happened after?",
                f"Yes. A rough swear slipped out before the child could stop it, and shame followed right away. {helper_cfg.label.capitalize()} still helped a little, but only after {child.label} apologized with careful words.",
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{child.label} learned that remembering the coin's lesson too late can still lead to regret. After that, {child.pronoun()} decided to touch the coin before speaking when anger flared.",
            )
        )
    return qa


KNOWLEDGE = {
    "coin": [
        (
            "Why might a coin matter in a folk tale?",
            "In a folk tale, a coin can be more than money. It can be a keepsake that carries a promise, a memory, or a lesson.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short look back at something that happened earlier. It helps readers understand why a character acts a certain way now.",
        )
    ],
    "swear": [
        (
            "What does it mean to swear in anger?",
            "It means to blurt out a harsh or rude word when you are upset. Stories often show that stopping for a breath can keep the hurt from spreading.",
        )
    ],
    "folk": [
        (
            "What makes a story feel like a folk tale?",
            "A folk tale often sounds old and simple, uses strong images, and ends with a lesson people could retell. It usually feels as if it might have been told beside a fire or on a village road.",
        )
    ],
    "help": [
        (
            "Why do calm words make it easier for people to help?",
            "Calm words let other people see the problem clearly instead of feeling attacked. When people feel respected, they are more ready to mend what went wrong.",
        )
    ],
}

KNOWLEDGE_ORDER = ["coin", "flashback", "swear", "help", "folk"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"coin", "flashback", "swear", "folk", "help"}
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:7} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for (name, *_) in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="market",
        trigger="spilled_flour",
        coin="star_mercy",
        helper="baker",
        child_name="Lina",
        child_gender="girl",
        temper=1,
    ),
    StoryParams(
        setting="bridge",
        trigger="lost_apple",
        coin="silver_honesty",
        helper="ferryman",
        child_name="Ivo",
        child_gender="boy",
        temper=1,
    ),
    StoryParams(
        setting="mill",
        trigger="torn_basket",
        coin="iron_steady",
        helper="miller",
        child_name="Mira",
        child_gender="girl",
        temper=1,
    ),
    StoryParams(
        setting="bridge",
        trigger="stubbed_toe",
        coin="copper_patience",
        helper="weaver",
        child_name="Tobin",
        child_gender="boy",
        temper=2,
    ),
    StoryParams(
        setting="market",
        trigger="spilled_flour",
        coin="star_mercy",
        helper="baker",
        child_name="Nella",
        child_gender="girl",
        temper=3,
    ),
]


ASP_RULES = r"""
valid(S,T,C,H) :- setting(S), trigger(T), coin(C), helper(H),
                  affords(S,H), need(T,N), offers(H,N), virtue(C,N).

restraint(C,H,R) :- power(C,P), chosen_coin(C), chosen_helper(H), chosen_trigger(T),
                    need(T,N), offers(H,N), R = P + 1.
anger(T,Temp,A) :- severity(T,S), chosen_trigger(T), temper(Temp), A = S + Temp.

repaired :- chosen_coin(C), chosen_helper(H), chosen_trigger(T), temper(Temp),
            restraint(C,H,R), anger(T,Temp,A), R >= A.
regret   :- chosen_coin(C), chosen_helper(H), chosen_trigger(T), temper(Temp),
            restraint(C,H,R), anger(T,Temp,A), R < A.

outcome(repaired) :- repaired.
outcome(regret) :- regret.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for helper_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, helper_id))
    for trigger_id, trigger in TRIGGERS.items():
        lines.append(asp.fact("trigger", trigger_id))
        lines.append(asp.fact("need", trigger_id, trigger.need))
        lines.append(asp.fact("severity", trigger_id, trigger.severity))
    for coin_id, coin in COINS.items():
        lines.append(asp.fact("coin", coin_id))
        lines.append(asp.fact("virtue", coin_id, coin.virtue))
        lines.append(asp.fact("power", coin_id, coin.power))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for offer in sorted(helper.offers):
            lines.append(asp.fact("offers", helper_id, offer))
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
            asp.fact("chosen_coin", params.coin),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_trigger", params.trigger),
            asp.fact("temper", params.temper),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    try:
        smoke_args = build_parser().parse_args([])
        smoke_params = resolve_params(smoke_args, random.Random(123))
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} curated scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} curated outcomes differ.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale storyworld: a child, an old coin, a near swear, and a flashback."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--coin", choices=COINS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--temper", type=int, choices=[1, 2, 3], help="higher temper makes the hard word harder to stop")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.trigger and args.coin and args.helper:
        if not valid_combo(args.setting, args.trigger, args.coin, args.helper):
            raise StoryError(explain_rejection(args.setting, args.trigger, args.coin, args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.trigger is None or combo[1] == args.trigger)
        and (args.coin is None or combo[2] == args.coin)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, trigger_id, coin_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    temper = args.temper if args.temper is not None else rng.choice([1, 2, 3])
    return StoryParams(
        setting=setting_id,
        trigger=trigger_id,
        coin=coin_id,
        helper=helper_id,
        child_name=name,
        child_gender=gender,
        temper=temper,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(f"{len(combos)} compatible (setting, trigger, coin, helper) combos:\n")
        for setting_id, trigger_id, coin_id, helper_id in combos:
            print(f"  {setting_id:7} {trigger_id:13} {coin_id:16} {helper_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.trigger} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
