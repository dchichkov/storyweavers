#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cushion_respite_teamwork_nursery_rhyme.py
====================================================================

A standalone story world for a gentle nursery-rhyme-like tale about teamwork,
a cushion, and a little respite.

Premise
-------
Three small friends are in a cozy place, busy with a bright little play-song.
One of them grows weary or frazzled and needs a quiet rest. The helpers notice,
work together to carry a bulky cushion to the right nook, and add one soothing
aid that truly matches the need. The ending image proves the change: the friend
rests softly, the helpers feel proud, and the game resumes in a gentler way.

Reasonableness constraint
-------------------------
Not every combination makes sense.

* A cushion must actually fit the chosen place.
* The cushion must be light enough for two little helpers to move together.
* The soothing aid must match the reason the friend needs respite.

So the world rejects stories like:
* a porch bench cushion in the nursery,
* a giant daybed cushion that two tiny helpers cannot move,
* a cool cloth offered for plain sleepiness when what is needed is a hush or a
  drowsy comfort.

Run it
------
    python storyworlds/worlds/gpt-5.4/cushion_respite_teamwork_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/cushion_respite_teamwork_nursery_rhyme.py --place nursery --need sleepy --cushion round --aid lullaby
    python storyworlds/worlds/gpt-5.4/cushion_respite_teamwork_nursery_rhyme.py --cushion daybed
    python storyworlds/worlds/gpt-5.4/cushion_respite_teamwork_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/cushion_respite_teamwork_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4/cushion_respite_teamwork_nursery_rhyme.py --verify
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
TEAM_STRENGTH = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    gender: str = "girl"
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.gender == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))


@dataclass
class Place:
    id: str
    label: str
    nook: str
    opening: str
    song_line: str
    allows: set[str] = field(default_factory=set)
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
    cause: str
    sign: str
    meter: str
    soothe_tags: set[str] = field(default_factory=set)
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
class Cushion:
    id: str
    label: str
    phrase: str
    bulk: int
    fits: set[str] = field(default_factory=set)
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
class Aid:
    id: str
    label: str
    phrase: str
    action_text: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "placed": False,
            "aid_given": False,
            "rest_started": False,
            "teamwork_used": False,
        }

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def helpers(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role == "helper"]


def _r_need_rest(world: World) -> list[str]:
    weary = world.get("weary")
    sig = ("need_rest", weary.id)
    if weary.meters["needs_rest"] >= THRESHOLD:
        return []
    for key in ("sleepy", "footsore", "frazzled"):
        if weary.meters[key] >= THRESHOLD:
            if sig in world.fired:
                return []
            world.fired.add(sig)
            weary.meters["needs_rest"] += 1
            weary.memes["droop"] += 1
            return ["__need_rest__"]
    return []


def _r_respite(world: World) -> list[str]:
    weary = world.get("weary")
    cushion = world.get("cushion")
    aid = world.get("aid")
    need = weary.attrs["need"]
    sig = ("respite", weary.id)
    if sig in world.fired:
        return []
    if (
        weary.meters["needs_rest"] >= THRESHOLD
        and cushion.meters["at_nook"] >= THRESHOLD
        and aid.meters["given"] >= THRESHOLD
        and need.id in aid.attrs["soothes"]
    ):
        world.fired.add(sig)
        weary.meters["rested"] += 1
        weary.meters["needs_rest"] = 0.0
        weary.memes["calm"] += 1
        weary.memes["comfort"] += 1
        for helper in world.helpers():
            helper.memes["pride"] += 1
            helper.memes["care"] += 1
        world.facts["rest_started"] = True
        return ["__respite__"]
    return []


