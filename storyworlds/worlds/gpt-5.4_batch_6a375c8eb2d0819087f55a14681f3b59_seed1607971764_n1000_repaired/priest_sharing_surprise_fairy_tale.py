#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/priest_sharing_surprise_fairy_tale.py
================================================================

A standalone story world for a fairy-tale domain about a child, a traveling
basket, a priest in need, an act of sharing, and a gentle surprise that proves
kindness was not lost.

The world models a few concrete things:

- a child carries one small gift through a storybook village
- a priest is met at a place touched by local wonder
- the priest has a simple need: hunger, cold, or darkness
- only a suitable gift can honestly help with that need
- once the child shares, the relieved priest blesses the place
- the place answers with a fitting surprise

Run it
------
    python storyworlds/worlds/gpt-5.4/priest_sharing_surprise_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/priest_sharing_surprise_fairy_tale.py --place chapel_garden --need hungry --gift loaf
    python storyworlds/worlds/gpt-5.4/priest_sharing_surprise_fairy_tale.py --need cold --gift loaf
    python storyworlds/worlds/gpt-5.4/priest_sharing_surprise_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/priest_sharing_surprise_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/priest_sharing_surprise_fairy_tale.py --trace
    python storyworlds/worlds/gpt-5.4/priest_sharing_surprise_fairy_tale.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "priest": "priest"}.get(self.type, self.type)
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
class Place:
    id: str
    label: str
    opening: str
    priest_spot: str
    wonder_start: str
    surprise_text: str
    ending_image: str
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
class Need:
    id: str
    label: str
    hint: str
    ask: str
    relief_text: str
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
class Gift:
    id: str
    label: str
    phrase: str
    article: str
    solves: set[str]
    share_text: str
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


