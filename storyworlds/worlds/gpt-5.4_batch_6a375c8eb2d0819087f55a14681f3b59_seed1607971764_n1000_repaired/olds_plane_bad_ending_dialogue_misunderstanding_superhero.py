#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/olds_plane_bad_ending_dialogue_misunderstanding_superhero.py
========================================================================================

A standalone story world about a small superhero-loving child who misunderstands
what grown-ups are saying about a plane. Trying to save the day too fast causes
real trouble, so the story ends sadly instead of neatly.

Seed ingredients rebuilt as world state:
- word: "olds"
- word: "plane"
- features: Bad Ending, Dialogue, Misunderstanding
- style: Superhero Story

The domain is intentionally small and constraint-checked: an eager child hears
an ambiguous line about a small flying craft at a community event, mistakes it
for a true emergency, and takes a dramatic "hero" action that damages the event.
A calm explanation follows, but the damage is done and the ending stays bad.

Run it
------
    python storyworlds/worlds/gpt-5.4/olds_plane_bad_ending_dialogue_misunderstanding_superhero.py
    python storyworlds/worlds/gpt-5.4/olds_plane_bad_ending_dialogue_misunderstanding_superhero.py --all
    python storyworlds/worlds/gpt-5.4/olds_plane_bad_ending_dialogue_misunderstanding_superhero.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/olds_plane_bad_ending_dialogue_misunderstanding_superhero.py --trace
    python storyworlds/worlds/gpt-5.4/olds_plane_bad_ending_dialogue_misunderstanding_superhero.py --asp
    python storyworlds/worlds/gpt-5.4/olds_plane_bad_ending_dialogue_misunderstanding_superhero.py --verify
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
CAUTION_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    movable: bool = False
    fragile: bool = False
    # physical + emotional state
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
class Setting:
    id: str
    place: str
    crowd: str
    sky: str
    props: str
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


@dataclass
class PlaneKind:
    id: str
    label: str
    phrase: str
    launch: str
    lands_badly: str
    fragile: bool
    needs_space: bool
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
class Message:
    id: str
    spoken: str
    meaning: str
    sounds_like_trouble: bool
    gravity: int
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
class HeroMove:
    id: str
    label: str
    act_line: str
    effect_text: str
    consequence_text: str
    caution: int
    breaks_plane: bool = False
    causes_alarm: bool = False
    spills_table: bool = False
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
class World:
    setting: Setting

    def __post_init__(self) -> None:
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