CAUSAL_RULES = [
    Rule(name="need_rest", tag="physical", apply=_r_need_rest),
    Rule(name="respite", tag="social", apply=_r_respite),
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


PLACES = {
    "nursery": Place(
        id="nursery",
        label="the nursery",
        nook="by the crib",
        opening="In the nursery, morning light made pale gold squares on the floor.",
        song_line="Clap and tap, tap and clap, the little game went round.",
        allows={"round", "window"},
        tags={"room", "rest"},
    ),
    "sunroom": Place(
        id="sunroom",
        label="the sunroom",
        nook="by the warm window",
        opening="In the sunroom, sunbeams striped the rug and made the dust look like little stars.",
        song_line="Hop and hum, hum and hop, the little tune skipped on.",
        allows={"round", "window"},
        tags={"window", "rest"},
    ),
    "porch": Place(
        id="porch",
        label="the porch",
        nook="on the painted bench",
        opening="On the porch, the boards were warm and the flowerpots nodded in a row.",
        song_line="Pat and sway, sway and pat, the porch-song bobbed along.",
        allows={"bench"},
        tags={"bench", "outside"},
    ),
}

NEEDS = {
    "sleepy": Need(
        id="sleepy",
        cause="too much dancing and humming",
        sign="her eyes began to blink more slowly than the song.",
        meter="sleepy",
        soothe_tags={"hush", "drowse"},
        tags={"sleep", "rest"},
    ),
    "footsore": Need(
        id="footsore",
        cause="too much tiptoe skipping",
        sign="her toes tucked in, and each little step came soft and small.",
        meter="footsore",
        soothe_tags={"soft", "cool"},
        tags={"feet", "rest"},
    ),
    "frazzled": Need(
        id="frazzled",
        cause="too much clang and bustle",
        sign="the bright noise made her ears fold back, and she wanted somewhere still.",
        meter="frazzled",
        soothe_tags={"hush", "cool"},
        tags={"quiet", "rest"},
    ),
}

CUSHIONS = {
    "round": Cushion(
        id="round",
        label="round cushion",
        phrase="a plump round cushion",
        bulk=2,
        fits={"nursery", "sunroom"},
        tags={"soft", "cushion"},
    ),
    "window": Cushion(
        id="window",
        label="window cushion",
        phrase="a long window cushion",
        bulk=2,
        fits={"nursery", "sunroom"},
        tags={"soft", "window", "cushion"},
    ),
    "bench": Cushion(
        id="bench",
        label="bench cushion",
        phrase="a striped bench cushion",
        bulk=2,
        fits={"porch"},
        tags={"soft", "bench", "cushion"},
    ),
    "daybed": Cushion(
        id="daybed",
        label="daybed cushion",
        phrase="a great puffy daybed cushion",
        bulk=4,
        fits={"sunroom"},
        tags={"soft", "huge", "cushion"},
    ),
}

AIDS = {
    "lullaby": Aid(
        id="lullaby",
        label="lullaby",
        phrase="a hush-hush lullaby",
        action_text="sang a hush-hush lullaby together",
        tags={"hush", "drowse"},
    ),
    "book": Aid(
        id="book",
        label="picture book",
        phrase="a small picture book with moonlit pages",
        action_text="opened the moonlit picture book and turned the pages slowly",
        tags={"hush", "drowse"},
    ),
    "coolcloth": Aid(
        id="coolcloth",
        label="cool cloth",
        phrase="a cool cloth",
        action_text="laid a cool cloth across the tired place and held it there gently",
        tags={"cool"},
    ),
    "blanket": Aid(
        id="blanket",
        label="soft blanket",
        phrase="a soft blanket",
        action_text="tucked a soft blanket close and made a quiet little tent of calm",
        tags={"hush", "soft"},
    ),
}

CHARACTERS = [
    {"name": "Pip", "species": "duckling", "gender": "boy"},
    {"name": "Mina", "species": "kitten", "gender": "girl"},
    {"name": "Tess", "species": "lamb", "gender": "girl"},
    {"name": "Ollie", "species": "mouse", "gender": "boy"},
    {"name": "Nell", "species": "bunny", "gender": "girl"},
    {"name": "Theo", "species": "puppy", "gender": "boy"},
]


def place_accepts_cushion(place: Place, cushion: Cushion) -> bool:
    return cushion.id in place.allows and place.id in cushion.fits


def movable(cushion: Cushion) -> bool:
    return cushion.bulk <= TEAM_STRENGTH


def aid_matches_need(aid: Aid, need: Need) -> bool:
    return bool(set(aid.tags) & set(need.soothe_tags))


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for need_id, need in NEEDS.items():
            for cushion_id, cushion in CUSHIONS.items():
                for aid_id, aid in AIDS.items():
                    if (
                        place_accepts_cushion(place, cushion)
                        and movable(cushion)
                        and aid_matches_need(aid, need)
                    ):
                        out.append((place_id, need_id, cushion_id, aid_id))
    return sorted(out)


@dataclass
class StoryParams:
    place: str
    need: str
    cushion: str
    aid: str
    weary_name: str
    weary_species: str
    weary_gender: str
    helper1_name: str
    helper1_species: str
    helper1_gender: str
    helper2_name: str
    helper2_species: str
    helper2_gender: str
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v.id if hasattr(v, 'id') else v for k, v in ent.attrs.items() if v}
            bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_cushion(place: Place, cushion: Cushion) -> str:
    if place.id not in cushion.fits or cushion.id not in place.allows:
        return (
            f"(No story: {cushion.phrase} does not belong in {place.label}. "
            f"It does not fit the resting nook there.)"
        )
    if cushion.bulk > TEAM_STRENGTH:
        return (
            f"(No story: {cushion.phrase} is too bulky for two little helpers to move "
            f"together, so the teamwork turn cannot happen.)"
        )
    return "(No story: this cushion does not work here.)"


