#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/corner_eel_rheumatic_sound_effects_happy_ending.py
=============================================================================

A standalone storyworld for a small fairy-tale domain built from the seed
words "corner", "eel", and "rheumatic", with child-facing sound effects and a
happy ending.

Premise
-------
A child in a watery fairy-tale place needs a music-making treasure for a small
celebration. The treasure has slipped into a hard-to-reach corner of a pond,
well, or fountain. An older grown-up with rheumatic aches cannot bend into the
cold water to fetch it. A shy eel can reach the stuck object, but only when the
child treats it gently. After the rescue, the elder uses a warm comfort that
actually suits rheumatic aches, and the ending proves the change with music,
light, and relief.

Reasonableness gate
-------------------
Not every explicit option makes sense.

* The eel needs water. A dry corner (like an attic chest) is rejected.
* A comfort for rheumatic aches must be warm and soothing. Cold comforts are
  known to the world but refused.
* The world includes a Python validity checker and an inline ASP twin. The
  verify mode checks parity and also smoke-tests ordinary story generation.

Run it
------
    python storyworlds/worlds/gpt-5.4/corner_eel_rheumatic_sound_effects_happy_ending.py
    python storyworlds/worlds/gpt-5.4/corner_eel_rheumatic_sound_effects_happy_ending.py --place well --item bell
    python storyworlds/worlds/gpt-5.4/corner_eel_rheumatic_sound_effects_happy_ending.py --place attic_corner
    python storyworlds/worlds/gpt-5.4/corner_eel_rheumatic_sound_effects_happy_ending.py --comfort ice_fan
    python storyworlds/worlds/gpt-5.4/corner_eel_rheumatic_sound_effects_happy_ending.py --all
    python storyworlds/worlds/gpt-5.4/corner_eel_rheumatic_sound_effects_happy_ending.py --verify
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

