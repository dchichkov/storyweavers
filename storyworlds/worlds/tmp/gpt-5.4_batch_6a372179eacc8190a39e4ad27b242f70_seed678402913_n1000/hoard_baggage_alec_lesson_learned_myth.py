#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hoard_baggage_alec_lesson_learned_myth.py
====================================================================

A small story world about Alec, a young pilgrim in a mythic land, who tries to
hoard sacred gifts in his baggage and learns that blessings travel best in open
hands.

The world is built around one concrete constraint and one moral turn:

* A setting only supports certain kinds of baggage.
* A baggage choice must be able to carry the chosen hoard.
* If Alec loads more than the path can bear, the journey turns into a stumble.
* If the load is light enough, the sacred guardian still refuses selfish gifts.

So every story stays plausible and still reaches the same lesson from world
state rather than from a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/hoard_baggage_alec_lesson_learned_myth.py
    python storyworlds/worlds/gpt-5.4/hoard_baggage_alec_lesson_learned_myth.py --setting sun_steps --baggage satchel --hoard figs --amount 2
    python storyworlds/worlds/gpt-5.4/hoard_baggage_alec_lesson_learned_myth.py --setting sky_stair --baggage cart
    python storyworlds/worlds/gpt-5.4/hoard_baggage_alec_lesson_learned_myth.py --all
    python storyworlds/worlds/gpt-5.4/hoard_baggage_alec_lesson_learned_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/hoard_baggage_alec_lesson_learned_myth.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "priestess"}
        male = {"boy", "man", "father", "pilgrim"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    id: str
    place: str
    road: str
    sacred_place: str
    guardian: str
    recipient: str
    image: str
    modes: set[str] = field(default_factory=set)
    safe_load: int = 3
    tags: set[str] = field(default_factory=set)


@dataclass
class Baggage:
    id: str
    label: str
    phrase: str
    mode: str
    capacity: int
    spill: str
    lighten: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HoardItem:
    id: str
    label: str
    unit: str
    plural: str
    bulk: int
    shine: str
    give_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_weight(world: World) -> list[str]:
    alec = world.get("alec")
    baggage = world.get("baggage")
    if baggage.meters["load"] <= world.setting.safe_load:
        return []
    sig = ("weight", int(baggage.meters["load"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    alec.meters["strain"] += 1
    baggage.meters["wobble"] += 1
    alec.memes["worry"] += 1
    return ["__heavy__"]


def _r_wobble(world: World) -> list[str]:
    baggage = world.get("baggage")
    if baggage.meters["wobble"] < THRESHOLD:
        return []
    sig = ("wobble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("alec").memes["fear"] += 1
    return ["__wobble__"]


CAUSAL_RULES = [
    Rule(name="weight", tag="physical", apply=_r_weight),
    Rule(name="wobble", tag="physical", apply=_r_wobble),
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
        for text in produced:
            if not text.startswith("__"):
                world.say(text)
    return produced


def load_of(hoard: HoardItem, amount: int) -> int:
    return hoard.bulk * amount


def combo_valid(setting: Setting, baggage: Baggage, hoard: HoardItem, amount: int) -> bool:
    return baggage.mode in setting.modes and load_of(hoard, amount) <= baggage.capacity


def outcome_of(params: "StoryParams") -> str:
    setting = SETTINGS[params.setting]
    hoard = HOARDS[params.hoard]
    return "stumble" if load_of(hoard, params.amount) > setting.safe_load else "refused"


def predict_journey(world: World, hoard: HoardItem, amount: int) -> dict:
    sim = world.copy()
    baggage = sim.get("baggage")
    baggage.meters["load"] = float(load_of(hoard, amount))
    propagate(sim, narrate=False)
    return {
        "too_heavy": baggage.meters["wobble"] >= THRESHOLD,
        "strain": sim.get("alec").meters["strain"],
        "fear": sim.get("alec").memes["fear"],
    }


def myth_opening(world: World, alec: Entity, setting: Setting) -> None:
    alec.memes["hope"] += 1
    world.say(
        f"In the old days, when hills were said to remember every footstep, Alec walked {setting.road} toward {setting.sacred_place}."
    )
    world.say(
        f"He was a young pilgrim, and he had been trusted to carry gifts for {setting.recipient}. Over the path lay {setting.image}."
    )


def receive_gifts(world: World, alec: Entity, baggage_ent: Entity, baggage: Baggage,
                  hoard: HoardItem, amount: int) -> None:
    world.say(
        f"At the last village, the people tucked {amount} {hoard.plural} into {baggage_ent.label}. The {hoard.label} {hoard.shine}."
    )
    world.say(
        f"Alec looked at them and thought, if he kept a little hoard for himself inside his baggage, perhaps luck would stay with him forever."
    )
    alec.memes["greed"] += 1
    baggage_ent.meters["load"] = float(load_of(hoard, amount))


def warning_beat(world: World, alec: Entity, setting: Setting, baggage: Baggage,
                 hoard: HoardItem, amount: int) -> None:
    pred = predict_journey(world, hoard, amount)
    world.facts["predicted_too_heavy"] = pred["too_heavy"]
    if pred["too_heavy"]:
        world.say(
            f"When Alec lifted {baggage.phrase}, the weight pulled at his shoulder and made the straps whisper against one another."
        )
        world.say(
            f"The old road seemed to answer him: gifts meant for {setting.recipient} do not like to be hoarded."
        )
    else:
        world.say(
            f"The load did not bend Alec low, yet his hands still tightened around it as if closed fingers could trap a blessing."
        )


def travel(world: World, alec: Entity, baggage_ent: Entity, setting: Setting) -> None:
    propagate(world, narrate=False)
    if baggage_ent.meters["wobble"] >= THRESHOLD:
        world.say(
            f"Alec started up the way, and soon {baggage_ent.label} knocked against his side. Each step felt less like a prayer and more like a tug-of-war."
        )
    else:
        world.say(
            f"Alec kept walking, but the path no longer felt bright. The more he clutched the gifts, the smaller the morning seemed."
        )


def stumble_turn(world: World, alec: Entity, baggage_ent: Entity, setting: Setting,
                 baggage: Baggage, hoard: HoardItem, amount: int) -> None:
    baggage_ent.meters["spilled"] += 1
    alec.memes["shame"] += 1
    world.say(
        f"Halfway to {setting.sacred_place}, {baggage.spill}. {amount} {hoard.plural} rolled out where all the light could see them."
    )
    world.say(
        f"Alec dropped to his knees. He understood at once that the road had not betrayed him. His own wanting had made the load clumsy."
    )


def refused_turn(world: World, alec: Entity, baggage_ent: Entity, setting: Setting,
                 hoard: HoardItem, amount: int) -> None:
    alec.memes["shame"] += 1
    world.say(
        f"At the gate of {setting.sacred_place}, the voice of {setting.guardian} rose like wind through stone."
    )
    world.say(
        f'"Why do you hold those {hoard.plural} so tightly, Alec?" the guardian asked. "A gift that is hidden in baggage for the self cannot enter a holy place."'
    )
    world.say(
        f"Alec felt his cheeks grow warm. The load was light enough for the road, but not light enough for his heart."
    )


def share_and_learn(world: World, alec: Entity, baggage_ent: Entity, setting: Setting,
                    baggage: Baggage, hoard: HoardItem, amount: int, outcome: str) -> None:
    alec.memes["greed"] = 0.0
    alec.memes["wisdom"] += 1
    alec.memes["gratitude"] += 1
    baggage_ent.meters["load"] = 0.0
    baggage_ent.meters["wobble"] = 0.0
    world.say(
        f"Very gently, Alec opened the baggage and {hoard.give_line}."
    )
    if outcome == "stumble":
        world.say(
            f"As he shared the scattered gifts instead of grabbing them back, even the road seemed to steady beneath him."
        )
    else:
        world.say(
            f"As he gave the gifts away with open hands, the gate no longer felt shut. It felt welcoming."
        )
    world.say(
        f"{baggage.lighten} at once, and Alec felt something else grow light as well."
    )


def closing_image(world: World, alec: Entity, setting: Setting, hoard: HoardItem) -> None:
    world.say(
        f"Then Alec climbed the last steps to {setting.sacred_place} with only one simple offering left to carry and a wiser heart to match it."
    )
    world.say(
        f"From that day on, when children spoke of hoards and lucky things, they also told the lesson Alec had learned: blessings do not stay with the one who hides them, but with the one who shares."
    )


def tell(setting: Setting, baggage: Baggage, hoard: HoardItem, amount: int) -> World:
    world = World(setting)
    alec = world.add(Entity(id="alec", kind="character", type="pilgrim", label="Alec", phrase="Alec the pilgrim"))
    baggage_ent = world.add(Entity(
        id="baggage",
        kind="thing",
        type="baggage",
        label=baggage.label,
        phrase=baggage.phrase,
        tags=set(baggage.tags),
    ))

    myth_opening(world, alec, setting)
    receive_gifts(world, alec, baggage_ent, baggage, hoard, amount)
    world.para()
    warning_beat(world, alec, setting, baggage, hoard, amount)
    travel(world, alec, baggage_ent, setting)

    world.para()
    outcome = "stumble" if baggage_ent.meters["load"] > setting.safe_load else "refused"
    if outcome == "stumble":
        stumble_turn(world, alec, baggage_ent, setting, baggage, hoard, amount)
    else:
        refused_turn(world, alec, baggage_ent, setting, hoard, amount)

    world.para()
    share_and_learn(world, alec, baggage_ent, setting, baggage, hoard, amount, outcome)
    closing_image(world, alec, setting, hoard)

    world.facts.update(
        alec=alec,
        baggage=baggage,
        baggage_ent=baggage_ent,
        hoard=hoard,
        setting=setting,
        amount=amount,
        load=load_of(hoard, amount),
        outcome=outcome,
        lesson="blessings do not stay with the one who hides them, but with the one who shares",
    )
    return world


SETTINGS = {
    "sun_steps": Setting(
        id="sun_steps",
        place="the Sun Steps",
        road="the bright Sun Steps",
        sacred_place="the House of Dawn",
        guardian="the Lion of Morning",
        recipient="the dawn altar",
        image="golden dust and warm stair-stones",
        modes={"back", "pack"},
        safe_load=3,
        tags={"mountain", "altar"},
    ),
    "moon_ford": Setting(
        id="moon_ford",
        place="the Moon Ford",
        road="the silver stones of the Moon Ford",
        sacred_place="the Well of Night",
        guardian="the Heron of the Well",
        recipient="the moon well",
        image="silver water holding the moon in broken pieces",
        modes={"back", "pack"},
        safe_load=2,
        tags={"river", "well"},
    ),
    "sky_stair": Setting(
        id="sky_stair",
        place="the Sky Stair",
        road="the hanging Sky Stair above the clouds",
        sacred_place="the Hall of Winds",
        guardian="the Keeper of the High Gate",
        recipient="the wind shrine",
        image="blue air and ropes that hummed in the breeze",
        modes={"back"},
        safe_load=2,
        tags={"sky", "gate"},
    ),
    "cedar_way": Setting(
        id="cedar_way",
        place="the Cedar Way",
        road="the cedar road through the old grove",
        sacred_place="the Hearth of Roots",
        guardian="the Deer of the Grove",
        recipient="the root hearth",
        image="red bark, shadowed needles, and the smell of rain on wood",
        modes={"back", "pack", "wheels"},
        safe_load=4,
        tags={"forest", "hearth"},
    ),
}

BAGGAGE = {
    "satchel": Baggage(
        id="satchel",
        label="his leather satchel",
        phrase="his leather satchel",
        mode="back",
        capacity=4,
        spill="the satchel's knot slipped loose and the bag tipped open",
        lighten="The satchel hung softly from Alec's shoulder",
        tags={"satchel", "baggage"},
    ),
    "goat_packs": Baggage(
        id="goat_packs",
        label="the little pack-saddle on his goat",
        phrase="the little pack-saddle on his goat",
        mode="pack",
        capacity=5,
        spill="his goat gave a worried hop, and the pack-saddle swung sideways",
        lighten="The little goat stopped trembling, and the pack-saddle sat straight again",
        tags={"goat", "baggage"},
    ),
    "cart": Baggage(
        id="cart",
        label="his two-wheeled cart",
        phrase="his two-wheeled cart",
        mode="wheels",
        capacity=6,
        spill="one wheel struck a stone, and the cart lurched with a wooden cry",
        lighten="The cart rolled easily behind him",
        tags={"cart", "baggage"},
    ),
}

HOARDS = {
    "figs": HoardItem(
        id="figs",
        label="figs",
        unit="fig",
        plural="figs",
        bulk=1,
        shine="were dark and sweet as little drops of dusk",
        give_line="set the figs into waiting hands and laid the ripest ones before the altar",
        tags={"fruit", "sharing"},
    ),
    "honey_jars": HoardItem(
        id="honey_jars",
        label="honey jars",
        unit="jar",
        plural="honey jars",
        bulk=2,
        shine="gleamed like trapped amber in the sun",
        give_line="passed the honey jars to the temple children and placed one before the holy fire",
        tags={"honey", "sharing"},
    ),
    "bronze_lamps": HoardItem(
        id="bronze_lamps",
        label="bronze lamps",
        unit="lamp",
        plural="bronze lamps",
        bulk=2,
        shine="caught the daylight and made it wink like tiny suns",
        give_line="gave the bronze lamps to the keepers of the shrine so they could shine for everyone",
        tags={"lamp", "sharing"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    baggage: str
    hoard: str
    amount: int
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="sun_steps",
        baggage="satchel",
        hoard="figs",
        amount=2,
    ),
    StoryParams(
        setting="moon_ford",
        baggage="goat_packs",
        hoard="honey_jars",
        amount=2,
    ),
    StoryParams(
        setting="sky_stair",
        baggage="satchel",
        hoard="bronze_lamps",
        amount=1,
    ),
    StoryParams(
        setting="cedar_way",
        baggage="cart",
        hoard="honey_jars",
        amount=2,
    ),
    StoryParams(
        setting="sun_steps",
        baggage="goat_packs",
        hoard="bronze_lamps",
        amount=2,
    ),
]


KNOWLEDGE = {
    "altar": [
        (
            "What is an altar?",
            "An altar is a special place where people set gifts, lights, or prayers. In old stories, it is a place for showing honor."
        )
    ],
    "well": [
        (
            "Why are wells important in myths?",
            "A well gives water, so it often stands for life and mystery in myths. People in stories may visit a well to ask for help or wisdom."
        )
    ],
    "gate": [
        (
            "What does a gate mean in a myth?",
            "A gate often means a choice or a test. Passing through it can show that someone has changed inside."
        )
    ],
    "baggage": [
        (
            "What is baggage?",
            "Baggage is what you carry with you, like a satchel, packs, or a cart of things. In stories, baggage can also remind us of burdens we should not keep."
        )
    ],
    "satchel": [
        (
            "What is a satchel?",
            "A satchel is a small bag with a strap that hangs from the shoulder. Travelers use it to carry a few things."
        )
    ],
    "goat": [
        (
            "Why do stories use goats as pack animals?",
            "Goats can walk on steep, rocky paths better than carts can. That makes them helpful on mountain roads in old tales."
        )
    ],
    "cart": [
        (
            "Why can't a cart go everywhere?",
            "A cart needs ground wide and smooth enough for wheels. On stairs or narrow hanging paths, wheels become awkward and unsafe."
        )
    ],
    "sharing": [
        (
            "Why is sharing important in this story world?",
            "Sharing turns a gift outward instead of locking it away. The stories here teach that blessings grow when they are given, not hoarded."
        )
    ],
    "fruit": [
        (
            "Why are figs used in old stories?",
            "Figs are sweet fruits that feel rich and special, so they often appear as gifts in old stories. They can stand for harvest and kindness."
        )
    ],
    "honey": [
        (
            "Why is honey special in myths?",
            "Honey is sweet, golden, and slow to make, so myths often treat it as precious. A jar of honey can feel like a gift from patient work."
        )
    ],
    "lamp": [
        (
            "What does a lamp mean in a myth?",
            "A lamp can mean light, guidance, or wisdom. When a lamp is shared, the light reaches more people."
        )
    ],
}
KNOWLEDGE_ORDER = ["altar", "well", "gate", "baggage", "satchel", "goat", "cart", "sharing", "fruit", "honey", "lamp"]


def valid_combos() -> list[tuple[str, str, str, int]]:
    combos: list[tuple[str, str, str, int]] = []
    for setting_id, setting in SETTINGS.items():
        for baggage_id, baggage in BAGGAGE.items():
            for hoard_id, hoard in HOARDS.items():
                for amount in (1, 2, 3):
                    if combo_valid(setting, baggage, hoard, amount):
                        combos.append((setting_id, baggage_id, hoard_id, amount))
    return combos


def explain_rejection(setting: Setting, baggage: Baggage, hoard: HoardItem, amount: int) -> str:
    load = load_of(hoard, amount)
    if baggage.mode not in setting.modes:
        allowed = ", ".join(sorted(setting.modes))
        return (
            f"(No story: {baggage.label} uses {baggage.mode}, but {setting.place} only allows {allowed}. "
            f"The journey itself would be unreasonable.)"
        )
    if load > baggage.capacity:
        return (
            f"(No story: {amount} {hoard.plural} would weigh load {load}, but {baggage.label} can only carry {baggage.capacity}. "
            f"A myth may be wondrous, but it should still respect its own burdens.)"
        )
    return "(No story: this combination does not fit the world's rules.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    baggage = f["baggage"]
    hoard = f["hoard"]
    amount = f["amount"]
    outcome = f["outcome"]
    turn = "stumbles because the load is too heavy" if outcome == "stumble" else "is stopped at a sacred gate because his heart is too closed"
    return [
        (
            f'Write a short myth for a young child about Alec carrying {amount} {hoard.plural} in {baggage.phrase}. '
            f'Include the words "hoard" and "baggage" and end with a lesson learned.'
        ),
        (
            f"Tell a mythic story set on {setting.place} where Alec tries to hoard sacred gifts for himself, but {turn}."
        ),
        (
            f"Write a gentle Lesson Learned tale in a myth style where Alec discovers that blessings are safer and brighter when shared."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    setting = f["setting"]
    baggage = f["baggage"]
    hoard = f["hoard"]
    amount = f["amount"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Alec, a young pilgrim carrying sacred gifts toward {setting.sacred_place}. He begins the journey hoping for blessing, but also wanting to keep too much for himself."
        ),
        (
            "What did Alec carry in his baggage?",
            f"He carried {amount} {hoard.plural} in {baggage.phrase}. The gifts had been trusted to him for {setting.recipient}, not for a private hoard."
        ),
        (
            "Why was Alec's choice wrong?",
            f"Alec tried to hide shared gifts inside his baggage so he could keep the luck for himself. That was wrong because the gifts were meant to be offered and shared, not locked away."
        ),
    ]
    if outcome == "stumble":
        qa.append(
            (
                "What happened on the road?",
                f"The load was heavier than {setting.place} could bear safely, so {baggage.label} lurched and spilled. The stumble showed Alec that his greed had become a real burden on the journey."
            )
        )
    else:
        qa.append(
            (
                "What happened at the sacred place?",
                f"{setting.guardian} stopped Alec at the gate and asked why he held the gifts so tightly. The road had carried him, but the holy place would not welcome a selfish heart."
            )
        )
    qa.append(
        (
            "How did Alec solve the problem?",
            f"He opened his baggage and shared the gifts instead of hiding them. When he gave them to others and to the shrine, both the load and his shame became lighter."
        )
    )
    qa.append(
        (
            "What lesson did Alec learn?",
            f"He learned that blessings do not stay with the one who hides them, but with the one who shares. The ending proves it because Alec reaches the holy place only after opening his hands."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"baggage", "sharing"} | set(f["setting"].tags) | set(f["baggage"].tags) | set(f["hoard"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% a story combo is physically feasible when the baggage mode is allowed in the
% setting and the load fits the baggage capacity.
load(H, A, L) :- hoard(H), amount(A), bulk(H, B), L = B * A.
valid(S, B, H, A) :- setting(S), baggage(B), hoard(H), amount(A),
                     mode_allowed(S, M), baggage_mode(B, M),
                     load(H, A, L), capacity(B, C), L <= C.

% the turning-point outcome depends on the path's safe load, not on the baggage's
% maximum carrying capacity.
stumble(S, H, A) :- safe_load(S, Lim), load(H, A, L), L > Lim.
refused(S, H, A) :- safe_load(S, Lim), load(H, A, L), L <= Lim.

outcome(stumble) :- chosen_setting(S), chosen_hoard(H), chosen_amount(A), stumble(S, H, A).
outcome(refused) :- chosen_setting(S), chosen_hoard(H), chosen_amount(A), refused(S, H, A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        lines.append(asp.fact("safe_load", setting_id, setting.safe_load))
        for mode in sorted(setting.modes):
            lines.append(asp.fact("mode_allowed", setting_id, mode))
    for baggage_id, baggage in BAGGAGE.items():
        lines.append(asp.fact("baggage", baggage_id))
        lines.append(asp.fact("baggage_mode", baggage_id, baggage.mode))
        lines.append(asp.fact("capacity", baggage_id, baggage.capacity))
    for hoard_id, hoard in HOARDS.items():
        lines.append(asp.fact("hoard", hoard_id))
        lines.append(asp.fact("bulk", hoard_id, hoard.bulk))
    for amount in (1, 2, 3):
        lines.append(asp.fact("amount", amount))
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
            asp.fact("chosen_hoard", params.hoard),
            asp.fact("chosen_amount", params.amount),
            asp.fact("chosen_baggage", params.baggage),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    items = asp.atoms(model, "outcome")
    return items[0][0] if items else "?"


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
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - explicit verify safety net
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: Alec, a mythic journey, and a lesson about not hoarding shared gifts."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--baggage", choices=BAGGAGE)
    ap.add_argument("--hoard", choices=HOARDS)
    ap.add_argument("--amount", type=int, choices=[1, 2, 3])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.baggage and args.hoard and args.amount is not None:
        setting = SETTINGS[args.setting]
        baggage = BAGGAGE[args.baggage]
        hoard = HOARDS[args.hoard]
        if not combo_valid(setting, baggage, hoard, args.amount):
            raise StoryError(explain_rejection(setting, baggage, hoard, args.amount))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.baggage is None or combo[1] == args.baggage)
        and (args.hoard is None or combo[2] == args.hoard)
        and (args.amount is None or combo[3] == args.amount)
    ]
    if not combos:
        if args.setting and args.baggage and args.hoard and args.amount is not None:
            raise StoryError(
                explain_rejection(SETTINGS[args.setting], BAGGAGE[args.baggage], HOARDS[args.hoard], args.amount)
            )
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, baggage_id, hoard_id, amount = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting_id,
        baggage=baggage_id,
        hoard=hoard_id,
        amount=amount,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.baggage not in BAGGAGE:
        raise StoryError(f"(Unknown baggage: {params.baggage})")
    if params.hoard not in HOARDS:
        raise StoryError(f"(Unknown hoard: {params.hoard})")

    setting = SETTINGS[params.setting]
    baggage = BAGGAGE[params.baggage]
    hoard = HOARDS[params.hoard]
    if not combo_valid(setting, baggage, hoard, params.amount):
        raise StoryError(explain_rejection(setting, baggage, hoard, params.amount))

    world = tell(setting, baggage, hoard, params.amount)
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
        print(f"{len(combos)} compatible (setting, baggage, hoard, amount) combos:\n")
        for setting, baggage, hoard, amount in combos:
            print(f"  {setting:10} {baggage:10} {hoard:12} {amount}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### Alec at {p.setting}: {p.hoard} in {p.baggage} x{p.amount} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
