#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/marriage_diller_tortilla_sound_effects_misunderstanding_nursery.py
================================================================================================

A standalone story world for a tiny nursery-rhyme-like tale about a child helper,
Diller the cook, a warm tortilla, and a sound-effect misunderstanding at a
marriage feast.

The world model is small but stateful:

- Diller cooks a tortilla for a marriage feast.
- A child helper hears a noisy cooking sound.
- The child mistakes the sound for another signal and carries the tortilla to the
  wrong place.
- The wrong turn delays the feast and cools the tortilla.
- A grown-up explains the misunderstanding.
- The ending depends on whether the tortilla is still warm enough to serve at
  once, or whether Diller must bake a fresh one while the child helps the right
  way.

Run it
------
    python storyworlds/worlds/gpt-5.4/marriage_diller_tortilla_sound_effects_misunderstanding_nursery.py
    python storyworlds/worlds/gpt-5.4/marriage_diller_tortilla_sound_effects_misunderstanding_nursery.py --setting orchard --sound spoon_ting --mistake bell
    python storyworlds/worlds/gpt-5.4/marriage_diller_tortilla_sound_effects_misunderstanding_nursery.py --sound spoon_ting --mistake carriage
    python storyworlds/worlds/gpt-5.4/marriage_diller_tortilla_sound_effects_misunderstanding_nursery.py --all
    python storyworlds/worlds/gpt-5.4/marriage_diller_tortilla_sound_effects_misunderstanding_nursery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/marriage_diller_tortilla_sound_effects_misunderstanding_nursery.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
INITIAL_WARMTH = 3
MAX_DELAY = 2


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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class MarriageSetting:
    id: str
    scene: str
    table_place: str
    decor: str
    finale: str
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
class SoundSource:
    id: str
    tool: str
    effect: str
    motion: str
    resembles: set[str] = field(default_factory=set)
    cool_loss: int = 0
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
class Mistake:
    id: str
    heard_as: str
    wrong_place: str
    correction: str
    delay_cost: int = 0
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


