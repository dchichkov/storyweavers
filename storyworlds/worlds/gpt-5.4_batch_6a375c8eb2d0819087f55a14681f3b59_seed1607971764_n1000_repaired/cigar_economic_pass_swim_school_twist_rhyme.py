#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cigar_economic_pass_swim_school_twist_rhyme.py
=========================================================================

A standalone storyworld for a tiny mystery at swim school.

Seed requirements folded into the domain:
- includes the words "cigar", "economic", and "pass"
- setting: swim school
- features: twist, rhyme
- style: mystery

Core tale imagined from the seed
--------------------------------
A child arrives at swim school with a special economic pool pass. The pass goes
missing just before class. The child worries they will miss the lesson and, for
one moment, suspects the wrong person. A grown-up gives a rhyming clue. The
search follows the real world state: splashes, dry spots, and who tried to keep
the pass safe. The twist is that a helper moved it into a dry place shaped like
a little cigar case or tube so it would not get wet. The pass is found, the
mystery is solved, and the ending image shows a new, safer habit.

Run it
------
    python storyworlds/worlds/gpt-5.4/cigar_economic_pass_swim_school_twist_rhyme.py
    python storyworlds/worlds/gpt-5.4/cigar_economic_pass_swim_school_twist_rhyme.py --pass-type paper_card
    python storyworlds/worlds/gpt-5.4/cigar_economic_pass_swim_school_twist_rhyme.py --hiding splash_bench
    python storyworlds/worlds/gpt-5.4/cigar_economic_pass_swim_school_twist_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/cigar_economic_pass_swim_school_twist_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/cigar_economic_pass_swim_school_twist_rhyme.py --verify
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
LATE_LIMIT = 2


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
        female = {"girl", "woman", "mother", "coach_f"}
        male = {"boy", "man", "father", "coach_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"coach_f": "coach", "coach_m": "coach"}.get(self.type, self.type)
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
class PassType:
    id: str
    label: str
    phrase: str
    material: str
    waterproof: bool
    reusable: bool
    economic_text: str
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
class HidingPlace:
    id: str
    label: str
    phrase: str
    dry: bool
    portable: bool
    cigar_like: bool
    clue_place: str
    reveal_text: str
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
class Helper:
    id: str
    label: str
    role_word: str
    reason: str
    moved_gently: str
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
class RhymeClue:
    id: str
    text: str
    points_to: set[str]
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
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def _r_wet_pass(world: World) -> list[str]:
    out: list[str] = []
    pool = world.get("pool")
    pass_ent = world.get("pass")
    hiding = world.facts["hiding_cfg"]
    if pool.meters["splash_risk"] < THRESHOLD:
        return out
    if hiding.dry:
        return out
    if pass_ent.meters["found"] >= THRESHOLD:
        return out
    sig = ("wet_pass", hiding.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pass_ent.meters["wet"] += 1
    pass_ent.meters["risk"] += 1
    hero = world.get("hero")
    hero.memes["worry"] += 1
    out.append("__wet__")
    return out


def _r_search_progress(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["searched"] < THRESHOLD:
        return out
    sig = ("search_progress", int(hero.meters["searched"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["focus"] += 1
    out.append("__search__")
    return out


CAUSAL_RULES = [
    Rule(name="wet_pass", tag="physical", apply=_r_wet_pass),
    Rule(name="search_progress", tag="mental", apply=_r_search_progress),
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


def needs_dry_hiding(pass_type: PassType) -> bool:
    return not pass_type.waterproof


def valid_combo(pass_type: PassType, hiding: HidingPlace, helper: Helper) -> bool:
    del helper
    if needs_dry_hiding(pass_type) and not hiding.dry:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pid, p in PASS_TYPES.items():
        for hid, h in HIDING_PLACES.items():
            for heid, helper in HELPERS.items():
                if valid_combo(p, h, helper):
                    combos.append((pid, hid, heid))
    return combos


def outcome_for(params: "StoryParams") -> str:
    return "late_join" if params.delay >= LATE_LIMIT else "on_time"


def prediction(pass_type: PassType, hiding: HidingPlace) -> dict:
    return {
        "will_stay_dry": hiding.dry or pass_type.waterproof,
        "risk": 0 if (hiding.dry or pass_type.waterproof) else 1,
    }


def introduce(world: World, hero: Entity, coach: Entity, pass_type: PassType) -> None:
    world.say(
        f"It was early at swim school, and the tiles still shone with sleepy blue light. "
        f"{hero.id} came in holding {pass_type.phrase}, the special economic pass "
        f"that helped {hero.pronoun('possessive')} family pay for lessons a little at a time."
    )
    world.say(
        f"{coach.label_word.capitalize()} {coach.id} smiled and said the class would earn a big-kid "
        f"deep-water badge if everyone remembered the rules and kicked with calm feet."
    )


def setup_need(world: World, hero: Entity, friend: Entity, pass_type: PassType) -> None:
    hero.memes["hope"] += 1
    friend.memes["friendliness"] += 1
    world.say(
        f"{hero.id} wanted that lesson very much. {friend.id}, waiting beside the warm little pool, "
        f"gave a small wave and said today's floating game looked extra fun."
    )
    world.say(
        f"Before class, everyone had to show a pass at the desk, then place towels and shoes in neat rows."
    )
    world.facts["economic_note"] = pass_type.economic_text


def helper_moves_pass(world: World, helper_cfg: Helper, hiding_cfg: HidingPlace) -> None:
    helper = world.get("helper")
    pass_ent = world.get("pass")
    helper.meters["noticed_risk"] = 1.0
    pass_ent.attrs["moved_by"] = helper_cfg.id
    pass_ent.attrs["hiding_place"] = hiding_cfg.id
    world.facts["move_reason"] = helper_cfg.reason
    world.facts["helper_action"] = helper_cfg.moved_gently


def misplace(world: World, hero: Entity, pass_type: PassType, hiding_cfg: HidingPlace) -> None:
    pass_ent = world.get("pass")
    pass_ent.meters["visible"] = 0.0
    pass_ent.meters["found"] = 0.0
    world.say(
        f"When {hero.id} reached for {hero.pronoun('possessive')} {pass_type.label} again, it was gone."
    )
    if hiding_cfg.cigar_like:
        world.say(
            "Near the desk sat a small waterproof tube, long and rounded like a toy cigar case, "
            "though of course it was only for pool things."
        )
    world.say(
        f"{hero.id}'s heart gave one quick thump. If the pass was lost, {hero.pronoun()} might miss the lesson."
    )


def first_suspicion(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["suspicion"] += 1
    friend.memes["hurt"] += 1
    world.say(
        f"For one worried blink, {hero.id} wondered if {friend.id} had picked it up by mistake. "
        f"It was the kind of thought that arrives fast when a mystery feels big."
    )
    world.say(
        f"But {friend.id} only blinked back and held up both empty hands."
    )


def coach_rhyme(world: World, coach: Entity, rhyme_cfg: RhymeClue) -> None:
    coach.memes["calm"] += 1
    world.say(
        f'Coach {coach.id} did not scold. Instead {coach.pronoun()} spoke in a quiet rhyme: '
        f'"{rhyme_cfg.text}"'
    )
    world.facts["rhyme_text"] = rhyme_cfg.text


def search(world: World, hero: Entity, friend: Entity, hiding_cfg: HidingPlace, delay: int) -> None:
    hero.meters["searched"] += 1
    propagate(world, narrate=False)
    hero.meters["searched"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} and {friend.id} searched the cubbies, the towel hooks, and the bench by the little wave picture."
    )
    if delay >= LATE_LIMIT:
        world.say(
            "The first whistle for kicking practice blew while they were still looking, and the mystery suddenly felt even larger."
        )
    else:
        world.say(
            "Water lapped softly nearby, but there was still time if they could solve the puzzle quickly."
        )
    if hiding_cfg.id in {"dry_tube", "goggles_case"}:
        world.say(
            f"Then {friend.id} noticed {hiding_cfg.phrase} near the desk and pointed with a wet little finger."
        )
    elif hiding_cfg.id == "locker_shelf":
        world.say(
            "Then a faint drip tapped below the lockers, and above that sound sat one shelf that stayed dry and still."
        )
    else:
        world.say(
            f"Then they peered toward {hiding_cfg.phrase}, where quiet things waited away from the splashes."
        )


def reveal(world: World, hero: Entity, friend: Entity, hiding_cfg: HidingPlace, helper_cfg: Helper) -> None:
    pass_ent = world.get("pass")
    helper = world.get("helper")
    pass_ent.meters["found"] = 1.0
    pass_ent.meters["visible"] = 1.0
    world.say(
        f"There it was: {hiding_cfg.reveal_text}."
    )
    world.say(
        f"Inside rested the pass, flat and safe."
    )
    world.say(
        f"That was the twist. {helper.label} had {helper_cfg.moved_gently} because {helper_cfg.reason}"
    )
    hero.memes["suspicion"] = 0.0
    friend.memes["hurt"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["kindness"] += 1
    world.facts["twist"] = True


def apology(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f'{hero.id} looked at {friend.id} and whispered, "I am sorry I wondered about you."'
    )
    world.say(
        f'{friend.id} smiled. "Mysteries can make thoughts run too fast," {friend.pronoun()} said. "Now we know."'
    )


def ending(world: World, hero: Entity, coach: Entity, hiding_cfg: HidingPlace, delay: int) -> None:
    hero.memes["confidence"] += 1
    coach.memes["pride"] += 1
    if delay >= LATE_LIMIT:
        hero.meters["missed_beats"] = 1.0
        world.say(
            f"{hero.id} missed the first slow kicks, but Coach {coach.id} waved {hero.pronoun('object')} in for the next turn."
        )
    else:
        world.say(
            f"{hero.id} reached the line just in time and handed over the pass with a breath that finally felt easy."
        )
    world.say(
        f"After class, {hero.id} clipped the pass to a dry strap instead of leaving it loose again."
    )
    if hiding_cfg.cigar_like:
        world.say(
            "The long little tube no longer looked suspicious at all. It looked helpful."
        )
    else:
        world.say(
            "The neat dry spot no longer felt secret. It felt smart."
        )
    world.say(
        f"And when the blue water settled, the whole mystery seemed to rhyme with its own answer: "
        f"keep it dry, and troubles pass by."
    )
def tell(
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    coach_name: str,
    coach_gender: str,
    delay: Delay,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    coach = world.add(Entity(id=coach_name, kind="character", type=coach_gender, role="coach", label="the coach"))
    helper = world.add(Entity(id=helper_cfg.label, kind="character", type="thing", role="helper", label=helper_cfg.label))
    pool = world.add(Entity(id="pool", type="pool", label="the pool"))
    pass_ent = world.add(
        Entity(
            id="pass",
            type="pass",
            label=pass_type.label,
            attrs={"material": pass_type.material, "moved_by": "", "hiding_place": ""},
        )
    )

    hero.memes["worry"] = 0.0
    hero.memes["suspicion"] = 0.0
    hero.memes["relief"] = 0.0
    friend.memes["hurt"] = 0.0
    pool.meters["splash_risk"] = 1.0 if not hiding_cfg.dry else 0.0
    pass_ent.meters["wet"] = 0.0
    pass_ent.meters["risk"] = 0.0
    pass_ent.meters["found"] = 0.0
    pass_ent.meters["visible"] = 1.0
    hero.meters["searched"] = 0.0
    hero.meters["missed_beats"] = 0.0

    world.facts.update(
        pass_cfg=pass_type,
        hiding_cfg=hiding_cfg,
        helper_cfg=helper_cfg,
        rhyme_cfg=rhyme_cfg,
        delay=delay,
    )

    introduce(world, hero, coach, pass_type)
    setup_need(world, hero, friend, pass_type)

    world.para()
    helper_moves_pass(world, helper_cfg, hiding_cfg)
    misplace(world, hero, pass_type, hiding_cfg)
    first_suspicion(world, hero, friend)
    coach_rhyme(world, coach, rhyme_cfg)

    if not prediction(pass_type, hiding_cfg)["will_stay_dry"]:
        propagate(world, narrate=False)

    world.para()
    search(world, hero, friend, hiding_cfg, delay)
    reveal(world, hero, friend, hiding_cfg, helper_cfg)
    apology(world, hero, friend)

    world.para()
    ending(world, hero, coach, hiding_cfg, delay)

    world.facts.update(
        hero=hero,
        friend=friend,
        coach=coach,
        helper=helper,
        pass_ent=pass_ent,
        found=pass_ent.meters["found"] >= THRESHOLD,
        wet=pass_ent.meters["wet"] >= THRESHOLD,
        outcome=outcome_for(
            StoryParams(
                pass_type=pass_type.id,
                hiding=hiding_cfg.id,
                helper=helper_cfg.id,
                rhyme=rhyme_cfg.id,
                hero_name=hero_name,
                hero_gender=hero_gender,
                friend_name=friend_name,
                friend_gender=friend_gender,
                coach_name=coach_name,
                coach_gender=coach_gender,
                delay=delay,
            )
        ),
    )
    return world
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


PASS_TYPES = {
    "paper_card": PassType(
        id="paper_card",
        label="paper pass card",
        phrase="a paper pass card in a clear sleeve",
        material="paper",
        waterproof=False,
        reusable=True,
        economic_text="It was an economic pass, bought in careful little bundles instead of one big fee.",
        tags={"pass", "paper", "economic"},
    ),
    "stamp_book": PassType(
        id="stamp_book",
        label="stamp pass booklet",
        phrase="a tiny stamp pass booklet",
        material="paper",
        waterproof=False,
        reusable=True,
        economic_text="It was an economic pass booklet, the sort families used to count lessons one by one.",
        tags={"pass", "booklet", "economic"},
    ),
    "plastic_tag": PassType(
        id="plastic_tag",
        label="plastic pass tag",
        phrase="a plastic pass tag on a soft band",
        material="plastic",
        waterproof=True,
        reusable=True,
        economic_text="It was an economic pass tag, made to last for many lessons.",
        tags={"pass", "plastic", "economic"},
    ),
}

HIDING_PLACES = {
    "dry_tube": HidingPlace(
        id="dry_tube",
        label="dry tube",
        phrase="the little dry tube",
        dry=True,
        portable=True,
        cigar_like=True,
        clue_place="where long things hide from tides",
        reveal_text="The cap clicked open on the long little dry tube, shaped almost like a cigar case",
        tags={"tube", "dry", "cigar"},
    ),
    "goggles_case": HidingPlace(
        id="goggles_case",
        label="goggles case",
        phrase="the blue goggles case",
        dry=True,
        portable=True,
        cigar_like=False,
        clue_place="where clear eyes sleep dry",
        reveal_text="The blue goggles case snapped open beside the desk",
        tags={"goggles", "dry"},
    ),
    "locker_shelf": HidingPlace(
        id="locker_shelf",
        label="locker shelf",
        phrase="the top locker shelf",
        dry=True,
        portable=False,
        cigar_like=False,
        clue_place="up high where drips do not fly",
        reveal_text="On the top locker shelf, tucked beneath a folded towel, something pale peeked out",
        tags={"locker", "dry"},
    ),
    "splash_bench": HidingPlace(
        id="splash_bench",
        label="splash bench",
        phrase="the splash bench by the pool",
        dry=False,
        portable=False,
        cigar_like=False,
        clue_place="where water can creep",
        reveal_text="On the splash bench by the pool, damp spots glimmered around a bent card",
        tags={"bench", "wet"},
    ),
}

HELPERS = {
    "desk_auntie": Helper(
        id="desk_auntie",
        label="Auntie June",
        role_word="desk helper",
        reason="she saw a bead of pool water near it and wanted to keep it dry",
        moved_gently="slipped it away into the safe spot",
        tags={"helper", "desk"},
    ),
    "coach": Helper(
        id="coach",
        label="Coach Mina",
        role_word="coach",
        reason="she did not want the pass to wrinkle before check-in",
        moved_gently="set it aside in a dry place",
        tags={"helper", "coach"},
    ),
    "janitor": Helper(
        id="janitor",
        label="Mr. Sol",
        role_word="caretaker",
        reason="he was wiping the tiles and did not want the pass blown into a puddle",
        moved_gently="picked it up and tucked it somewhere safe",
        tags={"helper", "cleaning"},
    ),
}

RHYMES = {
    "dry_high": RhymeClue(
        id="dry_high",
        text="If you want your pass to last, look where drips slide low and dry things stay high.",
        points_to={"locker_shelf"},
        tags={"rhyme"},
    ),
    "tube_hide": RhymeClue(
        id="tube_hide",
        text="When splashes swoop and worries grow, seek the snug tube where dry things go.",
        points_to={"dry_tube"},
        tags={"rhyme"},
    ),
    "eyes_case": RhymeClue(
        id="eyes_case",
        text="To solve this school-time little chase, search near the eyes that rest in a case.",
        points_to={"goggles_case"},
        tags={"rhyme"},
    ),
    "mist_near": RhymeClue(
        id="mist_near",
        text="Do not look where splashes creep. Dry secrets never choose wet sleep.",
        points_to={"dry_tube", "goggles_case", "locker_shelf"},
        tags={"rhyme"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Maya", "Ava", "Ella", "Zoe", "Mina", "Tara"]
BOY_NAMES = ["Ben", "Max", "Leo", "Noah", "Eli", "Sam", "Owen", "Finn"]


KNOWLEDGE = {
    "pass": [
        (
            "What is a swim-school pass?",
            "A swim-school pass is a ticket, card, tag, or booklet that shows a child may join class. It helps the grown-ups keep track of lessons."
        )
    ],
    "economic": [
        (
            "What does economic mean in a story like this?",
            "Economic means careful with money and made to cost less or be used wisely. An economic pass can help a family pay for lessons in a manageable way."
        )
    ],
    "paper": [
        (
            "Why should a paper card stay dry near a pool?",
            "Paper bends and wrinkles when it gets wet. If a pass is hard to read, it can be harder to use at the desk."
        )
    ],
    "plastic": [
        (
            "Why is plastic useful for pool things?",
            "Plastic does not soak up water the way paper does. That makes it handy for tags and cases near splashes."
        )
    ],
    "locker": [
        (
            "Why do people use lockers or high shelves at a pool?",
            "They keep towels and small things out of the way and away from splashes. A dry high spot can protect important items."
        )
    ],
    "goggles": [
        (
            "What is a goggles case for?",
            "A goggles case protects goggles when they are not being worn. It can also keep other tiny things dry for a moment if a grown-up uses it carefully."
        )
    ],
    "tube": [
        (
            "What is a dry tube?",
            "A dry tube is a small waterproof container for keeping tiny things dry near water. In this story it is long and rounded, so someone says it looks a bit like a cigar case."
        )
    ],
    "mystery": [
        (
            "What helps solve a mystery?",
            "Good mysteries are solved by looking for clues, checking the real places things could be, and staying calm. Guessing too fast can point at the wrong person."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme clue?",
            "A rhyme clue uses words with matching sounds to make a hint easy to remember. It can guide someone without giving the answer away all at once."
        )
    ],
    "apology": [
        (
            "Why is it good to apologize after a wrong suspicion?",
            "An apology helps mend hurt feelings when you guessed something unfairly. It shows you care more about the truth and the friendship than about being right."
        )
    ],
}
KNOWLEDGE_ORDER = ["pass", "economic", "paper", "plastic", "locker", "goggles", "tube", "mystery", "rhyme", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    pass_cfg = f["pass_cfg"]
    helper_cfg = f["helper_cfg"]
    hiding_cfg = f["hiding_cfg"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old set at swim school that includes the words "economic", "pass", and "cigar".',
        f"Tell a gentle swim-school mystery where {hero.id}'s {pass_cfg.label} goes missing, a grown-up gives a rhyme clue, and the twist is that {helper_cfg.label} moved it to {hiding_cfg.phrase} to keep it safe.",
        "Write a child-facing story with a calm mystery feeling, a wrong suspicion that gets corrected, and an ending image that shows a new careful habit.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    coach = f["coach"]
    pass_cfg = f["pass_cfg"]
    hiding_cfg = f["hiding_cfg"]
    helper_cfg = f["helper_cfg"]
    rhyme_cfg = f["rhyme_cfg"]
    delay = f["delay"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} at swim school, {friend.id} who helps search, and Coach {coach.id}. The mystery begins when {hero.id}'s {pass_cfg.label} disappears before class."
        ),
        (
            "Why was the pass important?",
            f"The pass let {hero.id} check in for the lesson, and it was an economic pass the family used carefully. Losing it felt serious because {hero.id} thought missing it might mean missing class."
        ),
        (
            f"What clue did Coach {coach.id} give?",
            f'Coach {coach.id} gave a rhyme clue: "{rhyme_cfg.text}" The rhyme pointed the search toward a place that stayed dry instead of somewhere splashy.'
        ),
        (
            f"Why did {hero.id} worry at first?",
            f"{hero.id} worried because the pass was needed right before the lesson and suddenly could not be seen. That fast worry made {hero.pronoun()} briefly suspect {friend.id}, even though {friend.id} had done nothing wrong."
        ),
        (
            "What was the twist?",
            f"The twist was that {helper.label} had moved the pass on purpose. {helper.pronoun('subject').capitalize() if helper.type in {'girl', 'boy', 'coach_f', 'coach_m'} else helper.label} {helper_cfg.moved_gently} because {helper_cfg.reason}."
        ),
        (
            "Where was the pass found?",
            f"It was found in {hiding_cfg.phrase}. That place mattered because it kept the pass safe and dry."
        ),
        (
            f"How did the mystery end?",
            (
                f"{hero.id} found the pass, apologized to {friend.id}, and learned to keep it clipped in a dry place after class. "
                + (
                    f"{hero.id} missed the first part of practice but still joined the next turn, so the ending feels relieved instead of sad."
                    if delay >= LATE_LIMIT
                    else f"{hero.id} reached the line in time, which shows the clue and the careful search worked."
                )
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"pass", "economic", "mystery", "rhyme", "apology"}
    pass_cfg = f["pass_cfg"]
    hiding_cfg = f["hiding_cfg"]
    if pass_cfg.material == "paper":
        tags.add("paper")
    if pass_cfg.material == "plastic":
        tags.add("plastic")
    if hiding_cfg.id == "locker_shelf":
        tags.add("locker")
    if hiding_cfg.id == "goggles_case":
        tags.add("goggles")
    if hiding_cfg.id == "dry_tube":
        tags.add("tube")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    pass_type: str
    hiding: str
    helper: str
    rhyme: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    coach_name: str
    coach_gender: str
    delay: int = 0
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        pass_type="paper_card",
        hiding="dry_tube",
        helper="desk_auntie",
        rhyme="tube_hide",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        coach_name="Mina",
        coach_gender="coach_f",
        delay=0,
    ),
    StoryParams(
        pass_type="stamp_book",
        hiding="locker_shelf",
        helper="janitor",
        rhyme="dry_high",
        hero_name="Leo",
        hero_gender="boy",
        friend_name="Ava",
        friend_gender="girl",
        coach_name="Mina",
        coach_gender="coach_f",
        delay=1,
    ),
    StoryParams(
        pass_type="plastic_tag",
        hiding="goggles_case",
        helper="coach",
        rhyme="eyes_case",
        hero_name="Ella",
        hero_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        coach_name="Mina",
        coach_gender="coach_f",
        delay=0,
    ),
    StoryParams(
        pass_type="plastic_tag",
        hiding="dry_tube",
        helper="desk_auntie",
        rhyme="mist_near",
        hero_name="Finn",
        hero_gender="boy",
        friend_name="Zoe",
        friend_gender="girl",
        coach_name="Mina",
        coach_gender="coach_f",
        delay=2,
    ),
]


def explain_rejection(pass_type: PassType, hiding: HidingPlace) -> str:
    return (
        f"(No story: {pass_type.label} is not waterproof, and {hiding.phrase} is a splashy place. "
        f"The helper would not hide an important pass where pool water could soak it. Pick a dry place.)"
    )


ASP_RULES = r"""
needs_dry(P) :- pass_type(P), not waterproof(P).
valid(P,H,He) :- pass_type(P), hiding(H), helper(He), not bad_hiding(P,H).
bad_hiding(P,H) :- needs_dry(P), splashy(H).

late_join :- delay(D), late_limit(L), D >= L.
on_time   :- delay(D), late_limit(L), D < L.

outcome(late_join) :- late_join.
outcome(on_time)   :- on_time.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PASS_TYPES.items():
        lines.append(asp.fact("pass_type", pid))
        if p.waterproof:
            lines.append(asp.fact("waterproof", pid))
    for hid, h in HIDING_PLACES.items():
        lines.append(asp.fact("hiding", hid))
        if not h.dry:
            lines.append(asp.fact("splashy", hid))
    for heid in HELPERS:
        lines.append(asp.fact("helper", heid))
    lines.append(asp.fact("late_limit", LATE_LIMIT))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_for(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_for() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a rhyming swim-school mystery about a missing pass."
    )
    ap.add_argument("--pass-type", choices=PASS_TYPES)
    ap.add_argument("--hiding", choices=HIDING_PLACES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2, 3], help="how long the search takes")
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def _choose_rhyme_for_hiding(rng: random.Random, hiding_id: str) -> str:
    fits = [rid for rid, rhyme in RHYMES.items() if hiding_id in rhyme.points_to]
    if not fits:
        fits = sorted(RHYMES)
    return rng.choice(sorted(fits))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.pass_type and args.hiding:
        pass_cfg = PASS_TYPES[args.pass_type]
        hiding_cfg = HIDING_PLACES[args.hiding]
        if not valid_combo(pass_cfg, hiding_cfg, next(iter(HELPERS.values()))):
            raise StoryError(explain_rejection(pass_cfg, hiding_cfg))

    combos = [
        combo
        for combo in valid_combos()
        if (args.pass_type is None or combo[0] == args.pass_type)
        and (args.hiding is None or combo[1] == args.hiding)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    pass_type, hiding, helper = rng.choice(sorted(combos))
    rhyme = args.rhyme or _choose_rhyme_for_hiding(rng, hiding)
    delay = args.delay if args.delay is not None else rng.randint(0, 3)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    return StoryParams(
        pass_type=pass_type,
        hiding=hiding,
        helper=helper,
        rhyme=rhyme,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        coach_name="Mina",
        coach_gender="coach_f",
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.pass_type not in PASS_TYPES:
        raise StoryError(f"(Unknown pass type: {params.pass_type})")
    if params.hiding not in HIDING_PLACES:
        raise StoryError(f"(Unknown hiding place: {params.hiding})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.rhyme not in RHYMES:
        raise StoryError(f"(Unknown rhyme clue: {params.rhyme})")

    pass_cfg = PASS_TYPES[params.pass_type]
    hiding_cfg = HIDING_PLACES[params.hiding]
    helper_cfg = HELPERS[params.helper]
    if not valid_combo(pass_cfg, hiding_cfg, helper_cfg):
        raise StoryError(explain_rejection(pass_cfg, hiding_cfg))

    world = tell(
        pass_cfg,
        hiding_cfg,
        helper_cfg,
        RHYMES[params.rhyme],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        coach_name=params.coach_name,
        coach_gender=params.coach_gender,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (pass_type, hiding, helper) combos:\n")
        for pass_type, hiding, helper in combos:
            print(f"  {pass_type:12} {hiding:12} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.hero_name}: {p.pass_type} in {p.hiding} ({outcome_for(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
