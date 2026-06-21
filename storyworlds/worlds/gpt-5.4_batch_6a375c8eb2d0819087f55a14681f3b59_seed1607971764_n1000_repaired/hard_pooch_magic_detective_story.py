#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hard_pooch_magic_detective_story.py
==============================================================

A small storyworld for a child-friendly magical detective story.

Premise:
A young detective and a loyal magical pooch solve a missing-object mystery.
The object is not gone by random magic; the world tracks who moved it, what
clues that left behind, which spell can honestly reveal those clues, and where
the object can finally be found.

Run it
------
    python storyworlds/worlds/gpt-5.4/hard_pooch_magic_detective_story.py
    python storyworlds/worlds/gpt-5.4/hard_pooch_magic_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/hard_pooch_magic_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/hard_pooch_magic_detective_story.py --asp
    python storyworlds/worlds/gpt-5.4/hard_pooch_magic_detective_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "witch", "woman"}
        male = {"boy", "father", "man", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"dog", "pooch", "animal"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Cause:
    id: str
    summary: str
    location: str
    place_need: str
    item_need: set[str] = field(default_factory=set)
    reveal_need: set[str] = field(default_factory=set)
    first_guess: str = ""
    opening_clue: str = ""
    turn_text: str = ""
    resolution_text: str = ""
    innocent: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Spell:
    id: str
    name: str
    incantation: str
    reveal_text: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_missing_worry(world: World) -> list[str]:
    item = world.get("item")
    owner = world.get("owner")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry", owner.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["worry"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    item = world.get("item")
    owner = world.get("owner")
    detective = world.get("detective")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief", owner.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["relief"] += 1
    owner.memes["joy"] += 1
    owner.memes["worry"] = 0.0
    detective.memes["pride"] += 1
    return []


def _r_spell_reveals(world: World) -> list[str]:
    spell = world.facts["spell_cfg"]
    cause = world.facts["cause_cfg"]
    detective = world.get("detective")
    pooch = world.get("pooch")
    if detective.meters["spell_cast"] < THRESHOLD:
        return []
    if not (cause.reveal_need <= spell.supports):
        return []
    sig = ("spell_reveals", spell.id, cause.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["clue_revealed"] = True
    pooch.memes["focus"] += 1
    detective.memes["clarity"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="found_relief", tag="emotion", apply=_r_found_relief),
    Rule(name="spell_reveals", tag="magic", apply=_r_spell_reveals),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "market_square": Setting(
        id="market_square",
        place="the market square",
        mood="Lanterns bobbed over the stalls, and every cobble looked ready to keep a secret.",
        affords={"tree", "craft_booth", "bench"},
    ),
    "moon_fair": Setting(
        id="moon_fair",
        place="the moon fair",
        mood="Blue lamps floated in the dusk, and music drifted between the tents like a clue.",
        affords={"tree", "craft_booth", "bench"},
    ),
    "library_lane": Setting(
        id="library_lane",
        place="the lane beside the library",
        mood="The stone path was quiet, the windows were golden, and even whispers sounded important there.",
        affords={"craft_booth", "bench"},
    ),
}

ITEMS = {
    "star_badge": MissingItem(
        id="star_badge",
        label="star badge",
        phrase="a bright tin star badge",
        glow="caught every little lamp-light",
        tags={"shiny", "small", "wearable"},
    ),
    "moon_ribbon": MissingItem(
        id="moon_ribbon",
        label="moon ribbon",
        phrase="a blue moon ribbon with a torn edge",
        glow="looked soft as folded twilight",
        tags={"sewable", "soft", "wearable"},
    ),
    "bell_collar": MissingItem(
        id="bell_collar",
        label="bell collar",
        phrase="a tiny bell collar with silver bells",
        glow="made the smallest tinkling sound when it moved",
        tags={"small", "jingles", "soft", "wearable"},
    ),
}

CAUSES = {
    "magpie_nest": Cause(
        id="magpie_nest",
        summary="A magpie carried off the shiny thing for its nest.",
        location="high in a nest in the old tree",
        place_need="tree",
        item_need={"shiny"},
        reveal_need={"spark"},
        first_guess="Someone must have stolen it.",
        opening_clue="A black feather lay near the empty hook.",
        turn_text="The clue looked hard to read at first, but the magic made a thin silver path leap upward through the air.",
        resolution_text="In the crook of the tree sat a magpie's nest, and inside it the missing thing gleamed among bits of string.",
        innocent=True,
        tags={"magpie", "tree"},
    ),
    "friend_mending": Cause(
        id="friend_mending",
        summary="A friend borrowed the item to mend it before the show.",
        location="inside a sewing basket at the craft booth",
        place_need="craft_booth",
        item_need={"sewable"},
        reveal_need={"thread"},
        first_guess="Maybe a sneaky hand had whisked it away.",
        opening_clue="A curl of blue thread clung to the table edge.",
        turn_text="That clue could have meant trouble, but the spell pulled the loose thread into a glowing line that led toward the craft booth.",
        resolution_text="Inside a sewing basket rested the missing thing, neatly mended and ready to wear.",
        innocent=True,
        tags={"craft", "thread"},
    ),
    "pooch_blanket": Cause(
        id="pooch_blanket",
        summary="The little pooch dragged the thing under a bench while making a bed.",
        location="under the bench in a nest of blankets",
        place_need="bench",
        item_need={"soft"},
        reveal_need={"whiff"},
        first_guess="It seemed as if the case had no footprints at all.",
        opening_clue="One curly dog hair stuck to the floorboard.",
        turn_text="The case still felt hard, until the magic pooch sneezed and a warm golden scent-trail curled toward the bench.",
        resolution_text="Under the bench was a soft nest of blankets, and tucked in the middle was the missing thing.",
        innocent=True,
        tags={"pooch", "blanket"},
    ),
}

SPELLS = {
    "sparkle_sift": Spell(
        id="sparkle_sift",
        name="Sparkle Sift",
        incantation="Sparkles, show the path you know.",
        reveal_text="A dusting of silver sparks spun in the air and pointed the way.",
        supports={"spark"},
        tags={"magic", "spark"},
    ),
    "stitch_glow": Spell(
        id="stitch_glow",
        name="Stitch Glow",
        incantation="Little threads, politely shine.",
        reveal_text="Loose threads lifted and shone like tiny blue fireflies.",
        supports={"thread"},
        tags={"magic", "thread"},
    ),
    "sniffle_star": Spell(
        id="sniffle_star",
        name="Sniffle Star",
        incantation="Nose so bright, sniff what hid from sight.",
        reveal_text="The pooch's nose glimmered gold, and a warm trail unwound ahead of him.",
        supports={"whiff"},
        tags={"magic", "scent"},
    ),
}


GIRL_NAMES = ["Mina", "Lila", "Tessa", "Nora", "Ruby", "Eva"]
BOY_NAMES = ["Owen", "Ben", "Milo", "Finn", "Theo", "Jude"]
OWNER_NAMES = ["Pia", "June", "Ivy", "Kit", "Mara", "Toby"]
POOCH_NAMES = ["Pip", "Moss", "Buttons", "Comet"]


def valid_combo(setting_id: str, item_id: str, cause_id: str, spell_id: str) -> bool:
    if setting_id not in SETTINGS or item_id not in ITEMS or cause_id not in CAUSES or spell_id not in SPELLS:
        return False
    setting = SETTINGS[setting_id]
    item = ITEMS[item_id]
    cause = CAUSES[cause_id]
    spell = SPELLS[spell_id]
    return (
        cause.place_need in setting.affords
        and cause.item_need <= item.tags
        and cause.reveal_need <= spell.supports
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for sid in SETTINGS:
        for iid in ITEMS:
            for cid in CAUSES:
                for spid in SPELLS:
                    if valid_combo(sid, iid, cid, spid):
                        out.append((sid, iid, cid, spid))
    return out


@dataclass
class StoryParams:
    setting: str
    item: str
    cause: str
    spell: str
    detective_name: str
    detective_gender: str
    owner_name: str
    owner_gender: str
    pooch_name: str
    parent: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def introduce(world: World, detective: Entity, pooch: Entity, owner: Entity, item: Entity) -> None:
    world.say(
        f"{detective.id} was the youngest detective in {world.setting.place}, and {detective.pronoun('possessive')} best helper was a curly-eared pooch named {pooch.id}."
    )
    world.say(world.setting.mood)
    world.say(
        f"That evening, {owner.id} came hurrying over with wide eyes. {owner.pronoun().capitalize()} had lost {owner.pronoun('possessive')} {item.label}, the one that {item.attrs['glow_text']}."
    )


def missing_alarm(world: World, owner: Entity, item: Entity) -> None:
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"My {item.label} is gone," {owner.id} said. "{item.phrase.capitalize()} was here a moment ago, and now it is not."'
    )
    world.say(
        f"{owner.id}'s voice trembled because the missing thing mattered for the evening's grand parade."
    )


def inspect_scene(world: World, detective: Entity, pooch: Entity, cause: Cause) -> None:
    detective.memes["focus"] += 1
    pooch.memes["alert"] += 1
    world.say(
        f'{detective.id} knelt beside the empty hook and narrowed {detective.pronoun("possessive")} eyes. "{cause.first_guess}"'
    )
    world.say(cause.opening_clue)
    world.say(f"{pooch.id} gave one thoughtful sniff and sat very still.")


def cast_spell(world: World, detective: Entity, pooch: Entity, spell: Spell) -> None:
    detective.meters["spell_cast"] += 1
    world.say(
        f'{detective.id} tapped the cobbles with a little wand. "{spell.incantation}"'
    )
    world.say(spell.reveal_text)
    propagate(world, narrate=False)
    if world.facts.get("clue_revealed"):
        world.say(
            f"{pooch.id} trotted after the magic at once, tail up like a question mark."
        )


def follow_clue(world: World, detective: Entity, pooch: Entity, cause: Cause) -> None:
    detective.memes["determination"] += 1
    pooch.memes["confidence"] += 1
    world.say(cause.turn_text)
    world.say(
        f'{detective.id} and {pooch.id} followed the clue through {world.setting.place} until they reached {cause.location}.'
    )


def recover_item(world: World, detective: Entity, owner: Entity, item: Entity, cause: Cause) -> None:
    item.meters["missing"] = 0.0
    item.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(cause.resolution_text)
    if cause.id == "magpie_nest":
        world.say(
            f'"So nobody wicked took it," {detective.id} said softly. "A magpie only loved the shine."'
        )
    elif cause.id == "friend_mending":
        world.say(
            f'Soon a kind booth-keeper came blushing over. "I borrowed it to fix the tear before the parade," {owner.pronoun()} explained.'
        )
    else:
        world.say(
            f'{pooch.id} thumped {pooch.pronoun("possessive")} tail against the bench. He had only wanted to make the blankets extra cozy.'
        )
    world.say(
        f"{detective.id} carried the {item.label} back to {owner.id}, and {owner.pronoun()} hugged it to {owner.pronoun('possessive')} chest."
    )


def closing(world: World, detective: Entity, pooch: Entity, owner: Entity, item: Entity, cause: Cause) -> None:
    detective.memes["joy"] += 1
    pooch.memes["joy"] += 1
    world.say(
        f'"Case closed," {detective.id} said, and this time {owner.id} laughed instead of worrying.'
    )
    if cause.id == "pooch_blanket":
        world.say(
            f"{owner.id} clipped on the {item.label}, and {pooch.id} pranced beside the parade as if he had helped solve the whole mystery, which in a way he had."
        )
    else:
        world.say(
            f"When the parade music began, the {item.label} was back where it belonged, and the lamps made it shine brighter than before."
        )
    world.say(
        f"From then on, whenever a case looked hard, children in {world.setting.place} knew exactly who to call: {detective.id} and the magic pooch {pooch.id}."
    )


def tell(
    setting: Setting,
    item_cfg: MissingItem,
    cause_cfg: Cause,
    spell_cfg: Spell,
    detective_name: str,
    detective_gender: str,
    owner_name: str,
    owner_gender: str,
    pooch_name: str,
    parent_type: str,
) -> World:
    world = World(setting)
    detective = world.add(
        Entity(
            id=detective_name,
            kind="character",
            type=detective_gender,
            label="the detective",
            role="detective",
            traits=["careful", "observant"],
        )
    )
    pooch = world.add(
        Entity(
            id=pooch_name,
            kind="character",
            type="pooch",
            label="the pooch",
            role="helper",
            traits=["loyal", "magical"],
        )
    )
    owner = world.add(
        Entity(
            id=owner_name,
            kind="character",
            type=owner_gender,
            label="the owner",
            role="owner",
            traits=["hopeful"],
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="adult",
        )
    )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="item",
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            attrs={"glow_text": item_cfg.glow},
        )
    )

    world.facts["setting_cfg"] = setting
    world.facts["item_cfg"] = item_cfg
    world.facts["cause_cfg"] = cause_cfg
    world.facts["spell_cfg"] = spell_cfg
    world.facts["clue_revealed"] = False

    introduce(world, detective, pooch, owner, item)
    world.para()
    missing_alarm(world, owner, item)
    inspect_scene(world, detective, pooch, cause_cfg)
    world.para()
    cast_spell(world, detective, pooch, spell_cfg)
    follow_clue(world, detective, pooch, cause_cfg)
    world.para()
    recover_item(world, detective, owner, item, cause_cfg)
    closing(world, detective, pooch, owner, item, cause_cfg)

    world.facts.update(
        detective=detective,
        pooch=pooch,
        owner=owner,
        parent=parent,
        item=item,
        found_location=cause_cfg.location,
        outcome=outcome_of(
            StoryParams(
                setting=setting.id,
                item=item_cfg.id,
                cause=cause_cfg.id,
                spell=spell_cfg.id,
                detective_name=detective_name,
                detective_gender=detective_gender,
                owner_name=owner_name,
                owner_gender=owner_gender,
                pooch_name=pooch_name,
                parent=parent_type,
                seed=None,
            )
        ),
        clue_revealed=bool(world.facts.get("clue_revealed")),
    )
    return world


