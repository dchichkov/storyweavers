#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/kraft_capital_quest_sharing_moral_value_fable.py
============================================================================

A standalone story world for a small fable-like domain: a young animal sets out
on a quest to bring a gift to the spring fair in Capital Meadow, but the road is
hard unless the travelers share what they carry. The world models hunger,
thirst, tiredness, trust, and generosity; the turn of the story comes from a
choice to share or hoard; the ending proves the moral by whether the gift arrives
whole and the friends arrive together.

Seed words woven into the domain:
- kraft: the travelers carry their trail lunch in a kraft-paper packet
- capital: the destination is Capital Meadow, the biggest field in the valley

Run it
------
python storyworlds/worlds/gpt-5.4/kraft_capital_quest_sharing_moral_value_fable.py
python storyworlds/worlds/gpt-5.4/kraft_capital_quest_sharing_moral_value_fable.py --hero mouse --helper sparrow --share share_bread
python storyworlds/worlds/gpt-5.4/kraft_capital_quest_sharing_moral_value_fable.py --gift pebble_crown --path hill --share hoard
python storyworlds/worlds/gpt-5.4/kraft_capital_quest_sharing_moral_value_fable.py --all --qa
python storyworlds/worlds/gpt-5.4/kraft_capital_quest_sharing_moral_value_fable.py --verify
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "it" if self.kind != "character" else "them"


@dataclass
class AnimalKind:
    id: str
    label: str
    phrase: str
    stride: str
    home: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    weight: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Path:
    id: str
    label: str
    phrase: str
    strain: int
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareMode:
    id: str
    sense: int
    shares_food: bool
    shares_water: bool
    shares_load: bool
    moral: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    hero: str
    helper: str
    gift: str
    path: str
    share: str
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

    def copy(self) -> "World":
        new = World()
        new.entities = copy.deepcopy(self.entities)
        new.fired = set(self.fired)
        new.paragraphs = [[]]
        new.facts = copy.deepcopy(self.facts)
        return new


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_needy(world: World) -> list[str]:
    out: list[str] = []
    for eid in ("hero", "helper"):
        actor = world.get(eid)
        if actor.meters["strain"] >= THRESHOLD:
            sig = ("need", eid)
            if sig not in world.fired:
                world.fired.add(sig)
                actor.meters["hunger"] += 1
                actor.meters["thirst"] += 1
                out.append("__need__")
    return out


