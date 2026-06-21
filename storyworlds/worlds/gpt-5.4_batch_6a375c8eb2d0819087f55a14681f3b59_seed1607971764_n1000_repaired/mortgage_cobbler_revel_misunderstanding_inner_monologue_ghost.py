#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mortgage_cobbler_revel_misunderstanding_inner_monologue_ghost.py
================================================================================================

A small, standalone storyworld for a gentle ghost-story misunderstanding:
a child overhears the grown-up word "mortgage," mistakes it for something
haunting, hears a night sound from an old cobbler's place, and must learn what
the sound and the word really mean before the family can revel at the village
festival.

The world is state-driven:
- physical meters track wind, tapping, loose objects, and repaired things
- emotional memes track misunderstanding, fear, curiosity, relief, and joy
- forward-chained rules turn wind into sound, and sound plus misunderstanding
  into fear

The stories are child-facing and complete:
premise -> misunderstanding -> spooky turn -> explanation -> warm ending image.

Run it
------
python storyworlds/worlds/gpt-5.4/mortgage_cobbler_revel_misunderstanding_inner_monologue_ghost.py
python storyworlds/worlds/gpt-5.4/mortgage_cobbler_revel_misunderstanding_inner_monologue_ghost.py --all
python storyworlds/worlds/gpt-5.4/mortgage_cobbler_revel_misunderstanding_inner_monologue_ghost.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/mortgage_cobbler_revel_misunderstanding_inner_monologue_ghost.py --trace
python storyworlds/worlds/gpt-5.4/mortgage_cobbler_revel_misunderstanding_inner_monologue_ghost.py --asp
python storyworlds/worlds/gpt-5.4/mortgage_cobbler_revel_misunderstanding_inner_monologue_ghost.py --verify
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
INVESTIGATING_TRAITS = {"curious", "steady", "brave"}


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Home:
    id: str
    label: str
    intro: str
    night: str
    affords: set[str] = field(default_factory=set)
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
    label: str
    location: str
    sound: str
    spooky: str
    cause: str
    repair: str
    reveal: str
    gift: str
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
class Revel:
    id: str
    label: str
    lights: str
    activity: str
    earnings: str
    ending: str
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
class CobblerCfg:
    id: str
    name: str
    title: str
    shop: str
    warm_line: str
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


