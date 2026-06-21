#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/spring_surprise_inner_monologue_suspense_fairy_tale.py
=================================================================================

A tiny fairy-tale storyworld about a child in spring who finds a mysterious
closed bloom and must choose the right gentle care instead of forcing it open.

The domain is built around a clear causal constraint:

    place affords bloom
    bloom has a hidden need (water | sun | song)
    care is valid only when it matches that need and is gentle enough

The suspense comes from not knowing what waits inside the bloom. The child's
inner monologue is driven by world state: worry while the bloom stays closed,
hope after the right care, and wonder when the surprise appears.

Run it
------
    python storyworlds/worlds/gpt-5.4/spring_surprise_inner_monologue_suspense_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/spring_surprise_inner_monologue_suspense_fairy_tale.py --place orchard --bloom crocus_bell
    python storyworlds/worlds/gpt-5.4/spring_surprise_inner_monologue_suspense_fairy_tale.py --care pull_petals
    python storyworlds/worlds/gpt-5.4/spring_surprise_inner_monologue_suspense_fairy_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/spring_surprise_inner_monologue_suspense_fairy_tale.py --verify
"""

from __future__ import annotations

import argparse
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "queen", "woman"}
        male = {"boy", "father", "grandfather", "king", "man"}
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
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    path: str
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
class Bloom:
    id: str
    label: str
    the: str
    shell: str
    sign: str
    need: str
    surprise: str
    ending_image: str
    clue: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Care:
    id: str
    label: str
    need: str
    sense: int
    action_text: str
    wait_text: str
    qa_text: str
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


def _r_gentle_care(world: World) -> list[str]:
    bud = world.get("bud")
    hero = world.get("hero")
    out: list[str] = []
    if bud.meters["closed"] < THRESHOLD:
        return out
    for need in ("water", "sun", "song"):
        if bud.attrs.get("need") != need:
            continue
        if bud.meters[f"given_{need}"] < THRESHOLD:
            continue
        sig = ("gentle_care", need)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        bud.meters["closed"] = 0.0
        bud.meters["open"] += 1
        bud.meters[f"needs_{need}"] = 0.0
        hero.memes["hope"] += 1
        hero.memes["worry"] = 0.0
        hero.memes["wonder"] += 1
        world.get("secret").meters["revealed"] += 1
        out.append("__opened__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="gentle_care", tag="physical", apply=_r_gentle_care),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            parts = rule.apply(world)
            if parts:
                changed = True
                produced.extend(parts)
    if narrate:
        for text in produced:
            if not text.startswith("__"):
                world.say(text)
    return produced


def compatible_care(bloom: Bloom, care: Care) -> bool:
    return bloom.need == care.need and care.sense >= SENSE_MIN


def sensible_cares() -> list[Care]:
    return [care for care in CARES.values() if care.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for bloom_id in sorted(setting.affords):
            bloom = BLOOMS[bloom_id]
            for care_id, care in CARES.items():
                if compatible_care(bloom, care):
                    combos.append((place_id, bloom_id, care_id))
    return combos


def spring_opening(world: World, hero: Entity, elder: Entity) -> None:
    world.say(
        f"In the green beginning of spring, {hero.id} walked with {hero.pronoun('possessive')} "
        f"{elder.label_word} through {world.setting.place}. {world.setting.scene}"
    )
    world.say(world.setting.path)


def discover_bloom(world: World, hero: Entity, bloom: Bloom) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1
    bud = world.get("bud")
    world.say(
        f"Near the path stood {bloom.the}, its petals still folded tight like {bloom.shell}. "
        f"{bloom.sign}"
    )
    world.say(
        f"{hero.id} stopped so suddenly that a loose ribbon of grass brushed {hero.pronoun('possessive')} shoes."
    )
    world.say(
        f'"What is hiding in there?" {hero.pronoun()} whispered.'
    )
    world.say(
        f'Inside, {hero.pronoun()} thought, "If I knew the secret now, my heart would stop fluttering. '
        f'But if I am rough, I may spoil the very wonder I am trying to find."'
    )
    bud.memes["suspense"] += 1


def elder_warning(world: World, hero: Entity, elder: Entity, bloom: Bloom) -> None:
    world.say(
        f'{elder.label_word.capitalize()} touched {hero.pronoun("possessive")} sleeve. '
        f'"Do not tug at {bloom.the}," {elder.pronoun()} said softly. '
        f'"Spring keeps some treasures behind closed petals until they are welcomed the right way."'
    )
    world.say(
        f"{hero.id} looked at the curled edges and felt patience and impatience tug inside {hero.pronoun('object')} at the same time."
    )


def read_clue(world: World, hero: Entity, bloom: Bloom) -> None:
    world.say(
        f"Then {hero.id} noticed {bloom.clue}. That was the bloom's small sign."
    )
    if bloom.need == "water":
        thought = "It is not stubborn, it is thirsty"
    elif bloom.need == "sun":
        thought = "It is not asleep forever, only cold in the shade"
    else:
        thought = "It is not empty, only shy"
    world.say(
        f'Inside, {hero.pronoun()} thought, "{thought}."'
    )


def do_care(world: World, hero: Entity, care: Care) -> None:
    bud = world.get("bud")
    hero.memes["hope"] += 0.5
    world.say(care.action_text.format(hero=hero.id))
    bud.meters[f"given_{care.need}"] += 1
    propagate(world, narrate=False)


def waiting_beat(world: World, hero: Entity, care: Care) -> None:
    bud = world.get("bud")
    if bud.meters["open"] < THRESHOLD:
        raise StoryError("The bloom did not open after the chosen care.")
    world.say(care.wait_text)
    world.say(
        f"For one breath nothing happened. {hero.id}'s hands pressed together."
    )
    world.say(
        f'Inside, {hero.pronoun()} thought, "Please, little flower. If a secret is waiting, let it be ready now."'
    )


def reveal(world: World, hero: Entity, elder: Entity, bloom: Bloom) -> None:
    secret = world.get("secret")
    if secret.meters["revealed"] < THRESHOLD:
        raise StoryError("The surprise was never revealed.")
    world.say(
        f"Then {bloom.The} loosened with a tiny sigh. Petal by petal, it opened."
    )
    world.say(
        f"Inside was {bloom.surprise}."
    )
    world.say(
        f'{hero.id} gave a delighted gasp. "{bloom.ending_image}"'
    )
    world.say(
        f"{elder.label_word.capitalize()} smiled as if {elder.pronoun()} had expected wonder all along. "
        f'"That is why spring asks for gentleness," {elder.pronoun()} said.'
    )
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1


def ending(world: World, hero: Entity, bloom: Bloom) -> None:
    world.say(
        f"After that, whenever {hero.id} found a quiet mystery in the garden, {hero.pronoun()} remembered not to snatch at it."
    )
    world.say(
        f"Above {hero.pronoun('object')}, the mild spring light shone on {bloom.the}, now open, and the whole path looked as if it had learned to smile."
    )


def tell(
    setting: Setting,
    bloom: Bloom,
    care: Care,
    hero_name: str = "Elin",
    hero_type: str = "girl",
    elder_type: str = "grandmother",
) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_type, role="elder"))
    bud = world.add(
        Entity(
            id="bud",
            type="bloom",
            label=bloom.label,
            role="bud",
            attrs={"need": bloom.need, "surprise": bloom.surprise},
            tags=set(bloom.tags),
        )
    )
    secret = world.add(
        Entity(
            id="secret",
            type="surprise",
            label="secret",
            role="secret",
            tags=set(bloom.tags),
        )
    )

    bud.meters["closed"] = 1.0
    bud.meters["open"] = 0.0
    bud.meters["needs_water"] = 1.0 if bloom.need == "water" else 0.0
    bud.meters["needs_sun"] = 1.0 if bloom.need == "sun" else 0.0
    bud.meters["needs_song"] = 1.0 if bloom.need == "song" else 0.0
    bud.meters["given_water"] = 0.0
    bud.meters["given_sun"] = 0.0
    bud.meters["given_song"] = 0.0
    secret.meters["revealed"] = 0.0

    hero.memes["curiosity"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["hope"] = 0.0
    hero.memes["wonder"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["joy"] = 0.0

    world.facts.update(
        hero=hero,
        elder=elder,
        bloom_cfg=bloom,
        care=care,
        place=setting,
        clue=bloom.clue,
        surprise=bloom.surprise,
    )

    spring_opening(world, hero, elder)
    discover_bloom(world, hero, bloom)

    world.para()
    elder_warning(world, hero, elder, bloom)
    read_clue(world, hero, bloom)

    world.para()
    do_care(world, hero, care)
    waiting_beat(world, hero, care)
    reveal(world, hero, elder, bloom)

    world.para()
    ending(world, hero, bloom)

    world.facts.update(
        bloom_open=bud.meters["open"] >= THRESHOLD,
        revealed=secret.meters["revealed"] >= THRESHOLD,
        hero_name=hero_name,
    )
    return world


SETTINGS = {
    "cottage_garden": Setting(
        id="cottage_garden",
        place="the cottage garden",
        scene="Dew hung on the mint, and the fence wore a lace of new leaves.",
        path="A narrow stone path wound between herbs, primroses, and the first waking roses.",
        affords={"dew_lily", "hush_rose"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the orchard behind the old mill",
        scene="Apple boughs were misted with pink, and the ground was soft with fallen petals.",
        path="Between the trunks, the morning wind moved as carefully as if it carried news.",
        affords={"crocus_bell", "hush_rose"},
    ),
    "brook_meadow": Setting(
        id="brook_meadow",
        place="the brook meadow",
        scene="The brook spoke in silver ripples, and bright grass leaned toward the water.",
        path="A stepping-stone path crossed the wet earth where every small thing seemed to be listening.",
        affords={"dew_lily", "crocus_bell"},
    ),
}

BLOOMS = {
    "dew_lily": Bloom(
        id="dew_lily",
        label="dew-lily",
        the="the dew-lily",
        shell="a folded green lantern",
        sign="A tiny tapping came from within, and the stem looked thirsty.",
        need="water",
        surprise="a round striped bumblebee, sleepy and powdered with gold pollen",
        ending_image="A bee! It was waiting for a kind sip before waking.",
        clue="the soil at its roots was pale and crumbly",
        tags={"spring", "flower", "water", "bee", "patience"},
    ),
    "crocus_bell": Bloom(
        id="crocus_bell",
        label="crocus bell",
        the="the crocus bell",
        shell="a little purple bell with its mouth shut",
        sign="Something inside gave one bright rustle, but the bloom stood in a cool patch of shadow.",
        need="sun",
        surprise="a blue butterfly, new-winged and shining as if the sky had folded itself small",
        ending_image="A butterfly! It wanted warmth before it dared unfold the day.",
        clue="a bar of sunlight lay only a few steps away, bright as honey",
        tags={"spring", "flower", "sun", "butterfly", "patience"},
    ),
    "hush_rose": Bloom(
        id="hush_rose",
        label="hush-rose",
        the="the hush-rose",
        shell="a crimson bud no bigger than a robin's heart",
        sign="A silver laugh, no louder than a raindrop, trembled from deep inside it.",
        need="song",
        surprise="a thumb-sized fairy messenger in a cloak of pale petals, carrying a curled note",
        ending_image="A fairy! It was waiting for a song brave enough to say welcome.",
        clue="the leaves around it stirred as if they were listening for music",
        tags={"spring", "flower", "song", "fairy", "patience"},
    ),
}

CARES = {
    "water_roots": Care(
        id="water_roots",
        label="water at the roots",
        need="water",
        sense=3,
        action_text="{hero} cupped cool brook water in both hands and let it fall gently around the roots.",
        wait_text="The dark earth drank, and the stem gave a tiny, hopeful lift.",
        qa_text="gave the bloom water at its roots",
        tags={"water", "flower"},
    ),
    "carry_to_sun": Care(
        id="carry_to_sun",
        label="carry it into the sun",
        need="sun",
        sense=3,
        action_text="{hero} loosened the little clod of earth with careful fingers and set the bloom where the sunlight could warm it.",
        wait_text="Sunlight spilled over the petals until the purple shell glowed from within.",
        qa_text="moved the bloom into a warm patch of sunlight",
        tags={"sun", "flower"},
    ),
    "sing_softly": Care(
        id="sing_softly",
        label="sing softly",
        need="song",
        sense=3,
        action_text="{hero} bent close and sang the gentlest spring song {hero} knew, hardly louder than the breeze.",
        wait_text="The leaves gave a pleased little shiver, as if the tune had found the very lock it needed.",
        qa_text="sang softly to the bloom",
        tags={"song", "flower"},
    ),
    "pull_petals": Care(
        id="pull_petals",
        label="pull the petals apart",
        need="force",
        sense=1,
        action_text="{hero} reached to pull the petals apart.",
        wait_text="The petals trembled unhappily.",
        qa_text="tried to force the bloom open",
        tags={"flower"},
    ),
    "shake_stem": Care(
        id="shake_stem",
        label="shake the stem",
        need="force",
        sense=1,
        action_text="{hero} reached to shake the stem.",
        wait_text="The whole bloom wobbled in distress.",
        qa_text="shook the bloom",
        tags={"flower"},
    ),
}

GIRL_NAMES = ["Elin", "Mira", "Lina", "Tansy", "Wren", "Asha", "Nella", "Ivy"]
BOY_NAMES = ["Rowan", "Theo", "Bram", "Oren", "Finn", "Alden", "Milo", "Sage"]


@dataclass
class StoryParams:
    place: str
    bloom: str
    care: str
    name: str
    gender: str
    elder: str
    seed: Optional[int] = None
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


KNOWLEDGE = {
    "spring": [
        (
            "What happens in spring?",
            "In spring, the weather warms, new leaves and flowers begin to grow, and many small animals wake up or become busy again."
        )
    ],
    "flower": [
        (
            "What is a flower bud?",
            "A flower bud is a flower before it opens. Its petals stay folded up until it is ready."
        )
    ],
    "water": [
        (
            "Why do flowers need water?",
            "Flowers need water to stay alive and grow. Water travels up through the roots and helps the plant keep its stems and petals fresh."
        )
    ],
    "sun": [
        (
            "Why does sunlight help plants?",
            "Sunlight gives plants energy to grow. Warm light can also help some flowers open."
        )
    ],
    "song": [
        (
            "Why can gentle singing feel comforting?",
            "A soft song can make a place feel calm and welcoming. In a fairy tale, that kind of kindness can help shy magic come out."
        )
    ],
    "bee": [
        (
            "What does a bee do around flowers?",
            "A bee visits flowers for nectar and pollen. As it moves from flower to flower, it can help plants make seeds."
        )
    ],
    "butterfly": [
        (
            "Why do butterflies like warm places?",
            "Butterflies are easier to wake and fly when they are warm. Sunshine helps their bodies get ready to move."
        )
    ],
    "fairy": [
        (
            "What is a fairy in a fairy tale?",
            "A fairy is a tiny magical being from storybook worlds. Fairies often appear when someone is gentle, brave, or kind."
        )
    ],
    "patience": [
        (
            "What does patience mean?",
            "Patience means waiting calmly instead of grabbing or rushing. Sometimes patience protects something delicate until the right moment."
        )
    ],
}
KNOWLEDGE_ORDER = ["spring", "flower", "water", "sun", "song", "bee", "butterfly", "fairy", "patience"]


def generation_prompts(world: World) -> list[str]:
    bloom = world.facts["bloom_cfg"]
    hero = world.facts["hero"]
    care = world.facts["care"]
    place = world.facts["place"]
    return [
        f'Write a fairy-tale story for a 3-to-5-year-old that includes the word "spring" and begins with a child finding a mysterious closed flower.',
        f"Tell a gentle suspense story set in {place.place} where a child named {hero.label} wonders what is hidden inside {bloom.the} and uses {care.label} instead of forcing it open.",
        f"Write a short story with inner monologue, a spring mystery, and a surprise ending where kindness reveals what was waiting inside a bloom.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    bloom = world.facts["bloom_cfg"]
    care = world.facts["care"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child walking in spring with {hero.pronoun('possessive')} {elder.label_word}. Together they find a mysterious bloom that has not opened yet."
        ),
        (
            f"What made the story feel mysterious at first?",
            f"{bloom.The} was closed, and a tiny sound came from inside it. {hero.label} could not see the secret yet, so the closed petals made the moment full of suspense."
        ),
        (
            f"What was {hero.label} thinking when {hero.pronoun()} found the bloom?",
            f"{hero.pronoun().capitalize()} wondered what was hidden inside and wanted to know at once. But {hero.pronoun()} also worried that rough hands might ruin the secret before it was ready."
        ),
        (
            f"How did {hero.label} help the bloom open?",
            f"{hero.label} {care.qa_text}. {bloom.clue[0].upper()}{bloom.clue[1:]}, so that gentle choice matched what the bloom needed."
        ),
    ]
    if world.facts.get("revealed"):
        qa.append(
            (
                "What was the surprise inside the bloom?",
                f"Inside was {bloom.surprise}. The surprise feels joyful because the whole story had been waiting for that hidden spring wonder to appear."
            )
        )
        qa.append(
            (
                "Why did the elder say spring asks for gentleness?",
                f"The secret only appeared after the bloom was treated kindly, not forced open. The story shows that patience protected the surprise until it was ready."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    bloom = world.facts["bloom_cfg"]
    care = world.facts["care"]
    tags = set(bloom.tags) | set(care.tags)
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="brook_meadow",
        bloom="dew_lily",
        care="water_roots",
        name="Elin",
        gender="girl",
        elder="grandmother",
    ),
    StoryParams(
        place="orchard",
        bloom="crocus_bell",
        care="carry_to_sun",
        name="Rowan",
        gender="boy",
        elder="grandfather",
    ),
    StoryParams(
        place="cottage_garden",
        bloom="hush_rose",
        care="sing_softly",
        name="Mira",
        gender="girl",
        elder="grandmother",
    ),
    StoryParams(
        place="orchard",
        bloom="hush_rose",
        care="sing_softly",
        name="Theo",
        gender="boy",
        elder="grandfather",
    ),
    StoryParams(
        place="brook_meadow",
        bloom="crocus_bell",
        care="carry_to_sun",
        name="Ivy",
        gender="girl",
        elder="grandmother",
    ),
]


def explain_rejection(bloom: Bloom, care: Care) -> str:
    if care.sense < SENSE_MIN:
        return (
            f"(No story: '{care.id}' is too rough for a fairy-tale spring mystery. "
            f"The child must choose a gentle way to help {bloom.the}, not force it open.)"
        )
    return (
        f"(No story: {bloom.the} needs {bloom.need}, but '{care.id}' does not provide that. "
        f"This world only tells stories where the clue honestly matches the care.)"
    )


ASP_RULES = r"""
sensible(C) :- care(C), sense(C,S), sense_min(M), S >= M.
compatible(B,C) :- bloom(B), care(C), needs(B,N), gives(C,N), sensible(C).
valid(P,B,C) :- place(P), affords(P,B), compatible(B,C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("place", place_id))
        for bloom_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, bloom_id))
    for bloom_id, bloom in BLOOMS.items():
        lines.append(asp.fact("bloom", bloom_id))
        lines.append(asp.fact("needs", bloom_id, bloom.need))
    for care_id, care in CARES.items():
        lines.append(asp.fact("care", care_id))
        lines.append(asp.fact("gives", care_id, care.need))
        lines.append(asp.fact("sense", care_id, care.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(c for (c,) in asp.atoms(model, "sensible"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale spring storyworld: a child finds a mysterious bloom and chooses the gentle right care."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--bloom", choices=BLOOMS)
    ap.add_argument("--care", choices=CARES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, bloom, care) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.bloom and args.care:
        bloom = BLOOMS[args.bloom]
        care = CARES[args.care]
        if not compatible_care(bloom, care):
            raise StoryError(explain_rejection(bloom, care))
    if args.place and args.bloom and args.bloom not in SETTINGS[args.place].affords:
        raise StoryError(
            f"(No story: {BLOOMS[args.bloom].the} does not grow in {SETTINGS[args.place].place} in this little world.)"
        )
    if args.care and CARES[args.care].sense < SENSE_MIN:
        care = CARES[args.care]
        bloom = BLOOMS[args.bloom] if args.bloom else next(iter(BLOOMS.values()))
        raise StoryError(explain_rejection(bloom, care))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.bloom is None or combo[1] == args.bloom)
        and (args.care is None or combo[2] == args.care)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, bloom_id, care_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    return StoryParams(
        place=place,
        bloom=bloom_id,
        care=care_id,
        name=name,
        gender=gender,
        elder=elder,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.bloom not in BLOOMS:
        raise StoryError(f"Unknown bloom: {params.bloom}")
    if params.care not in CARES:
        raise StoryError(f"Unknown care: {params.care}")
    setting = SETTINGS[params.place]
    bloom = BLOOMS[params.bloom]
    care = CARES[params.care]
    if params.bloom not in setting.affords:
        raise StoryError(
            f"{bloom.the.capitalize()} does not belong in {setting.place} in this world."
        )
    if not compatible_care(bloom, care):
        raise StoryError(explain_rejection(bloom, care))

    world = tell(
        setting=setting,
        bloom=bloom,
        care=care,
        hero_name=params.name,
        hero_type=params.gender,
        elder_type=params.elder,
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
    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: valid_combos parity matches ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))

    python_sensible = {care.id for care in sensible_cares()}
    clingo_sensible = set(asp_sensible())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible cares match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible cares:")
        print("  python:", sorted(python_sensible))
        print("  clingo:", sorted(clingo_sensible))

    smoke_cases = list(CURATED)
    parser = build_parser()
    for seed in range(10):
        try:
            ns = parser.parse_args([])
            params = resolve_params(ns, random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError as err:
            rc = 1
            print(f"SMOKE resolve failed for seed {seed}: {err}")

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if not sample.prompts or not sample.story_qa or not sample.world_qa:
                raise StoryError("missing prompts or QA")
            emit(sample, trace=False, qa=False)
        except Exception as err:
            rc = 1
            print(f"SMOKE generation failed for {params}: {err}")

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show sensible/1.\n#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sensible = asp_sensible()
        combos = asp_valid_combos()
        print(f"sensible cares: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (place, bloom, care) combos:\n")
        for place, bloom, care in combos:
            print(f"  {place:15} {bloom:12} {care}")
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
            header = f"### {p.name}: {p.bloom} in {p.place} with {p.care}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