def explain_aid(need: Need, aid: Aid) -> str:
    return (
        f"(No story: {aid.phrase} does not truly help a friend who feels {need.id}. "
        f"The respite aid must match the need.)"
    )


def pick_three_characters(rng: random.Random) -> list[dict]:
    return rng.sample(CHARACTERS, 3)


def introduce(world: World, weary: Entity, h1: Entity, h2: Entity, need: Need) -> None:
    world.say(world.place.opening)
    world.say(
        f"{weary.id} the {weary.type}, {h1.id} the {h1.type}, and {h2.id} the {h2.type} "
        f"played in a ring. {world.place.song_line}"
    )
    for ent in (weary, h1, h2):
        ent.memes["joy"] += 1
    world.say(
        f"They were busy with {need.cause}, and the room seemed to sing with them."
    )


def droop(world: World, weary: Entity, need: Need) -> None:
    weary.meters[need.meter] += 1
    propagate(world, narrate=False)
    world.say(
        f"But after a while, {weary.id} grew {need.id}. {need.sign}"
    )
    world.say(
        f'"I think I need a little respite," {weary.id} whispered.'
    )


def notice(world: World, h1: Entity, h2: Entity, weary: Entity, need: Need) -> None:
    for helper in (h1, h2):
        helper.memes["care"] += 1
    if need.id == "footsore":
        world.say(
            f"{h1.id} looked at {weary.id}'s tiny feet, and {h2.id} nodded at once."
        )
    elif need.id == "frazzled":
        world.say(
            f"{h1.id} heard the hurry in the room, and {h2.id} lowered the game-song to a murmur."
        )
    else:
        world.say(
            f"{h1.id} saw the slow blink in {weary.id}'s eyes, and {h2.id} grew gentle too."
        )


def try_alone(world: World, h1: Entity, cushion: Cushion) -> None:
    h1.memes["effort"] += 1
    world.say(
        f"{h1.id} hurried to fetch {cushion.phrase}. {h1.pronoun('subject').capitalize()} tugged once, "
        f"and the cushion scooted only a little puff."
    )
    world.say(
        f"It was too big for one pair of paws alone."
    )


def team_lift(world: World, h1: Entity, h2: Entity, cushion_ent: Entity, cushion: Cushion) -> None:
    world.facts["teamwork_used"] = True
    h1.memes["teamwork"] += 1
    h2.memes["teamwork"] += 1
    cushion_ent.meters["at_nook"] += 1
    world.facts["placed"] = True
    world.say(
        f'"Then two can do what one cannot do," said {h2.id}.'
    )
    world.say(
        f"So {h1.id} took one side, {h2.id} took the other, and together they carried "
        f"{cushion.phrase} to {world.place.nook}."
    )


def settle(world: World, weary: Entity, aid_ent: Entity, aid: Aid) -> None:
    aid_ent.meters["given"] += 1
    world.facts["aid_given"] = True
    if weary.attrs["need"].id == "footsore":
        world.say(
            f"{weary.id} curled upon the cushion, and the helpers {aid.action_text}."
        )
    else:
        world.say(
            f"{weary.id} curled upon the cushion while the helpers {aid.action_text}."
        )
    propagate(world, narrate=False)
    world.say(
        f"Soon {weary.id}'s breath went slow and easy."
    )


