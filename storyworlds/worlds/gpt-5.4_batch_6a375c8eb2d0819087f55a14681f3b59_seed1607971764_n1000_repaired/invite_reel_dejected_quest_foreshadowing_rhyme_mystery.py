#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/invite_reel_dejected_quest_foreshadowing_rhyme_mystery.py
====================================================================================

A standalone story world for a gentle child-facing mystery: a child receives a
mysterious invite, follows a rhyming clue on a small quest, becomes dejected
when the search seems to fail, then notices a reel of thread or line that had
quietly foreshadowed the answer all along.

The world models:
- a hidden token needed to answer the invite
- a physical reel whose loose line leads toward the hiding place
- an emotional dip into dejected uncertainty
- a recovered ending where the quest makes sense in hindsight

Run it
------
    python storyworlds/worlds/gpt-5.4/invite_reel_dejected_quest_foreshadowing_rhyme_mystery.py
    python storyworlds/worlds/gpt-5.4/invite_reel_dejected_quest_foreshadowing_rhyme_mystery.py --setting attic --reel ribbon_reel --spot hatbox
    python storyworlds/worlds/gpt-5.4/invite_reel_dejected_quest_foreshadowing_rhyme_mystery.py --setting boathouse --reel ribbon_reel
    python storyworlds/worlds/gpt-5.4/invite_reel_dejected_quest_foreshadowing_rhyme_mystery.py --all
    python storyworlds/worlds/gpt-5.4/invite_reel_dejected_quest_foreshadowing_rhyme_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/invite_reel_dejected_quest_foreshadowing_rhyme_mystery.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    hush: str
    glint: str
    reel_ids: set[str] = field(default_factory=set)
    spot_ids: set[str] = field(default_factory=set)
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
class ReelDef:
    id: str
    label: str
    line_label: str
    belongs_in: set[str] = field(default_factory=set)
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
class Token:
    id: str
    label: str
    phrase: str
    purpose: str
    size: int
    ending_image: str
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
class Spot:
    id: str
    label: str
    phrase: str
    setting: str
    size: int
    area: str
    decoy: str
    rhyme_a: str
    rhyme_b: str
    reveal: str
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
class HelperDef:
    id: str
    type: str
    label: str
    comfort: str
    notices: str
    patient: bool = True
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


