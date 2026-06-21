#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/camouflage_hand_pl_cautionary_humor_inner_monologue.py
==================================================================================

A standalone storyworld about a boastful child trying to use camouflage to sneak
past a temple goose and reach a shining prize. The world is small and highly
constrained: camouflage only works when its color matches the hiding place, and
some disguises are so itchy or silly that the world refuses them. The story is
told in a child-facing, myth-flavored voice with caution, humor, and bits of
inner monologue that come from simulated state.

Run it
------
    python storyworlds/worlds/gpt-5.4/camouflage_hand_pl_cautionary_humor_inner_monologue.py
    python storyworlds/worlds/gpt-5.4/camouflage_hand_pl_cautionary_humor_inner_monologue.py --place reeds --prize moon_pear
    python storyworlds/worlds/gpt-5.4/camouflage_hand_pl_cautionary_humor_inner_monologue.py --guise flour
    python storyworlds/worlds/gpt-5.4/camouflage_hand_pl_cautionary_humor_inner_monologue.py --all
    python storyworlds/worlds/gpt-5.4/camouflage_hand_pl_cautionary_humor_inner_monologue.py --qa --json
    python storyworlds/worlds/gpt-5.4/camouflage_hand_pl_cautionary_humor_inner_monologue.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "goose_hen"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)
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
    phrase: str
    color: str
    texture: str
    hiding_spot: str
    footfall: str
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
class Prize:
    id: str
    label: str
    phrase: str
    place_ids: set[str]
    glow: str
    moral_need: str
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
class Guise:
    id: str
    label: str
    phrase: str
    color: str
    smell: str
    itchy: bool
    silly: bool
    sense: int
    splash: str
    thought: str
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
class Guardian:
    id: str
    label: str
    phrase: str
    sound: str
    nose: str
    kind: str = "goose_hen"
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
class Gift:
    id: str
    label: str
    phrase: str
    use: str
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


def _r_spotted(world: World) -> list[str]:
    hero = world.get("hero")
    guardian = world.get("guardian")
    if hero.meters["moving"] < THRESHOLD:
        return []
    sig = ("spotted",)
    if sig in world.fired:
        return []
    if hero.meters["blend"] >= THRESHOLD and hero.meters["itch"] < THRESHOLD:
        return []
    world.fired.add(sig)
    hero.memes["alarm"] += 1
    guardian.memes["notice"] += 1
    world.facts["spotted"] = True
    return ["__spotted__"]