def _r_share_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    priest = world.get("priest")
    gift = world.get("gift")
    need = world.facts["need_cfg"]
    if hero.meters["shared"] < THRESHOLD:
        return out
    if need.id not in gift.attrs.get("solves", set()):
        return out
    sig = ("relief", need.id, gift.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    priest.meters["need"] = 0.0
    priest.meters["comfort"] += 1
    priest.memes["gratitude"] += 1
    hero.memes["kindness"] += 1
    out.append("__relief__")
    return out


def _r_blessing(world: World) -> list[str]:
    out: list[str] = []
    priest = world.get("priest")
    place = world.get("place")
    if priest.memes["gratitude"] < THRESHOLD:
        return out
    sig = ("blessing", place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    place.meters["blessed"] += 1
    priest.memes["wonder"] += 1
    out.append("__blessing__")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    place = world.get("place")
    hero = world.get("hero")
    if place.meters["blessed"] < THRESHOLD:
        return out
    sig = ("surprise", place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    place.meters["surprise"] += 1
    hero.memes["wonder"] += 1
    hero.memes["joy"] += 1
    out.append("__surprise__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="share_relief", tag="physical", apply=_r_share_relief),
    Rule(name="blessing", tag="social", apply=_r_blessing),
    Rule(name="surprise", tag="wonder", apply=_r_surprise),
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
    return produced


def gift_fits_need(gift: Gift, need: Need) -> bool:
    return need.id in gift.solves


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for need_id, need in NEEDS.items():
            for gift_id, gift in GIFTS.items():
                if gift_fits_need(gift, need):
                    combos.append((place_id, need_id, gift_id))
    return combos


def predict_relief(world: World, gift_id: str) -> dict:
    sim = world.copy()
    sim.get("gift").attrs["solves"] = set(GIFTS[gift_id].solves)
    sim.get("hero").meters["shared"] += 1
    propagate(sim, narrate=False)
    priest = sim.get("priest")
    place = sim.get("place")
    return {
        "relieved": priest.meters["need"] < THRESHOLD,
        "surprise": place.meters["surprise"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, place: Place, gift: Gift, elder: Entity) -> None:
    world.say(
        f"In a village of cobbled lanes and low blue hills, {hero.id} walked toward "
        f"{place.label} with {gift.article} in a basket for {elder.label}."
    )
    world.say(place.opening)
    hero.memes["duty"] += 1
    hero.memes["love"] += 1


def meet_priest(world: World, priest: Entity, place: Place, need: Need) -> None:
    priest.meters["need"] = 1.0
    priest.attrs["need"] = need.id
    world.say(
        f"By {place.priest_spot} sat a weary priest. {need.hint}"
    )


def worry(world: World, hero: Entity, gift: Gift, elder: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} held the basket with both hands. The {gift.label} was meant for "
        f"{elder.label}, and there was not much to spare."
    )


def ask(world: World, priest: Entity, need: Need) -> None:
    priest.memes["humility"] += 1
    world.say(
        f'The priest looked up kindly and said, "{need.ask}"'
    )


def choose_share(world: World, hero: Entity, priest: Entity, gift: Gift, need: Need) -> None:
    pred = predict_relief(world, gift.id)
    world.facts["predicted_relief"] = pred["relieved"]
    world.facts["predicted_surprise"] = pred["surprise"]
    hero.memes["mercy"] += 1
    hero.meters["shared"] += 1
    world.say(
        f"{hero.id} thought of home, then of the tired priest, and chose kindness. "
        f"{gift.share_text}"
    )
    propagate(world, narrate=False)
    if world.get("priest").meters["need"] < THRESHOLD:
        world.say(need.relief_text)


def bless(world: World, priest: Entity, place: Place) -> None:
    if world.get("place").meters["blessed"] >= THRESHOLD:
        world.say(
            f'The priest laid two fingers on the basket rim and whispered a blessing. '
            f"{place.wonder_start}"
        )


def reveal_surprise(world: World, place: Place, hero: Entity) -> None:
    if world.get("place").meters["surprise"] >= THRESHOLD:
        world.say(place.surprise_text)
        world.say(
            f"{hero.id} stood still with wide eyes, and even the evening seemed to listen."
        )


def ending(world: World, hero: Entity, elder: Entity, place: Place, gift: Gift) -> None:
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"When {hero.id} reached {elder.label}, the basket was no longer poorer for having shared. "
        f"{place.ending_image}"
    )
    world.say(
        f"From that day on, {hero.id} remembered that a kind hand may look smaller for a moment, "
        f"yet in a fairy-tale world it often comes home full."
    )


def tell(
    *,
    place: Place,
    need: Need,
    gift: Gift,
    hero_name: str = "Mira",
    hero_type: str = "girl",
    elder_type: str = "grandmother",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    priest = world.add(Entity(id="priest", kind="character", type="priest", label="the old priest", role="priest"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=f"{hero_name}'s {elder_type}", role="elder"))
    gift_ent = world.add(Entity(id="gift", type="gift", label=gift.label, attrs={"solves": set(gift.solves)}))
    place_ent = world.add(Entity(id="place", type="place", label=place.label))
    world.facts["place_cfg"] = place
    world.facts["need_cfg"] = need
    world.facts["gift_cfg"] = gift
    world.facts["hero_name"] = hero_name
    world.facts["hero_type"] = hero_type
    world.facts["elder_type"] = elder_type

    introduce(world, hero, place, gift, elder)
    world.para()
    meet_priest(world, priest, place, need)
    worry(world, hero, gift, elder)
    ask(world, priest, need)
    world.para()
    choose_share(world, hero, priest, gift, need)
    bless(world, priest, place)
    reveal_surprise(world, place, hero)
    world.para()
    ending(world, hero, elder, place, gift)

    world.facts.update(
        hero=hero,
        priest=priest,
        elder=elder,
        gift=gift_ent,
        place=place_ent,
        relieved=priest.meters["need"] < THRESHOLD,
        shared=hero.meters["shared"] >= THRESHOLD,
        surprised=place_ent.meters["surprise"] >= THRESHOLD,
    )
    return world


PLACES = {
    "chapel_garden": Place(
        id="chapel_garden",
        label="the chapel garden",
        opening="The chapel garden lay behind a white wall, and the pear tree there was bare as winter bone.",
        priest_spot="the mossy gate",
        wonder_start="At once the bare pear tree trembled as if a warm spring had passed through it.",
        surprise_text="Green buds burst open, white blossoms flashed, and three golden pears dropped softly into the basket.",
        ending_image="Three golden pears shone among the cloth, and the house smelled sweet long before the door was opened.",
        tags={"garden", "pear_tree", "fruit"},
    ),
    "stone_bridge": Place(
        id="stone_bridge",
        label="the stone bridge",
        opening="Beyond the mill stood the stone bridge, and the river below it was turning silver in the dusk.",
        priest_spot="the bridge rail",
        wonder_start="The water below the bridge brightened in thin silver lines.",
        surprise_text="Little lantern-fish rose from the river, each carrying a bead of light, and they swam beside the path like a floating string of stars.",
        ending_image="The path home stayed bright as candle-song, and one pearl-like bead of light slept in the basket until morning.",
        tags={"bridge", "river", "lantern"},
    ),
    "bell_tower": Place(
        id="bell_tower",
        label="the bell tower",
        opening="The bell tower watched over the village roofs, and evening had already gathered in its high stone corners.",
        priest_spot="the tower steps",
        wonder_start="Without a hand upon the rope, the old bell gave one clear, gentle note.",
        surprise_text="From the dark eaves flew white doves with ribbons of lamplight in their beaks, circling once before trailing brightness all the way down the lane.",
        ending_image="The lane to home gleamed softly behind those dove-lights, as if the night itself had learned to be gentle.",
        tags={"tower", "bell", "doves", "light"},
    ),
}

NEEDS = {
    "hungry": Need(
        id="hungry",
        label="hungry",
        hint="His shoulders drooped, and now and then his hand rested over his empty stomach.",
        ask="Child, have you a little bite to share? I have walked a long road with no supper.",
        relief_text="The priest ate slowly, and warm color returned to his face.",
        tags={"hunger", "food"},
    ),
    "cold": Need(
        id="cold",
        label="cold",
        hint="His hands trembled inside his sleeves, and the evening wind worried at his thin coat.",
        ask="Child, have you something warm to share? The night air has found every seam in my coat.",
        relief_text="The priest drew in a long breath, and the shaking left his hands.",
        tags={"cold", "warmth"},
    ),
    "dark": Need(
        id="dark",
        label="dark",
        hint="Twilight had thickened around him, and he kept peering at the path as if the stones had melted into shadow.",
        ask="Child, have you a little light to share? The path and my old eyes are quarreling with the dusk.",
        relief_text="The priest smiled as the darkness pulled back from his feet.",
        tags={"dark", "light"},
    ),
}

GIFTS = {
    "loaf": Gift(
        id="loaf",
        label="honey loaf",
        phrase="a honey loaf",
        article="a honey loaf wrapped in cloth",
        solves={"hungry"},
        share_text="She broke the honey loaf in two and placed the sweeter half in the priest's hands.",
        tags={"bread", "food"},
    ),
    "broth": Gift(
        id="broth",
        label="pot of broth",
        phrase="a pot of broth",
        article="a little pot of rosemary broth",
        solves={"hungry", "cold"},
        share_text="She lifted the lid from the broth, and the steam curled upward while she offered the priest the first warm sips.",
        tags={"broth", "food", "warmth"},
    ),
    "shawl": Gift(
        id="shawl",
        label="red shawl",
        phrase="a red shawl",
        article="a red shawl folded over the basket",
        solves={"cold"},
        share_text="She unfolded the red shawl and settled it around the priest's shoulders, tucking the corners against the wind.",
        tags={"shawl", "warmth"},
    ),
    "lantern": Gift(
        id="lantern",
        label="blue lantern",
        phrase="a blue lantern",
        article="a blue lantern with a steady wickless glow",
        solves={"dark"},
        share_text="She set the blue lantern beside the priest, and its calm light laid a bright ribbon over the stones.",
        tags={"lantern", "light"},
    ),
}

GIRL_NAMES = ["Mira", "Elsie", "Nora", "Lina", "Tessa", "Ivy", "Rosa", "Clara"]
BOY_NAMES = ["Rowan", "Tobin", "Eli", "Pavel", "Finn", "Leo", "Milo", "Jon"]
TRAITS = ["gentle", "brave", "thoughtful", "quiet", "cheerful", "careful"]


@dataclass
class StoryParams:
    place: str
    need: str
    gift: str
    hero_name: str
    hero_type: str
    elder_type: str
    trait: str
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
    "hunger": [(
        "Why does a hungry person feel weak?",
        "A hungry person has not had enough food, so the body has less energy to work and stay warm. That is why a meal can help someone feel steady again."
    )],
    "cold": [(
        "Why does a shawl help when someone is cold?",
        "A shawl holds warm air close to the body and blocks some of the wind. That helps a chilly person keep their heat."
    )],
    "light": [(
        "Why is a light useful at dusk?",
        "A light helps people see the path when the day grows dim. It can keep someone from stumbling or getting lost."
    )],
    "bread": [(
        "What is a loaf of bread?",
        "A loaf is bread baked in one whole shape that can be sliced or broken into pieces. Sharing bread is an old way of showing welcome."
    )],
    "broth": [(
        "What is broth?",
        "Broth is warm soup made from water and food flavors, often with herbs or vegetables. It is gentle to sip and can warm a person from the inside."
    )],
    "shawl": [(
        "What is a shawl?",
        "A shawl is a soft piece of cloth worn around the shoulders for warmth. People wrap it around themselves when the air is cold."
    )],
    "lantern": [(
        "What is a lantern?",
        "A lantern is a lamp with a handle or cover so it can be carried from place to place. It helps people travel when it is dark."
    )],
    "priest": [(
        "What is a priest?",
        "A priest is a religious leader who prays, teaches, and cares for people in a community. In many stories, a priest also gives comfort and blessing."
    )],
    "sharing": [(
        "What does sharing mean?",
        "Sharing means giving part of what you have so someone else can use it too. It is one way to show kindness and care."
    )],
    "surprise": [(
        "What is a surprise in a story?",
        "A surprise is something unexpected that happens after the story has already begun. It often shows that a character's choice changed what came next."
    )],
}
KNOWLEDGE_ORDER = ["priest", "sharing", "surprise", "hunger", "cold", "light", "bread", "broth", "shawl", "lantern"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero_name = f["hero_name"]
    hero_type = f["hero_type"]
    place = f["place_cfg"]
    need = f["need_cfg"]
    gift = f["gift_cfg"]
    return [
        f'Write a fairy tale for a 3-to-5-year-old that includes the word "priest" and turns on sharing and surprise.',
        f"Tell a gentle fairy tale where a {hero_type} named {hero_name} meets a priest at {place.label}, shares {gift.phrase}, and receives a magical surprise.",
        f"Write a small village fairy tale in which a child notices a priest who is {need.label}, gives up part of a precious gift, and discovers that kindness can come home fuller than it left.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    priest = f["priest"]
    elder = f["elder"]
    place = f["place_cfg"]
    need = f["need_cfg"]
    gift = f["gift_cfg"]
    hero_name = f["hero_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a child carrying {gift.phrase}, and a weary priest met at {place.label}. The story follows what happened after {hero_name} chose to share."
        ),
        (
            f"Why did {hero_name} worry before sharing?",
            f"{hero_name} worried because the {gift.label} was meant for {elder.label}, and there was not much to spare. That made the choice feel costly before it became kind."
        ),
        (
            f"How did {hero_name} help the priest?",
            f"{hero.pronoun('subject').capitalize()} shared the {gift.label} with the priest when he was {need.label}. That gift matched what the priest needed, so it truly helped instead of only sounding nice."
        ),
    ]
    if f.get("relieved"):
        qa.append((
            "What changed after the child shared?",
            f"The priest was no longer {need.label}, and his relief turned into gratitude. Because the child's kindness met a real need, the priest blessed the place and a surprise followed."
        ))
    if f.get("surprised"):
        qa.append((
            "What was the surprise?",
            f"{place.surprise_text} It came only after the act of sharing, so the wonder felt like an answer to kindness."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with {hero_name} reaching home no poorer for having shared. The last image shows that kindness changed the road itself, not just the child's feelings."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    need = world.facts["need_cfg"]
    gift = world.facts["gift_cfg"]
    tags = {"priest", "sharing", "surprise"} | set(need.tags) | set(gift.tags)
    mapped = {
        "food": "bread",
        "bread": "bread",
        "broth": "broth",
        "warmth": "cold",
        "shawl": "shawl",
        "light": "light",
        "lantern": "lantern",
        "hunger": "hunger",
        "cold": "cold",
        "dark": "light",
    }
    keys: set[str] = set()
    for tag in tags:
        if tag in KNOWLEDGE:
            keys.add(tag)
        elif tag in mapped:
            keys.add(mapped[tag])
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in keys:
            out.extend(KNOWLEDGE[key])
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
        attrs = {}
        for k, v in e.attrs.items():
            if isinstance(v, set):
                if v:
                    attrs[k] = sorted(v)
            elif v:
                attrs[k] = v
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="chapel_garden",
        need="hungry",
        gift="loaf",
        hero_name="Mira",
        hero_type="girl",
        elder_type="grandmother",
        trait="gentle",
    ),
    StoryParams(
        place="stone_bridge",
        need="dark",
        gift="lantern",
        hero_name="Rowan",
        hero_type="boy",
        elder_type="grandmother",
        trait="brave",
    ),
    StoryParams(
        place="bell_tower",
        need="cold",
        gift="shawl",
        hero_name="Clara",
        hero_type="girl",
        elder_type="aunt",
        trait="thoughtful",
    ),
    StoryParams(
        place="chapel_garden",
        need="cold",
        gift="broth",
        hero_name="Eli",
        hero_type="boy",
        elder_type="grandfather",
        trait="careful",
    ),
    StoryParams(
        place="stone_bridge",
        need="hungry",
        gift="broth",
        hero_name="Nora",
        hero_type="girl",
        elder_type="mother",
        trait="quiet",
    ),
]


def explain_rejection(need: Need, gift: Gift) -> str:
    return (
        f"(No story: {gift.phrase} does not reasonably solve being {need.label}. "
        f"In this world, a gift must truly help the priest's need before a blessing "
        f"and surprise can follow.)"
    )


ASP_RULES = r"""
solves_need(G, N) :- gift_solves(G, N).
valid(P, N, G) :- place(P), need(N), gift(G), solves_need(G, N).

shared_relief :- chosen_need(N), chosen_gift(G), solves_need(G, N).
blessed :- shared_relief.
surprised :- blessed.

outcome(surprised) :- surprised.
outcome(failed) :- not surprised.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for need_id in NEEDS:
        lines.append(asp.fact("need", need_id))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        for need_id in sorted(gift.solves):
            lines.append(asp.fact("gift_solves", gift_id, need_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_need", params.need),
        asp.fact("chosen_gift", params.gift),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "failed"


def outcome_of(params: StoryParams) -> str:
    return "surprised" if gift_fits_need(GIFTS[params.gift], NEEDS[params.need]) else "failed"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story during smoke test")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generated and emitted.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a child shares with a priest, and a surprise answers kindness."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father", "grandmother", "grandfather", "aunt"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.need and args.gift:
        need = NEEDS[args.need]
        gift = GIFTS[args.gift]
        if not gift_fits_need(gift, need):
            raise StoryError(explain_rejection(need, gift))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.need is None or combo[1] == args.need)
        and (args.gift is None or combo[2] == args.gift)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, need_id, gift_id = rng.choice(sorted(combos))
    hero_type = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    elder_type = args.elder or rng.choice(["mother", "father", "grandmother", "grandfather", "aunt"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        need=need_id,
        gift=gift_id,
        hero_name=hero_name,
        hero_type=hero_type,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.need not in NEEDS:
        raise StoryError(f"(Unknown need: {params.need})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    if not gift_fits_need(GIFTS[params.gift], NEEDS[params.need]):
        raise StoryError(explain_rejection(NEEDS[params.need], GIFTS[params.gift]))

    world = tell(
        place=PLACES[params.place],
        need=NEEDS[params.need],
        gift=GIFTS[params.gift],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        elder_type=params.elder_type,
    )
    world.get("hero").traits.append(params.trait)
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, need, gift) combos:\n")
        for place, need, gift in combos:
            print(f"  {place:14} {need:7} {gift}")
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
            header = f"### {p.hero_name}: {p.gift} for a {p.need} priest at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