def ending(world: World, weary: Entity, h1: Entity, h2: Entity, aid: Aid) -> None:
    if "drowse" in aid.tags:
        last = f"{weary.id} rested like a small moon on the cushion"
    elif "cool" in aid.tags:
        last = f"{weary.id} rested with a soft sigh on the cushion"
    else:
        last = f"{weary.id} rested in a hush of blanket and bloom on the cushion"
    world.say(
        f"{h1.id} and {h2.id} sat nearby, proud and still. Because they worked as a team, "
        f"{last}, and the whole place learned a quieter tune."
    )


def tell(
    place: Place,
    need: Need,
    cushion: Cushion,
    aid: Aid,
    weary_name: str,
    weary_species: str,
    weary_gender: str,
    helper1_name: str,
    helper1_species: str,
    helper1_gender: str,
    helper2_name: str,
    helper2_species: str,
    helper2_gender: str,
) -> World:
    world = World(place)
    weary = world.add(
        Entity(
            id=weary_name,
            kind="character",
            type=weary_species,
            label=weary_species,
            role="weary",
            gender=weary_gender,
            attrs={"need": need},
        )
    )
    h1 = world.add(
        Entity(
            id=helper1_name,
            kind="character",
            type=helper1_species,
            label=helper1_species,
            role="helper",
            gender=helper1_gender,
            attrs={},
        )
    )
    h2 = world.add(
        Entity(
            id=helper2_name,
            kind="character",
            type=helper2_species,
            label=helper2_species,
            role="helper",
            gender=helper2_gender,
            attrs={},
        )
    )
    cushion_ent = world.add(
        Entity(
            id="cushion",
            type="cushion",
            label=cushion.label,
            phrase=cushion.phrase,
            attrs={"bulk": cushion.bulk},
            tags=set(cushion.tags),
        )
    )
    aid_ent = world.add(
        Entity(
            id="aid",
            type="aid",
            label=aid.label,
            phrase=aid.phrase,
            attrs={"soothes": set(need_id for need_id, need_cfg in NEEDS.items() if aid_matches_need(aid, need_cfg))},
            tags=set(aid.tags),
        )
    )

    introduce(world, weary, h1, h2, need)
    world.para()
    droop(world, weary, need)
    notice(world, h1, h2, weary, need)
    try_alone(world, h1, cushion)
    team_lift(world, h1, h2, cushion_ent, cushion)
    world.para()
    settle(world, weary, aid_ent, aid)
    ending(world, weary, h1, h2, aid)

    world.facts.update(
        place=place,
        need=need,
        cushion_cfg=cushion,
        aid_cfg=aid,
        weary=weary,
        helper1=h1,
        helper2=h2,
        soothed=world.facts["rest_started"],
    )
    return world


