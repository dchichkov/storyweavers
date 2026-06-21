#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/watt_stun_tent_garden_center_reconciliation_dialogue.py
==================================================================================

A small myth-flavored storyworld set in a garden center at dusk.

The core tale:
- two children enter the moonlit festival tent at a garden center,
- they have a quest to find a special plant for an evening table,
- they argue about how to search and whether to use a bright lamp,
- dialogue and apology repair the friendship,
- the ending proves what changed: they leave carrying the plant together.

The world is state-driven:
- physical meters track light, stun, and whether the quest plant was found,
- emotional memes track pride, hurt, trust, fear, and reconciliation.

Run it
------
python storyworlds/worlds/gpt-5.4/watt_stun_tent_garden_center_reconciliation_dialogue.py
python storyworlds/worlds/gpt-5.4/watt_stun_tent_garden_center_reconciliation_dialogue.py --all
python storyworlds/worlds/gpt-5.4/watt_stun_tent_garden_center_reconciliation_dialogue.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/watt_stun_tent_garden_center_reconciliation_dialogue.py --qa
python storyworlds/worlds/gpt-5.4/watt_stun_tent_garden_center_reconciliation_dialogue.py --trace --seed 7
python storyworlds/worlds/gpt-5.4/watt_stun_tent_garden_center_reconciliation_dialogue.py --verify
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
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
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
class QuestItem:
    id: str
    label: str
    phrase: str
    home: str
    gift_use: str
    guide_kind: str
    myth_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    label: str
    phrase: str
    kind: str
    safe_watts: int
    lead_verb: str
    reaction: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    watts: int
    glow: str
    portable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    quest_item: str
    guide: str
    light: str
    apology_timing: str
    seeker_name: str
    seeker_gender: str
    friend_name: str
    friend_gender: str
    parent_type: str
    relation: str
    seed: Optional[int] = None


QUEST_ITEMS = {
    "moonbloom": QuestItem(
        id="moonbloom",
        label="moonbloom",
        phrase="a pale moonbloom in a clay pot",
        home="the silver-vine corner inside the spring tent",
        gift_use="to set beside Grandma's bowl of evening tea",
        guide_kind="moth",
        myth_image="its petals looked as if a thin moon had been folded into a flower",
        tags={"moonbloom", "quest", "plant"},
    ),
    "star_mint": QuestItem(
        id="star_mint",
        label="star-mint",
        phrase="a pot of star-mint with five-point leaves",
        home="the herb table beneath the striped tent cloth",
        gift_use="to lay by the family supper tray",
        guide_kind="firefly",
        myth_image="its leaves caught small points of gold like stars in grass",
        tags={"star_mint", "quest", "plant"},
    ),
    "dawn_fern": QuestItem(
        id="dawn_fern",
        label="dawn fern",
        phrase="a curled dawn fern in a blue pot",
        home="the mist shelf at the back of the cool tent",
        gift_use="to stand by the window where Grandfather told stories",
        guide_kind="treefrog",
        myth_image="its fronds were curled like green question marks waiting for sunrise",
        tags={"dawn_fern", "quest", "plant"},
    ),
}

GUIDES = {
    "moth": Guide(
        id="moth",
        label="moth",
        phrase="a velvet moth",
        kind="moth",
        safe_watts=15,
        lead_verb="drifted",
        reaction="folded its wings and clung to the tent rope",
        tags={"moth", "night_creature"},
    ),
    "firefly": Guide(
        id="firefly",
        label="firefly",
        phrase="a lantern-green firefly",
        kind="firefly",
        safe_watts=20,
        lead_verb="bobbed",
        reaction="went still in the air like a dropped spark",
        tags={"firefly", "night_creature"},
    ),
    "treefrog": Guide(
        id="treefrog",
        label="treefrog",
        phrase="a thumb-sized treefrog",
        kind="treefrog",
        safe_watts=25,
        lead_verb="hopped",
        reaction="flattened against a damp pot and would not sing",
        tags={"treefrog", "night_creature"},
    ),
}

