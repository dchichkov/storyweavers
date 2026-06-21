#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/logic_spaz_sound_effects_problem_solving_fable.py
==============================================================================

A small fable-like storyworld about a jumpy young squirrel named Spaz who hears
strange sounds, guesses danger too quickly, and learns to use logic with a calm
helper. Each story is a complete little problem-solving tale: a mysterious
noise, a sensible investigation, the right fix, and an ending image that proves
the place is peaceful again.

Run it
------
python storyworlds/worlds/gpt-5.4/logic_spaz_sound_effects_problem_solving_fable.py
python storyworlds/worlds/gpt-5.4/logic_spaz_sound_effects_problem_solving_fable.py --place barn --source loose_shutter
python storyworlds/worlds/gpt-5.4/logic_spaz_sound_effects_problem_solving_fable.py --source loose_shutter --fix pebble_pick
python storyworlds/worlds/gpt-5.4/logic_spaz_sound_effects_problem_solving_fable.py --all
python storyworlds/worlds/gpt-5.4/logic_spaz_sound_effects_problem_solving_fable.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/logic_spaz_sound_effects_problem_solving_fable.py --json
python storyworlds/worlds/gpt-5.4/logic_spaz_sound_effects_problem_solving_fable.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen", "goose", "fox", "owl"}
        male = {"boy", "badger", "toad", "mole"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    affords: set[str] = field(default_factory=set)
    image: str = ""
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Source:
    id: str
    label: str
    sound: str
    pattern: str
    clue: str
    location: str
    risk: str
    need: str
    solved_by: str
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
class Fix:
    id: str
    label: str
    handles: set[str] = field(default_factory=set)
    action: str = ""
    after: str = ""
    qa_text: str = ""
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
class Helper:
    id: str
    name: str
    type: str
    title: str
    manner: str
    wisdom: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
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


def _r_noise_fear(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    if source.meters["active_noise"] < THRESHOLD:
        return out
    room = world.get("place")
    sig = ("noise_fear", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["noise"] += 1
    for actor in world.characters():
        if actor.role == "hero":
            actor.memes["fear"] += 1
        if actor.role == "helper":
            actor.memes["focus"] += 1
    out.append("__noise__")
    return out


def _r_reason_relief(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    if source.meters["active_noise"] >= THRESHOLD:
        return out
    sig = ("reason_relief", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("place").meters["noise"] = 0.0
    for actor in world.characters():
        actor.memes["relief"] += 1
    out.append("__quiet__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise_fear", tag="physical", apply=_r_noise_fear),
    Rule(name="reason_relief", tag="emotional", apply=_r_reason_relief),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def source_fits_place(place: Place, source: Source) -> bool:
    return source.id in place.affords


def fix_solves_source(source: Source, fix: Fix) -> bool:
    return source.need in fix.handles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for source_id, source in SOURCES.items():
            if not source_fits_place(place, source):
                continue
            for fix_id, fix in FIXES.items():
                if fix_solves_source(source, fix):
                    combos.append((place_id, source_id, fix_id))
    return sorted(combos)


def expected_fix_ids(source_id: str) -> list[str]:
    if source_id not in SOURCES:
        return []
    source = SOURCES[source_id]
    return sorted(fid for fid, fix in FIXES.items() if fix_solves_source(source, fix))


def predict_solution(world: World, source_cfg: Source, fix_cfg: Fix) -> dict:
    sim = world.copy()
    sim_source = sim.get("source")
    if fix_solves_source(source_cfg, fix_cfg):
        sim_source.meters["active_noise"] = 0.0
        sim_source.meters["mended"] += 1
    propagate(sim, narrate=False)
    return {
        "solved": sim_source.meters["active_noise"] < THRESHOLD,
        "noise": sim.get("place").meters["noise"],
    }


def begin_fable(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"In {world.place.phrase}, a quick little squirrel named {hero.id} lived beside "
        f"{helper.id}, {helper.attrs['title']} of the lane. {world.place.image}"
    )
    world.say(
        f"{hero.id} could leap from barrel to fence in one bright bound, but when a surprise came, "
        f"{hero.pronoun()} gave a jump and a little tail spaz that made the sparrows blink."
    )


def evening_settle(world: World, hero: Entity) -> None:
    hero.memes["calm"] += 1
    world.say(
        f"At dusk the work was done, and {hero.id} hoped for a quiet meal of acorns and warm straw."
    )


def noise_begins(world: World, hero: Entity, source_cfg: Source) -> None:
    source = world.get("source")
    source.meters["active_noise"] = 1.0
    world.facts["heard_sound"] = source_cfg.sound
    propagate(world, narrate=False)
    world.say(
        f"Then the dark gave out a sound: {source_cfg.sound} {source_cfg.sound}!"
    )
    world.say(
        f"It came from {source_cfg.location}, and it {source_cfg.pattern}. "
        f"{hero.id}'s paws froze at once."
    )


def guess_wrong(world: World, hero: Entity, source_cfg: Source) -> None:
    hero.memes["panic"] += 1
    world.say(
        f'"A prowler! A goblin! A storm in a coat!" cried {hero.id}. '
        f'"Something dreadful is hiding there!"'
    )
    world.say(
        f"But the old lane had seen many nights, and the sound was only {source_cfg.risk}, "
        f"not the sort of thing that bites by itself."
    )


def invite_logic(world: World, helper: Entity, hero: Entity, source_cfg: Source) -> None:
    helper.memes["care"] += 1
    hero.memes["attention"] += 1
    world.say(
        f'{helper.id} did not run. {helper.pronoun().capitalize()} listened once, then twice, and said, '
        f'"Let us use logic before fear chooses a story for us."'
    )
    world.say(
        f'{helper.pronoun().capitalize()} pointed toward {source_cfg.location}. '
        f'"Hear how it sounds {source_cfg.pattern}? That is a clue."'
    )


def inspect(world: World, hero: Entity, helper: Entity, source_cfg: Source) -> None:
    hero.memes["curiosity"] += 1
    world.facts["clue"] = source_cfg.clue
    world.say(
        f"So they crept closer together. {helper.id} touched nothing at first and only watched, "
        f"while {hero.id} noticed {source_cfg.clue}."
    )


def choose_fix(world: World, helper: Entity, hero: Entity, source_cfg: Source, fix_cfg: Fix) -> None:
    pred = predict_solution(world, source_cfg, fix_cfg)
    world.facts["predicted_solved"] = pred["solved"]
    helper.memes["confidence"] += 1
    if not pred["solved"]:
        world.say(
            f'"That tool will not help," said {helper.id}. "It does not match the clue."'
        )
        return
    world.say(
        f'"Then the answer is plain," said {helper.id}. "{fix_cfg.label.capitalize()}." '
        f'"The sound tells us what the trouble is, and the trouble tells us what to do."'
    )


def repair(world: World, hero: Entity, helper: Entity, source_cfg: Source, fix_cfg: Fix) -> None:
    source = world.get("source")
    source.meters["active_noise"] = 0.0
    source.meters["mended"] += 1
    world.facts["solved_with"] = fix_cfg.id
    propagate(world, narrate=False)
    world.say(
        f"Together they {fix_cfg.action}."
    )
    world.say(
        f"The noise gave one last small reply -- {fix_cfg.after} -- and then the place grew still."
    )


def ending(world: World, hero: Entity, helper: Entity, source_cfg: Source) -> None:
    hero.memes["trust"] += 1
    hero.memes["wisdom"] += 1
    world.say(
        f"{hero.id} let out the breath {hero.pronoun()} had been hiding and laughed a little. "
        f"{source_cfg.ending}"
    )
    world.say(
        f'From then on, when a strange sound came in the dark, {hero.id} listened before leaping. '
        f"And the lane remembered that ears guided by thought can be braver than feet guided by fright."
    )


def tell(place: Place, source_cfg: Source, fix_cfg: Fix, helper_cfg: Helper) -> World:
    world = World(place)
    hero = world.add(Entity(
        id="Spaz",
        kind="character",
        type="squirrel",
        label="the squirrel",
        role="hero",
        traits=["quick", "jumpy"],
        attrs={},
    ))
    helper = world.add(Entity(
        id=helper_cfg.name,
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.title,
        role="helper",
        traits=[helper_cfg.manner],
        attrs={"title": helper_cfg.title, "wisdom": helper_cfg.wisdom},
    ))
    place_ent = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place.label,
        attrs={"image": place.image},
    ))
    source_ent = world.add(Entity(
        id="source",
        kind="thing",
        type="source",
        label=source_cfg.label,
        attrs={"need": source_cfg.need, "location": source_cfg.location},
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=fix_cfg.label,
        attrs={"handles": sorted(fix_cfg.handles)},
    ))

    world.facts.update(
        place=place,
        source_cfg=source_cfg,
        fix_cfg=fix_cfg,
        helper_cfg=helper_cfg,
        hero=hero,
        helper=helper,
        place_ent=place_ent,
        source=source_ent,
        tool=tool_ent,
        heard_sound=source_cfg.sound,
        clue=source_cfg.clue,
        predicted_solved=False,
        solved_with="",
        moral="Listen first; fear is loud, but logic is wiser.",
    )

    begin_fable(world, hero, helper)
    evening_settle(world, hero)

    world.para()
    noise_begins(world, hero, source_cfg)
    guess_wrong(world, hero, source_cfg)
    invite_logic(world, helper, hero, source_cfg)
    inspect(world, hero, helper, source_cfg)

    world.para()
    choose_fix(world, helper, hero, source_cfg, fix_cfg)
    repair(world, hero, helper, source_cfg, fix_cfg)
    ending(world, hero, helper, source_cfg)

    world.facts["resolved"] = source_ent.meters["active_noise"] < THRESHOLD
    world.facts["quiet"] = place_ent.meters["noise"] < THRESHOLD
    return world


PLACES = {
    "barn": Place(
        id="barn",
        label="barn",
        phrase="a red barn at the edge of the field",
        affords={"loose_shutter", "pebble_in_bucket"},
        image="The moon laid pale boards of light across the hay.",
    ),
    "mill_yard": Place(
        id="mill_yard",
        label="mill yard",
        phrase="the mill yard by the stream",
        affords={"pebble_in_wheel", "wind_in_pipe"},
        image="The wheel slept black and round beside the water.",
    ),
    "orchard_shed": Place(
        id="orchard_shed",
        label="orchard shed",
        phrase="the orchard shed under the pear trees",
        affords={"loose_shutter", "seed_in_tin", "wind_in_pipe"},
        image="Pears shone like little lanterns above the roof.",
    ),
}

SOURCES = {
    "loose_shutter": Source(
        id="loose_shutter",
        label="loose shutter",
        sound="clack-clack",
        pattern="only when the breeze pressed the wall",
        clue="one hook hanging free while the wind nudged the plank",
        location="the side window",
        risk="a board slapping where it should have been tied",
        need="tie",
        solved_by="ribbon_tie",
        ending="The shutter rested against the wall like a bird folding its wing.",
        tags={"wind", "sound", "repair"},
    ),
    "pebble_in_wheel": Source(
        id="pebble_in_wheel",
        label="pebble in a cart wheel",
        sound="ratta-tat",
        pattern="each time the old cart rolled an inch and then stopped",
        clue="a tiny stone caught where the rim kissed the axle",
        location="the leaning turnip cart",
        risk="a small hard thing knocking where a wheel should turn smoothly",
        need="pick",
        solved_by="pebble_pick",
        ending="The cart stood easy again, with nothing left to chatter in its spokes.",
        tags={"wheel", "sound", "repair"},
    ),
    "wind_in_pipe": Source(
        id="wind_in_pipe",
        label="wind in a hollow pipe",
        sound="whooo-eee",
        pattern="only when the gusts slipped across the roof",
        clue="a loose pipe mouth facing the wind like a little flute",
        location="the roof edge",
        risk="a draft singing through a hollow place",
        need="plug",
        solved_by="leaf_plug",
        ending="The roof kept its secrets, and the night air moved past in silence.",
        tags={"wind", "sound", "air"},
    ),
    "seed_in_tin": Source(
        id="seed_in_tin",
        label="seeds in a tin scoop",
        sound="shaka-shaka",
        pattern="whenever the hanging scoop swung from its nail",
        clue="a forgotten handful of pear seeds rattling inside the tin",
        location="a hook by the shed door",
        risk="a harmless little rattle with nowhere soft to rest",
        need="empty",
        solved_by="tip_out",
        ending="The scoop hung quiet at the door, light as an empty silver shell.",
        tags={"seeds", "sound", "tidy"},
    ),
}

FIXES = {
    "ribbon_tie": Fix(
        id="ribbon_tie",
        label="tie the shutter fast with a ribbon",
        handles={"tie"},
        action="looped a stout ribbon around the shutter and fastened it snug to its hook",
        after="clack ... hush",
        qa_text="They tied the loose shutter fast with a ribbon so the wind could not slap it anymore.",
        tags={"repair", "tie"},
    ),
    "pebble_pick": Fix(
        id="pebble_pick",
        label="lift the wheel and pick out the pebble",
        handles={"pick"},
        action="braced the cart, lifted the wheel a little, and picked the pebble from the rim",
        after="tat ... tick ... hush",
        qa_text="They lifted the wheel a little and picked the pebble out, so the knocking stopped.",
        tags={"repair", "wheel"},
    ),
    "leaf_plug": Fix(
        id="leaf_plug",
        label="plug the pipe mouth with a leaf wrap",
        handles={"plug"},
        action="wrapped a broad leaf over the pipe mouth and tied it in place",
        after="whooo ... hmm ... hush",
        qa_text="They covered the pipe mouth with a leaf wrap, so the wind could not whistle through it.",
        tags={"repair", "wind"},
    ),
    "tip_out": Fix(
        id="tip_out",
        label="tip the seeds from the tin scoop",
        handles={"empty"},
        action="tipped the scoop and poured the loose seeds into the grain jar",
        after="shaka ... shake ... hush",
        qa_text="They tipped the seeds out of the scoop, so nothing was left inside to rattle.",
        tags={"tidy", "seeds"},
    ),
    "broom_tap": Fix(
        id="broom_tap",
        label="tap around with a broom handle",
        handles={"poke"},
        action="tapped around with a broom handle and made more noise than before",
        after="tok-tok-tok",
        qa_text="They only tapped around with a broom handle, which did not truly fix the problem.",
        tags={"wrong_fix"},
    ),
}

HELPERS = {
    "owl": Helper(
        id="owl",
        name="Aunt Olwen",
        type="owl",
        title="the old owl",
        manner="calm",
        wisdom="patient listening",
        tags={"owl", "logic"},
    ),
    "toad": Helper(
        id="toad",
        name="Master Reed",
        type="toad",
        title="the old toad",
        manner="steady",
        wisdom="careful looking",
        tags={"toad", "logic"},
    ),
    "badger": Helper(
        id="badger",
        name="Mister Brindle",
        type="badger",
        title="the old badger",
        manner="gentle",
        wisdom="plain good sense",
        tags={"badger", "logic"},
    ),
}


@dataclass
class StoryParams:
    place: str
    source: str
    fix: str
    helper: str
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
    "sound": [
        (
            "Why can a repeated sound help solve a problem?",
            "A repeated sound is a clue. If you listen to when it starts and stops, you can learn what is making it."
        )
    ],
    "logic": [
        (
            "What does logic mean?",
            "Logic means using clues and careful thinking to figure something out. It helps you choose a reason instead of just a guess."
        )
    ],
    "wind": [
        (
            "Why do loose things make noise in the wind?",
            "Wind pushes and shakes anything that is not fastened well. When it bumps or whistles through a gap, you hear a sound."
        )
    ],
    "wheel": [
        (
            "Why would a pebble make a wheel knock?",
            "A wheel should turn smoothly. If a pebble gets stuck where the parts move, each turn can make a little knock."
        )
    ],
    "seeds": [
        (
            "Why do seeds rattle in a tin?",
            "Small hard seeds bounce against the metal sides when the tin moves. That makes a dry shaking sound."
        )
    ],
    "repair": [
        (
            "What is a repair?",
            "A repair is a careful fix for something that is not working right. A good repair matches the real problem."
        )
    ],
    "tidy": [
        (
            "Why does putting things back in the right place help?",
            "Loose things can roll, rattle, or get lost. Putting them away makes a place calmer and easier to use."
        )
    ],
}
KNOWLEDGE_ORDER = ["logic", "sound", "wind", "wheel", "seeds", "repair", "tidy"]


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"]
    source_cfg = world.facts["source_cfg"]
    helper_cfg = world.facts["helper_cfg"]
    return [
        'Write a short fable for a young child that includes the words "logic" and "Spaz", and uses sound effects to drive the plot.',
        f"Tell a gentle animal fable set in {place.phrase} where Spaz hears {source_cfg.sound} in the dark, fears the worst, and a wise helper solves the problem by listening carefully.",
        f"Write a story about problem solving in which {helper_cfg.name} teaches Spaz to use logic, follow a sound clue, and fix a small trouble instead of panicking.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    place = world.facts["place"]
    source_cfg = world.facts["source_cfg"]
    fix_cfg = world.facts["fix_cfg"]
    resolved = world.facts.get("resolved", False)
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little squirrel who startles easily, and {helper.id}, {helper.attrs['title']} who stays calm. They live near {place.label}, where the strange noise began."
        ),
        (
            f"What sound did {hero.id} hear?",
            f"{hero.id} heard '{source_cfg.sound}! {source_cfg.sound}!' coming from {source_cfg.location}. The sound repeated in a pattern, which turned out to be an important clue."
        ),
        (
            f"Why was {hero.id} frightened at first?",
            f"{hero.id} heard a sudden dark-night noise and imagined something dreadful. Fear made {hero.pronoun()} guess before {hero.pronoun()} looked."
        ),
        (
            f"How did {helper.id} use logic to solve the problem?",
            f"{helper.id} listened for when the sound happened and watched what moved nearby. That clue led {helper.pronoun('object')} to the real cause: {source_cfg.risk}."
        ),
    ]
    if resolved:
        out.append(
            (
                "How did they fix the trouble?",
                f"{fix_cfg.qa_text} They matched the fix to the true cause instead of poking around at random."
            )
        )
        out.append(
            (
                "What changed at the end of the story?",
                f"The noise stopped, and the place grew peaceful again. Spaz also changed, because {hero.pronoun()} learned to listen first and let thought guide {hero.pronoun('object')}."
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["source_cfg"].tags) | set(world.facts["fix_cfg"].tags) | set(world.facts["helper_cfg"].tags)
    tags.add("logic")
    tags.add("sound")
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
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", None, [], {})}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="barn",
        source="loose_shutter",
        fix="ribbon_tie",
        helper="owl",
    ),
    StoryParams(
        place="mill_yard",
        source="pebble_in_wheel",
        fix="pebble_pick",
        helper="badger",
    ),
    StoryParams(
        place="orchard_shed",
        source="seed_in_tin",
        fix="tip_out",
        helper="toad",
    ),
    StoryParams(
        place="mill_yard",
        source="wind_in_pipe",
        fix="leaf_plug",
        helper="owl",
    ),
]