KNOWLEDGE = {
    "sleep": [
        (
            "What does sleepy mean?",
            "Sleepy means your body and eyes are telling you they want rest. A sleepy child often blinks slowly and wants a quiet place."
        )
    ],
    "feet": [
        (
            "Why can feet feel sore after lots of skipping?",
            "Feet work hard when you hop and skip, so they can grow tired and sore. A soft place to sit and a little rest can help them feel better."
        )
    ],
    "quiet": [
        (
            "Why do some children want a quiet place after loud play?",
            "Loud play can make a body feel busy inside, even when the game is fun. A quiet corner gives the mind a chance to settle down."
        )
    ],
    "cushion": [
        (
            "What is a cushion for?",
            "A cushion is a soft pad for sitting or resting. It can make a hard place gentler and more comfortable."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another to do one job together. Sometimes two small helpers can do what one alone cannot."
        )
    ],
    "lullaby": [
        (
            "What is a lullaby?",
            "A lullaby is a soft, gentle song meant to calm someone who is tired or upset. Its slow rhythm helps the body feel safe and quiet."
        )
    ],
    "book": [
        (
            "Why can a quiet picture book help someone rest?",
            "A quiet picture book slows things down because you look and turn pages gently. That calm pace can help a busy mind settle."
        )
    ],
    "coolcloth": [
        (
            "What can a cool cloth do?",
            "A cool cloth feels fresh and soothing on a tired spot. It can help someone feel more comfortable while they rest."
        )
    ],
    "blanket": [
        (
            "Why can a blanket feel comforting?",
            "A blanket feels soft and close around you. That cozy feeling can make a resting place seem calmer and safer."
        )
    ],
}
KNOWLEDGE_ORDER = ["sleep", "feet", "quiet", "cushion", "teamwork", "lullaby", "book", "coolcloth", "blanket"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    weary = f["weary"]
    h1 = f["helper1"]
    h2 = f["helper2"]
    need = f["need"]
    cushion = f["cushion_cfg"]
    aid = f["aid_cfg"]
    return [
        (
            f'Write a short nursery-rhyme-style story for a 3-to-5-year-old that uses the words '
            f'"cushion" and "respite" and shows teamwork.'
        ),
        (
            f"Tell a gentle story where {weary.id} grows {need.id} during play, and "
            f"{h1.id} and {h2.id} work together to carry {cushion.phrase} and help "
            f"{weary.pronoun('object')} rest."
        ),
        (
            f"Write a cozy rhyming story in {f['place'].label} where two friends notice a tired child, "
            f"choose a fitting respite aid like {aid.label}, and solve the problem by helping together."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    weary = f["weary"]
    h1 = f["helper1"]
    h2 = f["helper2"]
    need = f["need"]
    cushion = f["cushion_cfg"]
    aid = f["aid_cfg"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {weary.id}, who needed a little respite, and {h1.id} and {h2.id}, who helped. "
            f"They were small friends playing together in {f['place'].label}."
        ),
        (
            f"Why did {weary.id} need a respite?",
            f"{weary.id} needed a respite because {need.cause} left {weary.pronoun('object')} feeling {need.id}. "
            f"The story shows that play can be happy and still make a small body need rest."
        ),
        (
            f"Why could {h1.id} not move the cushion alone?",
            f"{h1.id} tugged at {cushion.phrase}, but it was too bulky for one little helper. "
            f"The problem changed when {h2.id} joined in and they lifted one side each."
        ),
        (
            "How did teamwork solve the problem?",
            f"{h1.id} and {h2.id} carried the cushion together to the resting nook and then used {aid.label} to soothe {weary.id}. "
            f"Because they shared the job, the cushion reached the right place and the respite could begin."
        ),
        (
            f"How do you know the ending was peaceful?",
            f"The ending is peaceful because {weary.id}'s breathing grows slow and easy, and the helpers sit nearby in a quieter mood. "
            f"The last image of resting on the cushion proves the room changed from busy play to gentle calm."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    need = world.facts["need"]
    aid = world.facts["aid_cfg"]
    tags = {"cushion", "teamwork"}
    if need.id == "sleepy":
        tags.add("sleep")
    elif need.id == "footsore":
        tags.add("feet")
    else:
        tags.add("quiet")
    if aid.id in KNOWLEDGE:
        tags.add(aid.id)
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


CURATED = [
    StoryParams(
        place="nursery",
        need="sleepy",
        cushion="round",
        aid="lullaby",
        weary_name="Pip",
        weary_species="duckling",
        weary_gender="boy",
        helper1_name="Mina",
        helper1_species="kitten",
        helper1_gender="girl",
        helper2_name="Tess",
        helper2_species="lamb",
        helper2_gender="girl",
    ),
    StoryParams(
        place="sunroom",
        need="frazzled",
        cushion="window",
        aid="blanket",
        weary_name="Nell",
        weary_species="bunny",
        weary_gender="girl",
        helper1_name="Theo",
        helper1_species="puppy",
        helper1_gender="boy",
        helper2_name="Ollie",
        helper2_species="mouse",
        helper2_gender="boy",
    ),
    StoryParams(
        place="porch",
        need="footsore",
        cushion="bench",
        aid="coolcloth",
        weary_name="Tess",
        weary_species="lamb",
        weary_gender="girl",
        helper1_name="Pip",
        helper1_species="duckling",
        helper1_gender="boy",
        helper2_name="Nell",
        helper2_species="bunny",
        helper2_gender="girl",
    ),
    StoryParams(
        place="sunroom",
        need="sleepy",
        cushion="window",
        aid="book",
        weary_name="Mina",
        weary_species="kitten",
        weary_gender="girl",
        helper1_name="Theo",
        helper1_species="puppy",
        helper1_gender="boy",
        helper2_name="Pip",
        helper2_species="duckling",
        helper2_gender="boy",
    ),
]


ASP_RULES = r"""
fits_in_place(P,C) :- place(P), cushion(C), place_allows(P,C), cushion_fits(C,P).
movable(C) :- cushion(C), bulk(C,B), team_strength(T), B <= T.
aid_matches(N,A) :- need(N), aid(A), soothes(N,T), aid_tag(A,T).

valid(P,N,C,A) :- fits_in_place(P,C), movable(C), aid_matches(N,A).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for cid in sorted(place.allows):
            lines.append(asp.fact("place_allows", pid, cid))
    for nid, need in NEEDS.items():
        lines.append(asp.fact("need", nid))
        for tag in sorted(need.soothe_tags):
            lines.append(asp.fact("soothes", nid, tag))
    for cid, cushion in CUSHIONS.items():
        lines.append(asp.fact("cushion", cid))
        lines.append(asp.fact("bulk", cid, cushion.bulk))
        for pid in sorted(cushion.fits):
            lines.append(asp.fact("cushion_fits", cid, pid))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for tag in sorted(aid.tags):
            lines.append(asp.fact("aid_tag", aid_id, tag))
    lines.append(asp.fact("team_strength", TEAM_STRENGTH))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def outcome_smoke(params: StoryParams) -> bool:
    sample = generate(params)
    return bool(sample.story.strip()) and "cushion" in sample.story.lower() and "respite" in sample.story.lower()


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from curated smoke test")
        emit(sample, trace=False, qa=False, header="### smoke")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        if not outcome_smoke(params):
            raise StoryError("default-resolved story missed required seed words")
        print("OK: default resolve/generate smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A nursery-rhyme-like storyworld about teamwork, a cushion, and a little respite."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--need", choices=sorted(NEEDS))
    ap.add_argument("--cushion", choices=sorted(CUSHIONS))
    ap.add_argument("--aid", choices=sorted(AIDS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cushion:
        place = PLACES[args.place]
        cushion = CUSHIONS[args.cushion]
        if not place_accepts_cushion(place, cushion) or not movable(cushion):
            raise StoryError(explain_cushion(place, cushion))
    if args.need and args.aid:
        need = NEEDS[args.need]
        aid = AIDS[args.aid]
        if not aid_matches_need(aid, need):
            raise StoryError(explain_aid(need, aid))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.need is None or combo[1] == args.need)
        and (args.cushion is None or combo[2] == args.cushion)
        and (args.aid is None or combo[3] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, need_id, cushion_id, aid_id = rng.choice(combos)
    trio = pick_three_characters(rng)
    return StoryParams(
        place=place_id,
        need=need_id,
        cushion=cushion_id,
        aid=aid_id,
        weary_name=trio[0]["name"],
        weary_species=trio[0]["species"],
        weary_gender=trio[0]["gender"],
        helper1_name=trio[1]["name"],
        helper1_species=trio[1]["species"],
        helper1_gender=trio[1]["gender"],
        helper2_name=trio[2]["name"],
        helper2_species=trio[2]["species"],
        helper2_gender=trio[2]["gender"],
    )


def validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.need not in NEEDS:
        raise StoryError(f"(Unknown need: {params.need})")
    if params.cushion not in CUSHIONS:
        raise StoryError(f"(Unknown cushion: {params.cushion})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    place = PLACES[params.place]
    need = NEEDS[params.need]
    cushion = CUSHIONS[params.cushion]
    aid = AIDS[params.aid]
    if not place_accepts_cushion(place, cushion) or not movable(cushion):
        raise StoryError(explain_cushion(place, cushion))
    if not aid_matches_need(aid, need):
        raise StoryError(explain_aid(need, aid))


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(
        place=PLACES[params.place],
        need=NEEDS[params.need],
        cushion=CUSHIONS[params.cushion],
        aid=AIDS[params.aid],
        weary_name=params.weary_name,
        weary_species=params.weary_species,
        weary_gender=params.weary_gender,
        helper1_name=params.helper1_name,
        helper1_species=params.helper1_species,
        helper1_gender=params.helper1_gender,
        helper2_name=params.helper2_name,
        helper2_species=params.helper2_species,
        helper2_gender=params.helper2_gender,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, need, cushion, aid) combos:\n")
        for place, need, cushion, aid in combos:
            print(f"  {place:8} {need:9} {cushion:7} {aid}")
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
            header = f"### {p.weary_name}: {p.need} in {p.place} ({p.cushion}, {p.aid})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