def _r_trail_visible(world: World) -> list[str]:
    reel = world.get("reel")
    token = world.get("token")
    if reel.meters["unwound"] < THRESHOLD or token.meters["hidden"] < THRESHOLD:
        return []
    sig = ("trail_visible",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    reel.meters["trail_visible"] += 1
    return []


def _r_dejected(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["wrong_search"] < THRESHOLD:
        return []
    sig = ("dejected",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["dejected"] += 1
    hero.memes["hope"] = max(0.0, hero.memes["hope"] - 1.0)
    return []


def _r_found(world: World) -> list[str]:
    hero = world.get("hero")
    reel = world.get("reel")
    token = world.get("token")
    if hero.meters["following_line"] < THRESHOLD or reel.meters["trail_visible"] < THRESHOLD:
        return []
    sig = ("found",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    token.meters["hidden"] = 0.0
    token.meters["found"] += 1
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    hero.memes["dejected"] = 0.0
    hero.memes["hope"] += 2.0
    return []


CAUSAL_RULES = [
    Rule(name="trail_visible", tag="physical", apply=_r_trail_visible),
    Rule(name="dejected", tag="emotional", apply=_r_dejected),
    Rule(name="found", tag="quest", apply=_r_found),
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
        for sent in produced:
            world.say(sent)
    return produced


def compatible(setting_id: str, reel_id: str, spot_id: str, token_id: str) -> bool:
    if setting_id not in SETTINGS or reel_id not in REELS or spot_id not in SPOTS or token_id not in TOKENS:
        return False
    setting = SETTINGS[setting_id]
    reel = REELS[reel_id]
    spot = SPOTS[spot_id]
    token = TOKENS[token_id]
    return (
        reel_id in setting.reel_ids
        and spot_id in setting.spot_ids
        and setting_id in reel.belongs_in
        and spot.setting == setting_id
        and token.size <= spot.size
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for reel_id in REELS:
            for spot_id in SPOTS:
                for token_id in TOKENS:
                    if compatible(setting_id, reel_id, spot_id, token_id):
                        combos.append((setting_id, reel_id, spot_id, token_id))
    return combos


def explain_rejection(setting_id: str, reel_id: str, spot_id: str, token_id: str) -> str:
    if setting_id not in SETTINGS:
        return f"(No story: unknown setting '{setting_id}'.)"
    if reel_id not in REELS:
        return f"(No story: unknown reel '{reel_id}'.)"
    if spot_id not in SPOTS:
        return f"(No story: unknown spot '{spot_id}'.)"
    if token_id not in TOKENS:
        return f"(No story: unknown token '{token_id}'.)"
    setting = SETTINGS[setting_id]
    reel = REELS[reel_id]
    spot = SPOTS[spot_id]
    token = TOKENS[token_id]
    if reel_id not in setting.reel_ids or setting_id not in reel.belongs_in:
        return (
            f"(No story: {reel.label} does not belong naturally in {setting.place}. "
            f"The mystery needs a plausible reel whose loose line could really be found there.)"
        )
    if spot_id not in setting.spot_ids or spot.setting != setting_id:
        return (
            f"(No story: {spot.phrase} is not a fitting hiding place in {setting.place}. "
            f"Choose a hiding spot that belongs in that setting.)"
        )
    if token.size > spot.size:
        return (
            f"(No story: {token.phrase} is too large to hide in {spot.phrase}. "
            f"The hidden object must physically fit the chosen spot.)"
        )
    return "(No story: this combination is not reasonable in this world.)"


def introduce(world: World, hero: Entity, helper: Entity, token: Token, setting: Setting) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"On a still evening, {hero.id} found an invite tucked under a teacup at {setting.place}. "
        f"The card was folded into a tiny moon and sealed with blue wax."
    )
    world.say(
        f'Inside, neat silver letters said, "Bring the {token.label} if you wish to come." '
        f"That was odd, because nobody could see the {token.label} anywhere."
    )
    world.say(setting.opening)
    world.say(setting.hush)
    world.facts["invite_text"] = f"Bring the {token.label} if you wish to come."


def foreshadow(world: World, reel: Entity, setting: Setting) -> None:
    reel.meters["unwound"] += 1
    world.say(
        f"Near the doorway lay {reel.label}, and {setting.glint}."
    )
    world.facts["foreshadow_detail"] = setting.glint
    propagate(world, narrate=False)


def rhyme_clue(world: World, helper: Entity, spot: Spot) -> None:
    world.say(
        f'On the back of the invite was a rhyme: "{spot.rhyme_a} / {spot.rhyme_b}."'
    )
    world.say(
        f"{helper.id} read it twice and said {helper.comfort}"
    )
    world.facts["rhyme"] = f"{spot.rhyme_a} / {spot.rhyme_b}"


def first_search(world: World, hero: Entity, spot: Spot) -> None:
    hero.meters["wrong_search"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They began the quest in {spot.area}. {hero.id} lifted {spot.decoy}, peered behind it, "
        f"and found only dust and one lonely button."
    )
    world.say(
        f"For a moment {hero.pronoun()} looked dejected. The rhyme had sounded so sure, "
        f"but the secret still felt hidden."
    )


def notice_line(world: World, helper: Entity, reel: Entity, spot: Spot) -> None:
    helper.memes["care"] += 1
    world.say(
        f"Then {helper.id} noticed {helper.attrs['notices']}."
    )
    world.say(
        f"The loose {reel.attrs['line_word']} led past the wrong place and straight toward {spot.phrase}."
    )


def follow_trail(world: World, hero: Entity, spot: Spot) -> None:
    hero.meters["following_line"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} followed it on tiptoe and stopped at {spot.phrase}. {spot.reveal}"
    )


def reveal_token(world: World, hero: Entity, token: Token, helper: Entity) -> None:
    token_ent = world.get("token")
    if token_ent.meters["found"] < THRESHOLD:
        raise StoryError("(Generation failed: the token was not found after the trail was followed.)")
    world.say(
        f"There was the {token.label} at last. {hero.id} laughed with relief, and the whole mystery "
        f"suddenly made sense."
    )
    world.say(
        f"On the underside of the little hiding place was one more note: "
        f'"Some quests look dark before they shine. You kept looking, and that was the sign."'
    )
    world.facts["found_by"] = hero.id
    world.facts["helper_name"] = helper.id


def ending(world: World, hero: Entity, helper: Entity, token: Token) -> None:
    hero.memes["joy"] += 1
    hero.memes["trust"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Together they carried the {token.label} back to the moon-folded invite. "
        f"When {hero.id} touched it to the blue wax, a second message appeared."
    )
    world.say(
        f'"Come along," it said. "Kind eyes and patient hearts may enter." '
        f"{token.ending_image}"
    )
    world.say(
        f"So the quest ended not with a fright, but with a bright little mystery solved, "
        f"and {hero.id} no longer felt dejected at all."
    )


def tell(
    setting: Setting,
    reel_cfg: ReelDef,
    spot: Spot,
    token_cfg: Token,
    helper_cfg: HelperDef,
    hero_name: str = "Nora",
    hero_type: str = "girl",
    helper_name: str = "Ben",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", traits=["curious"]))
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_cfg.type,
            role="helper",
            traits=["patient" if helper_cfg.patient else "brisk"],
            attrs={"notices": helper_cfg.notices},
        )
    )
    world.add(Entity(id="invite", type="invite", label="the invite"))
    reel = world.add(
        Entity(
            id="reel",
            type="reel",
            label=f"a {reel_cfg.label}",
            attrs={"line_word": reel_cfg.line_label},
        )
    )
    token = world.add(
        Entity(
            id="token",
            type="token",
            label=token_cfg.label,
        )
    )
    token.meters["hidden"] = 1.0
    hero.meters["wrong_search"] = 0.0
    hero.meters["following_line"] = 0.0
    hero.memes["dejected"] = 0.0
    hero.memes["hope"] = 1.0
    reel.meters["unwound"] = 0.0
    reel.meters["trail_visible"] = 0.0
    token.meters["found"] = 0.0

    world.facts.update(
        setting=setting,
        reel_cfg=reel_cfg,
        spot=spot,
        token_cfg=token_cfg,
        helper_cfg=helper_cfg,
        hero=hero,
        helper=helper,
    )

    introduce(world, hero, helper, token_cfg, setting)
    foreshadow(world, reel, setting)

    world.para()
    rhyme_clue(world, helper, spot)
    first_search(world, hero, spot)

    world.para()
    notice_line(world, helper, reel, spot)
    follow_trail(world, hero, spot)
    reveal_token(world, hero, token_cfg, helper)

    world.para()
    ending(world, hero, helper, token_cfg)

    world.facts.update(
        dejected=hero.memes["dejected"] < THRESHOLD and hero.meters["wrong_search"] >= THRESHOLD,
        found=token.meters["found"] >= THRESHOLD,
        spot_phrase=spot.phrase,
    )
    return world


SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the attic",
        opening="Dust floated in the moonbeam like tiny secrets learning to dance.",
        hush="Nothing moved except the soft creak of the roof, which made the place feel full of mystery.",
        glint="a ribbon thread had slipped across the floorboards and flashed once in the moonlight",
        reel_ids={"ribbon_reel"},
        spot_ids={"hatbox", "toy_trunk"},
    ),
    "garden": Setting(
        id="garden",
        place="the garden",
        opening="The last light made the leaves look dark on one side and silver on the other.",
        hush="The gate clicked gently in the wind, as if the garden were whispering to itself.",
        glint="a twine line ran beside the stepping stones, almost too thin to see",
        reel_ids={"twine_reel"},
        spot_ids={"watering_can", "bench_slat"},
    ),
    "boathouse": Setting(
        id="boathouse",
        place="the boathouse",
        opening="Water tapped the posts below, and every tap sounded like a tiny knock.",
        hush="Oars leaned against the wall like tall quiet listeners.",
        glint="a fishing line caught the lantern glow and winked from the planks",
        reel_ids={"fishing_reel"},
        spot_ids={"life_jacket_hook", "oar_crate"},
    ),
}

REELS = {
    "ribbon_reel": ReelDef(
        id="ribbon_reel",
        label="ribbon reel",
        line_label="ribbon",
        belongs_in={"attic"},
        tags={"reel", "ribbon"},
    ),
    "twine_reel": ReelDef(
        id="twine_reel",
        label="twine reel",
        line_label="twine",
        belongs_in={"garden"},
        tags={"reel", "twine"},
    ),
    "fishing_reel": ReelDef(
        id="fishing_reel",
        label="fishing reel",
        line_label="line",
        belongs_in={"boathouse"},
        tags={"reel", "fishing"},
    ),
}

TOKENS = {
    "moon_key": Token(
        id="moon_key",
        label="moon key",
        phrase="a tiny moon key",
        purpose="to open the moon lock on the invite",
        size=1,
        ending_image="Soon a lantern shaped like a pearl was glowing in the dark.",
        tags={"key", "mystery"},
    ),
    "star_compass": Token(
        id="star_compass",
        label="star compass",
        phrase="a little star compass",
        purpose="to point the way to the invited place",
        size=2,
        ending_image="Soon its silver needle trembled toward a path of lanterns outside.",
        tags={"compass", "mystery"},
    ),
    "shell_seal": Token(
        id="shell_seal",
        label="shell seal",
        phrase="a shell seal with a blue mark",
        purpose="to press the hidden answer from the card",
        size=1,
        ending_image="Soon the blue mark shone softly, like a wave keeping a promise.",
        tags={"seal", "mystery"},
    ),
}

SPOTS = {
    "hatbox": Spot(
        id="hatbox",
        label="hatbox",
        phrase="the round hatbox on the high shelf",
        setting="attic",
        size=1,
        area="the dusty corner by the old clothes rack",
        decoy="an empty shoe box",
        rhyme_a="Where ribbons sleep in a moon-pale ring,",
        rhyme_b="look where quiet hats remember spring.",
        reveal="Inside, under a folded paper flower, something small gave a gold glimmer.",
        tags={"rhyme", "attic"},
    ),
    "toy_trunk": Spot(
        id="toy_trunk",
        label="toy trunk",
        phrase="the toy trunk with the brass clasp",
        setting="attic",
        size=2,
        area="the dark side of the attic near the trunks",
        decoy="a stack of puzzle boards",
        rhyme_a="Seek the latch that waits for play,",
        rhyme_b="where old toy sailors hide away.",
        reveal="When the lid opened a finger-width, a tucked object gleamed between two wooden blocks.",
        tags={"rhyme", "attic"},
    ),
    "watering_can": Spot(
        id="watering_can",
        label="watering can",
        phrase="the watering can beside the marigolds",
        setting="garden",
        size=1,
        area="the path by the flower bed",
        decoy="a cracked clay pot",
        rhyme_a="Where thirsty petals lean and bow,",
        rhyme_b="the answer waits in metal now.",
        reveal="Down near the handle, behind a leaf, something tiny flashed like a drop of moonlight.",
        tags={"rhyme", "garden"},
    ),
    "bench_slat": Spot(
        id="bench_slat",
        label="bench slat",
        phrase="the loose slat under the garden bench",
        setting="garden",
        size=2,
        area="the mossy bench by the hedge",
        decoy="a basket of gloves",
        rhyme_a="Count the slats where shadows stretch,",
        rhyme_b="one keeps a secret near the hedge.",
        reveal="The slat lifted just enough to show a hidden hollow and a waiting shine inside it.",
        tags={"rhyme", "garden"},
    ),
    "life_jacket_hook": Spot(
        id="life_jacket_hook",
        label="life-jacket hook",
        phrase="the hook behind the hanging life jackets",
        setting="boathouse",
        size=1,
        area="the wall of pegs near the door",
        decoy="a coiled rope bucket",
        rhyme_a="Where bright vests sway and sailors look,",
        rhyme_b="a secret clings behind a hook.",
        reveal="Behind the last jacket, tied neatly in place, something small tapped against the wall.",
        tags={"rhyme", "boathouse"},
    ),
    "oar_crate": Spot(
        id="oar_crate",
        label="oar crate",
        phrase="the crate under the spare oars",
        setting="boathouse",
        size=2,
        area="the far corner under the oars",
        decoy="an old cork float",
        rhyme_a="Below the blades that never row,",
        rhyme_b="a waiting clue lies tucked below.",
        reveal="In the crate, under a square of sailcloth, there was a hidden shape with a silver edge.",
        tags={"rhyme", "boathouse"},
    ),
}

HELPERS = {
    "brother": HelperDef(
        id="brother",
        type="boy",
        label="brother",
        comfort='"It is a mystery," he whispered, "but mysteries want patient feet."',
        notices="the line that had seemed only part of the room a moment before",
        patient=True,
        tags={"helper"},
    ),
    "sister": HelperDef(
        id="sister",
        type="girl",
        label="sister",
        comfort='"Slow down," she said softly. "A good rhyme hides twice before it tells the truth."',
        notices="the faint thread that had been gleaming since the beginning",
        patient=True,
        tags={"helper"},
    ),
    "uncle": HelperDef(
        id="uncle",
        type="uncle",
        label="uncle",
        comfort='"Listen to the room," he murmured. "Sometimes the room answers first."',
        notices="the almost-invisible line crossing the floor the way a clue crosses a thought",
        patient=True,
        tags={"helper"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mina", "Ava", "Ruth", "Ivy", "June", "Etta"]
BOY_NAMES = ["Ben", "Theo", "Max", "Eli", "Sam", "Noah", "Finn", "Leo"]


@dataclass
class StoryParams:
    setting: str
    reel: str
    spot: str
    token: str
    helper: str
    hero_name: str
    hero_type: str
    helper_name: str
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


KNOWLEDGE = {
    "invite": [
        (
            "What is an invite?",
            "An invite is a message that asks someone to come to a place or join an event. It often tells you what to bring or when to come.",
        )
    ],
    "reel": [
        (
            "What is a reel?",
            "A reel is something that holds a long strip or line, like ribbon, twine, or fishing line. When it unwinds, the line can lead from one place to another.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme clue?",
            "A rhyme clue is a hint written with words that sound alike at the end. It can make a puzzle feel playful while still hiding the answer.",
        )
    ],
    "mystery": [
        (
            "What makes something a mystery?",
            "A mystery is something hidden or unknown that people try to figure out. You solve it by noticing clues and thinking carefully.",
        )
    ],
    "dejected": [
        (
            "What does dejected mean?",
            "Dejected means sad and droopy after something seems to go wrong. A person may feel dejected when they try hard and still cannot find the answer right away.",
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is a small early hint about something important that will matter later. It helps the ending feel surprising and fair at the same time.",
        )
    ],
}
KNOWLEDGE_ORDER = ["invite", "reel", "rhyme", "mystery", "dejected", "foreshadowing"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    token = f["token_cfg"]
    return [
        f'Write a gentle mystery for a 3-to-5-year-old that includes the words "invite", "reel", and "dejected".',
        f"Tell a rhyming clue story where {hero.id} receives a strange invite in {setting.place} and must go on a small quest to find the missing {token.label}.",
        f"Write a child-friendly mystery with foreshadowing, where an early reel clue matters later and the ending proves why the first strange detail was important.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    setting = f["setting"]
    token = f["token_cfg"]
    spot = f["spot"]
    rhyme = f["rhyme"]
    foreshadow = f["foreshadow_detail"]
    qa: list[tuple[str, str]] = [
        (
            "What started the mystery?",
            f"The mystery began when {hero.id} found an invite asking for the {token.label}, but the {token.label} was missing. That strange request turned an ordinary evening into a quest.",
        ),
        (
            "What was the rhyme clue?",
            f'The rhyme clue said, "{rhyme}." It pointed them toward {spot.area}, even though the exact hiding place was still secret.',
        ),
        (
            f"Why did {hero.id} feel dejected?",
            f"{hero.id} searched the wrong place first and found only a small useless thing instead of the hidden token. That made {hero.pronoun('object')} feel dejected because the clue had sounded right, but the answer still seemed far away.",
        ),
        (
            "What clue had been foreshadowed earlier?",
            f"Earlier they noticed that {foreshadow}. Later, that detail mattered because the loose line led straight to the real hiding place.",
        ),
        (
            f"How did {hero.id} solve the mystery?",
            f"{helper.id} noticed the line from the reel, and together they followed it to {spot.phrase}. There they found the {token.label}, which solved the invite mystery and finished the quest.",
        ),
        (
            "How did the story end?",
            f"The ending was bright and calm: the hidden object was found, the invite could be answered, and the mystery no longer felt scary. The final message showed that patience and careful looking had changed everything.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [item for key in KNOWLEDGE_ORDER for item in KNOWLEDGE[key]]


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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="attic",
        reel="ribbon_reel",
        spot="hatbox",
        token="moon_key",
        helper="sister",
        hero_name="Nora",
        hero_type="girl",
        helper_name="Lily",
    ),
    StoryParams(
        setting="garden",
        reel="twine_reel",
        spot="bench_slat",
        token="star_compass",
        helper="brother",
        hero_name="Ava",
        hero_type="girl",
        helper_name="Theo",
    ),
    StoryParams(
        setting="boathouse",
        reel="fishing_reel",
        spot="oar_crate",
        token="shell_seal",
        helper="uncle",
        hero_name="Finn",
        hero_type="boy",
        helper_name="Uncle Ray",
    ),
    StoryParams(
        setting="garden",
        reel="twine_reel",
        spot="watering_can",
        token="moon_key",
        helper="sister",
        hero_name="June",
        hero_type="girl",
        helper_name="Etta",
    ),
    StoryParams(
        setting="attic",
        reel="ribbon_reel",
        spot="toy_trunk",
        token="star_compass",
        helper="brother",
        hero_name="Max",
        hero_type="boy",
        helper_name="Ben",
    ),
]


ASP_RULES = r"""
fits(Token, Spot) :- token(Token), token_size(Token, T), spot(Spot), spot_size(Spot, S), T <= S.
compatible(Setting, Reel, Spot, Token) :-
    setting(Setting),
    reel(Reel), belongs_in(Reel, Setting),
    spot(Spot), spot_in(Spot, Setting),
    token(Token),
    reel_allowed(Setting, Reel),
    spot_allowed(Setting, Spot),
    fits(Token, Spot).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for rid in sorted(s.reel_ids):
            lines.append(asp.fact("reel_allowed", sid, rid))
        for pid in sorted(s.spot_ids):
            lines.append(asp.fact("spot_allowed", sid, pid))
    for rid, r in REELS.items():
        lines.append(asp.fact("reel", rid))
        for sid in sorted(r.belongs_in):
            lines.append(asp.fact("belongs_in", rid, sid))
    for tid, t in TOKENS.items():
        lines.append(asp.fact("token", tid))
        lines.append(asp.fact("token_size", tid, t.size))
    for pid, p in SPOTS.items():
        lines.append(asp.fact("spot", pid))
        lines.append(asp.fact("spot_in", pid, p.setting))
        lines.append(asp.fact("spot_size", pid, p.size))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatible combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        smoke_cases.append(resolve_params(build_parser().parse_args([]), random.Random(123)))
    except StoryError as err:
        rc = 1
        print(f"SMOKE PARAM ERROR: {err}")
        smoke_cases = list(CURATED)

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if "invite" not in sample.story.lower():
                raise StoryError("story missing required word 'invite'")
            if "reel" not in sample.story.lower():
                raise StoryError("story missing required word 'reel'")
            if "dejected" not in sample.story.lower():
                raise StoryError("story missing required word 'dejected'")
        except Exception as err:
            rc = 1
            print(f"SMOKE TEST FAILED on case {idx}: {err}")
            break
    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mysterious invite, a reel clue, and a small quest solved by patience."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--reel", choices=REELS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.reel and args.spot and args.token:
        if not compatible(args.setting, args.reel, args.spot, args.token):
            raise StoryError(explain_rejection(args.setting, args.reel, args.spot, args.token))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.reel is None or combo[1] == args.reel)
        and (args.spot is None or combo[2] == args.spot)
        and (args.token is None or combo[3] == args.token)
    ]
    if not combos:
        setting_id = args.setting or next(iter(SETTINGS))
        reel_id = args.reel or next(iter(REELS))
        spot_id = args.spot or next(iter(SPOTS))
        token_id = args.token or next(iter(TOKENS))
        raise StoryError(explain_rejection(setting_id, reel_id, spot_id, token_id))

    setting_id, reel_id, spot_id, token_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    helper_name = args.helper_name
    if not helper_name:
        helper_name = {
            "brother": rng.choice([n for n in BOY_NAMES if n != hero_name] or ["Ben"]),
            "sister": rng.choice([n for n in GIRL_NAMES if n != hero_name] or ["Lily"]),
            "uncle": "Uncle Ray",
        }[helper_id]
    return StoryParams(
        setting=setting_id,
        reel=reel_id,
        spot=spot_id,
        token=token_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
    )


def generate(params: StoryParams) -> StorySample:
    if not compatible(params.setting, params.reel, params.spot, params.token):
        raise StoryError(explain_rejection(params.setting, params.reel, params.spot, params.token))
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    world = tell(
        setting=SETTINGS[params.setting],
        reel_cfg=REELS[params.reel],
        spot=SPOTS[params.spot],
        token_cfg=TOKENS[params.token],
        helper_cfg=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
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
        print(asp_program("", "#show compatible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, reel, spot, token) combos:\n")
        for setting_id, reel_id, spot_id, token_id in combos:
            print(f"  {setting_id:10} {reel_id:13} {spot_id:16} {token_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.hero_name}: {p.setting}, {p.reel}, {p.spot}, {p.token}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