def _r_tapping(world: World) -> list[str]:
    house = world.get("house")
    source = world.get("source")
    if house.meters["windy"] < THRESHOLD:
        return []
    if source.meters["loose"] < THRESHOLD:
        return []
    sig = ("tapping", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    source.meters["tapping"] += 1
    house.meters["noise"] += 1
    return ["__tap__"]


def _r_fear(world: World) -> list[str]:
    hero = world.get("hero")
    house = world.get("house")
    if hero.memes["misunderstanding"] < THRESHOLD:
        return []
    if house.meters["noise"] < THRESHOLD:
        return []
    sig = ("fear", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    return ["__fear__"]


def _r_seek_truth(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["curiosity"] < THRESHOLD:
        return []
    if hero.memes["fear"] < THRESHOLD:
        return []
    sig = ("seek_truth", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["resolve"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="tapping", tag="physical", apply=_r_tapping),
    Rule(name="fear", tag="emotional", apply=_r_fear),
    Rule(name="seek_truth", tag="emotional", apply=_r_seek_truth),
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
                produced.extend(out)
    if narrate:
        source_cfg = world.facts.get("source_cfg")
        hero = world.entities.get("hero")
        for marker in produced:
            if marker == "__tap__" and source_cfg is not None:
                world.say(
                    f"Then the wind turned, and from {source_cfg.location} came "
                    f"{source_cfg.sound}."
                )
            elif marker == "__fear__" and hero is not None:
                world.say(
                    f"The small sound went straight into {hero.id}'s chest and made "
                    f"the dark feel deeper."
                )
    return produced


HOMES = {
    "lane_cottage": Home(
        id="lane_cottage",
        label="a narrow cottage on Lantern Lane",
        intro="At the far end of Lantern Lane stood a narrow cottage with old floorboards and a window that looked toward the cobbler's shop.",
        night="At night the lane held its breath, and every little creak seemed to stand still in the air.",
        affords={"shoe_sign", "boot_rack"},
        tags={"house", "ghost"},
    ),
    "attic_flat": Home(
        id="attic_flat",
        label="a small attic flat above the cobbler's shop",
        intro="Above the cobbler's shop was a small attic flat where the rafters made long shadows across the ceiling.",
        night="At night the rafters sighed softly, and moonlight lay in silver strips across the floor.",
        affords={"shoe_sign", "shoe_lasts"},
        tags={"house", "ghost"},
    ),
    "orchard_house": Home(
        id="orchard_house",
        label="an old orchard house beside the cobbler's shed",
        intro="Beside the cobbler's shed stood an old orchard house with a pear tree leaning close to the eaves.",
        night="At night the tree scratched softly at the dark while the house listened.",
        affords={"boot_rack", "shoe_lasts"},
        tags={"house", "ghost"},
    ),
}

SOURCES = {
    "shoe_sign": SoundSource(
        id="shoe_sign",
        label="wooden shoe sign",
        location="the cobbler's shop front",
        sound="a hollow tap-tap from the swinging wooden shoe sign",
        spooky="It sounded almost like careful knuckles on a door that nobody had opened.",
        cause="the wind was knocking the loose wooden shoe sign against its iron hook",
        repair="He wrapped fresh cord around the sign and steadied it with one sure hand.",
        reveal="The sign gave one last little tap and then fell quiet.",
        gift="a polished pair of little festival shoes hanging from his arm",
        tags={"sign", "cobbler"},
    ),
    "shoe_lasts": SoundSource(
        id="shoe_lasts",
        label="bundle of shoe lasts",
        location="the narrow stair by the workshop",
        sound="a dry tok-tok from a bundle of wooden shoe lasts knocking together",
        spooky="It sounded like tiny heels walking where no one should have been walking.",
        cause="a string of wooden shoe lasts had come loose and was tapping against the stair rail",
        repair="He gathered the wooden lasts into his apron and tied the string tight again.",
        reveal="The last dry tok faded, and the stair sounded ordinary once more.",
        gift="a ribbon-tied parcel of repaired dancing shoes",
        tags={"shoe_last", "cobbler"},
    ),
    "boot_rack": SoundSource(
        id="boot_rack",
        label="rack of small boots",
        location="the back porch by the cobbler's shed",
        sound="a faint clack-clack from a rack of little boots touching in the wind",
        spooky="It sounded like small feet trying out the boards after midnight.",
        cause="a rack of mended boots was rocking in the wind and making the soles kiss the porch rail",
        repair="He set the rack down, tucked the boots under the porch, and latched the hook firmly.",
        reveal="The porch gave a sleepy creak, and the clacking stopped.",
        gift="a tiny pair of bright-button boots ready for the festival",
        tags={"boots", "cobbler"},
    ),
}

REVELS = {
    "lantern_revel": Revel(
        id="lantern_revel",
        label="the Lantern Revel",
        lights="lanterns glowed like warm stars along the street",
        activity="people sang and walked under paper lights",
        earnings="the extra sewing money from the revel would help with the mortgage",
        ending="By the time the music floated down the lane, the house no longer felt haunted at all.",
        tags={"revel", "lantern"},
    ),
    "harvest_revel": Revel(
        id="harvest_revel",
        label="the Harvest Revel",
        lights="lanterns and pumpkin candles shone across the square",
        activity="neighbors laughed beside baskets of apples and bread",
        earnings="the stall at the revel would bring in money for the mortgage",
        ending="When the fiddles started up, the shadows seemed small and friendly.",
        tags={"revel", "harvest"},
    ),
    "moon_revel": Revel(
        id="moon_revel",
        label="the Moon Revel",
        lights="silver lanterns swayed under the pale moon",
        activity="families danced slowly while bells chimed on the green",
        earnings="the night's good trade would help pay the mortgage",
        ending="Under the moon, even the old boards sounded like part of the music.",
        tags={"revel", "moon"},
    ),
}

COBBLERS = {
    "mr_finch": CobblerCfg(
        id="mr_finch",
        name="Mr. Finch",
        title="the cobbler",
        shop="the little cobbler's shop",
        warm_line="Shoes make enough taps on their own without pretending to be ghosts.",
        tags={"cobbler"},
    ),
    "ms_wren": CobblerCfg(
        id="ms_wren",
        name="Ms. Wren",
        title="the cobbler",
        shop="the neat cobbler's workshop",
        warm_line="Leather can whisper in the dark, but it is still only leather.",
        tags={"cobbler"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Elsie", "Nora", "June", "Tessa", "Willa"]
BOY_NAMES = ["Theo", "Bram", "Ellis", "Owen", "Milo", "Jasper", "Finn"]
TRAITS = ["timid", "curious", "steady", "dreamy", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for home_id, home in HOMES.items():
        for source_id in sorted(home.affords):
            for revel_id in REVELS:
                combos.append((home_id, source_id, revel_id))
    return sorted(combos)


@dataclass
class StoryParams:
    home: str
    sound: str
    revel: str
    cobbler: str
    name: str
    gender: str
    parent: str
    trait: str
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


def outcome_of(params: StoryParams) -> str:
    if params.trait in INVESTIGATING_TRAITS:
        return "investigate"
    return "call_parent"


def explain_rejection(home_id: str, sound_id: str) -> str:
    home = HOMES[home_id]
    source = SOURCES[sound_id]
    return (
        f"(No story: {source.label} does not belong in {home.label}. "
        f"Pick a sound source that this home can honestly afford.)"
    )


def introduce(world: World, hero: Entity, parent: Entity, home: Home, revel: Revel) -> None:
    world.say(
        f"{home.intro} {hero.id} lived there with {hero.pronoun('possessive')} "
        f"{parent.label_word}, and the coming of {revel.label} had filled the rooms "
        f"with folded cloth, candle stubs, and a hush that felt almost story-like."
    )
    trait = hero.traits[0] if hero.traits else "little"
    world.say(
        f"{hero.id} was a {trait} little {hero.type} who noticed every whisper a house made."
    )


def parent_worry(world: World, hero: Entity, parent: Entity, revel: Revel) -> None:
    parent.memes["worry"] += 1
    world.say(
        f"That evening {parent.label_word} counted coins at the table and said softly, "
        f'"If {revel.earnings}, we will be all right."'
    )
    world.facts["heard_phrase"] = "mortgage"


def misunderstand(world: World, hero: Entity) -> None:
    hero.memes["misunderstanding"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} had never heard the word mortgage before. "
        f"In {hero.pronoun('possessive')} mind it turned strange at once."
    )
    world.say(
        f'"Mortgage?" {hero.id} thought. "That sounds like the name of something '
        f'that comes in the dark and asks a house to follow it away."'
    )


def night_falls(world: World, home: Home) -> None:
    house = world.get("house")
    house.meters["windy"] += 1
    world.say(home.night)


def hear_sound(world: World, source: SoundSource) -> None:
    world.say(source.spooky)
    propagate(world, narrate=True)


def inner_monologue(world: World, hero: Entity) -> None:
    fear = hero.memes["fear"]
    if fear >= THRESHOLD:
        if hero.traits and hero.traits[0] in INVESTIGATING_TRAITS:
            world.say(
                f'"Maybe it is the mortgage," {hero.id} thought, '
                f'"but maybe if I look closely, it will turn back into something ordinary."'
            )
        else:
            world.say(
                f'"It heard the word too," {hero.id} thought. '
                f'"What if the mortgage has come to knock on our door?"'
            )


def choose_path(world: World, hero: Entity, parent: Entity, branch: str) -> None:
    if branch == "investigate":
        hero.memes["bravery"] += 1
        world.say(
            f"{hero.id} slid out of bed, picked up the little lantern by the door, "
            f"and followed the sound instead of hiding from it."
        )
    else:
        hero.memes["trust"] += 1
        world.say(
            f"{hero.id} hurried to {parent.label_word}'s room, climbed onto the blanket edge, "
            f"and whispered that something was tapping in the dark."
        )


def meet_cobbler_investigate(
    world: World,
    hero: Entity,
    source: SoundSource,
    cobbler_cfg: CobblerCfg,
) -> None:
    cobbler = world.get("cobbler")
    source_ent = world.get("source")
    source_ent.meters["repaired"] += 1
    source_ent.meters["loose"] = 0.0
    cobbler.meters["helping"] += 1
    world.say(
        f"At {source.location}, the lantern showed not a ghost at all, but {cobbler_cfg.name} "
        f"standing in his apron with {source.gift}."
    )
    world.say(
        f'"Hush now," said {cobbler_cfg.name}. "{source.cause}." '
        f"{source.repair}"
    )


def meet_cobbler_with_parent(
    world: World,
    hero: Entity,
    parent: Entity,
    source: SoundSource,
    cobbler_cfg: CobblerCfg,
) -> None:
    cobbler = world.get("cobbler")
    source_ent = world.get("source")
    source_ent.meters["repaired"] += 1
    source_ent.meters["loose"] = 0.0
    cobbler.meters["helping"] += 1
    world.say(
        f"{parent.label_word.capitalize()} took the lantern, and together they stepped to "
        f"{source.location}. There stood {cobbler_cfg.name}, apron on, one hand raised to the noise."
    )
    world.say(
        f'"Sorry for the fright," said {cobbler_cfg.name}. "{source.cause}." '
        f"{source.repair}"
    )


def reveal_truth(
    world: World,
    hero: Entity,
    parent: Entity,
    cobbler_cfg: CobblerCfg,
    source: SoundSource,
) -> None:
    hero.memes["misunderstanding"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.get("house").meters["noise"] = 0.0
    world.say(source.reveal)
    world.say(
        f'{parent.label_word.capitalize()} put a warm hand on {hero.id}\'s shoulder. '
        f'"A mortgage is not a ghost," {parent.pronoun()} said. '
        f'"It is the house money we pay a little at a time."'
    )
    world.say(
        f'{cobbler_cfg.name} smiled and said, "{cobbler_cfg.warm_line}"'
    )


def gift_and_revel(
    world: World,
    hero: Entity,
    parent: Entity,
    revel: Revel,
    source: SoundSource,
    cobbler_cfg: CobblerCfg,
) -> None:
    boots = world.get("gift")
    boots.meters["ready"] += 1
    hero.memes["gratitude"] += 1
    world.say(
        f"{cobbler_cfg.name} held out {source.gift}. They were for {hero.id}, "
        f"ready at last for {revel.label}."
    )
    world.say(
        f"The next evening {revel.lights}, and {revel.activity}. "
        f"{hero.id} heard the same boards and hooks and little knocks as before, "
        f"but now each sound belonged exactly where it was."
    )
    world.say(
        f"{hero.id} took {parent.label_word}'s hand, watched the village revel together, "
        f"and felt proud that the night had been explained instead of feared. "
        f"{revel.ending}"
    )


def tell(
    home: Home,
    source: SoundSource,
    revel: Revel,
    cobbler_cfg: CobblerCfg,
    name: str,
    gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name, role="hero", traits=[trait]))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    cobbler = world.add(Entity(id="cobbler", kind="character", type="adult", label=cobbler_cfg.name, role="cobbler"))
    house = world.add(Entity(id="house", type="house", label=home.label))
    source_ent = world.add(Entity(id="source", type="sound_source", label=source.label))
    gift = world.add(Entity(id="gift", type="shoes", label="festival shoes"))

    source_ent.meters["loose"] = 1.0
    house.meters["windy"] = 0.0
    house.meters["noise"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["misunderstanding"] = 0.0
    hero.memes["curiosity"] = 0.0
    hero.memes["joy"] = 0.0
    hero.memes["relief"] = 0.0
    world.facts.update(
        home=home,
        source_cfg=source,
        revel=revel,
        cobbler_cfg=cobbler_cfg,
        hero=hero,
        parent=parent,
        branch=outcome_of(
            StoryParams(
                home=home.id,
                sound=source.id,
                revel=revel.id,
                cobbler=cobbler_cfg.id,
                name=name,
                gender=gender,
                parent=parent_type,
                trait=trait,
                seed=None,
            )
        ),
    )

    introduce(world, hero, parent, home, revel)
    parent_worry(world, hero, parent, revel)
    misunderstand(world, hero)

    world.para()
    night_falls(world, home)
    hear_sound(world, source)
    inner_monologue(world, hero)

    world.para()
    branch = world.facts["branch"]
    choose_path(world, hero, parent, branch)
    if branch == "investigate":
        meet_cobbler_investigate(world, hero, source, cobbler_cfg)
    else:
        meet_cobbler_with_parent(world, hero, parent, source, cobbler_cfg)
    reveal_truth(world, hero, parent, cobbler_cfg, source)

    world.para()
    gift_and_revel(world, hero, parent, revel, source, cobbler_cfg)

    world.facts.update(
        heard_word="mortgage",
        explained_word=True,
        source_fixed=source_ent.meters["repaired"] >= THRESHOLD,
        gift_ready=gift.meters["ready"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "mortgage": [
        (
            "What is a mortgage?",
            "A mortgage is money a family pays over time for a house. It is not a creature or a spirit, just a grown-up money word."
        )
    ],
    "cobbler": [
        (
            "What does a cobbler do?",
            "A cobbler fixes and makes shoes. A cobbler uses tools, leather, thread, and careful hands."
        )
    ],
    "revel": [
        (
            "What does revel mean?",
            "To revel means to celebrate with happy energy. People might sing, laugh, dance, or enjoy a festival together."
        )
    ],
    "sign": [
        (
            "Why can a hanging sign make spooky sounds at night?",
            "Wind can push a loose sign against a hook or wall. In the dark, that ordinary tapping can sound much stranger than it really is."
        )
    ],
    "shoe_last": [
        (
            "What is a shoe last?",
            "A shoe last is a foot-shaped form a cobbler uses to make or repair shoes. Wooden lasts can knock together and make a hard tapping sound."
        )
    ],
    "boots": [
        (
            "Why do boots and shoes sound loud on porches or stairs?",
            "Hard soles can click on wood, and wood carries the sound. At night, small noises can seem bigger because everything else is quiet."
        )
    ],
    "ghost": [
        (
            "Why do ordinary sounds feel scarier in the dark?",
            "When you cannot see a sound, your imagination may try to finish the picture. That is why a tap or creak can feel ghostly before you know its cause."
        )
    ],
    "lantern": [
        (
            "Why does a lantern help in a scary place?",
            "A lantern gives light, and light helps you see what is really there. Seeing clearly often turns a mystery back into something ordinary."
        )
    ],
}
KNOWLEDGE_ORDER = ["mortgage", "cobbler", "revel", "sign", "shoe_last", "boots", "ghost", "lantern"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    home = world.facts["home"]
    revel = world.facts["revel"]
    source = world.facts["source_cfg"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "mortgage", "cobbler", and "revel".',
        f"Tell a story about a {hero.type} named {hero.label} in {home.label} who misunderstands the word mortgage and hears {source.sound}.",
        f"Write a child-facing ghostly misunderstanding story where a night noise near a cobbler turns out to be ordinary, and the ending arrives at {revel.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    home = world.facts["home"]
    source = world.facts["source_cfg"]
    revel = world.facts["revel"]
    cobbler_cfg = world.facts["cobbler_cfg"]
    branch = world.facts["branch"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a little {hero.type}, {hero.pronoun('possessive')} {parent.label_word}, and {cobbler_cfg.name} the cobbler. They all live close to {home.label}, where the spooky misunderstanding begins."
        ),
        (
            "Why did the night feel scary to the child?",
            f"{hero.label} heard the grown-up word mortgage and did not know what it meant, so {hero.pronoun()} imagined it as something haunting. Then {source.sound}, which made the misunderstanding feel real."
        ),
        (
            "What was the sound really coming from?",
            f"It came from {source.label} at {source.location}. The sound happened because {source.cause}."
        ),
        (
            "What did mortgage really mean in the story?",
            f"It meant house money that has to be paid a little at a time. The fear faded once {parent.label_word} explained that it was a money worry, not a ghost."
        ),
    ]
    if branch == "investigate":
        qa.append(
            (
                f"How did {hero.label} face the mystery?",
                f"{hero.label} followed the sound with a lantern instead of staying in bed. That brave choice led straight to {cobbler_cfg.name}, who showed the true cause."
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.label} solve the scary problem?",
                f"{hero.label} went to {parent.label_word} for help right away. With a grown-up and a lantern, the mystery became easier to understand."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended at {revel.label}, where the family could revel without fear. The same night sounds were still around, but now {hero.label} knew what they meant."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mortgage", "cobbler", "revel", "ghost", "lantern"}
    tags |= set(world.facts["source_cfg"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        home="lane_cottage",
        sound="shoe_sign",
        revel="lantern_revel",
        cobbler="mr_finch",
        name="Lina",
        gender="girl",
        parent="mother",
        trait="timid",
        seed=None,
    ),
    StoryParams(
        home="attic_flat",
        sound="shoe_lasts",
        revel="moon_revel",
        cobbler="ms_wren",
        name="Theo",
        gender="boy",
        parent="father",
        trait="curious",
        seed=None,
    ),
    StoryParams(
        home="orchard_house",
        sound="boot_rack",
        revel="harvest_revel",
        cobbler="mr_finch",
        name="Mira",
        gender="girl",
        parent="father",
        trait="steady",
        seed=None,
    ),
    StoryParams(
        home="lane_cottage",
        sound="boot_rack",
        revel="moon_revel",
        cobbler="ms_wren",
        name="Owen",
        gender="boy",
        parent="mother",
        trait="dreamy",
        seed=None,
    ),
]


ASP_RULES = r"""
valid(H,S,R) :- home(H), sound(S), revel(R), affords(H,S).

investigate_trait(T) :- trait(T), investigative(T).
call_parent_trait(T) :- trait(T), not investigative(T).

outcome(investigate) :- investigate_trait(T).
outcome(call_parent) :- call_parent_trait(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for home_id, home in HOMES.items():
        lines.append(asp.fact("home", home_id))
        for sound_id in sorted(home.affords):
            lines.append(asp.fact("affords", home_id, sound_id))
    for sound_id in SOURCES:
        lines.append(asp.fact("sound", sound_id))
    for revel_id in REVELS:
        lines.append(asp.fact("revel", revel_id))
    for tr in TRAITS:
        if tr in INVESTIGATING_TRAITS:
            lines.append(asp.fact("investigative", tr))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("trait", params.trait)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
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
        smoke = generate(
            StoryParams(
                home="lane_cottage",
                sound="shoe_sign",
                revel="lantern_revel",
                cobbler="mr_finch",
                name="Lina",
                gender="girl",
                parent="mother",
                trait="curious",
                seed=0,
            )
        )
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation/emit succeeded.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story storyworld: a misunderstood mortgage, a cobbler's night sound, and a revel."
    )
    ap.add_argument("--home", choices=HOMES)
    ap.add_argument("--sound", choices=SOURCES)
    ap.add_argument("--revel", choices=REVELS)
    ap.add_argument("--cobbler", choices=COBBLERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (home, sound, revel) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.home and args.sound and args.sound not in HOMES[args.home].affords:
        raise StoryError(explain_rejection(args.home, args.sound))

    combos = [
        combo
        for combo in valid_combos()
        if (args.home is None or combo[0] == args.home)
        and (args.sound is None or combo[1] == args.sound)
        and (args.revel is None or combo[2] == args.revel)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    home_id, sound_id, revel_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        home=home_id,
        sound=sound_id,
        revel=revel_id,
        cobbler=args.cobbler or rng.choice(sorted(COBBLERS.keys())),
        name=name,
        gender=gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        trait=args.trait or rng.choice(TRAITS),
        seed=None,
    )


def _hero_name(world: World) -> str:
    return world.facts["hero"].label


def generate(params: StoryParams) -> StorySample:
    if params.home not in HOMES:
        raise StoryError(f"(Unknown home: {params.home})")
    if params.sound not in SOURCES:
        raise StoryError(f"(Unknown sound source: {params.sound})")
    if params.revel not in REVELS:
        raise StoryError(f"(Unknown revel: {params.revel})")
    if params.cobbler not in COBBLERS:
        raise StoryError(f"(Unknown cobbler: {params.cobbler})")
    if params.sound not in HOMES[params.home].affords:
        raise StoryError(explain_rejection(params.home, params.sound))
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent: {params.parent})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    world = tell(
        home=HOMES[params.home],
        source=SOURCES[params.sound],
        revel=REVELS[params.revel],
        cobbler_cfg=COBBLERS[params.cobbler],
        name=params.name,
        gender=params.gender,
        parent_type=params.parent,
        trait=params.trait,
    )
    story = world.render().replace("hero", _hero_name(world))
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (home, sound, revel) combos:\n")
        for home_id, sound_id, revel_id in combos:
            print(f"  {home_id:13} {sound_id:11} {revel_id}")
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
            header = f"### {p.name}: {p.sound} at {p.home} ({p.revel}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