# Make the shared result containers importable when this nested script is run
# directly from the repo root.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    swims: bool = False
    warm: bool = False
    musical: bool = False
    water_place: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "grandmother", "woman", "witch"}
        male = {"boy", "father", "king", "wizard", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "queen": "queen",
            "wizard": "wizard",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    corner: str
    opening: str
    water_place: bool
    shimmer: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    sound: str
    festival_use: str
    difficulty: int = 1
    musical: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    action: str
    sense: int
    warm: bool = True
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


def _r_eel_free(world: World) -> list[str]:
    out: list[str] = []
    eel = world.entities.get("eel")
    item = world.entities.get("item")
    place = world.entities.get("place")
    if not eel or not item or not place:
        return out
    if eel.memes["trust"] < THRESHOLD:
        return out
    if item.meters["stuck"] < THRESHOLD:
        return out
    if not place.water_place:
        return out
    sig = ("eel_free",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["stuck"] = 0.0
    item.meters["freed"] += 1
    eel.memes["pride"] += 1
    world.get("child").memes["hope"] += 1
    world.get("elder").memes["relief"] += 1
    out.append("__freed__")
    return out


def _r_warm_relief(world: World) -> list[str]:
    out: list[str] = []
    elder = world.entities.get("elder")
    comfort = world.entities.get("comfort")
    if not elder or not comfort:
        return out
    if comfort.meters["used"] < THRESHOLD or not comfort.warm:
        return out
    sig = ("warm_relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    elder.meters["ache"] = max(0.0, elder.meters["ache"] - 1.0)
    elder.memes["comfort"] += 1
    out.append("__soothed__")
    return out


def _r_celebrate(world: World) -> list[str]:
    out: list[str] = []
    item = world.entities.get("item")
    elder = world.entities.get("elder")
    if not item or not elder:
        return out
    if item.meters["freed"] < THRESHOLD:
        return out
    sig = ("celebrate",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["joy"] += 1
    elder.memes["joy"] += 1
    world.get("eel").memes["joy"] += 1
    world.get("place").meters["music"] += 1
    out.append("__music__")
    return out


CAUSAL_RULES = [
    Rule("eel_free", "physical", _r_eel_free),
    Rule("warm_relief", "physical", _r_warm_relief),
    Rule("celebrate", "social", _r_celebrate),
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


PLACES = {
    "well": Place(
        "well",
        "the moon-well",
        "an old moon-well beside a willow tree",
        "the mossy corner below the round stones",
        "the round mouth of the well",
        True,
        "The water below gave a pale silver blink.",
        tags={"well", "water"},
    ),
    "pond": Place(
        "pond",
        "the lily pond",
        "a lily pond behind the cottage",
        "the reed-choked corner under the cattails",
        "the green edge of the pond",
        True,
        "Dragonflies stitched blue light over the water.",
        tags={"pond", "water"},
    ),
    "fountain": Place(
        "fountain",
        "the palace fountain",
        "a palace fountain where carved fish poured water all day",
        "the shadowy corner behind the carved basin",
        "the bright rim of the fountain",
        True,
        "Drops kept falling with a clear tippa-tippa sound.",
        tags={"fountain", "water"},
    ),
    "attic_corner": Place(
        "attic_corner",
        "the attic corner",
        "a dry attic under the roof beams",
        "the dusty corner behind an old chest",
        "the attic stairs",
        False,
        "Dust floated in the slant of light.",
        tags={"attic"},
    ),
}

ITEMS = {
    "bell": Item(
        "bell",
        "silver bell",
        "a little silver bell",
        "ting-ting!",
        "ring the evening wish bell",
        difficulty=1,
        tags={"bell", "music"},
    ),
    "flute": Item(
        "flute",
        "reed flute",
        "a reed flute wound with blue thread",
        "toot-loo!",
        "play the first tune of the lantern dance",
        difficulty=2,
        tags={"flute", "music"},
    ),
    "shell_harp": Item(
        "shell_harp",
        "shell harp",
        "a tiny shell harp strung with moon-silk",
        "pling-plong!",
        "sing the welcome song for the fireflies",
        difficulty=2,
        tags={"harp", "music"},
    ),
}

COMFORTS = {
    "shawl": Comfort(
        "shawl",
        "shawl",
        "a warm wool shawl",
        "wrapped the warm wool shawl around her aching shoulders",
        sense=3,
        warm=True,
        tags={"warmth", "shawl"},
    ),
    "tea": Comfort(
        "tea",
        "mint tea",
        "a steaming cup of mint tea",
        "held a steaming cup of mint tea between both hands",
        sense=3,
        warm=True,
        tags={"warmth", "tea"},
    ),
    "stone": Comfort(
        "stone",
        "sun-stone",
        "a sun-warmed river stone",
        "rested a sun-warmed river stone on his sore knee",
        sense=2,
        warm=True,
        tags={"warmth", "stone"},
    ),
    "ice_fan": Comfort(
        "ice_fan",
        "ice fan",
        "an icy fan of frost feathers",
        "waved the icy fan over the aching joints",
        sense=1,
        warm=False,
        tags={"cold"},
    ),
}

ELDERS = {
    "queen": {
        "type": "queen",
        "label": "the queen",
        "title": "the Willow Queen",
        "ailment": "rheumatic knees",
        "can't": "could not kneel on the stones without pain",
    },
    "grandmother": {
        "type": "grandmother",
        "label": "the grandmother",
        "title": "Grandmother Brindle",
        "ailment": "rheumatic hands",
        "can't": "could not reach into the cold water for long",
    },
    "wizard": {
        "type": "wizard",
        "label": "the wizard",
        "title": "Old Marsh Wizard Fen",
        "ailment": "rheumatic back",
        "can't": "could not bend deep into the corner without wincing",
    },
}

GIRL_NAMES = ["Lina", "Mira", "Elowen", "Poppy", "Tansy", "Nia"]
BOY_NAMES = ["Rowan", "Tobin", "Ari", "Milo", "Finn", "Bram"]
TRAITS = ["gentle", "bright", "curious", "kind", "brave", "patient"]


def place_supports_eel(place: Place) -> bool:
    return place.water_place


def sensible_comforts() -> list[Comfort]:
    return [c for c in COMFORTS.values() if c.sense >= SENSE_MIN and c.warm]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id in ITEMS:
            for comfort_id, comfort in COMFORTS.items():
                if place_supports_eel(place) and comfort.sense >= SENSE_MIN and comfort.warm:
                    combos.append((place_id, item_id, comfort_id))
    return combos


def explain_place(place: Place) -> str:
    return (
        f"(No story: the eel needs water to swim into a corner and fetch the lost thing. "
        f"{place.label.capitalize()} is dry, so the eel cannot help there.)"
    )


def explain_comfort(cid: str) -> str:
    c = COMFORTS[cid]
    better = " / ".join(sorted(x.id for x in sensible_comforts()))
    return (
        f"(Refusing comfort '{cid}': it is not a sensible comfort for rheumatic aches "
        f"(sense={c.sense} < {SENSE_MIN}). Warm comforts fit this fairy tale better. "
        f"Try: {better}.)"
    )


def predict_rescue(world: World) -> dict:
    sim = world.copy()
    sim.get("eel").memes["trust"] += 1
    propagate(sim, narrate=False)
    item = sim.get("item")
    return {
        "freed": item.meters["freed"] >= THRESHOLD,
        "music": sim.get("place").meters["music"],
    }


def introduce(world: World, child: Entity, elder: Entity, place: Place, item: Item) -> None:
    world.say(
        f"In a small kingdom where lamps were lit with wishes, {child.id} came with "
        f"{elder.attrs['title']} to {place.phrase}. {place.shimmer}"
    )
    world.say(
        f"They had gone there because {item.phrase} was needed to {item.festival_use} before moonrise."
    )


def trouble(world: World, elder: Entity, place: Place, item: Item) -> None:
    world.get("item").meters["stuck"] += 1
    world.say(
        f"But {item.the} had slipped into {place.corner}. It gave no music there at all, "
        f"only a faint little {item.sound.lower()}"
    )
    world.say(
        f"{elder.attrs['title']} sighed. {elder.pronoun('possessive').capitalize()} "
        f"{elder.attrs['ailment']} were bothering {elder.pronoun('object')} that day, and "
        f"{elder.attrs['cant']}."
    )


def notice_eel(world: World, child: Entity, place: Place) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Then, in the dark corner of the water, two bright bead-eyes blinked. "
        f'"Swish... slip... swish," went a little eel as it curled through the water.'
    )
    world.say(
        f"{child.id} did not shout or stamp. {child.pronoun().capitalize()} crouched by {place.opening} "
        f"and watched with a gentle face."
    )


def ask_kindly(world: World, child: Entity, eel: Entity, item: Item) -> None:
    child.memes["kindness"] += 1
    eel.memes["trust"] += 1
    pred = predict_rescue(world)
    world.facts["predicted_freed"] = pred["freed"]
    world.say(
        f'"Little eel," {child.id} whispered, "if you can nose out {item.the}, I will sing for you '
        f'instead of frightening you away."'
    )
    if pred["freed"]:
        world.say(
            f"The eel gave one shiny blink, as if it understood that kindness better than poking sticks."
        )


def eel_rescue(world: World, eel: Entity, item: Item, place: Place) -> None:
    propagate(world, narrate=False)
    world.say(
        f'The eel curled tighter and tighter. "Swish! Sloop! Glup!" it went, slipping into {place.corner}.'
    )
    world.say(
        f"At last its nose nudged {item.the}, and out came the treasure with a bright {item.sound}"
    )


def comfort_elder(world: World, elder: Entity, comfort: Comfort) -> None:
    world.get("comfort").meters["used"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{elder.attrs['title']} smiled and {comfort.action}. The warmth was gentle, and the ache eased enough "
        f"for a deep happy breath."
    )


def celebration(world: World, child: Entity, elder: Entity, eel: Entity, item: Item, place: Place) -> None:
    propagate(world, narrate=False)
    world.say(
        f"Soon {item.the} was singing where everyone could hear it: {item.sound} {item.sound} "
        f"The sound skipped across {place.label} like silver pebbles."
    )
    world.say(
        f"{child.id} danced, {elder.attrs['title']} laughed, and even the little eel made the water sparkle with "
        f'"swish-swish" loops of joy.'
    )
    world.say(
        f"From that night on, a crumb of cake and a kind song were always left by the corner for the helpful eel, "
        f"and the kingdom remembered that gentle hearts can untie hard little troubles."
    )


def tell(
    place: Place,
    item: Item,
    comfort: Comfort,
    child_name: str = "Lina",
    child_gender: str = "girl",
    trait: str = "gentle",
    elder_kind: str = "queen",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=[trait]))
    elder_cfg = ELDERS[elder_kind]
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_cfg["type"],
            role="elder",
            label=elder_cfg["label"],
            attrs={
                "title": elder_cfg["title"],
                "ailment": elder_cfg["ailment"],
                "cant": elder_cfg["can't"],
            },
        )
    )
    eel = world.add(Entity(id="eel", type="eel", label="the little eel", swims=True, role="helper"))
    place_ent = world.add(Entity(id="place", type="place", label=place.label, water_place=place.water_place))
    item_ent = world.add(Entity(id="item", type="item", label=item.label, musical=True))
    comfort_ent = world.add(Entity(id="comfort", type="comfort", label=comfort.label, warm=comfort.warm))

    elder.meters["ache"] = 1.0
    child.memes["hope"] = 1.0

    introduce(world, child, elder, place, item)
    world.para()
    trouble(world, elder, place, item)
    notice_eel(world, child, place)
    ask_kindly(world, child, eel, item)
    world.para()
    eel_rescue(world, eel, item, place)
    comfort_elder(world, elder, comfort)
    world.para()
    celebration(world, child, elder, eel, item, place)

    world.facts.update(
        child=child,
        elder=elder,
        eel=eel,
        place_cfg=place,
        item_cfg=item,
        comfort_cfg=comfort,
        stuck=item_ent.meters["freed"] < THRESHOLD,
        rescued=item_ent.meters["freed"] >= THRESHOLD,
        soothed=elder.meters["ache"] < THRESHOLD,
        happy=place_ent.meters["music"] >= THRESHOLD,
        predicted_freed=world.facts.get("predicted_freed", False),
    )
    return world


@dataclass
class StoryParams:
    place: str
    item: str
    comfort: str
    child_name: str
    child_gender: str
    trait: str
    elder: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "eel": [
        (
            "What is an eel?",
            "An eel is a long, slippery fish that can wiggle through water in narrow places. "
            "Its body helps it slip where bigger animals cannot."
        )
    ],
    "rheumatic": [
        (
            "What does rheumatic mean?",
            "Rheumatic means someone's joints or muscles ache and feel stiff, especially in cold or damp weather. "
            "That can make bending, kneeling, or reaching harder."
        )
    ],
    "well": [
        (
            "What is a well?",
            "A well is a deep stone hole where people draw up water. In stories, the inside can echo and hide shiny things."
        )
    ],
    "pond": [
        (
            "What is a pond?",
            "A pond is a small still pool of water where reeds, fish, and water bugs can live."
        )
    ],
    "fountain": [
        (
            "What is a fountain?",
            "A fountain is a place where water flows or sprays for people to see and hear."
        )
    ],
    "warmth": [
        (
            "Why can warmth help aching joints feel better?",
            "Gentle warmth can help tight, stiff muscles and joints relax. "
            "That is why a warm shawl, warm stone, or hot drink can feel soothing."
        )
    ],
    "bell": [
        (
            "What does a bell sound like?",
            "A little bell often rings with a bright sound like ting-ting or ding-ding."
        )
    ],
    "flute": [
        (
            "What is a flute?",
            "A flute is a musical instrument you blow into to make clear singing notes."
        )
    ],
    "harp": [
        (
            "What is a harp?",
            "A harp is a musical instrument with strings that can make soft ringing sounds when they are plucked."
        )
    ],
}
KNOWLEDGE_ORDER = ["eel", "rheumatic", "well", "pond", "fountain", "warmth", "bell", "flute", "harp"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    place = f["place_cfg"]
    item = f["item_cfg"]
    return [
        f'Write a fairy tale for a 3-to-5-year-old that includes the words "corner", "eel", and "rheumatic", '
        f'and ends happily with a musical sound effect.',
        f"Tell a gentle fairy tale where {child.id} helps {elder.attrs['title']} after {item.the} slips into "
        f"{place.corner}, and a kind eel saves the day.",
        f'Write a story with watery sound effects like "swish" and a joyful ending where kindness works better '
        f"than fear.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    place = f["place_cfg"]
    item = f["item_cfg"]
    comfort = f["comfort_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {elder.attrs['title']}, and a little eel in {place.label}. "
            f"They all matter because each one helps the problem change."
        ),
        (
            f"Why was {item.the} hard to get?",
            f"{item.the.capitalize()} had slipped into {place.corner}, which was too tricky to reach by hand. "
            f"The trouble was worse because the elder's {elder.attrs['ailment']} made bending or reaching painful."
        ),
        (
            f"Why could the eel help better than the elder?",
            f"The eel could wriggle through the wet corner because it was small and made for swimming. "
            f"{elder.attrs['title']} could not reach safely into that cold place while aching."
        ),
        (
            f"What did {child.id} do that helped the rescue happen?",
            f"{child.id} spoke kindly instead of frightening the eel away. "
            f"That gentle choice made the eel trust {child.pronoun('object')} and help with {item.the}."
        ),
    ]
    if f["rescued"]:
        qa.append(
            (
                f"How did the eel get {item.the} out?",
                f"The eel slipped into {place.corner} with little watery sounds and nudged {item.the} free. "
                f"Then it came out carrying the rescue into the light with a bright {item.sound}"
            )
        )
    if f["soothed"]:
        qa.append(
            (
                f"How did {elder.attrs['title']} feel better afterward?",
                f"{elder.attrs['title']} used {comfort.phrase}, which gave gentle warmth to the aching body. "
                f"That warmth soothed the rheumatic ache enough for a relieved smile."
            )
        )
    if f["happy"]:
        qa.append(
            (
                "How did the story end?",
                f"It ended happily with music, laughter, and the helpful eel honored at the corner. "
                f"The rescued {item.label} proved that the trouble was truly over."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"eel", "rheumatic"}
    tags |= set(f["place_cfg"].tags)
    tags |= set(f["item_cfg"].tags)
    tags |= set(f["comfort_cfg"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if e.swims:
            flags.append("swims")
        if e.warm:
            flags.append("warm")
        if e.musical:
            flags.append("musical")
        if e.water_place:
            flags.append("water_place")
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("well", "bell", "shawl", "Lina", "girl", "gentle", "queen"),
    StoryParams("pond", "flute", "tea", "Rowan", "boy", "kind", "grandmother"),
    StoryParams("fountain", "shell_harp", "stone", "Mira", "girl", "patient", "wizard"),
]


ASP_RULES = r"""
% Valid story choices: the place must have water for an eel rescue, and the
% comfort must be a sensible warm comfort for rheumatic aches.
valid(P, I, C) :- place(P), item(I), comfort(C), water_place(P), comfort_sense(C, S),
                  sense_min(M), S >= M, warm(C).

sensible_comfort(C) :- comfort(C), comfort_sense(C, S), sense_min(M), S >= M, warm(C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.water_place:
            lines.append(asp.fact("water_place", pid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for cid, comfort in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        lines.append(asp.fact("comfort_sense", cid, comfort.sense))
        if comfort.warm:
            lines.append(asp.fact("warm", cid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_comforts() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show sensible_comfort/1."))
    return sorted(c for (c,) in asp.atoms(model, "sensible_comfort"))


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_comforts = {c.id for c in sensible_comforts()}
    asp_comforts = set(asp_sensible_comforts())
    if py_comforts == asp_comforts:
        print(f"OK: sensible comforts match ({sorted(py_comforts)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible comforts: clingo={sorted(asp_comforts)} python={sorted(py_comforts)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a lost musical treasure, a watery corner, a helpful eel, and a happy ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if args.place and not PLACES[args.place].water_place:
        raise StoryError(explain_place(PLACES[args.place]))
    if args.comfort and (COMFORTS[args.comfort].sense < SENSE_MIN or not COMFORTS[args.comfort].warm):
        raise StoryError(explain_comfort(args.comfort))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.item is None or c[1] == args.item)
        and (args.comfort is None or c[2] == args.comfort)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, item, comfort = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    elder = args.elder or rng.choice(sorted(ELDERS))
    return StoryParams(place, item, comfort, name, gender, trait, elder)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        ITEMS[params.item],
        COMFORTS[params.comfort],
        child_name=params.child_name,
        child_gender=params.child_gender,
        trait=params.trait,
        elder_kind=params.elder,
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
        print(asp_program("#show valid/3.\n#show sensible_comfort/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        comforts = asp_sensible_comforts()
        print(f"sensible comforts: {', '.join(comforts)}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, comfort) combos:\n")
        for place, item, comfort in combos:
            print(f"  {place:12} {item:10} {comfort}")
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
            header = f"### {p.child_name}: {p.item} from {p.place} with {p.comfort}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