def _r_drop_prize(world: World) -> list[str]:
    hero = world.get("hero")
    prize = world.get("prize")
    if hero.memes["alarm"] < THRESHOLD:
        return []
    sig = ("drop",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["holding"] = 0.0
    prize.meters["safe"] += 1
    hero.memes["embarrassed"] += 1
    return ["__drop__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="spotted", tag="social", apply=_r_spotted),
    Rule(name="drop_prize", tag="physical", apply=_r_drop_prize),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def camouflage_works(place: Place, guise: Guise) -> bool:
    return place.color == guise.color


def sensible_guises() -> list[Guise]:
    return [g for g in GUISES.values() if g.sense >= SENSE_MIN and not g.silly]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for prize_id, prize in PRIZES.items():
            if place_id not in prize.place_ids:
                continue
            for guise_id, guise in GUISES.items():
                if guise.sense >= SENSE_MIN and not guise.silly:
                    combos.append((place_id, prize_id, guise_id))
    return combos


def predict_sneak(place: Place, guise: Guise) -> dict:
    works = camouflage_works(place, guise)
    itchy = guise.itchy
    return {
        "blend": 1 if works else 0,
        "itch": 1 if itchy else 0,
        "spotted": (not works) or itchy,
    }


def introduce(world: World, hero: Entity, elder: Entity, prize: Prize) -> None:
    world.say(
        f"In the old days, when temple ponds still listened and fig leaves remembered names, "
        f"there lived a little {hero.type} named {hero.id}."
    )
    world.say(
        f"{hero.id} loved bright wonders, and most of all {hero.pronoun()} longed for {prize.phrase}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had been told that {prize.moral_need}, not from greedy little fingers."
    )
    world.say(
        f"Still, a warm thought hopped inside {hero.pronoun('possessive')} head: "
        f'"If I can just get close enough, perhaps nobody will notice."'
    )
    world.say(
        f"Beside {hero.pronoun('object')} walked {hero.pronoun('possessive')} {elder.label_word}, "
        f"who knew how quickly a clever plan can turn into a muddy one."
    )


def approach(world: World, hero: Entity, elder: Entity, place: Place, guardian: Guardian, prize: Prize) -> None:
    world.say(
        f"One silver morning they came to {place.phrase}, where {prize.phrase} hung above {place.hiding_spot}."
    )
    world.say(
        f"There too stood {guardian.phrase}, keeper of that place, with {guardian.nose} and a neck like a question mark."
    )
    world.say(
        f'{elder.label_word.capitalize()} said, "That bird guards what is not yours. If you want a closer look, ask first."'
    )
    hero.memes["tempted"] += 1


def mix_guise(world: World, hero: Entity, guise: Guise) -> None:
    hero.meters["coated"] += 1
    if guise.itchy:
        hero.meters["itch"] += 1
    if guise.silly:
        hero.memes["ridiculous"] += 1
    world.say(
        f"But {hero.id} had already begun smearing on {guise.phrase}. "
        f"It was meant for camouflage."
    )
    world.say(
        f"The paste went {guise.splash} in {hero.pronoun('possessive')} palm -- hand-pl! -- "
        f"and left {hero.pronoun('object')} smelling of {guise.smell}."
    )
    world.say(
        f'Inside, {hero.pronoun()} thought, "{guise.thought}"'
    )


def warn(world: World, elder: Entity, hero: Entity, place: Place, guise: Guise, guardian: Guardian) -> None:
    pred = predict_sneak(place, guise)
    world.facts["predicted_spotted"] = pred["spotted"]
    world.facts["predicted_blend"] = pred["blend"]
    world.facts["predicted_itch"] = pred["itch"]
    if pred["spotted"]:
        reason_bits = []
        if not pred["blend"]:
            reason_bits.append(f"the {guise.label} does not match the {place.texture}")
        if pred["itch"]:
            reason_bits.append("itching makes still feet forget to stay still")
        reason = " and ".join(reason_bits)
        world.say(
            f'{elder.label_word.capitalize()} watched once and knew the trouble already. '
            f'"Little one, {reason}. {guardian.label.capitalize()} will hear or smell you before you reach the branch."'
        )
    else:
        world.say(
            f'{elder.label_word.capitalize()} narrowed {elder.pronoun("possessive")} eyes. '
            f'"Even good camouflage is not permission. A hidden hand can still do a wrong thing."'
        )


def defy(world: World, hero: Entity, place: Place, guise: Guise) -> None:
    hero.memes["defiance"] += 1
    hero.meters["moving"] += 1
    if camouflage_works(place, guise):
        hero.meters["blend"] += 1
    world.say(
        f"{hero.id} crouched low and padded toward {place.hiding_spot}, trying to make {place.footfall}."
    )
    if hero.meters["blend"] >= THRESHOLD:
        world.say(
            f'For a breath, {hero.pronoun()} almost vanished into the {place.texture}, and a proud thought puffed up: '
            f'"Look at me. I am as secret as moss."'
        )
    else:
        world.say(
            f'The very first glance at {hero.pronoun("possessive")} reflection in the pond should have helped, '
            f"but pride is a noisy drum."
        )
    propagate(world, narrate=False)


def near_prize(world: World, hero: Entity, prize_ent: Entity, prize: Prize) -> None:
    if world.facts.get("spotted"):
        return
    hero.meters["holding"] += 1
    prize_ent.meters["safe"] = 0.0
    world.say(
        f"{hero.id} reached the branch and gave {prize.phrase} a tiny twist."
    )
    world.say(
        f'At once another thought jumped in: "Oh. I have a thing that was never mine."'
    )


def comic_disaster(world: World, hero: Entity, guardian: Guardian, prize: Prize) -> None:
    if not world.facts.get("spotted"):
        return
    world.say(
        f"Then {guardian.label} cried {guardian.sound}, and the whole garden seemed to point one long feather at {hero.id}."
    )
    if hero.meters["itch"] >= THRESHOLD:
        world.say(
            f"{hero.pronoun().capitalize()} tried to stand still, but the itch ran up {hero.pronoun('possessive')} nose. "
            f"A sneeze burst out so grand it startled even the dragonflies."
        )
    else:
        world.say(
            f"{hero.pronoun().capitalize()} froze, but the disguise shone wrong against the leaves, like a dumpling trying to be a reed."
        )
    world.say(
        f"In a flurry of shame and flapping, {hero.pronoun()} dropped the prize and sat down right in the mud."
    )


def confess(world: World, hero: Entity, elder: Entity, prize: Prize) -> None:
    hero.memes["remorse"] += 1
    world.say(
        f'{hero.id} looked at the ground. "I wanted {prize.label} because it shone," {hero.pronoun()} admitted.'
    )
    world.say(
        f'Inside, the brave-sounding plan had shrunk to one small truth: "I should have asked."'
    )
    world.say(
        f'{elder.label_word.capitalize()} did not laugh first. {elder.pronoun().capitalize()} lifted {hero.pronoun("possessive")} chin and said, '
        f'"A quick hand can grab. A wiser hand can wait."'
    )


def restore(world: World, elder: Entity, guardian: Guardian, gift: Gift, prize: Prize) -> None:
    world.say(
        f"{elder.label_word.capitalize()} bowed to {guardian.label} and spoke kindly until the feathers settled."
    )
    world.say(
        f"Then {elder.pronoun()} was given {gift.phrase}, so the little one could {gift.use} without stealing."
    )
    world.say(
        f"{guardian.label.capitalize()} kept the true {prize.label}, and peace stayed where it belonged."
    )


def ending(world: World, hero: Entity, elder: Entity, place: Place, gift: Gift) -> None:
    hero.memes["joy"] += 1
    hero.memes["lesson"] += 1
    hero.memes["alarm"] = 0.0
    world.say(
        f"By sunset, {hero.id} stood beside {elder.label_word} with {gift.phrase} in {hero.pronoun('possessive')} clean paws."
    )
    world.say(
        f"{hero.pronoun().capitalize()} peered from {place.hiding_spot} no more. {hero.pronoun().capitalize()} looked openly, laughed at the memory of the hand-pl splat, and stayed where asking was easy."
    )
    world.say(
        f"And that is why, the old storytellers say, clever feet must walk behind honest hearts, or else even camouflage will lead them straight into a goose."
    )


def tell(
    place: Place,
    prize: Prize,
    guise: Guise,
    guardian_cfg: Guardian,
    gift: Gift,
    hero_name: str = "Piko",
    hero_type: str = "fox",
    elder_type: str = "mother",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label="the elder", role="elder"))
    guardian = world.add(Entity(id="guardian", kind="character", type=guardian_cfg.kind, label=guardian_cfg.label, role="guardian"))
    prize_ent = world.add(Entity(id="prize", kind="thing", type="prize", label=prize.label))
    prize_ent.meters["safe"] = 1.0
    world.facts.update(
        place=place,
        prize_cfg=prize,
        guise=guise,
        guardian_cfg=guardian_cfg,
        gift=gift,
        spotted=False,
    )

    introduce(world, hero, elder, prize)
    world.para()
    approach(world, hero, elder, place, guardian_cfg, prize)
    mix_guise(world, hero, guise)
    warn(world, elder, hero, place, guise, guardian_cfg)
    world.para()
    defy(world, hero, place, guise)
    near_prize(world, hero, prize_ent, prize)
    propagate(world, narrate=False)
    comic_disaster(world, hero, guardian_cfg, prize)
    world.para()
    confess(world, hero, elder, prize)
    restore(world, elder, guardian_cfg, gift, prize)
    ending(world, hero, elder, place, gift)

    outcome = "spotted" if world.facts.get("spotted") else "unspotted"
    world.facts.update(
        hero=hero,
        elder=elder,
        guardian=guardian,
        prize=prize_ent,
        outcome=outcome,
        took_prize=hero.meters["holding"] >= THRESHOLD,
        learned=hero.memes["lesson"] >= THRESHOLD,
        itchy=guise.itchy,
        matched=camouflage_works(place, guise),
    )
    return world


PLACES = {
    "reeds": Place(
        id="reeds",
        label="reed bank",
        phrase="the reed bank of Moon-Pond",
        color="green",
        texture="green reeds",
        hiding_spot="the tallest reeds",
        footfall="the smallest whisper of steps",
        tags={"pond", "reeds", "green"},
    ),
    "moss": Place(
        id="moss",
        label="moss stair",
        phrase="the moss stairs below the fig shrine",
        color="green",
        texture="soft moss",
        hiding_spot="the mossy steps",
        footfall="a priest's quiet breath",
        tags={"moss", "green", "shrine"},
    ),
    "clay": Place(
        id="clay",
        label="clay bank",
        phrase="the red clay bank behind the shrine wall",
        color="red",
        texture="red clay",
        hiding_spot="the warm clay jars",
        footfall="sand settling in a bowl",
        tags={"clay", "red", "wall"},
    ),
}

PRIZES = {
    "moon_pear": Prize(
        id="moon_pear",
        label="moon pear",
        phrase="a moon pear",
        place_ids={"reeds", "moss"},
        glow="pale as a small moon",
        moral_need="shining things ripen for blessing and sharing",
        tags={"pear", "fruit"},
    ),
    "sun_fig": Prize(
        id="sun_fig",
        label="sun fig",
        phrase="a sun fig",
        place_ids={"moss", "clay"},
        glow="gold in the leaves",
        moral_need="holy fruit is given by keepers",
        tags={"fig", "fruit"},
    ),
}

GUISES = {
    "moss_paste": Guise(
        id="moss_paste",
        label="moss paste",
        phrase="cool moss paste",
        color="green",
        smell="wet leaves",
        itchy=False,
        silly=False,
        sense=3,
        splash="splut",
        thought="If I am green enough, I will slide right past those goose eyes.",
        tags={"camouflage", "moss"},
    ),
    "clay_smear": Guise(
        id="clay_smear",
        label="clay smear",
        phrase="red clay smear",
        color="red",
        smell="warm earth",
        itchy=False,
        silly=False,
        sense=3,
        splash="plop",
        thought="No bird will notice one more patch of honest clay.",
        tags={"camouflage", "clay"},
    ),
    "pollen_dust": Guise(
        id="pollen_dust",
        label="pollen dust",
        phrase="gold pollen dust",
        color="gold",
        smell="flowers and sneezes",
        itchy=True,
        silly=False,
        sense=2,
        splash="puff",
        thought="I look glorious. Perhaps glorious is close enough to invisible.",
        tags={"camouflage", "pollen"},
    ),
    "flour": Guise(
        id="flour",
        label="flour coat",
        phrase="kitchen flour",
        color="white",
        smell="dumplings",
        itchy=False,
        silly=True,
        sense=1,
        splash="foof",
        thought="Surely a goose will believe I am a cloud with legs.",
        tags={"flour", "silly"},
    ),
}

GUARDIANS = {
    "temple_goose": Guardian(
        id="temple_goose",
        label="the temple goose",
        phrase="the temple goose",
        sound='"Honk-hraaa!"',
        nose="sharp temple-bird nostrils",
        kind="goose_hen",
        tags={"goose", "guardian"},
    ),
    "bronze_goose": Guardian(
        id="bronze_goose",
        label="the bronze-neck goose",
        phrase="the bronze-neck goose",
        sound='"Hronk!"',
        nose="a nose that could smell mischief under rain",
        kind="goose_hen",
        tags={"goose", "guardian"},
    ),
}

GIFTS = {
    "viewing_stool": Gift(
        id="viewing_stool",
        label="viewing stool",
        phrase="a little viewing stool",
        use="stand at a proper distance and admire the fruit",
        tags={"stool", "asking"},
    ),
    "blessing_bowl": Gift(
        id="blessing_bowl",
        label="blessing bowl",
        phrase="a small blessing bowl",
        use="receive fruit properly when the keeper chose to share",
        tags={"bowl", "asking"},
    ),
}

HERO_NAMES = ["Piko", "Tavi", "Miri", "Nilo", "Suri", "Keta", "Omi", "Riku"]
HERO_TYPES = ["fox", "raccoon", "otter"]
ELDER_TYPES = ["mother", "father"]


@dataclass
class StoryParams:
    place: str
    prize: str
    guise: str
    guardian: str
    gift: str
    hero_name: str
    hero_type: str
    elder_type: str
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
    "camouflage": [
        (
            "What is camouflage?",
            "Camouflage is a way of blending in with the colors and shapes around you so you are harder to notice. Animals use it to hide, but hiding does not make a wrong choice right."
        )
    ],
    "goose": [
        (
            "Why can a goose notice someone quickly?",
            "A goose can be very alert, with good eyes, loud warning sounds, and a sharp sense for movement. That is why sneaking past one is a poor plan."
        )
    ],
    "moss": [
        (
            "What is moss?",
            "Moss is a soft green plant that grows in damp places on stones and ground. It can make something look green, but it cannot make a child invisible."
        )
    ],
    "clay": [
        (
            "What is clay?",
            "Clay is a kind of soft earth that can be red or brown and sticky when wet. People can shape it, but smearing it on yourself can be messy."
        )
    ],
    "pollen": [
        (
            "Why can pollen make someone sneeze?",
            "Pollen is tiny dust from flowers, and it can tickle a nose. When a nose is tickled too much, a sneeze can burst out before you are ready."
        )
    ],
    "asking": [
        (
            "Why should you ask before taking something that is not yours?",
            "You should ask because other people's things, and special shared things, deserve respect. Asking keeps trust strong and stops a grabby moment from turning into trouble."
        )
    ],
}

