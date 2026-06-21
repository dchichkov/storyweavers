#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gill_square_repetition_pirate_tale.py
================================================================

A standalone storyworld about two children playing pirates who find a little
fish trapped in a square bit of shore-water. The story uses repetition as a
sea-chant-like rescue line, keeps a child-facing pirate-tale tone, and models
whether the children's chosen rescue method can solve the problem alone or
whether a nearby grown-up must help.

Run it
------
python storyworlds/worlds/gpt-5.4/gill_square_repetition_pirate_tale.py
python storyworlds/worlds/gpt-5.4/gill_square_repetition_pirate_tale.py --trap square_crate --method shell_pail
python storyworlds/worlds/gpt-5.4/gill_square_repetition_pirate_tale.py --method drag_tail
python storyworlds/worlds/gpt-5.4/gill_square_repetition_pirate_tale.py --all
python storyworlds/worlds/gpt-5.4/gill_square_repetition_pirate_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/gill_square_repetition_pirate_tale.py --trace --seed 777
python storyworlds/worlds/gpt-5.4/gill_square_repetition_pirate_tale.py --json
python storyworlds/worlds/gpt-5.4/gill_square_repetition_pirate_tale.py --verify
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

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
STORYWORLDS_DIR = os.path.dirname(os.path.dirname(THIS_DIR))
sys.path.insert(0, STORYWORLDS_DIR)
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
    shore: str
    pirate_opening: str
    sea: str
    helper_title: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trap:
    id: str
    label: str
    the: str
    shape_text: str
    found_text: str
    exposure: int
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class FishKind:
    id: str
    label: str
    phrase: str
    shimmer: str
    need: int
    tags: set[str] = field(default_factory=set)


@dataclass
class RescueMethod:
    id: str
    label: str
    phrase: str
    power: int
    gentle: int
    sense: int
    works_on: set[str] = field(default_factory=set)
    try_text: str = ""
    success_text: str = ""
    help_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    trap: str
    fish: str
    method: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    parent: str
    delay: int = 0
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
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

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