class World:
    def __init__(self, setting: MarriageSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _r_wait_and_cool(world: World) -> list[str]:
    tortilla = world.get("tortilla")
    feast = world.get("feast")
    child = world.get("child")
    if tortilla.attrs.get("place") == "table":
        return []
    sig = ("wait_and_cool", tortilla.attrs.get("place"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    feast.meters["waiting"] += 1
    child.memes["confusion"] += 1
    loss = 1 + int(world.facts["extra_delay"]) + int(world.facts["mistake_delay"]) + int(world.facts["sound_loss"])
    tortilla.meters["warmth"] = max(0.0, tortilla.meters["warmth"] - float(loss))
    return []


def _r_embarrassment(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["corrected"] < THRESHOLD:
        return []
    sig = ("embarrassment", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["embarrassment"] += 1
    return []


def _r_quick_relief(world: World) -> list[str]:
    tortilla = world.get("tortilla")
    child = world.get("child")
    feast = world.get("feast")
    if tortilla.attrs.get("place") != "table" or tortilla.meters["warmth"] <= 0:
        return []
    sig = ("quick_relief", tortilla.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    feast.memes["joy"] += 1
    return []


def _r_mended_relief(world: World) -> list[str]:
    child = world.get("child")
    feast = world.get("feast")
    if child.memes["helped_second_round"] < THRESHOLD:
        return []
    sig = ("mended_relief", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    feast.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="wait_and_cool", tag="physical", apply=_r_wait_and_cool),
    Rule(name="embarrassment", tag="social", apply=_r_embarrassment),
    Rule(name="quick_relief", tag="emotional", apply=_r_quick_relief),
    Rule(name="mended_relief", tag="emotional", apply=_r_mended_relief),
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


SETTINGS = {
    "orchard": MarriageSetting(
        id="orchard",
        scene="an orchard where white ribbons swung from the apple branches",
        table_place="the long ribbon table",
        decor="Marigolds nodded by the plates, and little cups shone like suns.",
        finale="Under the apple leaves, the marriage feast hummed soft and sweet.",
        tags={"orchard", "marriage"},
    ),
    "courtyard": MarriageSetting(
        id="courtyard",
        scene="a cobbled courtyard with bright cloths tied from wall to wall",
        table_place="the blue-cloth table",
        decor="Pigeons bobbed by the fountain, and the napkins looked like folded clouds.",
        finale="In the warm courtyard, the marriage feast glowed like a lantern.",
        tags={"courtyard", "marriage"},
    ),
    "riverside": MarriageSetting(
        id="riverside",
        scene="a riverside lawn where streamers flickered in the breeze",
        table_place="the willow table",
        decor="The river made a silver line, and little spoons winked in the light.",
        finale="By the river, the marriage feast rustled and laughed together.",
        tags={"river", "marriage"},
    ),
}

SOUNDS = {
    "spoon_ting": SoundSource(
        id="spoon_ting",
        tool="a brass spoon on the pan rim",
        effect="ting-ting! ting-ting!",
        motion="tapped the rim with a bright brass spoon",
        resembles={"bell"},
        cool_loss=0,
        tags={"sound", "bell"},
    ),
    "cart_rattle": SoundSource(
        id="cart_rattle",
        tool="the little flour cart",
        effect="rattle-rattle! clitter-clatter!",
        motion="shook the little flour cart over the stones",
        resembles={"carriage"},
        cool_loss=1,
        tags={"sound", "carriage"},
    ),
    "lid_tum": SoundSource(
        id="lid_tum",
        tool="two round pan lids",
        effect="tum-ta-tum! tam-tam!",
        motion="drummed two pan lids together for fun",
        resembles={"band"},
        cool_loss=0,
        tags={"sound", "band"},
    ),
    "pan_clang": SoundSource(
        id="pan_clang",
        tool="the iron pan",
        effect="clang-cling! clink-clang!",
        motion="shook the iron pan and laughed at the noise",
        resembles={"bell", "band"},
        cool_loss=1,
        tags={"sound", "bell", "band"},
    ),
}

MISTAKES = {
    "bell": Mistake(
        id="bell",
        heard_as="the feast bell",
        wrong_place="the bell post",
        correction="Those were only Diller's cooking taps, not the feast bell.",
        delay_cost=0,
        tags={"bell", "misunderstanding"},
    ),
    "carriage": Mistake(
        id="carriage",
        heard_as="the carriage at the gate",
        wrong_place="the carriage gate",
        correction="That was only Diller's cart and pan, not a carriage at all.",
        delay_cost=1,
        tags={"carriage", "misunderstanding"},
    ),
    "band": Mistake(
        id="band",
        heard_as="the little marriage band",
        wrong_place="the bandstand",
        correction="Those were only Diller's lids, not the band beginning to play.",
        delay_cost=1,
        tags={"band", "misunderstanding"},
    ),
}

GIRL_NAMES = ["Mina", "Nell", "Tess", "Poppy", "June", "Daisy"]
BOY_NAMES = ["Pip", "Ben", "Ollie", "Kit", "Ned", "Robin"]
ADULT_TYPES = ["mother", "father", "aunt", "uncle"]
TRAITS = ["eager", "bouncy", "careful", "curious", "sunny", "swift"]


def valid_combo(sound_id: str, mistake_id: str) -> bool:
    return mistake_id in SOUNDS[sound_id].resembles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for sound_id, sound in SOUNDS.items():
            for mistake_id in MISTAKES:
                if valid_combo(sound_id, mistake_id):
                    combos.append((setting_id, sound_id, mistake_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    sound: str
    mistake: str
    child_name: str
    child_gender: str
    adult: str
    trait: str
    delay: int = 0
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


def total_loss_for(params: StoryParams) -> int:
    return 1 + params.delay + SOUNDS[params.sound].cool_loss + MISTAKES[params.mistake].delay_cost


def outcome_of(params: StoryParams) -> str:
    return "warm" if INITIAL_WARMTH - total_loss_for(params) > 0 else "mended"


CURATED = [
    StoryParams(
        setting="orchard",
        sound="spoon_ting",
        mistake="bell",
        child_name="Pip",
        child_gender="boy",
        adult="aunt",
        trait="eager",
        delay=0,
    ),
    StoryParams(
        setting="courtyard",
        sound="pan_clang",
        mistake="band",
        child_name="Mina",
        child_gender="girl",
        adult="mother",
        trait="curious",
        delay=0,
    ),
    StoryParams(
        setting="riverside",
        sound="cart_rattle",
        mistake="carriage",
        child_name="Nell",
        child_gender="girl",
        adult="uncle",
        trait="bouncy",
        delay=1,
    ),
    StoryParams(
        setting="orchard",
        sound="pan_clang",
        mistake="bell",
        child_name="Robin",
        child_gender="boy",
        adult="father",
        trait="swift",
        delay=1,
    ),
    StoryParams(
        setting="courtyard",
        sound="cart_rattle",
        mistake="carriage",
        child_name="Daisy",
        child_gender="girl",
        adult="aunt",
        trait="careful",
        delay=2,
    ),
]


KNOWLEDGE = {
    "marriage": [
        (
            "What is a marriage feast?",
            "A marriage feast is a special meal people share when two grown-ups are getting married. Families gather, eat, and celebrate together.",
        )
    ],
    "tortilla": [
        (
            "What is a tortilla?",
            "A tortilla is a thin round flatbread. It can be soft and warm when it comes fresh from the pan.",
        )
    ],
    "bell": [
        (
            "Why can a bell be confusing from far away?",
            "A bell has a clear ringing sound, and from far away another bright metal noise can seem a little like it. That is why people sometimes check before they hurry off.",
        )
    ],
    "carriage": [
        (
            "What is a carriage?",
            "A carriage is a small wagon or coach that people or animals can pull. Its wheels can rattle on stones and make a bumpy sound.",
        )
    ],
    "band": [
        (
            "What is a bandstand?",
            "A bandstand is a little platform where musicians can play. Drums and metal sounds can make people think music is starting.",
        )
    ],
    "sound": [
        (
            "Why do people sometimes misunderstand sounds?",
            "Different things can make noises that seem alike for a moment. Listening for the whole message helps you understand better.",
        )
    ],
}
KNOWLEDGE_ORDER = ["marriage", "tortilla", "sound", "bell", "carriage", "band"]


def introduce(world: World, child: Entity, adult: Entity, diller: Entity, tortilla: Entity) -> None:
    world.say(
        f"In {world.setting.scene}, {child.id} helped {adult.label_word} at a marriage feast."
    )
    world.say(world.setting.decor)
    world.say(
        f"Near the fire stood {diller.id}, the diller cook, patting {tortilla.label} round and thin."
    )
    child.memes["joy"] += 1
    diller.memes["focus"] += 1


def cook_song(world: World, diller: Entity, sound: SoundSource) -> None:
    world.say(
        f'"Pat-a-pat, round and neat; warm tortilla for the wedding treat," sang {diller.id}. '
        f"Then {diller.pronoun()} {sound.motion}: {sound.effect}"
    )


def task(world: World, child: Entity) -> None:
    world.say(
        f'"When I call clearly, carry the tortilla to {world.setting.table_place}," '
        f"said Diller."
    )
    child.memes["duty"] += 1


def misunderstand(world: World, child: Entity, tortilla: Entity, sound: SoundSource, mistake: Mistake) -> None:
    child.memes["eagerness"] += 1
    child.memes["confusion"] += 1
    tortilla.attrs["place"] = "wrong_place"
    world.facts["wrong_place_name"] = mistake.wrong_place
    world.say(
        f"But {sound.effect} skipped through the air, and {child.id} thought it meant {mistake.heard_as}."
    )
    world.say(
        f'Off went {child.id}, patter-pat, carrying the tortilla to {mistake.wrong_place} instead of {world.setting.table_place}.'
    )
    propagate(world, narrate=False)


def search_and_correct(world: World, child: Entity, adult: Entity, diller: Entity, mistake: Mistake) -> None:
    child.memes["corrected"] += 1
    world.say(
        f"Soon {adult.label_word} came hurrying after {child.pronoun('object')} and found {child.pronoun('object')} standing small and puzzled."
    )
    world.say(
        f'"{mistake.correction} The tortilla belongs at {world.setting.table_place}," '
        f"{adult.pronoun()} said."
    )
    world.say(
        f"{child.id}'s cheeks grew pink. {child.pronoun().capitalize()} looked at Diller, then at the tray, and understood the muddle at last."
    )
    propagate(world, narrate=False)


def quick_return(world: World, child: Entity, adult: Entity, tortilla: Entity) -> None:
    tortilla.attrs["place"] = "table"
    child.memes["lesson"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Together they hurried back, step-a-step, and set the tortilla on {world.setting.table_place} while it was still warm.'
    )
    world.say(
        f'Soft steam curled up. "There now," said {adult.label_word}, and the waiting faces turned bright again.'
    )


def mended_return(world: World, child: Entity, diller: Entity, tortilla: Entity) -> None:
    tortilla.attrs["place"] = "table"
    child.memes["lesson"] += 1
    child.memes["helped_second_round"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They hurried back, but the tortilla had gone cool on the tray."
    )
    world.say(
        f'Diller only smiled. "Then we mend it the merry way," {diller.pronoun()} said, laying a fresh round on the pan.'
    )
    world.say(
        f'{child.id} stayed close this time, listening for words instead of clangs, and helped carry the next warm tortilla straight to {world.setting.table_place}.'
    )


def close_feast(world: World, child: Entity, outcome: str) -> None:
    if outcome == "warm":
        world.say(
            f"Guests shared the warm tortilla in happy pieces, and {child.id} learned to wait for the true call, not only the noise."
        )
    else:
        world.say(
            f"When the fresh tortilla arrived, everyone laughed kindly, and {child.id} learned that clear words matter more than clatter."
        )
    world.say(world.setting.finale)


def tell(
    setting: MarriageSetting,
    sound: SoundSource,
    mistake: Mistake,
    child_name: str = "Pip",
    child_gender: str = "boy",
    adult_type: str = "aunt",
    trait: str = "eager",
    delay: int = 0,
) -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            attrs={"trait": trait},
            tags={"child"},
        )
    )
    adult = world.add(
        Entity(
            id="Adult",
            kind="character",
            type=adult_type,
            label="the grown-up",
            role="adult",
            attrs={},
            tags={"adult"},
        )
    )
    diller = world.add(
        Entity(
            id="Diller",
            kind="character",
            type="person",
            label="the diller cook",
            role="cook",
            attrs={},
            tags={"diller"},
        )
    )
    tortilla = world.add(
        Entity(
            id="tortilla",
            kind="thing",
            type="food",
            label="the tortilla",
            role="food",
            attrs={"place": "pan"},
            tags={"tortilla"},
        )
    )
    feast = world.add(
        Entity(
            id="feast",
            kind="thing",
            type="feast",
            label="the marriage feast",
            role="feast",
            attrs={"table_place": setting.table_place},
            tags={"marriage"},
        )
    )

    tortilla.meters["warmth"] = float(INITIAL_WARMTH)
    child.memes["confusion"] = 0.0
    child.memes["corrected"] = 0.0
    child.memes["helped_second_round"] = 0.0
    feast.meters["waiting"] = 0.0
    feast.memes["joy"] = 0.0
    world.facts["extra_delay"] = delay
    world.facts["mistake_delay"] = mistake.delay_cost
    world.facts["sound_loss"] = sound.cool_loss
    world.facts["setting"] = setting
    world.facts["sound"] = sound
    world.facts["mistake"] = mistake
    world.facts["child"] = child
    world.facts["adult"] = adult
    world.facts["diller"] = diller
    world.facts["tortilla"] = tortilla
    world.facts["feast"] = feast
    world.facts["predicted_loss"] = 1 + delay + mistake.delay_cost + sound.cool_loss

    introduce(world, child, adult, diller, tortilla)
    cook_song(world, diller, sound)
    task(world, child)

    world.para()
    misunderstand(world, child, tortilla, sound, mistake)
    search_and_correct(world, child, adult, diller, mistake)

    world.para()
    if tortilla.meters["warmth"] > 0:
        outcome = "warm"
        quick_return(world, child, adult, tortilla)
    else:
        outcome = "mended"
        mended_return(world, child, diller, tortilla)

    world.para()
    close_feast(world, child, outcome)

    world.facts["outcome"] = outcome
    world.facts["still_warm"] = tortilla.meters["warmth"] > 0
    world.facts["waiting"] = feast.meters["waiting"]
    world.facts["warmth_left"] = tortilla.meters["warmth"]
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    sound = world.facts["sound"]
    mistake = world.facts["mistake"]
    setting = world.facts["setting"]
    return [
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old that uses the words "marriage", "diller", and "tortilla".',
        f"Tell a gentle marriage-feast story set in {setting.scene} where a child named {child.id} hears {sound.effect} and misunderstands it as {mistake.heard_as}.",
        f"Write a small rhythmic story with sound effects, a misunderstanding, and a warm ending where Diller is cooking a tortilla.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    adult = world.facts["adult"]
    sound = world.facts["sound"]
    mistake = world.facts["mistake"]
    setting = world.facts["setting"]
    outcome = world.facts["outcome"]
    predicted_loss = world.facts["predicted_loss"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child helper at a marriage feast, Diller the cook, and {adult.label_word} who helped set things right.",
        ),
        (
            "What was Diller making?",
            "Diller was making a warm tortilla for the marriage feast. It was meant to be carried to the table at the right moment.",
        ),
        (
            f"Why did {child.id} take the tortilla to the wrong place?",
            f"{child.id} heard {sound.effect} and mistook it for {mistake.heard_as}. The noisy sound covered the real meaning for a moment, so {child.pronoun()} hurried to {mistake.wrong_place} instead of {setting.table_place}.",
        ),
        (
            "How was the misunderstanding fixed?",
            f"{adult.label_word.capitalize()} followed and explained that the sound came from Diller's cooking, not from the signal {child.id} imagined. Once the mistake was named clearly, {child.id} understood what the sound really meant.",
        ),
    ]
    if outcome == "warm":
        qa.append(
            (
                "How did the story end?",
                f"The tortilla was still warm when they brought it back to {setting.table_place}. Because the delay was small, the marriage feast could go on at once and everyone brightened.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"The first tortilla had cooled, so Diller made a fresh warm one while {child.id} stayed close and listened carefully. The ending is happy because the mistake was mended and the child learned to trust clear words over clanging sounds.",
            )
        )
    qa.append(
        (
            f"Why did the tortilla cool so quickly?",
            f"It lost warmth because it was carried away from the table during the misunderstanding. The trip, plus the extra delay of {predicted_loss}, meant the feast had to wait while the tortilla sat too long off the pan.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"marriage", "tortilla", "sound"}
    tags |= set(world.facts["mistake"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != 0 and v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(sound_id: str, mistake_id: str) -> str:
    sound = SOUNDS[sound_id]
    mistake = MISTAKES[mistake_id]
    options = ", ".join(sorted(sound.resembles))
    return (
        f"(No story: {sound.effect} from {sound.tool} does not reasonably sound like {mistake.heard_as}. "
        f"That sound only plausibly causes these misunderstandings: {options}.)"
    )


ASP_RULES = r"""
valid(S, So, M) :- setting(S), sound(So), mistake(M), resembles(So, M).

loss(1 + D + C + Md) :- chosen_delay(D), chosen_sound(So), cool_loss(So, C),
                        chosen_mistake(M), mistake_delay(M, Md).

warm :- initial_warmth(W), loss(L), W - L > 0.
mended :- initial_warmth(W), loss(L), W - L <= 0.

outcome(warm) :- warm.
outcome(mended) :- mended.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for sound_id, sound in SOUNDS.items():
        lines.append(asp.fact("sound", sound_id))
        lines.append(asp.fact("cool_loss", sound_id, sound.cool_loss))
        for mistake_id in sorted(sound.resembles):
            lines.append(asp.fact("resembles", sound_id, mistake_id))
    for mistake_id, mistake in MISTAKES.items():
        lines.append(asp.fact("mistake", mistake_id))
        lines.append(asp.fact("mistake_delay", mistake_id, mistake.delay_cost))
    lines.append(asp.fact("initial_warmth", INITIAL_WARMTH))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_sound", params.sound),
            asp.fact("chosen_mistake", params.mistake),
            asp.fact("chosen_delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _pick_child(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool), gender


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a marriage feast, Diller's tortilla, and a sound-effect misunderstanding."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--mistake", choices=MISTAKES)
    ap.add_argument("--adult", choices=ADULT_TYPES)
    ap.add_argument("--delay", type=int, choices=list(range(0, MAX_DELAY + 1)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sound and args.mistake and not valid_combo(args.sound, args.mistake):
        raise StoryError(explain_rejection(args.sound, args.mistake))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.sound is None or combo[1] == args.sound)
        and (args.mistake is None or combo[2] == args.mistake)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, sound_id, mistake_id = rng.choice(sorted(combos))
    child_name, child_gender = _pick_child(rng)
    adult = args.adult or rng.choice(ADULT_TYPES)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, MAX_DELAY)
    return StoryParams(
        setting=setting_id,
        sound=sound_id,
        mistake=mistake_id,
        child_name=child_name,
        child_gender=child_gender,
        adult=adult,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.sound not in SOUNDS:
        raise StoryError(f"(Unknown sound: {params.sound})")
    if params.mistake not in MISTAKES:
        raise StoryError(f"(Unknown mistake: {params.mistake})")
    if params.adult not in ADULT_TYPES:
        raise StoryError(f"(Unknown adult type: {params.adult})")
    if params.delay not in range(0, MAX_DELAY + 1):
        raise StoryError(f"(Delay must be between 0 and {MAX_DELAY}.)")
    if not valid_combo(params.sound, params.mistake):
        raise StoryError(explain_rejection(params.sound, params.mistake))

    world = tell(
        setting=SETTINGS[params.setting],
        sound=SOUNDS[params.sound],
        mistake=MISTAKES[params.mistake],
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_type=params.adult,
        trait=params.trait,
        delay=params.delay,
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

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid_combos() matches ASP ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke_params = CURATED[0]
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("Generated empty story.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, sound, mistake) combos:\n")
        for setting_id, sound_id, mistake_id in combos:
            print(f"  {setting_id:10} {sound_id:12} {mistake_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.child_name}: {p.sound} -> {p.mistake} ({p.setting}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