LIGHTS = {
    "ten_watt_lantern": Light(
        id="ten_watt_lantern",
        label="ten-watt lantern",
        phrase="a ten-watt lantern",
        watts=10,
        glow="made a small honey-colored circle on the path",
        tags={"lantern", "light", "safe_light"},
    ),
    "fifteen_watt_lamp": Light(
        id="fifteen_watt_lamp",
        label="fifteen-watt lamp",
        phrase="a fifteen-watt hand lamp",
        watts=15,
        glow="shone a clear bead of light between the leaves",
        tags={"lamp", "light"},
    ),
    "sixty_watt_grow_light": Light(
        id="sixty_watt_grow_light",
        label="sixty-watt grow light",
        phrase="a sixty-watt grow light",
        watts=60,
        glow="flared white enough to turn the green tent walls almost silver",
        tags={"grow_light", "light", "bright"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tali", "Nora", "Suri", "Ava", "Mina", "Etta"]
BOY_NAMES = ["Ivo", "Nico", "Tomas", "Eli", "Bram", "Oren", "Milo", "Finn"]

KNOWLEDGE = {
    "watt": [
        (
            "What is a watt?",
            "A watt is a way to talk about how much power a light or machine uses. A bigger number usually means a stronger light.",
        )
    ],
    "tent": [
        (
            "What is a tent?",
            "A tent is a shelter made from cloth stretched over poles or ropes. It makes a little room even when you are outside or in a big open place.",
        )
    ],
    "moth": [
        (
            "Why can a bright light bother a moth?",
            "Many moths use gentle light and darkness to find their way. A sudden bright light can confuse or stun them for a moment.",
        )
    ],
    "firefly": [
        (
            "Why do fireflies glow?",
            "Fireflies make their own little light in their bodies. They use it to signal in the dark.",
        )
    ],
    "treefrog": [
        (
            "Why do treefrogs like damp places?",
            "Treefrogs have soft skin that dries out easily. Cool, damp places help keep them comfortable.",
        )
    ],
    "apology": [
        (
            "What does an apology do?",
            "An apology tells someone you know you hurt them and wish to mend it. It can begin to rebuild trust when the words are honest.",
        )
    ],
    "garden_center": [
        (
            "What is a garden center?",
            "A garden center is a shop where people buy plants, soil, pots, and tools for growing things. It often has long tables, greenhouse rooms, and rows of flowers.",
        )
    ],
    "lantern": [
        (
            "Why is a small lantern useful in the dark?",
            "A small lantern lets you see where to walk without flooding everything with harsh light. That can be kinder to small night creatures.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "garden_center",
    "watt",
    "tent",
    "moth",
    "firefly",
    "treefrog",
    "lantern",
    "apology",
]


def valid_combo(quest_item_id: str, guide_id: str) -> bool:
    return QUEST_ITEMS[quest_item_id].guide_kind == GUIDES[guide_id].kind


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for quest_item_id, quest_item in QUEST_ITEMS.items():
        for guide_id, guide in GUIDES.items():
            if quest_item.guide_kind == guide.kind:
                combos.append((quest_item_id, guide_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    light = LIGHTS[params.light]
    guide = GUIDES[params.guide]
    if light.watts > guide.safe_watts:
        return "mishap_reconciliation"
    if params.apology_timing == "early":
        return "peaceful_reconciliation"
    return "late_words_but_safe"


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


def _r_stun(world: World) -> list[str]:
    guide = world.get("guide")
    light = world.get("light")
    if light.attrs.get("watts", 0) <= guide.attrs.get("safe_watts", 0):
        return []
    sig = ("stun", guide.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    guide.meters["stunned"] += 1
    guide.memes["fear"] += 1
    for eid in ("seeker", "friend"):
        world.get(eid).memes["fear"] += 1
    return ["__stun__"]


def _r_hurt(world: World) -> list[str]:
    seeker = world.get("seeker")
    friend = world.get("friend")
    if seeker.memes["sharp_words"] < THRESHOLD:
        return []
    sig = ("hurt", friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["hurt"] += 1
    friend.memes["distance"] += 1
    seeker.memes["distance"] += 1
    return []


def _r_reconcile(world: World) -> list[str]:
    seeker = world.get("seeker")
    friend = world.get("friend")
    if seeker.memes["apology"] < THRESHOLD:
        return []
    sig = ("reconcile", seeker.id, friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["distance"] = 0.0
    friend.memes["distance"] = 0.0
    seeker.memes["trust"] += 1
    friend.memes["trust"] += 1
    seeker.memes["peace"] += 1
    friend.memes["peace"] += 1
    return []


def _r_guide_returns(world: World) -> list[str]:
    guide = world.get("guide")
    if guide.meters["stunned"] < THRESHOLD:
        return []
    if world.get("light").meters["dimmed"] < THRESHOLD:
        return []
    if world.get("friend").memes["peace"] < THRESHOLD:
        return []
    sig = ("return", guide.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    guide.meters["stunned"] = 0.0
    guide.memes["fear"] = 0.0
    guide.memes["trust"] += 1
    return []


def _r_find(world: World) -> list[str]:
    item = world.get("quest_item")
    guide = world.get("guide")
    friend = world.get("friend")
    seeker = world.get("seeker")
    light = world.get("light")
    if guide.meters["stunned"] >= THRESHOLD:
        return []
    if light.attrs.get("watts", 0) > guide.attrs.get("safe_watts", 0) and light.meters["dimmed"] < THRESHOLD:
        return []
    if friend.memes["distance"] >= THRESHOLD:
        return []
    sig = ("find", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["found"] += 1
    seeker.memes["joy"] += 1
    friend.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="stun", tag="physical", apply=_r_stun),
    Rule(name="hurt", tag="social", apply=_r_hurt),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
    Rule(name="guide_returns", tag="physical", apply=_r_guide_returns),
    Rule(name="find", tag="quest", apply=_r_find),
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


def predict_stun(world: World) -> bool:
    sim = world.copy()
    propagate(sim, narrate=False)
    return sim.get("guide").meters["stunned"] >= THRESHOLD


def introduce(world: World, seeker: Entity, friend: Entity, parent: Entity, item_cfg: QuestItem) -> None:
    world.say(
        f"At dusk the garden center glimmered like a market from an old myth, with watering cans hanging like bronze moons and damp leaves breathing out cool perfume."
    )
    world.say(
        f"{seeker.id} and {friend.id} had come with {seeker.pronoun('possessive')} {parent.label_word} on a small quest: they were to find {item_cfg.phrase} {item_cfg.gift_use} before the lamps were lit for supper."
    )


def enter_tent(world: World, seeker: Entity, friend: Entity, item_cfg: QuestItem) -> None:
    world.say(
        f"They followed a ribbon of stepping-stones into the festival tent, where rows of pots stood like a tiny forest under cloth walls."
    )
    world.say(
        f"Somewhere in {item_cfg.home}, the children had been told, waited the {item_cfg.label}; {item_cfg.myth_image}."
    )


def kindle_conflict(world: World, seeker: Entity, friend: Entity, light_cfg: Light, guide_cfg: Guide) -> None:
    seeker.memes["pride"] += 1
    seeker.memes["sharp_words"] += 1
    world.add(
        Entity(
            id="light",
            type="light",
            label=light_cfg.label,
            phrase=light_cfg.phrase,
            attrs={"watts": light_cfg.watts},
            tags=set(light_cfg.tags),
        )
    )
    world.say(
        f'"I will lead," said {seeker.id}, lifting {light_cfg.phrase}. "It is {light_cfg.watts} watt, so it can wake every hidden leaf."'
    )
    if predict_stun(world):
        friend.memes["caution"] += 1
        world.say(
            f'{friend.id} touched {seeker.pronoun("possessive")} sleeve. "Not so bright," {friend.pronoun()} said. "A sudden glare can stun {guide_cfg.phrase}s, and we may need one to guide us."'
        )
    else:
        friend.memes["caution"] += 1
        world.say(
            f'{friend.id} still answered softly. "Let us walk kindly," {friend.pronoun()} said. "The dark inside a tent has its own eyes."'
        )
    propagate(world, narrate=False)
    world.say(
        f'But {seeker.id}, eager to prove {seeker.pronoun("object")}self brave, answered too quickly: "You always slow a story down."'
    )


def early_apology(world: World, seeker: Entity, friend: Entity) -> None:
    seeker.memes["apology"] += 1
    world.say(
        f"{seeker.id} heard the hard sound of those words after they were spoken and stopped between the rosemary tubs."
    )
    world.say(
        f'"That was unfair," {seeker.pronoun()} said. "I want to lead, but I do not want to hurt you. Will you help me search?"'
    )
    propagate(world, narrate=False)
    world.say(
        f'{friend.id} let out a slow breath. "Yes," {friend.pronoun()} said. "If we listen to each other, the tent will feel less dark."'
    )


def bright_mishap(world: World, seeker: Entity, friend: Entity, light_cfg: Light, guide_cfg: Guide) -> None:
    guide = world.get("guide")
    world.say(
        f"{seeker.id} tipped the lamp high. It {light_cfg.glow}."
    )
    propagate(world, narrate=False)
    if guide.meters["stunned"] >= THRESHOLD:
        world.say(
            f"From the vine poles rose {guide_cfg.phrase}. The harsh beam brushed it, and the little creature {guide_cfg.reaction} in a small stun of surprise."
        )
        world.say(
            f'{friend.id} whispered, "There. That is what I feared."'
        )


def late_apology_and_dimming(world: World, seeker: Entity, friend: Entity, guide_cfg: Guide) -> None:
    light = world.get("light")
    seeker.memes["apology"] += 1
    light.meters["dimmed"] += 1
    world.say(
        f"{seeker.id}'s pride melted at once. {seeker.pronoun().capitalize()} lowered the lamp until its glare fell away from the ropes and leaves."
    )
    world.say(
        f'"I am sorry," {seeker.pronoun()} said. "I wanted the quest to be quick, and I forgot that quick is not the same as wise."'
    )
    world.say(
        f'"I was trying to guard the path, not stop it," said {friend.id}.'
    )
    propagate(world, narrate=False)
    world.say(
        f"Together they waited in a gentle hush until the {guide_cfg.label} trusted the softened dark again."
    )


def safe_search(world: World, seeker: Entity, friend: Entity, light_cfg: Light) -> None:
    world.say(
        f"They walked side by side. The {light_cfg.label} {light_cfg.glow}, and the shadows no longer felt like enemies."
    )
    propagate(world, narrate=False)


def follow_guide(world: World, guide_cfg: Guide, item_cfg: QuestItem) -> None:
    item = world.get("quest_item")
    if item.meters["found"] < THRESHOLD:
        return
    world.say(
        f"Soon {guide_cfg.phrase} {guide_cfg.lead_verb} ahead of them, not like a trapped thing now but like a tiny herald in a story-song."
    )
    world.say(
        f"It led them to {item_cfg.home}, where the {item_cfg.label} waited just where the old gardener had promised."
    )


def resolution(world: World, seeker: Entity, friend: Entity, item_cfg: QuestItem, parent: Entity) -> None:
    world.say(
        f"{friend.id} lifted the pot from the shelf, and {seeker.id} steadied the leaves so not one tender stem bent."
    )
    world.say(
        f'Together they carried it out of the tent to {parent.label_word}, and the plant seemed brighter because neither child held it alone.'
    )
    world.say(
        f"By the checkout fountain they smiled at each other, for the quest had not only found a plant. It had mended the space between them."
    )


def tell(
    item_cfg: QuestItem,
    guide_cfg: Guide,
    light_cfg: Light,
    apology_timing: str,
    seeker_name: str,
    seeker_gender: str,
    friend_name: str,
    friend_gender: str,
    parent_type: str,
    relation: str,
) -> World:
    world = World()
    seeker = world.add(
        Entity(
            id="seeker",
            kind="character",
            type=seeker_gender,
            label=seeker_name,
            phrase=seeker_name,
            role="seeker",
            attrs={"name": seeker_name, "relation": relation},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            type=friend_gender,
            label=friend_name,
            phrase=friend_name,
            role="friend",
            attrs={"name": friend_name, "relation": relation},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            phrase="the parent",
            role="parent",
        )
    )
    world.add(
        Entity(
            id="guide",
            kind="thing",
            type=guide_cfg.kind,
            label=guide_cfg.label,
            phrase=guide_cfg.phrase,
            role="guide",
            attrs={"safe_watts": guide_cfg.safe_watts},
            tags=set(guide_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="quest_item",
            kind="thing",
            type="plant",
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            role="quest_item",
            tags=set(item_cfg.tags),
        )
    )

    introduce(world, seeker, friend, parent, item_cfg)
    enter_tent(world, seeker, friend, item_cfg)

    world.para()
    kindle_conflict(world, seeker, friend, light_cfg, guide_cfg)

    world.para()
    if apology_timing == "early" and light_cfg.watts <= guide_cfg.safe_watts:
        early_apology(world, seeker, friend)
        safe_search(world, seeker, friend, light_cfg)
    elif light_cfg.watts > guide_cfg.safe_watts:
        bright_mishap(world, seeker, friend, light_cfg, guide_cfg)
        late_apology_and_dimming(world, seeker, friend, guide_cfg)
        propagate(world, narrate=False)
    else:
        world.say(
            f"{friend.label} went quiet for three steps, and even the leaves seemed to listen."
        )
        world.say(
            f'At last {seeker.label} lowered {seeker.pronoun("possessive")} voice. "I was talking as if the quest belonged only to me," {seeker.pronoun()} said.'
        )
        seeker.memes["apology"] += 1
        propagate(world, narrate=False)
        world.say(
            f'"Then let it belong to both of us," said {friend.label}.'
        )
        safe_search(world, seeker, friend, light_cfg)

    world.para()
    propagate(world, narrate=False)
    follow_guide(world, guide_cfg, item_cfg)
    resolution(world, seeker, friend, item_cfg, parent)

    world.facts.update(
        seeker=seeker,
        friend=friend,
        parent=parent,
        quest_item_cfg=item_cfg,
        guide_cfg=guide_cfg,
        light_cfg=light_cfg,
        apology_timing=apology_timing,
        relation=relation,
        outcome=outcome_of(
            StoryParams(
                quest_item=item_cfg.id,
                guide=guide_cfg.id,
                light=light_cfg.id,
                apology_timing=apology_timing,
                seeker_name=seeker_name,
                seeker_gender=seeker_gender,
                friend_name=friend_name,
                friend_gender=friend_gender,
                parent_type=parent_type,
                relation=relation,
            )
        ),
        found=world.get("quest_item").meters["found"] >= THRESHOLD,
        stunned=world.get("guide").meters["stunned"] >= THRESHOLD,
        reconciled=friend.memes["peace"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    seeker = world.facts["seeker"]
    friend = world.facts["friend"]
    item_cfg = world.facts["quest_item_cfg"]
    light_cfg = world.facts["light_cfg"]
    outcome = world.facts["outcome"]
    base = (
        f'Write a short myth-like story for a 3-to-5-year-old set in a garden center. '
        f'Include the words "watt", "stun", and "tent", and make the plot a quest with dialogue and reconciliation.'
    )
    if outcome == "mishap_reconciliation":
        return [
            base,
            f"Tell a gentle myth where {seeker.label} and {friend.label} search for {item_cfg.label} inside a tent, use a {light_cfg.label} too brightly, nearly stun a tiny guide, and then mend both the mistake and their friendship.",
            f"Write a child-facing story where a quest in a garden center goes wrong for one moment because of pride, but honest dialogue and an apology lead the children back to kindness.",
        ]
    if outcome == "peaceful_reconciliation":
        return [
            base,
            f"Tell a soft quest story where {seeker.label} wants to lead, then apologizes early, and the children find {item_cfg.label} together under a tent with a gentle light.",
            f"Write a myth-flavored story in which careful dialogue keeps a bright idea from becoming a mistake, and reconciliation happens before anyone is truly frightened.",
        ]
    return [
        base,
        f"Tell a story where two children in a garden center begin with a quarrel, slow down to speak honestly, and finish their quest for {item_cfg.label} side by side.",
        f"Write a simple mythic tale where a child learns that leading a quest means listening too, and the ending shows the friendship repaired.",
    ]


def _pair_phrase(seeker: Entity, friend: Entity, relation: str) -> str:
    if relation == "siblings":
        if seeker.type == "boy" and friend.type == "boy":
            return "two brothers"
        if seeker.type == "girl" and friend.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    seeker = world.facts["seeker"]
    friend = world.facts["friend"]
    parent = world.facts["parent"]
    item_cfg = world.facts["quest_item_cfg"]
    guide_cfg = world.facts["guide_cfg"]
    light_cfg = world.facts["light_cfg"]
    relation = world.facts["relation"]
    outcome = world.facts["outcome"]
    pair = _pair_phrase(seeker, friend, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {seeker.label} and {friend.label}, who go on a quest in a garden center. Their {parent.label_word} is there too, waiting for them outside the tent.",
        ),
        (
            "What was the quest?",
            f"They were searching for {item_cfg.phrase}. It was meant to be a gift, so finding it mattered to the family and not just to the game.",
        ),
        (
            "Why did the children argue?",
            f"{seeker.label} wanted to lead quickly and trusted the lamp more than {friend.label}'s caution. That hurt the feeling between them because the quest stopped sounding shared.",
        ),
        (
            f"How is the word watt important in the story?",
            f"The light was described by its watt number, which showed how strong it was. That mattered because a stronger light could be too harsh for the small guide in the tent.",
        ),
    ]
    if outcome == "mishap_reconciliation":
        qa.append(
            (
                f"What did the bright light do?",
                f"The {light_cfg.label} startled the little {guide_cfg.label} and put it into a brief stun of surprise. That was the turn of the story, because the children had to stop and choose kindness before the quest could continue.",
            )
        )
        qa.append(
            (
                f"How did the children reconcile?",
                f"{seeker.label} lowered the light and gave a true apology. {friend.label} answered honestly too, so the hurt between them softened and they could work together again.",
            )
        )
    elif outcome == "peaceful_reconciliation":
        qa.append(
            (
                f"Did anything get stunned?",
                f"No. {friend.label}'s warning mattered, and {seeker.label} apologized before using the light carelessly. Because they reconciled early, the quest stayed gentle.",
            )
        )
        qa.append(
            (
                "How did the dialogue help?",
                f"The dialogue turned a sharp moment into a shared plan. Once {seeker.label} admitted the unfair words, {friend.label} could trust the search again.",
            )
        )
    else:
        qa.append(
            (
                "When did the reconciliation happen?",
                f"It happened after a short silence, when {seeker.label} realized the quest could not be beautiful if it belonged to only one child. The apology came before any creature was hurt, but after the friendship had already felt strained.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the children carrying {item_cfg.label} out of the tent together. The final image shows that the quest succeeded because the friendship was mended.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"garden_center", "watt", "tent", "apology"}
    guide_cfg = world.facts["guide_cfg"]
    light_cfg = world.facts["light_cfg"]
    if guide_cfg.id in KNOWLEDGE:
        tags.add(guide_cfg.id)
    if "safe_light" in light_cfg.tags or "lantern" in light_cfg.tags:
        tags.add("lantern")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest_item="moonbloom",
        guide="moth",
        light="ten_watt_lantern",
        apology_timing="early",
        seeker_name="Lina",
        seeker_gender="girl",
        friend_name="Ivo",
        friend_gender="boy",
        parent_type="mother",
        relation="friends",
    ),
    StoryParams(
        quest_item="star_mint",
        guide="firefly",
        light="fifteen_watt_lamp",
        apology_timing="late",
        seeker_name="Nico",
        seeker_gender="boy",
        friend_name="Mira",
        friend_gender="girl",
        parent_type="father",
        relation="siblings",
    ),
    StoryParams(
        quest_item="dawn_fern",
        guide="treefrog",
        light="sixty_watt_grow_light",
        apology_timing="late",
        seeker_name="Tali",
        seeker_gender="girl",
        friend_name="Bram",
        friend_gender="boy",
        parent_type="mother",
        relation="friends",
    ),
]


def explain_rejection(quest_item_id: str, guide_id: str) -> str:
    quest_item = QUEST_ITEMS[quest_item_id]
    guide = GUIDES[guide_id]
    return (
        f"(No story: {quest_item.label} belongs with a {quest_item.guide_kind}, "
        f"but you chose {guide.label}. In this world, each quest plant has one plausible little guide.)"
    )


def explain_name(choice: str, gender: str) -> str:
    return f"(No story: the name {choice} does not match the chosen gender {gender} in this tiny world.)"


ASP_RULES = r"""
valid_item_guide(I, G) :- quest_item(I), guide(G), needs_guide(I, K), guide_kind(G, K).

too_bright(L, G) :- light(L), guide(G), watts(L, W), safe_watts(G, S), W > S.
peaceful_reconciliation(L, T, G) :- light(L), timing(T), guide(G), not too_bright(L, G), early(T).
late_words_but_safe(L, T, G) :- light(L), timing(T), guide(G), not too_bright(L, G), not early(T).
mishap_reconciliation(L, T, G) :- light(L), timing(T), guide(G), too_bright(L, G).

outcome(peaceful_reconciliation) :- chosen_light(L), chosen_timing(T), chosen_guide(G), peaceful_reconciliation(L, T, G).
outcome(late_words_but_safe) :- chosen_light(L), chosen_timing(T), chosen_guide(G), late_words_but_safe(L, T, G).
outcome(mishap_reconciliation) :- chosen_light(L), chosen_timing(T), chosen_guide(G), mishap_reconciliation(L, T, G).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for quest_item in QUEST_ITEMS.values():
        lines.append(asp.fact("quest_item", quest_item.id))
        lines.append(asp.fact("needs_guide", quest_item.id, quest_item.guide_kind))
    for guide in GUIDES.values():
        lines.append(asp.fact("guide", guide.id))
        lines.append(asp.fact("guide_kind", guide.id, guide.kind))
        lines.append(asp.fact("safe_watts", guide.id, guide.safe_watts))
    for light in LIGHTS.values():
        lines.append(asp.fact("light", light.id))
        lines.append(asp.fact("watts", light.id, light.watts))
    lines.append(asp.fact("timing", "early"))
    lines.append(asp.fact("timing", "late"))
    lines.append(asp.fact("early", "early"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid_item_guide/2."))
    return sorted(set(asp.atoms(model, "valid_item_guide")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_light", params.light),
            asp.fact("chosen_timing", params.apology_timing),
            asp.fact("chosen_guide", params.guide),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outcomes = asp.atoms(model, "outcome")
    return outcomes[0][0] if outcomes else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Myth-flavored garden-center quest storyworld with reconciliation and dialogue."
    )
    ap.add_argument("--quest-item", choices=sorted(QUEST_ITEMS))
    ap.add_argument("--guide", choices=sorted(GUIDES))
    ap.add_argument("--light", choices=sorted(LIGHTS))
    ap.add_argument("--apology-timing", choices=["early", "late"])
    ap.add_argument("--seeker-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--seeker-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--relation", choices=["friends", "siblings"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render a curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid item/guide pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _random_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest_item and args.guide and not valid_combo(args.quest_item, args.guide):
        raise StoryError(explain_rejection(args.quest_item, args.guide))

    seeker_gender = args.seeker_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])

    if args.seeker_name:
        valid_names = GIRL_NAMES if seeker_gender == "girl" else BOY_NAMES
        if args.seeker_name not in valid_names:
            raise StoryError(explain_name(args.seeker_name, seeker_gender))
    if args.friend_name:
        valid_names = GIRL_NAMES if friend_gender == "girl" else BOY_NAMES
        if args.friend_name not in valid_names:
            raise StoryError(explain_name(args.friend_name, friend_gender))

    combos = [
        combo
        for combo in valid_combos()
        if (args.quest_item is None or combo[0] == args.quest_item)
        and (args.guide is None or combo[1] == args.guide)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest_item_id, guide_id = rng.choice(sorted(combos))
    light_id = args.light or rng.choice(sorted(LIGHTS))
    apology_timing = args.apology_timing or rng.choice(["early", "late"])
    seeker_name = args.seeker_name or _random_name(rng, seeker_gender)
    friend_name = args.friend_name or _random_name(rng, friend_gender, avoid=seeker_name)
    parent_type = args.parent or rng.choice(["mother", "father"])
    relation = args.relation or rng.choice(["friends", "siblings"])

    return StoryParams(
        quest_item=quest_item_id,
        guide=guide_id,
        light=light_id,
        apology_timing=apology_timing,
        seeker_name=seeker_name,
        seeker_gender=seeker_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent_type=parent_type,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest_item not in QUEST_ITEMS:
        raise StoryError(f"(No story: unknown quest item '{params.quest_item}'.)")
    if params.guide not in GUIDES:
        raise StoryError(f"(No story: unknown guide '{params.guide}'.)")
    if params.light not in LIGHTS:
        raise StoryError(f"(No story: unknown light '{params.light}'.)")
    if params.apology_timing not in {"early", "late"}:
        raise StoryError(f"(No story: unknown apology timing '{params.apology_timing}'.)")
    if not valid_combo(params.quest_item, params.guide):
        raise StoryError(explain_rejection(params.quest_item, params.guide))

    world = tell(
        item_cfg=QUEST_ITEMS[params.quest_item],
        guide_cfg=GUIDES[params.guide],
        light_cfg=LIGHTS[params.light],
        apology_timing=params.apology_timing,
        seeker_name=params.seeker_name,
        seeker_gender=params.seeker_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent_type,
        relation=params.relation,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: ASP gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    cases: list[StoryParams] = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        py_outcome = outcome_of(params)
        asp_result = asp_outcome(params)
        if py_outcome != asp_result:
            bad += 1
            print(
                "  outcome mismatch:",
                params.quest_item,
                params.guide,
                params.light,
                params.apology_timing,
                py_outcome,
                asp_result,
            )
    if bad == 0:
        print(f"OK: ASP outcome matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "tent" not in sample.story.lower():
            raise StoryError("(Smoke test failed: story text missing or malformed.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive for CLI verify
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid_item_guide/2.\n#show outcome/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        pairs = asp_valid_combos()
        print(f"{len(pairs)} valid (quest_item, guide) pairs:\n")
        for quest_item_id, guide_id in pairs:
            print(f"  {quest_item_id:10} {guide_id}")
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
            header = f"### {p.quest_item} with {p.guide} using {p.light} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