def _r_gasp(world: World) -> list[str]:
    fish = world.get("fish")
    trap = world.get("trap")
    if fish.meters["trapped"] < THRESHOLD:
        return []
    sig = ("gasp",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    fish.meters["air_hunger"] += 1
    fish.memes["fear"] += 1
    trap.meters["danger"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    fish = world.get("fish")
    if fish.meters["safe_water"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    fish.meters["air_hunger"] = 0.0
    fish.memes["fear"] = 0.0
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["care"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="gasp", tag="physical", apply=_r_gasp),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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


SETTINGS = {
    "cove": Setting(
        id="cove",
        shore="the little cove",
        pirate_opening="the driftwood log was their pirate ship and a red towel was their flag",
        sea="the bay",
        helper_title="harbor mom",
        tags={"sea", "pirate"},
    ),
    "harbor": Setting(
        id="harbor",
        shore="the sunny harbor edge",
        pirate_opening="the low wall was their pirate ship and a coil of rope was their anchor line",
        sea="the harbor water",
        helper_title="dock dad",
        tags={"sea", "pirate"},
    ),
    "lagoon": Setting(
        id="lagoon",
        shore="the warm lagoon shore",
        pirate_opening="the flat rock was their pirate deck and a striped scarf was their captain's sash",
        sea="the lagoon",
        helper_title="beach mom",
        tags={"sea", "pirate"},
    ),
}

TRAPS = {
    "square_pool": Trap(
        id="square_pool",
        label="square tide pool",
        the="the square tide pool",
        shape_text="a square patch of water between four flat rocks",
        found_text="a square tide pool that the last wave had forgotten",
        exposure=2,
        tags={"square", "tide_pool"},
    ),
    "square_bucket": Trap(
        id="square_bucket",
        label="square bait bucket",
        the="the square bait bucket",
        shape_text="a square bucket left beside a piling",
        found_text="a square bait bucket with only a puddle left in the bottom",
        exposure=2,
        tags={"square", "bucket"},
    ),
    "square_crate": Trap(
        id="square_crate",
        label="square fish crate",
        the="the square fish crate",
        shape_text="a square crate with slats that pinched little fins",
        found_text="a square fish crate where a splashy puddle was shrinking fast",
        exposure=3,
        tags={"square", "crate"},
    ),
}

FISH = {
    "minnow": FishKind(
        id="minnow",
        label="minnow",
        phrase="a little minnow",
        shimmer="silver as a tiny coin",
        need=1,
        tags={"fish", "gill"},
    ),
    "goby": FishKind(
        id="goby",
        label="goby",
        phrase="a sandy goby",
        shimmer="striped like brushed sand",
        need=2,
        tags={"fish", "gill"},
    ),
    "sprat": FishKind(
        id="sprat",
        label="sprat",
        phrase="a bright sprat",
        shimmer="bright as a dropped spoon",
        need=2,
        tags={"fish", "gill"},
    ),
}

METHODS = {
    "both_hands": RescueMethod(
        id="both_hands",
        label="both hands",
        phrase="their two careful hands",
        power=2,
        gentle=2,
        sense=3,
        works_on={"square_pool", "square_bucket"},
        try_text="cupped their wet hands under the little fish",
        success_text="lifted the fish in their wet hands and hurried it back to the sea",
        help_text="tried to lift the fish with their hands, but the crate slats and the slipping water made the rescue too slow",
        qa_text="used their wet hands to carry the fish back to the sea",
        tags={"hands", "care"},
    ),
    "shell_pail": RescueMethod(
        id="shell_pail",
        label="shell pail",
        phrase="a little shell pail",
        power=3,
        gentle=2,
        sense=3,
        works_on={"square_pool", "square_bucket", "square_crate"},
        try_text="filled a little shell pail with water and slid it under the fish",
        success_text="slid the fish into the water-filled shell pail and ran it back to the sea",
        help_text="got the shell pail under the fish, but the fish was already too weak and needed a grown-up's faster help",
        qa_text="used a water-filled shell pail to carry the fish back to the sea",
        tags={"pail", "care"},
    ),
    "fishing_net": RescueMethod(
        id="fishing_net",
        label="fishing net",
        phrase="a child-sized fishing net",
        power=2,
        gentle=1,
        sense=2,
        works_on={"square_pool", "square_crate"},
        try_text="dipped a small net under the fish as softly as they could",
        success_text="scooped the fish in the little net and rushed it into the sea",
        help_text="caught the fish in the net, but the fish still needed a grown-up's water bucket before it could swim strongly",
        qa_text="used a small net to scoop the fish and rush it into the sea",
        tags={"net", "care"},
    ),
    "drag_tail": RescueMethod(
        id="drag_tail",
        label="drag by the tail",
        phrase="a tail tug",
        power=3,
        gentle=0,
        sense=1,
        works_on={"square_pool", "square_bucket", "square_crate"},
        try_text="reached to drag the fish by the tail",
        success_text="dragged the fish away",
        help_text="made the fish thrash harder",
        qa_text="tried to drag the fish by the tail",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Ella", "Nora", "Zoe"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn"]


def sensible_methods() -> list[RescueMethod]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def method_fits_trap(method: RescueMethod, trap: Trap) -> bool:
    return trap.id in method.works_on


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for trap_id, trap in TRAPS.items():
            for fish_id, fish in FISH.items():
                for method_id, method in METHODS.items():
                    if method.sense >= SENSE_MIN and method_fits_trap(method, trap):
                        combos.append((setting_id, trap_id, fish_id, method_id))
    return combos


def urgency(trap: Trap, fish: FishKind, delay: int) -> int:
    return trap.exposure + fish.need + delay


def can_save_without_help(method: RescueMethod, trap: Trap, fish: FishKind, delay: int) -> bool:
    return method.power + method.gentle >= urgency(trap, fish, delay)


def outcome_of(params: StoryParams) -> str:
    method = METHODS[params.method]
    trap = TRAPS[params.trap]
    fish = FISH[params.fish]
    if not (method.sense >= SENSE_MIN and method_fits_trap(method, trap)):
        raise StoryError("(No story: that rescue method is not a reasonable fit for this trap.)")
    return "saved" if can_save_without_help(method, trap, fish, params.delay) else "helped"


def chant(setting: Setting) -> str:
    return f'"Lift and hurry, lift and hurry, back to {setting.sea} before the gill goes dry!"'


def play_setup(world: World, captain: Entity, mate: Entity, setting: Setting) -> None:
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a bright morning, {captain.id} and {mate.id} played pirates by {setting.shore}. "
        f"To them, {setting.pirate_opening}."
    )
    world.say(
        f'"Captain {captain.id}!" cried {mate.id}. "The treasure wind is blowing!"'
    )
    world.say(
        f'"Then we sail!" said {captain.id}, stamping one sandy foot as if the whole shore were a deck.'
    )


def find_fish(world: World, captain: Entity, mate: Entity, trap: Trap, fish_kind: FishKind) -> None:
    fish = world.get("fish")
    trap_ent = world.get("trap")
    trap_ent.meters["holding"] += 1
    fish.meters["trapped"] += 1
    fish.meters["air_hunger"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But before they could hunt any pretend treasure, {mate.id} pointed at {trap.found_text}. "
        f"There, in {trap.shape_text}, lay {fish_kind.phrase}, {fish_kind.shimmer}."
    )
    world.say(
        f"One little gill opened and shut. Opened and shut. Opened and shut."
    )
    world.say(
        f'"A pirate must help!" {captain.id} said at once.'
    )


def decide(world: World, captain: Entity, mate: Entity, method: RescueMethod, setting: Setting) -> None:
    captain.memes["care"] += 1
    mate.memes["care"] += 1
    world.say(
        f'{mate.id} knelt close. "{method.phrase.capitalize()} might work," {mate.pronoun()} whispered.'
    )
    world.say(chant(setting))
    world.say(
        f'Soon both children were saying it too: {chant(setting)[1:-1]}'
    )


def attempt_rescue(world: World, captain: Entity, mate: Entity, method: RescueMethod) -> None:
    captain.memes["brave"] += 1
    mate.memes["brave"] += 1
    world.say(
        f"Very carefully, they {method.try_text}."
    )


def finish_saved(world: World, captain: Entity, mate: Entity, parent: Entity,
                 setting: Setting, method: RescueMethod, fish_kind: FishKind) -> None:
    fish = world.get("fish")
    fish.meters["trapped"] = 0.0
    fish.meters["safe_water"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They did not stop. They did not stop. They did not stop until they reached {setting.sea}."
    )
    world.say(
        f"There they {method.success_text}. For one tiny blink, {fish_kind.phrase} tilted in the sunlight, "
        f"and then it flashed away in a silver curl."
    )
    world.say(
        f'{parent.label_word.capitalize()} smiled from nearby. "That was pirate work of the best kind," '
        f'{parent.pronoun()} said.'
    )
    world.say(
        f'{captain.id} and {mate.id} looked at the quiet water and whispered the chant one more time, softer now: '
        f'{chant(setting)}'
    )


def finish_helped(world: World, captain: Entity, mate: Entity, parent: Entity,
                  setting: Setting, method: RescueMethod, fish_kind: FishKind) -> None:
    fish = world.get("fish")
    fish.meters["trapped"] = 0.0
    fish.meters["safe_water"] += 1
    fish.meters["weak"] += 1
    propagate(world, narrate=False)
    helper_name = parent.label_word.capitalize()
    world.say(
        f"But the water in the trap had grown too shallow, and their first brave try was not enough. "
        f"{helper_name} came hurrying over with a wide bucket of clean seawater."
    )
    world.say(
        f'"Quick now," {parent.pronoun()} said kindly, and together they {method.help_text}. '
        f'Then {parent.pronoun()} lowered {fish_kind.phrase} into deeper water.'
    )
    world.say(
        f"For a moment the fish only wobbled. Then the little tail gave one, two, three quick flicks, and off it swam."
    )
    world.say(
        f'{captain.id} let out a breath. "{setting.helper_title.capitalize()} saved the day," {captain.pronoun()} said.'
    )
    world.say(
        f'"And you started the rescue," {parent.pronoun()} answered. "You stopped your game and helped before it was too late."'
    )


def ending_image(world: World, captain: Entity, mate: Entity, setting: Setting) -> None:
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"After that, their pirate game changed. Whenever they pretended to sail {setting.sea}, "
        f"they called themselves the Fish-Friend Crew."
    )
    world.say(
        f"And their grandest treasure was not gold at all, but the shining patch of water where a little life had swum free."
    )


def tell(setting: Setting, trap: Trap, fish_kind: FishKind, method: RescueMethod,
         captain_name: str, captain_gender: str, mate_name: str, mate_gender: str,
         parent_type: str, delay: int) -> World:
    world = World()
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_gender, role="captain"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    trap_ent = world.add(Entity(id="trap", type="trap", label=trap.label, phrase=trap.the))
    fish = world.add(Entity(id="fish", type="fish", label=fish_kind.label, phrase=fish_kind.phrase))

    play_setup(world, captain, mate, setting)
    world.para()
    find_fish(world, captain, mate, trap, fish_kind)
    decide(world, captain, mate, method, setting)
    world.para()
    attempt_rescue(world, captain, mate, method)

    if delay > 0:
        world.say(
            f"But the sun had already been warming the stones, and every small moment mattered."
        )

    outcome = "saved" if can_save_without_help(method, trap, fish_kind, delay) else "helped"
    world.para()
    if outcome == "saved":
        finish_saved(world, captain, mate, parent, setting, method, fish_kind)
    else:
        finish_helped(world, captain, mate, parent, setting, method, fish_kind)
    world.para()
    ending_image(world, captain, mate, setting)

    world.facts.update(
        setting=setting,
        trap_cfg=trap,
        fish_cfg=fish_kind,
        method=method,
        captain=captain,
        mate=mate,
        parent=parent,
        outcome=outcome,
        delay=delay,
        chant=chant(setting),
        fish=fish,
        trap=trap_ent,
        urgent=urgency(trap, fish_kind, delay),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    trap = f["trap_cfg"]
    fish_kind = f["fish_cfg"]
    method = f["method"]
    outcome = f["outcome"]
    if outcome == "saved":
        return [
            'Write a pirate tale for a 3-to-5-year-old that includes the words "gill" and "square" and uses repetition.',
            f"Tell a gentle rescue story where {captain.id} and {mate.id} are playing pirates, find {fish_kind.phrase} trapped in {trap.the}, and save it themselves.",
            f'Write a story with a repeated chant about hurrying a fish back to the sea, and let the children use {method.label} to rescue it.',
        ]
    return [
        'Write a pirate tale for a 3-to-5-year-old that includes the words "gill" and "square" and uses repetition.',
        f"Tell a rescue story where {captain.id} and {mate.id} stop playing pirates to help {fish_kind.phrase} trapped in {trap.the}, but a nearby grown-up must help finish the rescue.",
        f'Write a story with a repeated sea-chant and a happy ending where the fish gets back to the water in time.',
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    return "a girl and a boy"


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    parent = f["parent"]
    trap = f["trap_cfg"]
    fish_kind = f["fish_cfg"]
    method = f["method"]
    outcome = f["outcome"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(captain, mate)} named {captain.id} and {mate.id} who were playing pirates by the shore. "
            f"It is also about {fish_kind.phrase} they found trapped in {trap.the}."
        ),
        (
            "What problem did the children find?",
            f"They found {fish_kind.phrase} stuck in {trap.the}. One little gill kept opening and shutting, which showed the fish needed deeper water quickly."
        ),
        (
            "Why did the children stop their pirate game?",
            f"They stopped because they saw a living creature in trouble. The fish was trapped in a square bit of shallow water, so helping it mattered more than pretend treasure."
        ),
        (
            "What words did they keep repeating?",
            f'They kept repeating, {f["chant"]} The repeated line pushed them to move fast and work together.'
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                "How did they rescue the fish?",
                f"They {method.qa_text}. They kept hurrying until they reached deeper water, and then the fish flashed away."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the fish safe in the water and the children calling themselves the Fish-Friend Crew. The ending image shows that their game changed because they had done something kind and brave."
            )
        )
    else:
        qa.append(
            (
                "Did the children rescue the fish all by themselves?",
                f"No. They began the rescue bravely, but the fish needed faster help, so {parent.label_word} came with clean seawater and finished the job. The children still mattered because they noticed the danger first and asked for help in time."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily because the fish swam away after the grown-up helped. Afterward the children played pirates in a new way, proud that they had stopped their game to save a little life."
            )
        )
    return qa


KNOWLEDGE = {
    "gill": [
        (
            "What is a gill?",
            "A gill is the part of a fish that helps it breathe in water. Fish need water moving over their gills so they can stay alive."
        )
    ],
    "square": [
        (
            "What is a square?",
            "A square is a shape with four equal sides and four corners. In the story, the trapped water or container had a square shape."
        )
    ],
    "fish": [
        (
            "Why does a fish need water?",
            "A fish needs water so its gills can work and its body can stay safe. Out of deep water, a fish can get weak very quickly."
        )
    ],
    "pail": [
        (
            "What is a pail?",
            "A pail is a small bucket for carrying water. A water-filled pail can help move a little sea animal gently."
        )
    ],
    "net": [
        (
            "What is a fishing net?",
            "A fishing net is something with holes that can scoop or catch things in water. If it is used gently, it can help lift a small fish."
        )
    ],
    "hands": [
        (
            "Why should hands be wet when you help a fish?",
            "Wet hands are gentler than dry hands on a fish's body. That helps protect the fish while you move it quickly."
        )
    ],
    "care": [
        (
            "Why is it good to stop a game to help an animal?",
            "It is kind and responsible to help a creature that is in trouble. Games can wait, but a small animal may need help right away."
        )
    ],
}
KNOWLEDGE_ORDER = ["gill", "square", "fish", "pail", "net", "hands", "care"]


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    tags = {"gill", "square", "fish", "care"} | set(world.facts["method"].tags)
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
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def explain_combo(trap: Trap, method: RescueMethod) -> str:
    return (
        f"(No story: {method.label} is not a good way to rescue a fish from {trap.the}. "
        f"Pick a method that can really reach into that trap.)"
    )


CURATED = [
    StoryParams(
        setting="cove",
        trap="square_pool",
        fish="minnow",
        method="both_hands",
        captain="Tom",
        captain_gender="boy",
        mate="Lily",
        mate_gender="girl",
        parent="mother",
        delay=0,
    ),
    StoryParams(
        setting="harbor",
        trap="square_crate",
        fish="goby",
        method="shell_pail",
        captain="Mia",
        captain_gender="girl",
        mate="Ben",
        mate_gender="boy",
        parent="father",
        delay=0,
    ),
    StoryParams(
        setting="lagoon",
        trap="square_crate",
        fish="sprat",
        method="fishing_net",
        captain="Max",
        captain_gender="boy",
        mate="Ava",
        mate_gender="girl",
        parent="mother",
        delay=1,
    ),
    StoryParams(
        setting="cove",
        trap="square_bucket",
        fish="sprat",
        method="both_hands",
        captain="Ella",
        captain_gender="girl",
        mate="Finn",
        mate_gender="boy",
        parent="father",
        delay=1,
    ),
]


ASP_RULES = r"""
sensible_method(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
fits(T, M) :- works_on(M, T).

valid(S, T, F, M) :- setting(S), trap(T), fish(F), method(M),
                     sensible_method(M), fits(T, M).

urgency(T, F, D, U) :- exposure(T, E), need(F, N), U = E + N + D.
ability(M, A) :- power(M, P), gentle(M, G), A = P + G.

saved(T, F, M, D) :- ability(M, A), urgency(T, F, D, U), A >= U.
helped(T, F, M, D) :- valid(_, T, F, M), not saved(T, F, M, D).

outcome(saved) :- chosen_trap(T), chosen_fish(F), chosen_method(M), delay(D), saved(T, F, M, D).
outcome(helped) :- chosen_trap(T), chosen_fish(F), chosen_method(M), delay(D), helped(T, F, M, D).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for trap_id, trap in TRAPS.items():
        lines.append(asp.fact("trap", trap_id))
        lines.append(asp.fact("exposure", trap_id, trap.exposure))
    for fish_id, fish in FISH.items():
        lines.append(asp.fact("fish", fish_id))
        lines.append(asp.fact("need", fish_id, fish.need))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("power", method_id, method.power))
        lines.append(asp.fact("gentle", method_id, method.gentle))
        for trap_id in sorted(method.works_on):
            lines.append(asp.fact("works_on", method_id, trap_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
            asp.fact("chosen_trap", params.trap),
            asp.fact("chosen_fish", params.fish),
            asp.fact("chosen_method", params.method),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A pirate rescue storyworld with a trapped fish, a square trap, and a repeated chant."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trap", choices=TRAPS)
    ap.add_argument("--fish", choices=FISH)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the children take before the rescue")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))
    if args.trap and args.method:
        trap = TRAPS[args.trap]
        method = METHODS[args.method]
        if not method_fits_trap(method, trap):
            raise StoryError(explain_combo(trap, method))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.trap is None or combo[1] == args.trap)
        and (args.fish is None or combo[2] == args.fish)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, trap_id, fish_id, method_id = rng.choice(sorted(combos))
    captain, captain_gender = pick_kid(rng)
    mate, mate_gender = pick_kid(rng, avoid=captain)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting_id,
        trap=trap_id,
        fish=fish_id,
        method=method_id,
        captain=captain,
        captain_gender=captain_gender,
        mate=mate,
        mate_gender=mate_gender,
        parent=parent,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.trap not in TRAPS:
        raise StoryError(f"(Unknown trap: {params.trap})")
    if params.fish not in FISH:
        raise StoryError(f"(Unknown fish: {params.fish})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    method = METHODS[params.method]
    trap = TRAPS[params.trap]
    if method.sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))
    if not method_fits_trap(method, trap):
        raise StoryError(explain_combo(trap, method))

    world = tell(
        setting=SETTINGS[params.setting],
        trap=trap,
        fish_kind=FISH[params.fish],
        method=method,
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
        parent_type=params.parent,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_items(world)],
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

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        try:
            py = outcome_of(params)
            asp = asp_outcome(params)
            if py != asp:
                mismatches += 1
                print(f"Outcome mismatch for {params}: python={py} asp={asp}")
        except Exception as err:
            mismatches += 1
            print(f"Outcome check crashed for {params}: {err}")
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story.")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"Smoke test failed: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, trap, fish, method) combos:\n")
        for setting_id, trap_id, fish_id, method_id in combos:
            print(f"  {setting_id:8} {trap_id:13} {fish_id:7} {method_id}")
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
            header = f"### {p.captain} & {p.mate}: {p.fish} in {p.trap} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