def explain_rejection(place_id: Optional[str], source_id: Optional[str], fix_id: Optional[str]) -> str:
    if source_id and source_id not in SOURCES:
        return f"(No story: unknown source '{source_id}'.)"
    if fix_id and fix_id not in FIXES:
        return f"(No story: unknown fix '{fix_id}'.)"
    if place_id and place_id not in PLACES:
        return f"(No story: unknown place '{place_id}'.)"
    if place_id and source_id:
        place = PLACES[place_id]
        source_cfg = SOURCES[source_id]
        if not source_fits_place(place, source_cfg):
            return (
                f"(No story: {source_cfg.label} does not belong in {place.label}. "
                f"Pick a source the place can honestly afford.)"
            )
    if source_id and fix_id:
        source_cfg = SOURCES[source_id]
        fix_cfg = FIXES[fix_id]
        if not fix_solves_source(source_cfg, fix_cfg):
            needed = source_cfg.need
            good = ", ".join(expected_fix_ids(source_id))
            return (
                f"(No story: {fix_cfg.label} does not solve {source_cfg.label}. "
                f"That problem needs a '{needed}' fix. Try: {good}.)"
            )
    return "(No story: this combination does not make sense in the world.)"


ASP_RULES = r"""
fits_place(P, S) :- affords(P, S).
solves(S, F) :- source(S), fix(F), needs(S, N), handles(F, N).
valid(P, S, F) :- place(P), source(S), fix(F), fits_place(P, S), solves(S, F).

expected_fix(S, F) :- solves(S, F).

#show valid/3.
#show expected_fix/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for source_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, source_id))
    for source_id, source_cfg in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("needs", source_id, source_cfg.need))
    for fix_id, fix_cfg in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for handle in sorted(fix_cfg.handles):
            lines.append(asp.fact("handles", fix_id, handle))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_expected_fixes() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "expected_fix")))


def _smoke_emit(sample: StorySample) -> None:
    with contextlib.redirect_stdout(io.StringIO()):
        emit(sample, trace=False, qa=True, header="")


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos() matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in asp:", sorted(asp_valid - py_valid))

    py_expected = {(sid, fid) for sid in SOURCES for fid in expected_fix_ids(sid)}
    asp_expected = set(asp_expected_fixes())
    if py_expected == asp_expected:
        print(f"OK: expected fixes match ASP ({len(py_expected)} source/fix pairs).")
    else:
        rc = 1
        print("MISMATCH in expected fixes:")
        if py_expected - asp_expected:
            print("  only in python:", sorted(py_expected - asp_expected))
        if asp_expected - py_expected:
            print("  only in asp:", sorted(asp_expected - py_expected))

    parser = build_parser()
    smoke_cases: list[StoryParams] = [CURATED[0]]
    try:
        default_args = parser.parse_args([])
        params = resolve_params(default_args, random.Random(123))
        params.seed = 123
        smoke_cases.append(params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE FAIL: default resolve_params crashed: {err}")

    for case in smoke_cases:
        try:
            sample = generate(case)
            if not sample.story.strip():
                raise StoryError("empty story")
            _smoke_emit(sample)
        except Exception as err:  # pragma: no cover - verify path
            rc = 1
            print(f"SMOKE FAIL: generate/emit crashed for {case}: {err}")
    if rc == 0:
        print("OK: generate/emit smoke tests passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fable-like storyworld where Spaz hears a strange sound and learns to solve the problem with logic."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (place, source, fix) combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place is not None and args.place not in PLACES:
        raise StoryError(explain_rejection(args.place, None, None))
    if args.source is not None and args.source not in SOURCES:
        raise StoryError(explain_rejection(None, args.source, None))
    if args.fix is not None and args.fix not in FIXES:
        raise StoryError(explain_rejection(None, None, args.fix))

    if args.place and args.source and not source_fits_place(PLACES[args.place], SOURCES[args.source]):
        raise StoryError(explain_rejection(args.place, args.source, None))
    if args.source and args.fix and not fix_solves_source(SOURCES[args.source], FIXES[args.fix]):
        raise StoryError(explain_rejection(None, args.source, args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id, fix_id = rng.choice(combos)
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(
        place=place_id,
        source=source_id,
        fix=fix_id,
        helper=helper_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.source not in SOURCES or params.fix not in FIXES or params.helper not in HELPERS:
        raise StoryError("(No story: one or more requested parameters are unknown.)")
    if not source_fits_place(PLACES[params.place], SOURCES[params.source]):
        raise StoryError(explain_rejection(params.place, params.source, None))
    if not fix_solves_source(SOURCES[params.source], FIXES[params.fix]):
        raise StoryError(explain_rejection(None, params.source, params.fix))

    world = tell(
        place=PLACES[params.place],
        source_cfg=SOURCES[params.source],
        fix_cfg=FIXES[params.fix],
        helper_cfg=HELPERS[params.helper],
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
        print(f"{len(combos)} valid (place, source, fix) combos:\n")
        for place_id, source_id, fix_id in combos:
            print(f"  {place_id:12} {source_id:16} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = f"### {p.place}: {p.source} -> {p.fix} ({p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