def _r_broken_plane(world: World) -> list[str]:
    plane = world.entities.get("plane")
    if plane is None or plane.meters["broken"] < THRESHOLD:
        return []
    sig = ("broken_plane",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    event = world.get("event")
    event.meters["ruined"] += 1
    organizer = world.get("organizer")
    organizer.memes["sad"] += 1
    hero = world.get("hero")
    hero.memes["guilt"] += 1
    elder = world.get("elder")
    elder.memes["disappointed"] += 1
    return ["__ruined__"]


def _r_alarm(world: World) -> list[str]:
    event = world.get("event")
    if event.meters["alarm"] < THRESHOLD:
        return []
    sig = ("alarm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    event.meters["ruined"] += 1
    event.meters["stopped"] += 1
    for eid in ("hero", "organizer", "elder"):
        world.get(eid).memes["shock"] += 1
    world.get("hero").memes["guilt"] += 1
    return ["__ruined__"]


def _r_spill(world: World) -> list[str]:
    event = world.get("event")
    if event.meters["spilled"] < THRESHOLD:
        return []
    sig = ("spill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    event.meters["ruined"] += 1
    world.get("elder").memes["sad"] += 1
    world.get("hero").memes["guilt"] += 1
    return ["__ruined__"]


CAUSAL_RULES = [
    Rule(name="broken_plane", tag="physical", apply=_r_broken_plane),
    Rule(name="alarm", tag="social", apply=_r_alarm),
    Rule(name="spill", tag="physical", apply=_r_spill),
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
        for s in produced:
            world.say(s)
    return produced


def misunderstanding_plausible(message: Message, action: HeroMove) -> bool:
    return message.sounds_like_trouble and action.caution >= CAUTION_MIN


def action_hits_plane(action: HeroMove, plane: PlaneKind) -> bool:
    if action.breaks_plane:
        return plane.fragile
    if action.causes_alarm:
        return True
    if action.spills_table:
        return True
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for plane_id in setting.supports:
            plane = PLANES[plane_id]
            for message_id, message in MESSAGES.items():
                for action_id, action in ACTIONS.items():
                    if misunderstanding_plausible(message, action) and action_hits_plane(action, plane):
                        combos.append((setting_id, message_id, action_id))
    return combos


def severity_of(action: HeroMove) -> str:
    if action.causes_alarm:
        return "evacuated"
    if action.breaks_plane:
        return "broken_plane"
    if action.spills_table:
        return "spilled_show"
    return "sad"


def predict_damage(world: World, action: HeroMove) -> dict:
    sim = world.copy()
    do_hero_move(sim, action, narrate=False)
    event = sim.get("event")
    plane = sim.get("plane")
    return {
        "ruined": event.meters["ruined"] >= THRESHOLD,
        "broken": plane.meters["broken"] >= THRESHOLD,
        "alarm": event.meters["alarm"] >= THRESHOLD,
        "spilled": event.meters["spilled"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, elder: Entity, organizer: Entity, plane: PlaneKind) -> None:
    world.say(
        f"{hero.id} tied on a bright cape and marched into {world.setting.place} as if {hero.pronoun()} were the smallest hero in the city."
    )
    world.say(
        f"{world.setting.crowd} had gathered there, and {world.setting.props}."
    )
    world.say(
        f"At one long table, {elder.id} and the other olds were getting {plane.phrase} ready for a little show."
    )
    world.say(
        f"{organizer.id}, the event leader, smiled at the busy room while {world.setting.sky} above them."
    )


def show_plane(world: World, hero: Entity, plane: PlaneKind) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"{hero.id} loved the look of the {plane.label}. In {hero.pronoun('possessive')} head it was not a small craft at all, but a rescue machine waiting for a call."
    )


def overhear(world: World, elder: Entity, organizer: Entity, message: Message, plane: PlaneKind) -> None:
    world.say(
        f'"{message.spoken}" {elder.id} said to {organizer.id}, pointing at the {plane.label}.'
    )
    world.say(
        f"{organizer.id} nodded, because they only meant {message.meaning}."
    )


def misunderstand(world: World, hero: Entity, message: Message) -> None:
    hero.memes["alarm"] += 1
    hero.memes["bravery"] += 1
    world.facts["heard_line"] = message.spoken
    world.say(
        f"But {hero.id} only caught part of the sentence. To {hero.pronoun('object')}, it sounded like danger had dropped right into the middle of the party."
    )
    world.say(
        f'"The olds need help with a plane!" {hero.id} gasped. "{hero.pronoun("possessive").capitalize()} city-saving moment is here!"'
    )


def rush(world: World, hero: Entity, action: HeroMove) -> None:
    hero.memes["haste"] += 1
    world.say(
        f"Without asking one more question, {hero.id} {action.act_line}."
    )


def do_hero_move(world: World, action: HeroMove, narrate: bool = True) -> None:
    plane = world.get("plane")
    event = world.get("event")
    if action.breaks_plane:
        plane.meters["broken"] += 1
    if action.causes_alarm:
        event.meters["alarm"] += 1
    if action.spills_table:
        event.meters["spilled"] += 1
        plane.meters["tilted"] += 1
    propagate(world, narrate=narrate)


def impact(world: World, action: HeroMove) -> None:
    world.say(action.effect_text)
    world.say(action.consequence_text)


def explain(world: World, elder: Entity, organizer: Entity, hero: Entity, message: Message, plane: PlaneKind) -> None:
    hero.memes["bravery"] = 0.0
    hero.memes["shame"] += 1
    elder.memes["kindness"] += 1
    world.say(
        f'"Wait," {organizer.id} said, hurrying over. "No one was in danger."'
    )
    world.say(
        f'{elder.id} put a soft hand on {hero.id}\'s shoulder. "We only meant {message.meaning}," {elder.pronoun()} said. "This {plane.label} was for fun, not for a rescue."'
    )
    world.say(
        f'The brave feeling inside {hero.id} sank all at once. "{hero.id} whispered, "I thought I was helping."'
    )


def bad_ending(world: World, hero: Entity, action: HeroMove, plane: PlaneKind) -> None:
    event = world.get("event")
    if action.causes_alarm:
        world.say(
            f"The hall emptied, the little show was over before it began, and the {plane.label} never flew at all."
        )
    elif action.breaks_plane:
        world.say(
            f"The {plane.label} lay bent on the floor, and the careful work from all morning was gone."
        )
    else:
        world.say(
            f"Juice ran across the table, the little show fell into a sticky mess, and no one felt like cheering anymore."
        )
    if event.meters["ruined"] >= THRESHOLD:
        world.say(
            f"{hero.id} kept the cape on, but it did not feel like a hero cape now. It felt heavy."
        )
    world.say(
        "The party ended early, and even though the grown-ups forgave the mistake, the sad part could not be undone that day."
    )


def tell(
    setting: Setting,
    plane_cfg: PlaneKind,
    message_cfg: Message,
    action_cfg: HeroMove,
    hero_name: str = "Milo",
    hero_type: str = "boy",
    elder_name: str = "Mrs. Vale",
    organizer_name: str = "Nurse Jo",
) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", traits=["eager", "brave"], attrs={"cape": "red"}))
    elder = world.add(Entity(id=elder_name, kind="character", type="woman", role="elder", traits=["patient"]))
    organizer = world.add(Entity(id=organizer_name, kind="character", type="woman", role="organizer", traits=["busy", "kind"]))
    plane = world.add(Entity(id="plane", type="plane", label=plane_cfg.label, fragile=plane_cfg.fragile, movable=True))
    event = world.add(Entity(id="event", type="event", label="the event"))

    world.facts.update(
        hero=hero,
        elder=elder,
        organizer=organizer,
        plane_cfg=plane_cfg,
        message_cfg=message_cfg,
        action_cfg=action_cfg,
        setting=setting,
        predicted={},
    )

    introduce(world, hero, elder, organizer, plane_cfg)
    show_plane(world, hero, plane_cfg)

    world.para()
    overhear(world, elder, organizer, message_cfg, plane_cfg)
    misunderstand(world, hero, message_cfg)

    world.para()
    world.facts["predicted"] = predict_damage(world, action_cfg)
    rush(world, hero, action_cfg)
    do_hero_move(world, action_cfg, narrate=False)
    impact(world, action_cfg)

    world.para()
    explain(world, elder, organizer, hero, message_cfg, plane_cfg)
    bad_ending(world, hero, action_cfg, plane_cfg)

    world.facts.update(
        plane=plane,
        event=event,
        outcome=severity_of(action_cfg),
        ruined=event.meters["ruined"] >= THRESHOLD,
        broken=plane.meters["broken"] >= THRESHOLD,
        alarmed=event.meters["alarm"] >= THRESHOLD,
        spilled=event.meters["spilled"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "senior_hall": Setting(
        id="senior_hall",
        place="the bright senior hall",
        crowd="Paper stars and folding chairs",
        sky="sunlight poured through the high windows",
        props="a snack table waited under blue streamers",
        supports={"paper_plane", "glider"},
        tags={"hall", "party"},
    ),
    "garden_fair": Setting(
        id="garden_fair",
        place="the garden fair beside the library",
        crowd="Flower pots and little booths",
        sky="a warm afternoon shone",
        props="a lemonade table stood near a string of flags",
        supports={"paper_plane", "foam_plane"},
        tags={"garden", "fair"},
    ),
    "porch_club": Setting(
        id="porch_club",
        place="the long porch of Maple House",
        crowd="Rocking chairs and a jar of pencils",
        sky="soft clouds drifted slowly",
        props="a card table held ribbons and cookies",
        supports={"glider", "foam_plane"},
        tags={"porch", "neighbors"},
    ),
}

PLANES = {
    "paper_plane": PlaneKind(
        id="paper_plane",
        label="paper plane",
        phrase="a neat paper plane",
        launch="glide from one end of the room to the other",
        lands_badly="crumples at once if grabbed too hard",
        fragile=True,
        needs_space=False,
        tags={"paper_plane"},
    ),
    "glider": PlaneKind(
        id="glider",
        label="balsa plane",
        phrase="a tiny balsa plane",
        launch="float in a slow circle",
        lands_badly="snaps if twisted",
        fragile=True,
        needs_space=True,
        tags={"glider"},
    ),
    "foam_plane": PlaneKind(
        id="foam_plane",
        label="foam plane",
        phrase="a soft foam plane",
        launch="loop gently through the air",
        lands_badly="bounces when it falls",
        fragile=False,
        needs_space=True,
        tags={"foam_plane"},
    ),
}

MESSAGES = {
    "going_down": Message(
        id="going_down",
        spoken="If the plane goes down, catch it by the tail",
        meaning="they should gently catch the toy if it dips during the game",
        sounds_like_trouble=True,
        gravity=3,
        tags={"misheard", "dialogue"},
    ),
    "clear_the_way": Message(
        id="clear_the_way",
        spoken="Clear the way for the plane",
        meaning="they needed a little open space before the toss",
        sounds_like_trouble=True,
        gravity=2,
        tags={"misheard", "dialogue"},
    ),
    "drop_fast": Message(
        id="drop_fast",
        spoken="That plane may drop fast",
        meaning="the small craft might dive quickly when thrown",
        sounds_like_trouble=True,
        gravity=3,
        tags={"misheard", "dialogue"},
    ),
}

ACTIONS = {
    "snatch": HeroMove(
        id="snatch",
        label="snatch",
        act_line="leaped like a comic-book rescuer and snatched for the plane in midair",
        effect_text="The quick grab was too rough. Paper and thin wood gave a sad little crackle.",
        consequence_text="Everyone froze when the flight ended in a broken little wreck instead of a cheer.",
        caution=2,
        breaks_plane=True,
        tags={"grab", "break"},
    ),
    "pull_alarm": HeroMove(
        id="pull_alarm",
        label="pull_alarm",
        act_line="raced to the red wall handle and yanked the alarm with both hands",
        effect_text="A bell exploded through the room. Chairs scraped, cookies shook, and voices turned frightened all at once.",
        consequence_text="The whole event had to stop while people hurried outside.",
        caution=3,
        causes_alarm=True,
        tags={"alarm", "evacuate"},
    ),
    "dive_table": HeroMove(
        id="dive_table",
        label="dive_table",
        act_line="threw {hero}self across the table to shield everyone from the 'crash'",
        effect_text="The cape swooped, the cups toppled, and bright juice slid through napkins and ribbons.",
        consequence_text="By the time the sliding stopped, the little plane show was a sticky mess.",
        caution=2,
        spills_table=True,
        tags={"spill", "mess"},
    ),
}


GIRL_NAMES = ["Maya", "Lila", "Zoe", "Nina", "Ava", "Ivy"]
BOY_NAMES = ["Milo", "Ben", "Theo", "Eli", "Finn", "Max"]
ELDER_NAMES = ["Mrs. Vale", "Mr. Reed", "Mrs. Song", "Grandpa Lee"]
ORGANIZER_NAMES = ["Nurse Jo", "Ms. Tia", "Coach June", "Miss Alma"]


@dataclass
class StoryParams:
    setting: str
    plane: str
    message: str
    action: str
    hero_name: str
    hero_gender: str
    elder_name: str
    organizer_name: str
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
        setting="senior_hall",
        plane="paper_plane",
        message="going_down",
        action="snatch",
        hero_name="Milo",
        hero_gender="boy",
        elder_name="Mrs. Vale",
        organizer_name="Nurse Jo",
    ),
    StoryParams(
        setting="garden_fair",
        plane="foam_plane",
        message="clear_the_way",
        action="pull_alarm",
        hero_name="Lila",
        hero_gender="girl",
        elder_name="Mr. Reed",
        organizer_name="Ms. Tia",
    ),
    StoryParams(
        setting="porch_club",
        plane="glider",
        message="drop_fast",
        action="dive_table",
        hero_name="Theo",
        hero_gender="boy",
        elder_name="Mrs. Song",
        organizer_name="Miss Alma",
    ),
    StoryParams(
        setting="garden_fair",
        plane="paper_plane",
        message="going_down",
        action="snatch",
        hero_name="Ivy",
        hero_gender="girl",
        elder_name="Grandpa Lee",
        organizer_name="Coach June",
    ),
]


KNOWLEDGE = {
    "paper_plane": [
        (
            "What is a paper plane?",
            "A paper plane is a toy folded from paper and tossed through the air. It is light and can bend or crumple very easily.",
        )
    ],
    "glider": [
        (
            "What is a glider toy?",
            "A glider toy is a small plane-shaped toy that floats through the air without an engine. Many are light, so rough hands can damage them.",
        )
    ],
    "foam_plane": [
        (
            "Why is a foam plane softer than a paper one?",
            "Foam is squishy and springy, so a foam plane can bounce more than paper or thin wood. It is still a toy, though, and not a real emergency.",
        )
    ],
    "misheard": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or understands something the wrong way. It can cause trouble even when nobody meant to be unkind.",
        )
    ],
    "alarm": [
        (
            "What is a fire alarm for?",
            "A fire alarm is for real danger, like a fire or another true emergency. Pulling it by mistake can scare people and stop everything around you.",
        )
    ],
    "ask_first": [
        (
            "What should you do if you are not sure what grown-ups mean?",
            "Ask a calm question first. A quick question can stop a big mistake.",
        )
    ],
    "break": [
        (
            "Why do careful hands matter with small projects?",
            "Small projects can be fragile, which means they break easily. Careful hands protect the work someone spent time making.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    setting = world.facts["setting"]
    plane = world.facts["plane_cfg"]
    message = world.facts["message_cfg"]
    action = world.facts["action_cfg"]
    return [
        f'Write a short superhero-style story for a 3-to-5-year-old that includes the words "olds" and "plane".',
        f"Tell a story where {hero.id}, wearing a cape at {setting.place}, hears the line {message.spoken!r}, misunderstands it, and makes a big mistake.",
        f"Write a child-facing story with dialogue, a misunderstanding, and a bad ending where a would-be hero chooses to {action.label.replace('_', ' ')} around a {plane.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    organizer = world.facts["organizer"]
    plane = world.facts["plane_cfg"]
    message = world.facts["message_cfg"]
    action = world.facts["action_cfg"]
    pred = world.facts.get("predicted", {})
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a small child in a cape who wanted to act like a superhero. The story also includes {elder.id}, the other olds at the event, and {organizer.id}, who was helping run it.",
        ),
        (
            "What did the grown-ups really mean about the plane?",
            f"They meant {message.meaning}. The words were about a little toy plane at the event, not about people being in danger.",
        ),
        (
            f"Why did {hero.id} make a mistake?",
            f"{hero.id} only heard part of the dialogue and thought it was an emergency. Because {hero.pronoun()} rushed to be brave before asking a question, the misunderstanding turned into real trouble.",
        ),
    ]
    if action.causes_alarm:
        qa.append(
            (
                f"What happened after {hero.id} pulled the alarm?",
                f"The whole event stopped and people had to hurry outside. That happened because the loud bell made everyone think there might be a real emergency.",
            )
        )
    elif action.breaks_plane:
        qa.append(
            (
                f"What happened to the {plane.label}?",
                f"It broke when {hero.id} grabbed at it too roughly. The plane was a small, fragile project, so a fast rescue move ruined it instead of saving anything.",
            )
        )
    elif action.spills_table:
        qa.append(
            (
                f"Why did the table become a mess?",
                f"{hero.id} dove across it to stop an imagined crash, and cups and juice tipped over. The mess spoiled the little show because the misunderstanding made {hero.pronoun('object')} act before listening.",
            )
        )
    ruined = world.facts.get("ruined")
    if ruined:
        qa.append(
            (
                "How did the story end?",
                f"It ended sadly: the event was spoiled and the superhero moment {hero.id} imagined never came true. Even though the grown-ups forgave {hero.pronoun('object')}, the damage could not be undone that day.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["plane_cfg"].tags) | set(world.facts["message_cfg"].tags)
    action = world.facts["action_cfg"]
    if action.causes_alarm:
        tags.add("alarm")
    if action.breaks_plane:
        tags.add("break")
    tags.add("ask_first")
    out: list[tuple[str, str]] = []
    order = ["paper_plane", "glider", "foam_plane", "misheard", "alarm", "break", "ask_first"]
    for tag in order:
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [n for n, on in (("movable", e.movable), ("fragile", e.fragile)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting_id: str, plane_id: str, message_id: str, action_id: str) -> str:
    plane = PLANES[plane_id]
    message = MESSAGES[message_id]
    action = ACTIONS[action_id]
    if plane_id not in SETTINGS[setting_id].supports:
        return (
            f"(No story: {SETTINGS[setting_id].place} does not host a {plane.label} event here, so the misunderstanding has no stage.)"
        )
    if not misunderstanding_plausible(message, action):
        return (
            f"(No story: the line {message.spoken!r} is not strong enough to make {action.label.replace('_', ' ')} a believable superhero misunderstanding.)"
        )
    if not action_hits_plane(action, plane):
        return (
            f"(No story: {action.label.replace('_', ' ')} would not cause a meaningful bad ending with a {plane.label} in this world.)"
        )
    return "(No story: that combination does not make a reasonable misunderstanding story.)"


ASP_RULES = r"""
plausible(Msg, Act) :- message(Msg), action(Act), sounds_like_trouble(Msg), caution(Act, C), caution_min(M), C >= M.
hits_plane(Pl, Act) :- plane(Pl), action(Act), breaks_plane(Act), fragile(Pl).
hits_plane(Pl, Act) :- plane(Pl), action(Act), causes_alarm(Act).
hits_plane(Pl, Act) :- plane(Pl), action(Act), spills_table(Act).

valid(Set, Msg, Act) :- supports(Set, Pl), plausible(Msg, Act), hits_plane(Pl, Act).

outcome(evacuated) :- chosen_action(A), causes_alarm(A).
outcome(broken_plane) :- chosen_action(A), breaks_plane(A), not causes_alarm(A).
outcome(spilled_show) :- chosen_action(A), spills_table(A), not causes_alarm(A), not breaks_plane(A).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for pid in sorted(setting.supports):
            lines.append(asp.fact("supports", sid, pid))
    for pid, plane in PLANES.items():
        lines.append(asp.fact("plane", pid))
        if plane.fragile:
            lines.append(asp.fact("fragile", pid))
    for mid, message in MESSAGES.items():
        lines.append(asp.fact("message", mid))
        if message.sounds_like_trouble:
            lines.append(asp.fact("sounds_like_trouble", mid))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("caution", aid, action.caution))
        if action.breaks_plane:
            lines.append(asp.fact("breaks_plane", aid))
        if action.causes_alarm:
            lines.append(asp.fact("causes_alarm", aid))
        if action.spills_table:
            lines.append(asp.fact("spills_table", aid))
    lines.append(asp.fact("caution_min", CAUTION_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_action", params.action)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return severity_of(ACTIONS[params.action])


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
    for seed in range(20):
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
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(smoke, trace=False, qa=False)
        print("OK: smoke test generate/emit succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero misunderstanding about a plane at an event for olds."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plane", choices=PLANES)
    ap.add_argument("--message", choices=MESSAGES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    plane_filter = args.plane
    if args.setting and args.plane and args.plane not in SETTINGS[args.setting].supports:
        message_guess = args.message or next(iter(MESSAGES))
        action_guess = args.action or next(iter(ACTIONS))
        raise StoryError(explain_rejection(args.setting, args.plane, message_guess, action_guess))
    if args.setting and args.plane and args.message and args.action:
        if (args.setting, args.message, args.action) not in valid_combos() or args.plane not in SETTINGS[args.setting].supports:
            raise StoryError(explain_rejection(args.setting, args.plane, args.message, args.action))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.message is None or c[1] == args.message)
        and (args.action is None or c[2] == args.action)
        and (plane_filter is None or plane_filter in SETTINGS[c[0]].supports)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, message_id, action_id = rng.choice(sorted(combos))
    supported_planes = sorted(pid for pid in SETTINGS[setting_id].supports if action_hits_plane(ACTIONS[action_id], PLANES[pid]))
    if plane_filter is not None:
        if plane_filter not in supported_planes:
            raise StoryError(explain_rejection(setting_id, plane_filter, message_id, action_id))
        plane_id = plane_filter
    else:
        plane_id = rng.choice(supported_planes)

    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder_name = rng.choice(ELDER_NAMES)
    organizer_name = rng.choice([n for n in ORGANIZER_NAMES if n != elder_name])

    return StoryParams(
        setting=setting_id,
        plane=plane_id,
        message=message_id,
        action=action_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_name=elder_name,
        organizer_name=organizer_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.plane not in PLANES:
        raise StoryError(f"(Unknown plane: {params.plane})")
    if params.message not in MESSAGES:
        raise StoryError(f"(Unknown message: {params.message})")
    if params.action not in ACTIONS:
        raise StoryError(f"(Unknown action: {params.action})")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown hero gender: {params.hero_gender})")
    if params.plane not in SETTINGS[params.setting].supports:
        raise StoryError(explain_rejection(params.setting, params.plane, params.message, params.action))
    if (params.setting, params.message, params.action) not in valid_combos():
        raise StoryError(explain_rejection(params.setting, params.plane, params.message, params.action))

    world = tell(
        setting=SETTINGS[params.setting],
        plane_cfg=PLANES[params.plane],
        message_cfg=MESSAGES[params.message],
        action_cfg=ACTIONS[params.action],
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        elder_name=params.elder_name,
        organizer_name=params.organizer_name,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, message, action) combos:\n")
        for setting_id, message_id, action_id in combos:
            supports = ", ".join(sorted(SETTINGS[setting_id].supports))
            print(f"  {setting_id:12} {message_id:12} {action_id:10} [planes: {supports}]")
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
            header = f"### {p.hero_name}: {p.action} at {p.setting} ({p.plane}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