KNOWLEDGE = {
    "magic": [
        (
            "What is magic in a story like this?",
            "Magic in a story is a special power that can do unusual things, like make clues glow or help someone find a hidden object. It is make-believe, but it can help tell a mystery in a fun way.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues, asks careful questions, and figures out what really happened. Good detectives do not just guess; they check the facts.",
        )
    ],
    "pooch": [
        (
            "What is a pooch?",
            "A pooch is another word for a dog. It is a friendly, playful word people use when talking about a dog they like.",
        )
    ],
    "magpie": [
        (
            "Why might a magpie take something shiny?",
            "Magpies are birds that notice bright, sparkling things. In stories, they are often shown carrying shiny bits away because the shine catches their eye.",
        )
    ],
    "thread": [
        (
            "What does thread do?",
            "Thread is a thin string used for sewing. It helps hold cloth together when something needs to be stitched or mended.",
        )
    ],
    "scent": [
        (
            "How can a dog help find something?",
            "Dogs can follow smells much better than people can. A dog that knows the scent can lead someone toward where an object or person has been.",
        )
    ],
}

KNOWLEDGE_ORDER = ["magic", "detective", "pooch", "magpie", "thread", "scent"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item_cfg = f["item_cfg"]
    setting_cfg = f["setting_cfg"]
    cause_cfg = f["cause_cfg"]
    detective = f["detective"]
    pooch = f["pooch"]
    return [
        f'Write a magical detective story for a 3-to-5-year-old that includes the words "hard" and "pooch".',
        f"Tell a gentle mystery set in {setting_cfg.place} where {detective.id} and a pooch named {pooch.id} solve the case of a missing {item_cfg.label}.",
        f"Write a child-friendly detective story where the case seems hard at first, but a magic clue leads to the truth: {cause_cfg.summary}",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    pooch = f["pooch"]
    owner = f["owner"]
    item = f["item"]
    cause_cfg = f["cause_cfg"]
    spell_cfg = f["spell_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who solved the mystery?",
            f"{detective.id} solved the mystery with help from the magical pooch {pooch.id}. {pooch.id} helped follow the clue instead of just barking and guessing.",
        ),
        (
            f"What was missing?",
            f"The missing thing was {owner.id}'s {item.label}. It mattered because {owner.pronoun()} needed it for the evening parade.",
        ),
        (
            "Why did the case seem hard at first?",
            f"The object was simply gone, and the first clue did not explain the whole truth. {detective.id} had to slow down, look carefully, and use magic before the case made sense.",
        ),
        (
            f"How did the magic help?",
            f"{detective.id} used the spell {spell_cfg.name}, and the magic revealed a clue that could be followed. That changed the case from a worried guess into a real trail.",
        ),
        (
            "Where was the missing thing found?",
            f"It was found {f['found_location']}. The clue led them there step by step, which is why they could solve the mystery honestly.",
        ),
    ]
    if cause_cfg.id == "magpie_nest":
        qa.append(
            (
                "Did someone mean to be unkind?",
                f"No. A magpie had carried the shiny thing away because it liked the sparkle, so the loss was not a cruel trick. The detective learned what really happened before blaming anyone.",
            )
        )
    elif cause_cfg.id == "friend_mending":
        qa.append(
            (
                "Why had the item been moved?",
                f"It had been borrowed so its torn part could be mended before the parade. What looked suspicious at first turned out to be a helpful act.",
            )
        )
    else:
        qa.append(
            (
                f"Why was the item under the bench?",
                f"The pooch had dragged it into a nest of blankets while making himself cozy. He was not trying to hide it forever; he simply mixed play with detective work.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    cause_cfg = world.facts["cause_cfg"]
    spell_cfg = world.facts["spell_cfg"]
    tags = {"magic", "detective", "pooch"}
    if "magpie" in cause_cfg.tags:
        tags.add("magpie")
    if "thread" in cause_cfg.tags or "thread" in spell_cfg.tags:
        tags.add("thread")
    if "blanket" in cause_cfg.tags or "scent" in spell_cfg.tags:
        tags.add("scent")
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: clue_revealed={world.facts.get('clue_revealed')} location={world.facts.get('found_location')}")
    return "\n".join(lines)


def explain_rejection(setting_id: str, item_id: str, cause_id: str, spell_id: str) -> str:
    parts: list[str] = []
    if setting_id in SETTINGS and cause_id in CAUSES:
        setting = SETTINGS[setting_id]
        cause = CAUSES[cause_id]
        if cause.place_need not in setting.affords:
            parts.append(
                f"{setting.place} has no {cause.place_need.replace('_', ' ')}, so this case would have nowhere honest for that clue to lead"
            )
    if item_id in ITEMS and cause_id in CAUSES:
        item = ITEMS[item_id]
        cause = CAUSES[cause_id]
        if not (cause.item_need <= item.tags):
            need = ", ".join(sorted(cause.item_need))
            parts.append(
                f"the {item.label} is missing the needed property ({need}) for that event"
            )
    if spell_id in SPELLS and cause_id in CAUSES:
        spell = SPELLS[spell_id]
        cause = CAUSES[cause_id]
        if not (cause.reveal_need <= spell.supports):
            need = ", ".join(sorted(cause.reveal_need))
            parts.append(
                f"{spell.name} cannot reveal the right kind of clue ({need})"
            )
    if not parts:
        return "(No valid combination matches the given options.)"
    return "(No story: " + "; ".join(parts) + ".)"


def outcome_of(params: StoryParams) -> str:
    if params.cause == "magpie_nest":
        return "nest"
    if params.cause == "friend_mending":
        return "basket"
    if params.cause == "pooch_blanket":
        return "bench"
    return "unknown"


ASP_RULES = r"""
valid(S,I,C,Sp) :- setting(S), item(I), cause(C), spell(Sp),
                   needs_place(C,P), affords(S,P),
                   needs_item(C,T), has_tag(I,T),
                   needs_reveal(C,R), supports(Sp,R).

all_item_needs_met(I,C) :- cause(C), item(I), not unmet_item_need(I,C).
unmet_item_need(I,C)    :- needs_item(C,T), not has_tag(I,T).

all_reveal_needs_met(Sp,C) :- cause(C), spell(Sp), not unmet_reveal_need(Sp,C).
unmet_reveal_need(Sp,C)    :- needs_reveal(C,R), not supports(Sp,R).

valid2(S,I,C,Sp) :- setting(S), item(I), cause(C), spell(Sp),
                    needs_place(C,P), affords(S,P),
                    all_item_needs_met(I,C),
                    all_reveal_needs_met(Sp,C).

outcome(bench)  :- chosen_cause(pooch_blanket).
outcome(basket) :- chosen_cause(friend_mending).
outcome(nest)   :- chosen_cause(magpie_nest).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for afford in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, afford))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for tag in sorted(item.tags):
            lines.append(asp.fact("has_tag", iid, tag))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("needs_place", cid, cause.place_need))
        for tag in sorted(cause.item_need):
            lines.append(asp.fact("needs_item", cid, tag))
        for tag in sorted(cause.reveal_need):
            lines.append(asp.fact("needs_reveal", cid, tag))
    for spid, spell in SPELLS.items():
        lines.append(asp.fact("spell", spid))
        for sup in sorted(spell.supports):
            lines.append(asp.fact("supports", spid, sup))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid2/4."))
    return sorted(set(asp.atoms(model, "valid2")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_cause", params.cause)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "unknown"


CURATED = [
    StoryParams(
        setting="moon_fair",
        item="star_badge",
        cause="magpie_nest",
        spell="sparkle_sift",
        detective_name="Mina",
        detective_gender="girl",
        owner_name="Pia",
        owner_gender="girl",
        pooch_name="Pip",
        parent="mother",
        seed=None,
    ),
    StoryParams(
        setting="market_square",
        item="moon_ribbon",
        cause="friend_mending",
        spell="stitch_glow",
        detective_name="Owen",
        detective_gender="boy",
        owner_name="June",
        owner_gender="girl",
        pooch_name="Buttons",
        parent="father",
        seed=None,
    ),
    StoryParams(
        setting="library_lane",
        item="bell_collar",
        cause="pooch_blanket",
        spell="sniffle_star",
        detective_name="Ruby",
        detective_gender="girl",
        owner_name="Kit",
        owner_gender="boy",
        pooch_name="Moss",
        parent="mother",
        seed=None,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a magical child detective and a pooch solve a missing-object case."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--detective-name")
    ap.add_argument("--owner-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--owner-gender", choices=["girl", "boy"])
    ap.add_argument("--pooch-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render curated stories instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations via clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.item and args.cause and args.spell:
        if not valid_combo(args.setting, args.item, args.cause, args.spell):
            raise StoryError(explain_rejection(args.setting, args.item, args.cause, args.spell))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.item is None or c[1] == args.item)
        and (args.cause is None or c[2] == args.cause)
        and (args.spell is None or c[3] == args.spell)
    ]
    if not combos:
        sid = args.setting or next(iter(SETTINGS))
        iid = args.item or next(iter(ITEMS))
        cid = args.cause or next(iter(CAUSES))
        spid = args.spell or next(iter(SPELLS))
        raise StoryError(explain_rejection(sid, iid, cid, spid))

    setting_id, item_id, cause_id, spell_id = rng.choice(sorted(combos))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    owner_gender = args.owner_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    owner_pool = [n for n in OWNER_NAMES if n != detective_name]
    owner_name = args.owner_name or rng.choice(owner_pool)
    pooch_name = args.pooch_name or rng.choice(POOCH_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        item=item_id,
        cause=cause_id,
        spell=spell_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        owner_name=owner_name,
        owner_gender=owner_gender,
        pooch_name=pooch_name,
        parent=parent,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.setting, params.item, params.cause, params.spell):
        raise StoryError(explain_rejection(params.setting, params.item, params.cause, params.spell))
    try:
        setting = SETTINGS[params.setting]
        item_cfg = ITEMS[params.item]
        cause_cfg = CAUSES[params.cause]
        spell_cfg = SPELLS[params.spell]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]}.)") from err

    world = tell(
        setting=setting,
        item_cfg=item_cfg,
        cause_cfg=cause_cfg,
        spell_cfg=spell_cfg,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        pooch_name=params.pooch_name,
        parent_type=params.parent,
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid combos match ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during random resolve for seed {s}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=False, qa=False, header="smoke")
        finally:
            sys.stdout = old
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid2/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, cause, spell) combos:\n")
        for setting_id, item_id, cause_id, spell_id in combos:
            print(f"  {setting_id:13} {item_id:12} {cause_id:14} {spell_id}")
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
            header = f"### {p.detective_name} and {p.pooch_name}: {p.item} at {p.setting} ({p.cause})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
