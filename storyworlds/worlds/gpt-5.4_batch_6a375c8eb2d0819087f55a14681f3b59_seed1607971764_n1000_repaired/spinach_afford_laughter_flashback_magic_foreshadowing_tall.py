#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/spinach_afford_laughter_flashback_magic_foreshadowing_tall.py
==========================================================================================

A standalone story world for a tall-tale domain about magical spinach, an
unreachable town problem, and a child who helps when ordinary tools cost too
much. The world uses explicit state: physical meters like height and repair, and
emotional memes like worry, hope, pride, and laughter.

Seed ingredients rebuilt here:
- word: spinach
- word: afford
- word: laughter
- feature: Flashback
- feature: Magic
- feature: Foreshadowing
- style: Tall Tale

Run it
------
    python storyworlds/worlds/gpt-5.4/spinach_afford_laughter_flashback_magic_foreshadowing_tall.py
    python storyworlds/worlds/gpt-5.4/spinach_afford_laughter_flashback_magic_foreshadowing_tall.py --target bell --spinach soup
    python storyworlds/worlds/gpt-5.4/spinach_afford_laughter_flashback_magic_foreshadowing_tall.py --target moon_kite --spinach biscuit
    python storyworlds/worlds/gpt-5.4/spinach_afford_laughter_flashback_magic_foreshadowing_tall.py --all --qa
    python storyworlds/worlds/gpt-5.4/spinach_afford_laughter_flashback_magic_foreshadowing_tall.py --verify
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
BASE_REACH = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "aunt"}
        male = {"boy", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
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
class Setting:
    id: str
    place: str
    boast: str
    sky_sign: str
    patch_name: str
    closing_image: str
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
class Target:
    id: str
    label: str
    the: str
    need: int
    problem: str
    opening_need: str
    fix_text: str
    ending: str
    can_afford: str
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
class SpinachMagic:
    id: str
    label: str
    phrase: str
    power: int
    swirl: str
    bite_text: str
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
class Charm:
    id: str
    label: str
    boost: int
    cast_text: str
    memory_line: str
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


def _r_tall_from_spinach(world: World) -> list[str]:
    hero = world.get("hero")
    spinach = world.get("spinach")
    if spinach.meters["eaten"] < THRESHOLD:
        return []
    sig = ("tall_from_spinach",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["height"] += spinach.attrs["power"]
    hero.memes["wonder"] += 1
    return ["__grow__"]


def _r_tall_from_charm(world: World) -> list[str]:
    hero = world.get("hero")
    elder = world.get("elder")
    if elder.meters["cast"] < THRESHOLD:
        return []
    sig = ("tall_from_charm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["height"] += elder.attrs["boost"]
    hero.memes["hope"] += 1
    return ["__shine__"]


def _r_reach_and_fix(world: World) -> list[str]:
    hero = world.get("hero")
    target = world.get("target")
    if hero.meters["trying"] < THRESHOLD:
        return []
    if hero.meters["height"] < target.attrs["need"]:
        return []
    sig = ("reach_and_fix",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    target.meters["fixed"] += 1
    world.get("town").memes["relief"] += 1
    hero.memes["pride"] += 1
    return ["__fixed__"]


def _r_grand_laughter(world: World) -> list[str]:
    target = world.get("target")
    hero = world.get("hero")
    if target.meters["fixed"] < THRESHOLD:
        return []
    if hero.meters["height"] < target.attrs["need"] + 2:
        return []
    sig = ("grand_laughter",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("town").memes["laughter"] += 2
    hero.memes["joy"] += 1
    return ["__grand__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="tall_from_spinach", tag="magic", apply=_r_tall_from_spinach),
    Rule(name="tall_from_charm", tag="magic", apply=_r_tall_from_charm),
    Rule(name="reach_and_fix", tag="physical", apply=_r_reach_and_fix),
    Rule(name="grand_laughter", tag="social", apply=_r_grand_laughter),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


def total_reach(spinach: SpinachMagic, charm: Charm) -> int:
    return BASE_REACH + spinach.power + charm.boost


def can_solve(target: Target, spinach: SpinachMagic, charm: Charm) -> bool:
    return total_reach(spinach, charm) >= target.need


def grandeur(target: Target, spinach: SpinachMagic, charm: Charm) -> str:
    return "legendary" if total_reach(spinach, charm) >= target.need + 2 else "steady"


def predict_fix(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    sim.get("spinach").meters["eaten"] += 1
    sim.get("elder").meters["cast"] += 1
    hero.meters["trying"] += 1
    propagate(sim, narrate=False)
    return {
        "height": int(sim.get("hero").meters["height"]),
        "fixed": sim.get("target").meters["fixed"] >= THRESHOLD,
        "grand": sim.get("town").memes["laughter"] >= THRESHOLD,
    }


def foreshadow(world: World, hero: Entity, target: Target) -> None:
    world.say(
        f"In {world.setting.place}, things grew so tall that fence posts had to duck for geese. "
        f"That morning, {world.setting.sky_sign}, as if the sky already knew {target.opening_need}."
    )
    world.say(
        f"{hero.id} could feel the day leaning toward something big, the way a pond leans toward a skipped stone."
    )


def introduce(world: World, hero: Entity, elder: Entity, target: Target) -> None:
    world.say(
        f"{hero.id} lived beside {world.setting.patch_name}, where the spinach leaves were broad enough to shade a calf at noon."
    )
    world.say(
        f"By breakfast, the whole town was talking about {target.problem}, and folks kept sighing that they could not afford {target.can_afford}."
    )
    hero.memes["care"] += 1
    world.get("town").memes["worry"] += 1


def flashback(world: World, elder: Entity, charm: Charm) -> None:
    elder.memes["memory"] += 1
    world.say(
        f"{elder.label_word.capitalize()} rubbed a thumb over the old wooden spoon on the mantle and slipped into a flashback. "
        f'"When I was small," {elder.pronoun()} said, "{charm.memory_line}"'
    )
    world.say(
        "The memory seemed to shine right into the room, as clear as if yesterday had put on clean boots and walked back in."
    )


def plan(world: World, hero: Entity, elder: Entity, spinach: SpinachMagic, charm: Charm, target: Target) -> None:
    pred = predict_fix(world)
    world.facts["predicted_height"] = pred["height"]
    world.facts["predicted_fixed"] = pred["fixed"]
    world.facts["predicted_grand"] = pred["grand"]
    world.say(
        f'{hero.id} looked from {target.the} to the spinach patch. "If money cannot buy a tall enough tool," {hero.pronoun()} said, '
        f'"maybe supper can."'
    )
    world.say(
        f"{elder.label_word.capitalize()} nodded and set out {spinach.phrase}. {spinach.swirl} "
        f"{charm.cast_text}"
    )


def eat_spinach(world: World, hero: Entity, spinach: SpinachMagic) -> None:
    world.get("spinach").meters["eaten"] += 1
    hero.memes["bravery"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} took {spinach.bite_text}. The spinach tasted green and bold, like summer had learned to sing."
    )
    world.say(
        f"At once, {hero.pronoun('possessive')} shadow stretched over the yard, and {hero.pronoun('possessive')} boots seemed to remember taller roads."
    )


def cast_charm(world: World, elder: Entity, charm: Charm) -> None:
    elder.meters["cast"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {elder.label_word} touched the spoon to the kettle and whispered the {charm.label}. "
        f"The kitchen window flashed as if a star had winked on purpose."
    )


def attempt_fix(world: World, hero: Entity, target: Target) -> None:
    hero.meters["trying"] += 1
    propagate(world, narrate=False)
    hero_height = int(world.get("hero").meters["height"])
    world.say(
        f"Up rose {hero.id} until {hero.pronoun('possessive')} cap brushed the weather and {hero.pronoun()} could look a cloud straight in its puffy eye."
    )
    if world.get("target").meters["fixed"] >= THRESHOLD:
        world.say(
            f"{hero.pronoun().capitalize()} reached {target.the} and {target.fix_text}."
        )
    else:
        world.say(
            f"{hero.pronoun().capitalize()} stretched and stretched, but even at {hero_height} tall-tale feet, {target.the} stayed just out of reach."
        )


def celebrate(world: World, hero: Entity, elder: Entity, target: Target) -> None:
    town = world.get("town")
    if town.memes["laughter"] >= THRESHOLD:
        world.say(
            f"The town square burst into laughter so warm and loud that sparrows popped out of the eaves to listen. "
            f"Children laughed, grown-ups laughed, and even the mayor laughed until tears shone in the corners of {world.get('mayor').pronoun('possessive')} eyes."
        )
    else:
        world.say(
            "A relieved cheer rolled down the street, softer than thunder but steadier than a drum."
        )
    world.say(
        f"{elder.label_word.capitalize()} hugged {hero.id}'s knee -- it was the only part within easy reach just then -- and grinned."
    )
    world.say(
        f"By sundown, {target.ending} {world.setting.closing_image}"
    )


def come_back_down(world: World, hero: Entity) -> None:
    hero.meters["height"] = BASE_REACH
    hero.memes["calm"] += 1
    world.say(
        f"By bedtime, the magic had settled kindly back into {hero.id}'s bones, leaving {hero.pronoun('object')} ordinary-sized again but not ordinary-hearted."
    )


SETTINGS = {
    "prairie": Setting(
        id="prairie",
        place="the whistling prairie town of Mile-High Mesa",
        boast="where fence posts had to duck for geese",
        sky_sign="the clouds hung low like silver hats on giant heads",
        patch_name="Grandma's back-lot spinach patch",
        closing_image="while the sunset lay across the prairie like a rolled-out red quilt.",
        tags={"prairie", "tall_tale"},
    ),
    "river": Setting(
        id="river",
        place="the river town of Hucklebend",
        boast="where catfish told stories longer than church sermons",
        sky_sign="the river flashed bright as a mirror trying to signal somebody",
        patch_name="the levee-side spinach rows",
        closing_image="while river water slapped the docks in a happy rhythm.",
        tags={"river", "tall_tale"},
    ),
    "hills": Setting(
        id="hills",
        place="the hill country hamlet of Big Briar",
        boast="where even the scarecrows cast afternoon shadows before breakfast",
        sky_sign="the ridgeline looked as if it were standing on tiptoe",
        patch_name="Auntie's hillside spinach garden",
        closing_image="while the hills turned purple and the first stars blinked awake.",
        tags={"hills", "tall_tale"},
    ),
}

TARGETS = {
    "bell": Target(
        id="bell",
        label="meeting bell",
        the="the meeting bell",
        need=4,
        problem="the meeting bell had jammed high in the tower before market day",
        opening_need="the bell would need a brave hand before noon",
        fix_text="gave it one mighty tug until it sang across three counties",
        ending="the bell rang bright enough to call farmers, bakers, and sleepy mules all at once,",
        can_afford="a new iron ladder",
        tags={"bell", "market"},
    ),
    "banner": Target(
        id="banner",
        label="parade banner",
        the="the parade banner",
        need=5,
        problem="the parade banner had blown loose and knotted itself around the tallest pole in town",
        opening_need="the parade banner would not come down without a miracle or a very long reach",
        fix_text="untied the knot and snapped the banner free so it streamed like a river of color",
        ending="the parade marched under a banner as straight as a promise,",
        can_afford="a town crane",
        tags={"banner", "parade"},
    ),
    "moon_kite": Target(
        id="moon_kite",
        label="moon kite",
        the="the moon kite",
        need=6,
        problem="the baker's moon kite had snagged on the courthouse weathercock the night before the fair",
        opening_need="something near the moon kite was going to ask a very tall favor",
        fix_text="lifted the kite loose from the weathercock and sent it swooping back to the baker's hands",
        ending="the fair lanterns bobbed beneath a kite that sailed smooth as moonlight,",
        can_afford="a brass sky-hook",
        tags={"kite", "fair"},
    ),
}

SPINACH = {
    "biscuit": SpinachMagic(
        id="biscuit",
        label="spinach biscuit",
        phrase="a hot spinach biscuit split with butter",
        power=2,
        swirl="The butter ran green-gold over the crust.",
        bite_text="one brave bite of the spinach biscuit",
        tags={"spinach", "biscuit"},
    ),
    "skillet": SpinachMagic(
        id="skillet",
        label="skillet spinach",
        phrase="a smoking pan of skillet spinach",
        power=3,
        swirl="Steam rose from it in twisting fiddle-note curls.",
        bite_text="three forkfuls of the skillet spinach",
        tags={"spinach", "skillet"},
    ),
    "soup": SpinachMagic(
        id="soup",
        label="spinach soup",
        phrase="a bowl of spinach soup with star-shaped noodles",
        power=4,
        swirl="Every noodle spun once before settling down.",
        bite_text="a deep spoonful of the spinach soup",
        tags={"spinach", "soup"},
    ),
}

CHARMS = {
    "hum": Charm(
        id="hum",
        label="porch-step hum",
        boost=1,
        cast_text="As the spoon circled, a porch-step hum slipped from the old boards and joined the steam.",
        memory_line="my mother hummed over spinach, and the porch posts grew so tall they had to bow to passing clouds.",
        tags={"magic", "hum"},
    ),
    "rhyme": Charm(
        id="rhyme",
        label="moon-up rhyme",
        boost=2,
        cast_text="The elder spoke a moon-up rhyme, and the kettle lid danced three small jig steps.",
        memory_line="we whispered a moon-up rhyme over a kettle of spinach, and my brother reached a runaway rooster off the church roof without leaving the yard.",
        tags={"magic", "rhyme"},
    ),
}

ELDERS = {
    "grandmother": {"type": "grandmother", "label": "Grandma"},
    "grandfather": {"type": "grandfather", "label": "Grandpa"},
    "aunt": {"type": "aunt", "label": "Aunt May"},
    "uncle": {"type": "uncle", "label": "Uncle Jed"},
}

GIRL_NAMES = ["Mabel", "June", "Elsie", "Nell", "Dora", "Birdie"]
BOY_NAMES = ["Jasper", "Otis", "Levi", "Clem", "Bo", "Tucker"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for target_id, target in TARGETS.items():
            for spinach_id, spinach in SPINACH.items():
                for charm_id, charm in CHARMS.items():
                    if can_solve(target, spinach, charm):
                        combos.append((setting_id, target_id, spinach_id, charm_id))
    return combos


@dataclass
class StoryParams:
    setting: str = "prairie"
    target: str = "bell"
    spinach: str = "skillet"
    charm: str = "hum"
    hero: str = "Mabel"
    gender: str = "girl"
    elder: str = "grandmother"
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


CURATED = [
    StoryParams(
        setting="prairie",
        target="bell",
        spinach="skillet",
        charm="hum",
        hero="Mabel",
        gender="girl",
        elder="grandmother",
    ),
    StoryParams(
        setting="river",
        target="banner",
        spinach="soup",
        charm="hum",
        hero="Jasper",
        gender="boy",
        elder="grandfather",
    ),
    StoryParams(
        setting="hills",
        target="moon_kite",
        spinach="soup",
        charm="rhyme",
        hero="June",
        gender="girl",
        elder="aunt",
    ),
    StoryParams(
        setting="prairie",
        target="banner",
        spinach="skillet",
        charm="rhyme",
        hero="Otis",
        gender="boy",
        elder="uncle",
    ),
]


def tell(
    setting: Setting,
    target_cfg: Target,
    spinach_cfg: SpinachMagic,
    charm_cfg: Charm,
    hero_name: str = "Mabel",
    gender: str = "girl",
    elder_key: str = "grandmother",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=hero_name, role="hero"))
    elder_def = ELDERS[elder_key]
    elder = world.add(
        Entity(
            id="elder",
            kind="character",
            type=elder_def["type"],
            label=elder_def["label"],
            role="elder",
        )
    )
    world.add(Entity(id="town", type="town", label="the town"))
    mayor_type = "man" if gender == "girl" else "woman"
    world.add(Entity(id="mayor", kind="character", type=mayor_type, label="the mayor", role="mayor"))
    world.add(
        Entity(
            id="spinach",
            type="food",
            label=spinach_cfg.label,
            attrs={"power": spinach_cfg.power},
            tags=set(spinach_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="target",
            type="high_thing",
            label=target_cfg.label,
            attrs={"need": target_cfg.need},
            tags=set(target_cfg.tags),
        )
    )

    hero.meters["height"] = BASE_REACH
    hero.meters["trying"] = 0
    hero.memes["hope"] = 0
    hero.memes["pride"] = 0
    elder.meters["cast"] = 0
    elder.attrs["boost"] = charm_cfg.boost
    world.get("town").memes["worry"] = 0
    world.get("town").memes["laughter"] = 0
    world.get("town").memes["relief"] = 0
    world.get("target").meters["fixed"] = 0
    world.get("spinach").meters["eaten"] = 0

    foreshadow(world, hero, target_cfg)
    introduce(world, hero, elder, target_cfg)

    world.para()
    flashback(world, elder, charm_cfg)
    plan(world, hero, elder, spinach_cfg, charm_cfg, target_cfg)

    world.para()
    eat_spinach(world, hero, spinach_cfg)
    cast_charm(world, elder, charm_cfg)
    attempt_fix(world, hero, target_cfg)

    if world.get("target").meters["fixed"] < THRESHOLD:
        raise StoryError("The chosen spinach and charm do not make a tall enough tall tale.")

    world.para()
    celebrate(world, hero, elder, target_cfg)
    come_back_down(world, hero)

    world.facts.update(
        setting=setting,
        target_cfg=target_cfg,
        spinach_cfg=spinach_cfg,
        charm_cfg=charm_cfg,
        hero=hero,
        elder=elder,
        target=world.get("target"),
        town=world.get("town"),
        outcome=grandeur(target_cfg, spinach_cfg, charm_cfg),
        fixed=world.get("target").meters["fixed"] >= THRESHOLD,
        total_reach=total_reach(spinach_cfg, charm_cfg),
        predicted_fixed=world.facts.get("predicted_fixed", False),
        predicted_grand=world.facts.get("predicted_grand", False),
    )
    return world


KNOWLEDGE = {
    "spinach": [
        (
            "What is spinach?",
            "Spinach is a leafy green vegetable. People cook it or eat it fresh, and it helps make a meal healthy."
        )
    ],
    "magic": [
        (
            "What is magic in a story?",
            "Magic in a story is something impossible in ordinary life that can still change what happens. It lets a tale show wonder in a clear, playful way."
        )
    ],
    "flashback": [
        (
            "What is a flashback?",
            "A flashback is a short memory scene that tells about something from earlier. It helps explain why a character knows what to do now."
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing?",
            "Foreshadowing is an early clue about something important that will happen later. It makes the ending feel prepared instead of sudden."
        )
    ],
    "laughter": [
        (
            "Why do people laugh together when a problem is solved?",
            "People often laugh together when worry lifts and everyone feels safe again. Shared laughter can show relief as well as joy."
        )
    ],
    "afford": [
        (
            "What does afford mean?",
            "Afford means having enough money or means to get something. If a town cannot afford a tool, it does not have enough to buy it."
        )
    ],
    "bell": [
        (
            "Why would a town bell matter?",
            "A town bell can call people together for market, news, or help. If it is stuck, the whole town may miss an important signal."
        )
    ],
    "banner": [
        (
            "Why is a parade banner important?",
            "A parade banner helps mark the start of a celebration and gives everyone something bright to follow. If it gets tangled high up, the parade can feel spoiled."
        )
    ],
    "kite": [
        (
            "Why can a kite get stuck high up?",
            "A kite can snag on a roof, pole, or weather vane when wind pulls it too hard. The higher it sticks, the harder it is to reach safely."
        )
    ],
}
KNOWLEDGE_ORDER = ["spinach", "magic", "flashback", "foreshadowing", "laughter", "afford", "bell", "banner", "kite"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    target = f["target_cfg"]
    spinach = f["spinach_cfg"]
    elder = f["elder"]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the word "spinach" and the word "laughter".',
        f"Tell a magical tall tale where {hero.label} helps fix {target.the} after the town says it cannot afford {target.can_afford}. Include a flashback from {elder.label_word}.",
        f"Write a child-friendly story with foreshadowing at the start, a flashback in the middle, and a magical meal of {spinach.label} that helps solve a very high-up problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    target = f["target_cfg"]
    spinach = f["spinach_cfg"]
    charm = f["charm_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who wanted to help the town, and {elder.label_word}, who remembered an old bit of magic. Together they used courage, memory, and spinach to solve a problem high above the ground."
        ),
        (
            f"Why was everyone worried about {target.the}?",
            f"Everyone was worried because {target.problem}. The town also said it could not afford {target.can_afford}, so the usual way to fix it was out of reach."
        ),
        (
            "How did the story use foreshadowing?",
            f"The story began with the sky acting as if it already knew a tall job was coming. That early clue prepared the reader for the moment when {hero.label} would need to reach something far above the town."
        ),
        (
            "What happened in the flashback?",
            f"{elder.label_word.capitalize()} remembered an older time when magic was whispered over spinach and something impossible became possible. That memory gave them a reason to trust the strange plan in the present."
        ),
        (
            f"How did {hero.label} become tall enough to help?",
            f"{hero.label} ate {spinach.label}, and then {elder.label_word} used the {charm.label}. The food gave height, and the charm added just enough magic to turn hope into a real reach."
        ),
    ]
    if outcome == "legendary":
        qa.append(
            (
                "Why did the town burst into laughter at the end?",
                f"The fix worked so grandly that relief turned into laughter all across town. {hero.label} had grown far taller than needed, so the ending felt joyful, surprising, and bigger than ordinary life."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with {target.ending} and the town feeling relieved. Then the magic settled down, showing that the problem was solved and life could become calm again."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"spinach", "magic", "flashback", "foreshadowing", "laughter", "afford"}
    target_cfg = world.facts["target_cfg"]
    if target_cfg.id == "bell":
        tags.add("bell")
    elif target_cfg.id == "banner":
        tags.add("banner")
    else:
        tags.add("kite")
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *rest in world.fired))}")
    return "\n".join(lines)


def explain_rejection(target: Target, spinach: SpinachMagic, charm: Charm) -> str:
    return (
        f"(No story: {spinach.label} plus the {charm.label} only reaches {total_reach(spinach, charm)}, "
        f"but {target.the} needs {target.need}. In this world, the magic must honestly solve the high-up problem.)"
    )


ASP_RULES = r"""
valid(S,T,Sp,Ch) :- setting(S), target(T), spinach(Sp), charm(Ch),
                    base_reach(B), power(Sp,P), boost(Ch,C), need(T,N), B+P+C >= N.

grand(T,Sp,Ch) :- base_reach(B), power(Sp,P), boost(Ch,C), need(T,N), B+P+C >= N+2.
steady(T,Sp,Ch) :- valid(_,T,Sp,Ch), not grand(T,Sp,Ch).

outcome(legendary) :- chosen_target(T), chosen_spinach(Sp), chosen_charm(Ch), grand(T,Sp,Ch).
outcome(steady) :- chosen_target(T), chosen_spinach(Sp), chosen_charm(Ch), steady(T,Sp,Ch).

#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        lines.append(asp.fact("need", target_id, target.need))
    for spinach_id, spinach in SPINACH.items():
        lines.append(asp.fact("spinach", spinach_id))
        lines.append(asp.fact("power", spinach_id, spinach.power))
    for charm_id, charm in CHARMS.items():
        lines.append(asp.fact("charm", charm_id))
        lines.append(asp.fact("boost", charm_id, charm.boost))
    lines.append(asp.fact("base_reach", BASE_REACH))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_spinach", params.spinach),
            asp.fact("chosen_charm", params.charm),
        ]
    )
    model = asp.one_model(asp_program(scenario))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if params.target not in TARGETS or params.spinach not in SPINACH or params.charm not in CHARMS:
        raise StoryError("(No story: unknown target, spinach, or charm.)")
    return grandeur(TARGETS[params.target], SPINACH[params.spinach], CHARMS[params.charm])


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
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} scenario outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: magical spinach, a costly problem, and a child who grows tall enough to help."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--spinach", choices=SPINACH)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and args.spinach and args.charm:
        target = TARGETS[args.target]
        spinach = SPINACH[args.spinach]
        charm = CHARMS[args.charm]
        if not can_solve(target, spinach, charm):
            raise StoryError(explain_rejection(target, spinach, charm))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.target is None or combo[1] == args.target)
        and (args.spinach is None or combo[2] == args.spinach)
        and (args.charm is None or combo[3] == args.charm)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, target_id, spinach_id, charm_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(sorted(ELDERS))
    return StoryParams(
        setting=setting_id,
        target=target_id,
        spinach=spinach_id,
        charm=charm_id,
        hero=hero,
        gender=gender,
        elder=elder,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("(No story: unknown setting.)")
    if params.target not in TARGETS:
        raise StoryError("(No story: unknown target.)")
    if params.spinach not in SPINACH:
        raise StoryError("(No story: unknown spinach choice.)")
    if params.charm not in CHARMS:
        raise StoryError("(No story: unknown charm.)")
    if params.elder not in ELDERS:
        raise StoryError("(No story: unknown elder.)")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("(No story: unknown gender.)")

    target = TARGETS[params.target]
    spinach = SPINACH[params.spinach]
    charm = CHARMS[params.charm]
    if not can_solve(target, spinach, charm):
        raise StoryError(explain_rejection(target, spinach, charm))

    world = tell(
        setting=SETTINGS[params.setting],
        target_cfg=target,
        spinach_cfg=spinach,
        charm_cfg=CHARMS[params.charm],
        hero_name=params.hero,
        gender=params.gender,
        elder_key=params.elder,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, target, spinach, charm) combos:\n")
        for setting_id, target_id, spinach_id, charm_id in combos:
            legend = grandeur(TARGETS[target_id], SPINACH[spinach_id], CHARMS[charm_id])
            print(f"  {setting_id:8} {target_id:10} {spinach_id:8} {charm_id:6} [{legend}]")
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
            header = f"### {p.hero}: {p.target} with {p.spinach} + {p.charm} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