def _r_unshared_load(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    gift = world.get("gift")
    if gift.meters["carried_by_one"] >= THRESHOLD:
        sig = ("unshared_load", "gift")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["tired"] += float(gift.attrs.get("weight", 1))
            helper.memes["worry"] += 1
            return ["__load__"]
    return []


def _r_shared_relief(world: World) -> list[str]:
    gift = world.get("gift")
    hero = world.get("hero")
    helper = world.get("helper")
    if gift.meters["carried_together"] >= THRESHOLD:
        sig = ("shared_relief", "gift")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["trust"] += 1
            helper.memes["trust"] += 1
            if hero.meters["tired"] > 0:
                hero.meters["tired"] -= 1
            return ["__trust__"]
    return []


def _r_friendship(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes["shared"] + helper.memes["shared"] >= 2:
        sig = ("friendship", "pair")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["joy"] += 1
            helper.memes["joy"] += 1
            return ["__friendship__"]
    return []


CAUSAL_RULES = [
    Rule(name="needy", tag="physical", apply=_r_needy),
    Rule(name="unshared_load", tag="physical", apply=_r_unshared_load),
    Rule(name="shared_relief", tag="social", apply=_r_shared_relief),
    Rule(name="friendship", tag="social", apply=_r_friendship),
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
        for sent in produced:
            world.say(sent)
    return produced


ANIMALS = {
    "mouse": AnimalKind(
        id="mouse",
        label="mouse",
        phrase="a small gray mouse",
        stride="quick little feet",
        home="a burrow under the berry hedge",
        tags={"mouse"},
    ),
    "rabbit": AnimalKind(
        id="rabbit",
        label="rabbit",
        phrase="a long-eared rabbit",
        stride="springy hops",
        home="a warm den by the clover patch",
        tags={"rabbit"},
    ),
    "sparrow": AnimalKind(
        id="sparrow",
        label="sparrow",
        phrase="a brown sparrow",
        stride="light wingbeats",
        home="a nest tucked in the willow tree",
        tags={"sparrow", "bird"},
    ),
    "turtle": AnimalKind(
        id="turtle",
        label="turtle",
        phrase="a patient turtle",
        stride="slow, steady steps",
        home="a mossy bank beside the pond",
        tags={"turtle"},
    ),
}

GIFTS = {
    "seed_cake": Gift(
        id="seed_cake",
        label="seed cake",
        phrase="a round seed cake tied with blue grass",
        fragile=False,
        weight=1,
        tags={"cake", "gift"},
    ),
    "berry_jar": Gift(
        id="berry_jar",
        label="berry jam jar",
        phrase="a little jar of berry jam with a cork top",
        fragile=True,
        weight=2,
        tags={"berries", "jar", "gift"},
    ),
    "pebble_crown": Gift(
        id="pebble_crown",
        label="pebble crown",
        phrase="a tiny crown made of smooth bright pebbles",
        fragile=True,
        weight=2,
        tags={"crown", "gift"},
    ),
}

PATHS = {
    "brook": Path(
        id="brook",
        label="brook path",
        phrase="the brook path, where flat stones shone in the water",
        strain=1,
        risk="slipping on wet stones",
        tags={"brook", "water"},
    ),
    "hill": Path(
        id="hill",
        label="hill path",
        phrase="the hill path, where the wind pushed against every step",
        strain=2,
        risk="the long climb",
        tags={"hill", "wind"},
    ),
    "bramble": Path(
        id="bramble",
        label="bramble path",
        phrase="the bramble path, narrow and scratchy beside the thorns",
        strain=2,
        risk="snagging the bundle on thorns",
        tags={"bramble", "thorns"},
    ),
}

SHARE_MODES = {
    "share_bread": ShareMode(
        id="share_bread",
        sense=2,
        shares_food=True,
        shares_water=False,
        shares_load=False,
        moral="bread tastes better when it is shared",
        tags={"sharing", "food"},
    ),
    "share_load": ShareMode(
        id="share_load",
        sense=2,
        shares_food=False,
        shares_water=False,
        shares_load=True,
        moral="a heavy gift feels lighter with two kind hearts",
        tags={"sharing", "help"},
    ),
    "share_all": ShareMode(
        id="share_all",
        sense=3,
        shares_food=True,
        shares_water=True,
        shares_load=True,
        moral="when friends share what they have, everyone can keep going",
        tags={"sharing", "food", "water", "help"},
    ),
    "hoard": ShareMode(
        id="hoard",
        sense=1,
        shares_food=False,
        shares_water=False,
        shares_load=False,
        moral="keeping everything to yourself leaves both paws and hearts empty",
        tags={"hoard"},
    ),
}

NAMES = {
    "mouse": ["Mimi", "Pip", "Moss"],
    "rabbit": ["Hopper", "Nell", "Clover"],
    "sparrow": ["Pip", "Feather", "Tansy"],
    "turtle": ["Moss", "Shell", "Tumble"],
}

KNOWLEDGE = {
    "sharing": [
        (
            "Why does sharing help on a long trip?",
            "Sharing helps because one traveler may be hungry, thirsty, or tired when another still has enough. When friends divide food, water, or work, the whole group can keep going."
        )
    ],
    "gift": [
        (
            "Why should you carry a gift carefully?",
            "A gift is special because someone made or chose it with care. Carrying it gently shows respect for both the giver and the one who will receive it."
        )
    ],
    "water": [
        (
            "Why do travelers need water?",
            "Bodies need water to keep going, especially on a warm or tiring walk. Drinking a little can help you feel steadier and less weak."
        )
    ],
    "food": [
        (
            "Why do travelers eat on a quest?",
            "Food gives the body energy for walking, climbing, or carrying things. A small meal can help tired legs keep moving."
        )
    ],
    "capital": [
        (
            "What does capital mean in this story?",
            "Here, Capital Meadow means the biggest and busiest meadow in the valley. It is the place where many animals gather for the fair."
        )
    ],
    "kraft": [
        (
            "What is kraft paper?",
            "Kraft paper is a strong brown paper often used for wrapping things. In the story, it keeps the travelers' lunch tucked together."
        )
    ],
}
KNOWLEDGE_ORDER = ["sharing", "gift", "food", "water", "capital", "kraft"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for hero in ANIMALS:
        for helper in ANIMALS:
            if hero == helper:
                continue
            for gift_id, gift in GIFTS.items():
                for path_id, path in PATHS.items():
                    for share_id, share in SHARE_MODES.items():
                        if reasonable_choice(ANIMALS[hero], ANIMALS[helper], gift, path, share):
                            combos.append((hero, helper, gift_id, path_id, share_id))
    return combos


def reasonable_choice(hero: AnimalKind, helper: AnimalKind, gift: Gift, path: Path, share: ShareMode) -> bool:
    if hero.id == helper.id:
        return False
    if share.sense < SENSE_MIN and (gift.fragile or path.strain >= 2):
        return False
    return True


def explain_rejection(hero: str, helper: str, gift: Gift, path: Path, share: ShareMode) -> str:
    if hero == helper:
        return "(No story: the quest needs two different travelers so sharing can change the outcome.)"
    if share.sense < SENSE_MIN and (gift.fragile or path.strain >= 2):
        return (
            f"(No story: '{share.id}' is too unkind for a hard trip with {gift.phrase} on {path.label}. "
            f"This world refuses combinations where hoarding would make the quest plainly unreasonable.)"
        )
    return "(No story: this combination is outside the world's reasonableness gate.)"


def predict_outcome(gift: Gift, path: Path, share: ShareMode) -> dict:
    severe = path.strain + gift.weight
    success = share.shares_load or share.shares_water or severe <= 2
    whole = not (gift.fragile and not share.shares_load and path.strain >= 2)
    together = share.sense >= SENSE_MIN
    return {"success": success and whole and together, "whole": whole, "together": together, "severe": severe}


def quest_intro(world: World, hero: Entity, helper: Entity, gift: Entity, path: Path) -> None:
    world.say(
        f"In the valley below the willow trees stood Capital Meadow, the biggest field for many miles."
    )
    world.say(
        f"One bright morning, {hero.id}, {hero.phrase}, set out from {hero.attrs['home']} with {gift.phrase} for the spring fair."
    )
    world.say(
        f"{helper.id}, {helper.phrase}, came along too, for the road to Capital Meadow followed {path.phrase}."
    )


def lunch_intro(world: World, hero: Entity) -> None:
    world.say(
        f"In {hero.pronoun('possessive')} satchel rustled a kraft-paper packet with two pieces of oat bread and a tiny bottle of cool water."
    )


def begin_quest(world: World, hero: Entity, helper: Entity, gift: Entity, path: Path) -> None:
    world.para()
    world.say(
        f"They started in good cheer. {hero.id} carried the {gift.label}, and {helper.id} kept watch for {path.risk}."
    )
    hero.meters["strain"] += path.strain
    helper.meters["strain"] += path.strain
    gift.meters["carried_by_one"] += 1
    propagate(world, narrate=False)
    world.facts["risk"] = path.risk


def need_turn(world: World, hero: Entity, helper: Entity) -> None:
    if hero.meters["hunger"] >= THRESHOLD or helper.meters["hunger"] >= THRESHOLD:
        world.say(
            f"Before long, the road felt longer than it had at dawn. {hero.id}'s steps slowed, and {helper.id} licked dry lips."
        )


def choose_share(world: World, hero: Entity, helper: Entity, gift: Entity, share: ShareMode) -> None:
    world.para()
    if share.id == "hoard":
        hero.memes["greed"] += 1
        helper.memes["sadness"] += 1
        world.say(
            f'"The bread and water are mine for later," said {hero.id}, hugging the satchel close.'
        )
        world.say(
            f'{helper.id} said nothing, but the silence between them grew as heavy as the gift itself.'
        )
    else:
        if share.shares_food:
            hero.memes["shared"] += 1
            helper.memes["shared"] += 1
            hero.meters["hunger"] = max(0.0, hero.meters["hunger"] - 1)
            helper.meters["hunger"] = max(0.0, helper.meters["hunger"] - 1)
            world.say(
                f'{hero.id} opened the kraft-paper packet and broke the oat bread into equal pieces.'
            )
            world.say(
                f'"Half for you and half for me," {hero.pronoun()} said, and {helper.id} smiled at once.'
            )
        if share.shares_water:
            hero.memes["shared"] += 1
            helper.memes["shared"] += 1
            hero.meters["thirst"] = max(0.0, hero.meters["thirst"] - 1)
            helper.meters["thirst"] = max(0.0, helper.meters["thirst"] - 1)
            world.say(
                f'Then {hero.id} tipped the little bottle so each traveler could drink a careful sip.'
            )
        if share.shares_load:
            hero.memes["shared"] += 1
            helper.memes["shared"] += 1
            gift.meters["carried_by_one"] = 0.0
            gift.meters["carried_together"] += 1
            world.say(
                f'When the path grew steep, {helper.id} stepped close. Together they carried the {gift.label} between them.'
            )
        propagate(world, narrate=False)


def travel_result(world: World, hero: Entity, helper: Entity, gift: Entity, path: Path, share: ShareMode, outcome: dict) -> None:
    world.para()
    if outcome["success"]:
        hero.memes["joy"] += 1
        helper.memes["joy"] += 1
        world.say(
            f"Because kindness had lightened the journey, the rest of the way did not seem so fierce."
        )
        world.say(
            f"By afternoon they reached Capital Meadow side by side, and the {gift.label} arrived safe and neat."
        )
        world.say(
            f"The fair bells rang, and the two friends looked at one another as proudly as if they had carried sunshine itself."
        )
    else:
        if gift.attrs.get("fragile") and not share.shares_load and path.strain >= 2:
            gift.meters["broken"] += 1
            world.say(
                f"But on the roughest part of {path.label}, the burden shifted in {hero.id}'s tired paws."
            )
            world.say(
                f"The {gift.label} slipped, bumped a stone, and lost some of its beauty before they ever saw Capital Meadow."
            )
        else:
            world.say(
                f"But the road dragged on, for tired feet and lonely hearts make every hill seem higher."
            )
        if share.sense < SENSE_MIN:
            hero.memes["regret"] += 1
            helper.memes["sadness"] += 1
            world.say(
                f"When they finally reached the edge of Capital Meadow, neither felt like singing. They had arrived, yet the quest had grown smaller inside them."
            )
        else:
            world.say(
                f"They reached the meadow at last, though the journey had cost more worry than it needed to."
            )


def moral_close(world: World, hero: Entity, helper: Entity, share: ShareMode, outcome: dict) -> None:
    world.para()
    if outcome["success"]:
        world.say(
            f"Old Owl, who watched the fair from an oak branch, nodded and said, \"A road is shortest when friends share it.\""
        )
    else:
        world.say(
            f"Old Owl, who watched the fair from an oak branch, said, \"A traveler who keeps everything clenched soon learns how empty a closed paw can feel.\""
        )
    world.say(
        f"And so {hero.id} and {helper.id} learned that {share.moral}."
    )


def tell(hero_cfg: AnimalKind, helper_cfg: AnimalKind, gift_cfg: Gift, path_cfg: Path, share_cfg: ShareMode) -> World:
    world = World()
    hero_name = random.choice(NAMES[hero_cfg.id])
    helper_pool = [n for n in NAMES[helper_cfg.id] if n != hero_name]
    helper_name = random.choice(helper_pool) if helper_pool else helper_cfg.label.title()

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_cfg.id,
        label=hero_cfg.label,
        phrase=hero_cfg.phrase,
        role="hero",
        attrs={"home": hero_cfg.home, "display_name": hero_name},
        tags=set(hero_cfg.tags),
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.id,
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        role="helper",
        attrs={"home": helper_cfg.home, "display_name": helper_name},
        tags=set(helper_cfg.tags),
    ))
    gift = world.add(Entity(
        id="gift",
        kind="thing",
        type=gift_cfg.id,
        label=gift_cfg.label,
        phrase=gift_cfg.phrase,
        attrs={"fragile": gift_cfg.fragile, "weight": gift_cfg.weight},
        tags=set(gift_cfg.tags),
    ))

    world.facts.update(
        hero_cfg=hero_cfg,
        helper_cfg=helper_cfg,
        gift_cfg=gift_cfg,
        path_cfg=path_cfg,
        share_cfg=share_cfg,
        hero_name=hero_name,
        helper_name=helper_name,
    )

    quest_intro(world, hero, helper, gift, path_cfg)
    lunch_intro(world, hero)
    begin_quest(world, hero, helper, gift, path_cfg)
    need_turn(world, hero, helper)
    outcome = predict_outcome(gift_cfg, path_cfg, share_cfg)
    choose_share(world, hero, helper, gift, share_cfg)
    travel_result(world, hero, helper, gift, path_cfg, share_cfg, outcome)
    moral_close(world, hero, helper, share_cfg, outcome)

    world.facts.update(
        hero=hero,
        helper=helper,
        gift=gift,
        outcome=outcome,
        success=outcome["success"],
        whole=outcome["whole"],
        together=outcome["together"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short fable for a young child that includes the words "kraft" and "capital".',
        f"Tell a quest story about two animals carrying {f['gift_cfg'].phrase} to Capital Meadow, where sharing changes the journey.",
        "Write a moral fable in which generosity on the road matters more than arriving first.",
    ]


def display_name(ent: Entity) -> str:
    return ent.attrs.get("display_name", ent.label.title())


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    gift = f["gift_cfg"]
    path = f["path_cfg"]
    share = f["share_cfg"]
    outcome = f["outcome"]
    hname = display_name(hero)
    pname = display_name(helper)

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hname} the {hero.label} and {pname} the {helper.label}. They travel together to Capital Meadow with a gift for the spring fair."
        ),
        (
            "What was their quest?",
            f"Their quest was to carry {gift.phrase} along {path.phrase} to Capital Meadow. The trip mattered because the gift was meant for the fair there."
        ),
        (
            "What was inside the satchel?",
            "Inside the satchel was a kraft-paper packet with oat bread and a tiny bottle of water. Those simple things became important when the road made the travelers hungry and tired."
        ),
    ]
    if share.id == "hoard":
        qa.append(
            (
                f"Why did the journey grow harder after {hname} kept the food and water?",
                f"The journey grew harder because {hname} chose not to share the bread, water, or work. That left both travelers more tired and sad, so the road felt longer than it really was."
            )
        )
    else:
        parts = []
        if share.shares_food:
            parts.append("bread")
        if share.shares_water:
            parts.append("water")
        if share.shares_load:
            parts.append("the weight of the gift")
        qa.append(
            (
                "What did they share on the road?",
                f"They shared {', '.join(parts)}. Sharing met the need that the long path created, so their bodies felt steadier and their friendship grew stronger."
            )
        )
    if outcome["success"]:
        qa.append(
            (
                "How did the story end?",
                f"They reached Capital Meadow side by side, and the {gift.label} arrived safely. The ending shows that kindness helped both the travelers and the gift they were carrying."
            )
        )
    else:
        if gift.fragile and not share.shares_load and path.strain >= 2:
            qa.append(
                (
                    "What went wrong with the gift?",
                    f"The {gift.label} was fragile, and one tired traveler carried it alone over a hard path. Because the load was not shared, it slipped and was damaged before the fair."
                )
            )
        qa.append(
            (
                "What lesson did they learn?",
                f"They learned that {share.moral}. The road itself taught the lesson, because selfishness made the quest heavier while generosity would have helped everyone."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sharing", "gift", "capital", "kraft"}
    if f["share_cfg"].shares_food:
        tags.add("food")
    if f["share_cfg"].shares_water or f["path_cfg"].id == "brook":
        tags.add("water")
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
    for ent_id, ent in world.entities.items():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            bits.append(f"attrs={shown}")
        lines.append(f"  {ent_id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hero="mouse",
        helper="sparrow",
        gift="seed_cake",
        path="brook",
        share="share_all",
    ),
    StoryParams(
        hero="rabbit",
        helper="turtle",
        gift="berry_jar",
        path="hill",
        share="share_load",
    ),
    StoryParams(
        hero="sparrow",
        helper="rabbit",
        gift="pebble_crown",
        path="bramble",
        share="share_all",
    ),
    StoryParams(
        hero="mouse",
        helper="turtle",
        gift="seed_cake",
        path="brook",
        share="share_bread",
    ),
]


ASP_RULES = r"""
different_pair(H, Hp) :- animal(H), animal(Hp), H != Hp.

reasonable_share(S, G, P) :- share_mode(S), gift(G), path(P), sense(S, X), sense_min(M), X >= M.
reasonable_share(S, G, P) :- share_mode(S), gift(G), path(P), sense(S, X), sense_min(M), X < M, not fragile(G), strain(P, 1).

valid(H, Hp, G, P, S) :- different_pair(H, Hp), gift(G), path(P), share_mode(S), reasonable_share(S, G, P).

severe(G, P) :- gift(G), path(P), weight(G, W), strain(P, S), W + S >= 3.
success(S, G, P) :- valid(_, _, G, P, S), carries_together(S).
success(S, G, P) :- valid(_, _, G, P, S), shares_water(S), not severe(G, P).
success(S, G, P) :- valid(_, _, G, P, S), not severe(G, P), not fragile(G), sense(S, X), X >= sense_min(M), X >= M.

whole(S, G, P) :- valid(_, _, G, P, S), not fragile(G).
whole(S, G, P) :- valid(_, _, G, P, S), fragile(G), carries_together(S).
whole(S, G, P) :- valid(_, _, G, P, S), fragile(G), strain(P, 1).

together(S) :- share_mode(S), sense(S, X), sense_min(M), X >= M.

outcome(success) :- chosen_share(S), chosen_gift(G), chosen_path(P), success(S, G, P), whole(S, G, P), together(S).
outcome(hard_lesson) :- not outcome(success).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("weight", gid, gift.weight))
        if gift.fragile:
            lines.append(asp.fact("fragile", gid))
    for pid, path in PATHS.items():
        lines.append(asp.fact("path", pid))
        lines.append(asp.fact("strain", pid, path.strain))
    for sid, share in SHARE_MODES.items():
        lines.append(asp.fact("share_mode", sid))
        lines.append(asp.fact("sense", sid, share.sense))
        if share.shares_food:
            lines.append(asp.fact("shares_food", sid))
        if share.shares_water:
            lines.append(asp.fact("shares_water", sid))
        if share.shares_load:
            lines.append(asp.fact("carries_together", sid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_share", params.share),
        asp.fact("chosen_gift", params.gift),
        asp.fact("chosen_path", params.path),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    outcome = predict_outcome(GIFTS[params.gift], PATHS[params.path], SHARE_MODES[params.share])
    return "success" if outcome["success"] else "hard_lesson"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a fable-like quest where sharing changes the journey."
    )
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--helper", choices=ANIMALS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--share", choices=SHARE_MODES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hero and args.helper and args.hero == args.helper:
        raise StoryError("(No story: choose two different animals so sharing can matter.)")
    if args.hero and args.helper and args.gift and args.path and args.share:
        if not reasonable_choice(ANIMALS[args.hero], ANIMALS[args.helper], GIFTS[args.gift], PATHS[args.path], SHARE_MODES[args.share]):
            raise StoryError(explain_rejection(args.hero, args.helper, GIFTS[args.gift], PATHS[args.path], SHARE_MODES[args.share]))

    combos = [
        combo for combo in valid_combos()
        if (args.hero is None or combo[0] == args.hero)
        and (args.helper is None or combo[1] == args.helper)
        and (args.gift is None or combo[2] == args.gift)
        and (args.path is None or combo[3] == args.path)
        and (args.share is None or combo[4] == args.share)
    ]
    if not combos:
        chosen_hero = args.hero or next(iter(ANIMALS))
        chosen_helper = args.helper or next(k for k in ANIMALS if k != chosen_hero)
        chosen_gift = GIFTS[args.gift] if args.gift else next(iter(GIFTS.values()))
        chosen_path = PATHS[args.path] if args.path else next(iter(PATHS.values()))
        chosen_share = SHARE_MODES[args.share] if args.share else next(iter(SHARE_MODES.values()))
        raise StoryError(explain_rejection(chosen_hero, chosen_helper, chosen_gift, chosen_path, chosen_share))

    hero, helper, gift, path, share = rng.choice(sorted(combos))
    return StoryParams(
        hero=hero,
        helper=helper,
        gift=gift,
        path=path,
        share=share,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        hero_cfg = ANIMALS[params.hero]
        helper_cfg = ANIMALS[params.helper]
        gift_cfg = GIFTS[params.gift]
        path_cfg = PATHS[params.path]
        share_cfg = SHARE_MODES[params.share]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter: {exc.args[0]})") from exc

    if not reasonable_choice(hero_cfg, helper_cfg, gift_cfg, path_cfg, share_cfg):
        raise StoryError(explain_rejection(params.hero, params.helper, gift_cfg, path_cfg, share_cfg))

    rng = random.Random(params.seed if params.seed is not None else 0)
    old_state = random.getstate()
    random.setstate(rng.getstate())
    try:
        world = tell(hero_cfg, helper_cfg, gift_cfg, path_cfg, share_cfg)
    finally:
        rng.setstate(random.getstate())
        random.setstate(old_state)

    story = world.render().replace("hero", display_name(world.get("hero"))).replace("helper", display_name(world.get("helper")))
    story = story.replace("hero's", f"{display_name(world.get('hero'))}'s")
    story = story.replace("helper's", f"{display_name(world.get('helper'))}'s")
    story = story.replace(" hero ", f" {display_name(world.get('hero'))} ")
    story = story.replace(" helper ", f" {display_name(world.get('helper'))} ")

    hero_name = world.facts["hero_name"]
    helper_name = world.facts["helper_name"]
    story = story.replace("hero", hero_name).replace("helper", helper_name)

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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for i in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(i))
            p.seed = i
            cases.append(p)
        except StoryError:
            pass

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(StoryParams(
            hero="mouse",
            helper="sparrow",
            gift="seed_cake",
            path="brook",
            share="share_all",
            seed=123,
        ))
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hero, helper, gift, path, share) combos:\n")
        for hero, helper, gift, path, share in combos:
            print(f"  {hero:8} {helper:8} {gift:12} {path:8} {share}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for idx, p in enumerate(CURATED):
            p = StoryParams(
                hero=p.hero,
                helper=p.helper,
                gift=p.gift,
                path=p.path,
                share=p.share,
                seed=base_seed + idx,
            )
            samples.append(generate(p))
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
            header = f"### {p.hero} with {p.helper}: {p.gift} on {p.path} ({p.share}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