KNOWLEDGE_ORDER = ["camouflage", "goose", "moss", "clay", "pollen", "asking"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    prize = f["prize_cfg"]
    guise = f["guise"]
    return [
        f'Write a short myth-like cautionary story for a 3-to-5-year-old that includes the word "camouflage" and the odd sound word "hand-pl".',
        f"Tell a funny, child-facing myth in which a small animal tries {guise.label} to sneak through {place.label} and reach {prize.phrase}, but learns that asking is wiser than sneaking.",
        f"Write a gentle story with inner monologue where a boastful little creature thinks a hidden plan will work, gets embarrassed, and ends with an honest lesson.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    place = f["place"]
    prize = f["prize_cfg"]
    guise = f["guise"]
    guardian = f["guardian_cfg"]
    gift = f["gift"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a little {hero.type}, and {hero.pronoun('possessive')} {elder.label_word}. They went to {place.phrase}, where {guardian.label} guarded {prize.phrase}."
        ),
        (
            f"Why did {hero.label} use camouflage?",
            f"{hero.label} wanted to get close to {prize.phrase} without being stopped. {hero.pronoun().capitalize()} hoped the disguise would hide {hero.pronoun('object')} from {guardian.label}."
        ),
    ]
    if f.get("matched"):
        qa.append(
            (
                f"Did the disguise match the place?",
                f"Yes. The {guise.label} matched the color of the {place.texture}, so for a moment {hero.label} really did blend in. But matching colors was not enough to make sneaking a good choice."
            )
        )
    else:
        qa.append(
            (
                f"Why was the disguise easy to notice?",
                f"The {guise.label} did not match the {place.texture}, so it looked wrong right away. The hiding plan was weak before {hero.label} even took a second step."
            )
        )
    if f.get("itchy"):
        qa.append(
            (
                f"Why did the sneaking plan fail so quickly?",
                f"It failed because the disguise was itchy as well as sneaky, and {hero.label} could not stay still. The tickle led to a big sneeze, which gave the hiding place away."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {guardian.label} noticed {hero.label}?",
                f"{guardian.label.capitalize()} gave a loud cry, and {hero.label} panicked and dropped the prize. The funny part was that the proud secret plan ended with mud and shame instead of triumph."
            )
        )
    qa.append(
        (
            f"What did {hero.label} learn?",
            f"{hero.label} learned that hiding does not turn taking into something right. {elder.label_word.capitalize()} helped {hero.pronoun('object')} see that asking first is wiser than grabbing in secret."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended peacefully, with {gift.phrase} letting {hero.label} enjoy the wonder in the proper way. The ending image shows that open hands and honest words changed the whole day."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"camouflage", "goose", "asking"}
    guise = f["guise"]
    if "moss" in guise.tags:
        tags.add("moss")
    if "clay" in guise.tags:
        tags.add("clay")
    if "pollen" in guise.tags:
        tags.add("pollen")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="reeds",
        prize="moon_pear",
        guise="moss_paste",
        guardian="temple_goose",
        gift="viewing_stool",
        hero_name="Piko",
        hero_type="fox",
        elder_type="mother",
    ),
    StoryParams(
        place="clay",
        prize="sun_fig",
        guise="clay_smear",
        guardian="bronze_goose",
        gift="blessing_bowl",
        hero_name="Tavi",
        hero_type="raccoon",
        elder_type="father",
    ),
    StoryParams(
        place="moss",
        prize="moon_pear",
        guise="pollen_dust",
        guardian="temple_goose",
        gift="viewing_stool",
        hero_name="Miri",
        hero_type="otter",
        elder_type="mother",
    ),
]


def explain_rejection(place: Place, prize: Prize, guise: Guise) -> str:
    if place.id not in prize.place_ids:
        return (
            f"(No story: {prize.phrase} does not belong at {place.label} in this little myth, so the chase has no home.)"
        )
    if guise.sense < SENSE_MIN or guise.silly:
        return (
            f"(No story: {guise.label} is too silly to be a reasonable plan here. The world knows it exists, but refuses to build a whole myth around it.)"
        )
    return "(No story: this combination does not fit the world's rules.)"


ASP_RULES = r"""
valid(P, Pr, G) :- place(P), prize(Pr), guise(G), grows_at(Pr, P), sense(G, S), sense_min(M), S >= M, not silly(G).

match(P, G) :- place_color(P, C), guise_color(G, C).
spotted(P, G) :- valid(P, _, G), not match(P, G).
spotted(P, G) :- valid(P, _, G), itchy(G).

outcome(P, G, spotted) :- spotted(P, G).
outcome(P, G, unspotted) :- valid(P, _, G), not spotted(P, G).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_color", pid, place.color))
    for prid, prize in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        for pid in sorted(prize.place_ids):
            lines.append(asp.fact("grows_at", prid, pid))
    for gid, guise in GUISES.items():
        lines.append(asp.fact("guise", gid))
        lines.append(asp.fact("guise_color", gid, guise.color))
        lines.append(asp.fact("sense", gid, guise.sense))
        if guise.itchy:
            lines.append(asp.fact("itchy", gid))
        if guise.silly:
            lines.append(asp.fact("silly", gid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_guise", params.guise),
        ]
    )
    rules = r"""
chosen_valid :- valid(P, Pr, G), chosen_place(P), chosen_guise(G), prize(Pr).
chosen_spotted :- spotted(P, G), chosen_place(P), chosen_guise(G).
chosen_outcome(spotted) :- chosen_valid, chosen_spotted.
chosen_outcome(unspotted) :- chosen_valid, not chosen_spotted.
"""
    model = asp.one_model(f"{asp_facts()}\n{ASP_RULES}\n{scenario}\n{rules}\n#show chosen_outcome/1.\n")
    out = asp.atoms(model, "chosen_outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    place = PLACES[params.place]
    guise = GUISES[params.guise]
    return "spotted" if ((not camouflage_works(place, guise)) or guise.itchy) else "unspotted"


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
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
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
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: camouflage, a temple goose, and a lesson about asking first."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--guise", choices=GUISES)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--elder-type", choices=ELDER_TYPES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.prize and args.guise:
        place = PLACES[args.place]
        prize = PRIZES[args.prize]
        guise = GUISES[args.guise]
        if not (args.place in prize.place_ids and guise.sense >= SENSE_MIN and not guise.silly):
            raise StoryError(explain_rejection(place, prize, guise))
    if args.guise:
        guise = GUISES[args.guise]
        if guise.sense < SENSE_MIN or guise.silly:
            place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
            prize = PRIZES[args.prize] if args.prize else next(iter(PRIZES.values()))
            raise StoryError(explain_rejection(place, prize, guise))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.prize is None or combo[1] == args.prize)
        and (args.guise is None or combo[2] == args.guise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, prize_id, guise_id = rng.choice(sorted(combos))
    guardian = args.guardian or rng.choice(sorted(GUARDIANS))
    gift = args.gift or rng.choice(sorted(GIFTS))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    elder_type = args.elder_type or rng.choice(ELDER_TYPES)
    hero_name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(
        place=place_id,
        prize=prize_id,
        guise=guise_id,
        guardian=guardian,
        gift=gift,
        hero_name=hero_name,
        hero_type=hero_type,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        prize = PRIZES[params.prize]
        guise = GUISES[params.guise]
        guardian = GUARDIANS[params.guardian]
        gift = GIFTS[params.gift]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if place.id not in prize.place_ids or guise.sense < SENSE_MIN or guise.silly:
        raise StoryError(explain_rejection(place, prize, guise))

    world = tell(
        place=place,
        prize=prize,
        guise=guise,
        guardian_cfg=guardian,
        gift=gift,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        elder_type=params.elder_type,
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
        print(asp_program("", "#show valid/3.\n#show outcome/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, prize, guise) combos:\n")
        for place, prize, guise in combos:
            print(f"  {place:6} {prize:10} {guise}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name}: {p.guise} at {p.place} for {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
