#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sigh_murky_adoption_garage_magic_tall_tale.py
========================================================================

A standalone storyworld for a tall-tale garage story about a magical foundling.
A child hears a great sigh in a murky garage corner, discovers a tiny magical
creature, and learns that adoption means making a safe home, not simply saying
"mine."

Run it
------
    python storyworlds/worlds/gpt-5.4/sigh_murky_adoption_garage_magic_tall_tale.py
    python storyworlds/worlds/gpt-5.4/sigh_murky_adoption_garage_magic_tall_tale.py --creature wrench_dragon
    python storyworlds/worlds/gpt-5.4/sigh_murky_adoption_garage_magic_tall_tale.py --delay 2
    python storyworlds/worlds/gpt-5.4/sigh_murky_adoption_garage_magic_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/sigh_murky_adoption_garage_magic_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/sigh_murky_adoption_garage_magic_tall_tale.py --json
    python storyworlds/worlds/gpt-5.4/sigh_murky_adoption_garage_magic_tall_tale.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"grandfather": "grandpa", "grandmother": "grandma"}.get(self.type, self.type)


@dataclass
class Creature:
    id: str
    label: str
    phrase: str
    boast: str
    sigh_text: str
    spark_text: str
    comfort_need: str
    home_need: str
    skittishness: int
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
    murk_word: str
    severity: int
    found_here: set[str] = field(default_factory=set)
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
class Comfort:
    id: str
    label: str
    phrase: str
    soothe_text: str
    need_tag: str
    soothe: int
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
class Home:
    id: str
    label: str
    phrase: str
    build_text: str
    need_tag: str
    stability: int
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
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        clone.paragraphs = [[]]
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
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


def _r_fear_from_murk(world: World) -> list[str]:
    creature = world.entities.get("creature")
    if creature is None:
        return []
    if creature.meters["murk"] < THRESHOLD:
        return []
    sig = ("fear_from_murk", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.memes["fear"] += 1
    creature.memes["lonely"] += 1
    return ["__murky__"]


def _r_trust_when_settled(world: World) -> list[str]:
    creature = world.entities.get("creature")
    child = world.entities.get("child")
    if creature is None or child is None:
        return []
    if creature.meters["clean"] < THRESHOLD or creature.meters["settled"] < THRESHOLD:
        return []
    sig = ("trust_when_settled", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.memes["trust"] += 1
    child.memes["hope"] += 1
    return ["__trust__"]


def _r_magic_grows(world: World) -> list[str]:
    creature = world.entities.get("creature")
    if creature is None:
        return []
    if creature.memes["trust"] < THRESHOLD:
        return []
    sig = ("magic_grows", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["glow"] += 1
    return ["__glow__"]


CAUSAL_RULES = [
    Rule(name="fear_from_murk", tag="emotion", apply=_r_fear_from_murk),
    Rule(name="trust_when_settled", tag="emotion", apply=_r_trust_when_settled),
    Rule(name="magic_grows", tag="physical", apply=_r_magic_grows),
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


def valid_combo(creature: Creature, hiding: HidingPlace, comfort: Comfort, home: Home) -> bool:
    return (
        creature.id in hiding.found_here
        and creature.comfort_need == comfort.need_tag
        and creature.home_need == home.need_tag
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for cid, creature in CREATURES.items():
        for hid, hiding in HIDING_PLACES.items():
            for comfort_id, comfort in COMFORTS.items():
                for home_id, home in HOMES.items():
                    if valid_combo(creature, hiding, comfort, home):
                        combos.append((cid, hid, comfort_id, home_id))
    return combos


def adoption_score(creature: Creature, hiding: HidingPlace, comfort: Comfort, home: Home, delay: int) -> int:
    return comfort.soothe + home.stability - (hiding.severity + creature.skittishness + delay)


def outcome_of(params: "StoryParams") -> str:
    creature = CREATURES[params.creature]
    hiding = HIDING_PLACES[params.hiding]
    comfort = COMFORTS[params.comfort]
    home = HOMES[params.home]
    return "adopted" if adoption_score(creature, hiding, comfort, home, params.delay) >= 0 else "visited"


def explain_rejection(creature: Creature, hiding: HidingPlace, comfort: Comfort, home: Home) -> str:
    if creature.id not in hiding.found_here:
        return (
            f"(No story: {creature.label} does not sensibly hide in {hiding.phrase}. "
            f"Pick a hiding place where that magical creature could plausibly be found.)"
        )
    if creature.comfort_need != comfort.need_tag:
        return (
            f"(No story: {comfort.label} is the wrong kind of comfort for a {creature.label}. "
            f"That creature needs {creature.comfort_need.replace('_', ' ')}.)"
        )
    if creature.home_need != home.need_tag:
        return (
            f"(No story: {home.label} is not a proper nook for a {creature.label}. "
            f"That creature needs {creature.home_need.replace('_', ' ')}.)"
        )
    return "(No story: that combination does not make sense in this world.)"


def predict_outcome(world: World, comfort: Comfort, home: Home, delay: int) -> dict:
    sim = world.copy()
    creature_cfg: Creature = sim.facts["creature_cfg"]
    hiding_cfg: HidingPlace = sim.facts["hiding_cfg"]
    creature = sim.get("creature")
    creature.meters["clean"] += 1
    creature.meters["settled"] += 1
    sim.facts["care_score"] = comfort.soothe + home.stability
    sim.facts["fear_score"] = hiding_cfg.severity + creature_cfg.skittishness + delay
    propagate(sim, narrate=False)
    adopted = sim.facts["care_score"] >= sim.facts["fear_score"]
    return {
        "adopted": adopted,
        "care_score": sim.facts["care_score"],
        "fear_score": sim.facts["fear_score"],
        "glow": sim.get("creature").meters["glow"],
    }


@dataclass
class StoryParams:
    creature: str
    hiding: str
    comfort: str
    home: str
    child_name: str
    child_gender: str
    grownup: str
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


def introduce(world: World, child: Entity, grownup: Entity) -> None:
    world.say(
        f"On a rainy afternoon, {child.id} helped {child.pronoun('possessive')} "
        f"{grownup.label_word} sort the garage, where towers of boxes leaned so high "
        f"they looked ready to shake hands with the clouds."
    )


def garage_tall_tale(world: World, child: Entity) -> None:
    world.say(
        f"The old garage was a kingdom of ladders, coffee cans full of bolts, and "
        f"shelves that stretched so far above {child.id}'s head they seemed to comb the thunder."
    )


def hear_sigh(world: World, child: Entity, hiding: HidingPlace) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Just then a sigh rolled out of {hiding.phrase}, long and low and lonely, "
        f"as if the garage door itself had grown a heart and decided to complain."
    )
    world.say(
        f"{child.id} followed the sound to {hiding.phrase}, where the shadows looked {hiding.murk_word}."
    )


def discover(world: World, child: Entity, creature_cfg: Creature, hiding: HidingPlace) -> None:
    creature = world.get("creature")
    creature.meters["murk"] = float(hiding.severity)
    propagate(world, narrate=False)
    world.say(
        f"There, blinking through the {hiding.murk_word} gloom, was {creature_cfg.phrase}. "
        f"{creature_cfg.sigh_text}"
    )
    world.say(
        f"{child.id}'s eyes went round as hubcaps. \"Well now,\" {child.pronoun()} whispered, "
        f"\"that is the grandest piece of garage Magic I ever saw.\""
    )


def ask_adoption(world: World, child: Entity, grownup: Entity, creature_cfg: Creature) -> None:
    child.memes["hope"] += 1
    world.say(
        f"At once {child.id} wanted adoption. "
        f"\"Can I keep {creature_cfg.label}?\" {child.pronoun()} asked. "
        f"\"I would name {creature.pronoun('object') if False else 'it'} after the brightest spark in the toolbox.\""
    )
    world.say(
        f"{grownup.label_word.capitalize()} smiled but did not answer too fast. "
        f"\"A creature is not a loose screw for a pocket,\" {grownup.pronoun()} said. "
        f"\"Adoption starts with care.\""
    )


def predict_and_warn(world: World, child: Entity, grownup: Entity, comfort: Comfort, home: Home, delay: int) -> None:
    pred = predict_outcome(world, comfort, home, delay)
    world.facts["predicted"] = pred
    child.memes["attention"] += 1
    outcome_word = "stay" if pred["adopted"] else "bolt for the rafters"
    world.say(
        f"{grownup.label_word.capitalize()} studied the tiny stranger and said, "
        f"\"If we clean that little one and build a true nook, it may {outcome_word}. "
        f"If we only gape, the poor thing will stay scared.\""
    )


def boast_delay(world: World, child: Entity, creature_cfg: Creature, delay: int) -> None:
    if delay <= 0:
        return
    child.memes["brag"] += 1
    if delay == 1:
        world.say(
            f"But {child.id} spent one long moment telling how {creature_cfg.boast}, "
            f"and that small wait made the creature's whiskers tremble."
        )
    else:
        world.say(
            f"But {child.id} took two mighty moments to boast that {creature_cfg.boast}, "
            f"and by the time the speech was done the little foundling had tucked itself tight as a bolt in winter."
        )


def clean_creature(world: World, child: Entity, comfort: Comfort, hiding: HidingPlace) -> None:
    creature = world.get("creature")
    creature.meters["murk"] = 0.0
    creature.meters["clean"] += 1
    world.say(
        f"{child.id} reached slowly with {comfort.phrase} and {comfort.soothe_text}. "
        f"The {hiding.murk_word} smudges came away in curls, and the creature's eyes stopped looking quite so stormy."
    )


def build_home(world: World, child: Entity, home: Home) -> None:
    creature = world.get("creature")
    creature.meters["settled"] += 1
    world.say(
        f"Then {child.id} {home.build_text}, making {home.phrase} so neat and snug "
        f"it seemed fit for a prince of sparks."
    )
    propagate(world, narrate=False)


def decide_adoption(world: World, child: Entity, grownup: Entity, creature_cfg: Creature,
                    hiding: HidingPlace, comfort: Comfort, home: Home, delay: int) -> None:
    creature = world.get("creature")
    care_score = comfort.soothe + home.stability
    fear_score = hiding.severity + creature_cfg.skittishness + delay
    world.facts["care_score"] = care_score
    world.facts["fear_score"] = fear_score
    world.facts["care_beats_fear"] = care_score >= fear_score
    if care_score >= fear_score:
        creature.memes["belonging"] += 1
        creature.memes["fear"] = 0.0
        world.say(
            f"For half a breath the garage held still. Then {creature_cfg.spark_text} "
            f"It stepped into {home.phrase} and curled there as calmly as if it had been expected all along."
        )
        world.say(
            f"{grownup.label_word.capitalize()} gave a slow nod. "
            f"\"That is how adoption ought to begin,\" {grownup.pronoun()} said. "
            f"\"Not with grabbing. With work, room, and kindness.\""
        )
        world.say(
            f"From that day on, the garage never stayed ordinary for long. "
            f"When the rain came down in ropes, {child.id}'s new friend made the rafters shine like a pocketful of dawn."
        )
        outcome = "adopted"
    else:
        creature.memes["fear"] += 1
        world.say(
            f"The creature gave one bright, uncertain blink. {creature_cfg.spark_text} "
            f"But the fear in its tiny bones was still bigger than the welcome."
        )
        world.say(
            f"It touched {child.id}'s knuckle in thanks, sprang to the highest shelf, "
            f"and vanished among the cans and cobwebs, leaving one silver curl of magic behind."
        )
        world.say(
            f"{grownup.label_word.capitalize()} laid a hand on {child.id}'s shoulder. "
            f"\"We helped it, and that matters,\" {grownup.pronoun()} said. "
            f"\"Maybe adoption must wait until trust grows larger.\""
        )
        world.say(
            f"After that, {child.id} kept {home.phrase} ready anyway, and sometimes on rainy nights "
            f"a warm spark winked from the garage as if the little visitor still remembered the way."
        )
        outcome = "visited"
    world.facts["outcome"] = outcome


def tell(creature_cfg: Creature, hiding: HidingPlace, comfort: Comfort, home: Home,
         child_name: str = "Nora", child_gender: str = "girl",
         grownup_type: str = "grandfather", trait: str = "curious",
         delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
        label=child_name,
    ))
    grownup = world.add(Entity(
        id="Grownup",
        kind="character",
        type=grownup_type,
        role="grownup",
        label="the grownup",
    ))
    creature = world.add(Entity(
        id="creature",
        kind="thing",
        type="magic_creature",
        role="foundling",
        label=creature_cfg.label,
        phrase=creature_cfg.phrase,
        tags=set(creature_cfg.tags),
    ))
    child.memes["curiosity"] = 0.0
    child.memes["hope"] = 0.0
    child.memes["attention"] = 0.0
    child.memes["brag"] = 0.0
    creature.meters["murk"] = 0.0
    creature.meters["clean"] = 0.0
    creature.meters["settled"] = 0.0
    creature.meters["glow"] = 0.0
    creature.memes["fear"] = 0.0
    creature.memes["trust"] = 0.0
    creature.memes["lonely"] = 0.0
    creature.memes["belonging"] = 0.0
    world.facts.update(
        creature_cfg=creature_cfg,
        hiding_cfg=hiding,
        comfort_cfg=comfort,
        home_cfg=home,
        delay=delay,
        garage="garage",
    )

    introduce(world, child, grownup)
    garage_tall_tale(world, child)

    world.para()
    hear_sigh(world, child, hiding)
    discover(world, child, creature_cfg, hiding)

    world.para()
    ask_adoption(world, child, grownup, creature_cfg)
    predict_and_warn(world, child, grownup, comfort, home, delay)
    boast_delay(world, child, creature_cfg, delay)

    world.para()
    clean_creature(world, child, comfort, hiding)
    build_home(world, child, home)

    world.para()
    decide_adoption(world, child, grownup, creature_cfg, hiding, comfort, home, delay)

    world.facts.update(
        child=child,
        grownup=grownup,
        creature=creature,
        adoption_score=adoption_score(creature_cfg, hiding, comfort, home, delay),
    )
    return world


CREATURES = {
    "wrench_dragon": Creature(
        id="wrench_dragon",
        label="the wrench-dragon",
        phrase="a thumb-sized wrench-dragon with silver scales and a tail shaped like a curling socket key",
        boast="one day a dragon that small could tow a train and still have breath left to toast marshmallows",
        sigh_text="It gave another sigh, and a puff of blue spark-smoke curled out of its nose.",
        spark_text="Its scales flashed bright enough to make every screwdriver in the garage look newly forged.",
        comfort_need="polish",
        home_need="toolbox_nest",
        skittishness=2,
        tags={"dragon", "garage", "magic"},
    ),
    "lamp_moth": Creature(
        id="lamp_moth",
        label="the lamp-moth",
        phrase="a velvet lamp-moth whose wings looked like tiny golden shades around a pair of shy glowing eyes",
        boast="a moth like that could light a parade from here to the county line",
        sigh_text="It let out a papery sigh that fluttered the loose receipts nearby.",
        spark_text="Its wings opened, and soft honey-colored light washed over the workbench.",
        comfort_need="warm_glow",
        home_need="lantern_shelf",
        skittishness=1,
        tags={"moth", "garage", "magic"},
    ),
    "tire_toad": Creature(
        id="tire_toad",
        label="the tire-toad",
        phrase="a round tire-toad with tread marks on its back and eyes like polished lug nuts",
        boast="a toad built like that could hop clear over a hay barn without bending a whisker",
        sigh_text="It gave a rubbery little sigh and tucked its feet under its belly.",
        spark_text="Its back shone black and glossy, and every old hubcap threw back a moon-bright gleam.",
        comfort_need="warm_rag",
        home_need="tire_bed",
        skittishness=2,
        tags={"toad", "garage", "magic"},
    ),
}

HIDING_PLACES = {
    "oil_pan": HidingPlace(
        id="oil_pan",
        label="the oil pan",
        phrase="an old drain pan under the workbench",
        murk_word="murky",
        severity=2,
        found_here={"wrench_dragon", "tire_toad"},
        tags={"oil", "garage"},
    ),
    "paint_bucket": HidingPlace(
        id="paint_bucket",
        label="the paint bucket",
        phrase="a half-open paint bucket beside the wall",
        murk_word="murky",
        severity=1,
        found_here={"lamp_moth", "wrench_dragon"},
        tags={"paint", "garage"},
    ),
    "tire_stack": HidingPlace(
        id="tire_stack",
        label="the tire stack",
        phrase="a cave under the oldest stack of tires",
        murk_word="murky",
        severity=1,
        found_here={"tire_toad", "lamp_moth"},
        tags={"tire", "garage"},
    ),
}

COMFORTS = {
    "polishing_cloth": Comfort(
        id="polishing_cloth",
        label="polishing cloth",
        phrase="a clean polishing cloth",
        soothe_text="wiped each little scale until the metal gleamed",
        need_tag="polish",
        soothe=2,
        tags={"polish", "care"},
    ),
    "lantern_hum": Comfort(
        id="lantern_hum",
        label="lantern hum",
        phrase="an old camping lantern turned low and warm",
        soothe_text="held the kind little glow nearby and hummed so softly the shadows seemed to sit down and listen",
        need_tag="warm_glow",
        soothe=2,
        tags={"light", "care"},
    ),
    "wool_rag": Comfort(
        id="wool_rag",
        label="wool rag",
        phrase="a folded wool rag fresh from the dryer",
        soothe_text="wrapped the shivering body in dry warmth until the tiny toes uncurled",
        need_tag="warm_rag",
        soothe=2,
        tags={"warmth", "care"},
    ),
}

HOMES = {
    "toolbox_nest": Home(
        id="toolbox_nest",
        label="toolbox nest",
        phrase="a little nest in the top drawer of the red toolbox",
        build_text="lined the top drawer of the red toolbox with cotton and a bottle-cap bowl",
        need_tag="toolbox_nest",
        stability=2,
        tags={"toolbox", "home"},
    ),
    "lantern_shelf": Home(
        id="lantern_shelf",
        label="lantern shelf",
        phrase="a lantern-warm nook on the middle shelf",
        build_text="cleared a middle shelf and set a safe lantern beside a saucer of sugar water",
        need_tag="lantern_shelf",
        stability=1,
        tags={"shelf", "home"},
    ),
    "tire_bed": Home(
        id="tire_bed",
        label="tire bed",
        phrase="a blanket bed tucked inside a clean tire",
        build_text="scrubbed one small tire clean and tucked a folded shop towel inside like a blanket",
        need_tag="tire_bed",
        stability=2,
        tags={"tire", "home"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Ella", "June", "Tess", "Ruby", "Ava", "Lila"]
BOY_NAMES = ["Eli", "Finn", "Leo", "Max", "Ben", "Sam", "Theo", "Jack"]
TRAITS = ["curious", "steady", "kind", "brisk", "careful", "hopeful"]


KNOWLEDGE = {
    "garage": [
        (
            "What is a garage?",
            "A garage is a building or room where people keep cars, tools, and workbench things. It can also be a place for fixing, sorting, and building.",
        )
    ],
    "adoption": [
        (
            "What does adoption mean for a pet or creature?",
            "Adoption means giving a creature a safe home and taking care of it every day. It is not just choosing a name; it is a promise to feed, protect, and comfort it.",
        )
    ],
    "magic": [
        (
            "What is Magic in a tall tale?",
            "Magic in a tall tale makes ordinary things feel bigger, stranger, and more wonderful than usual. It lets a small spark seem grand enough to light up the whole story.",
        )
    ],
    "dragon": [
        (
            "What is a dragon in make-believe stories?",
            "A dragon in make-believe stories is a magical creature that may breathe fire or guard treasure. In a gentle story, it can also be tiny, shy, and in need of help.",
        )
    ],
    "moth": [
        (
            "What is a moth?",
            "A moth is an insect with wings, a bit like a butterfly. Many moths come out in dim light and are drawn toward lamps.",
        )
    ],
    "toad": [
        (
            "What is a toad?",
            "A toad is a small hopping animal with bumpy skin. It often likes cool, tucked-away places.",
        )
    ],
    "care": [
        (
            "Why does a scared creature need gentle care first?",
            "A scared creature needs to feel safe before it can trust anyone. Gentle hands, warmth, and a quiet place can calm fear better than grabbing can.",
        )
    ],
    "toolbox": [
        (
            "What is a toolbox for?",
            "A toolbox is for holding tools in one safe place so they are easy to find. Drawers and little spaces can also make a snug pretend nest in a story.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives light so people can see in dim places. A warm, gentle lantern can also make a place feel calm and welcoming.",
        )
    ],
    "tire": [
        (
            "What is a tire?",
            "A tire is the round rubber part of a wheel. It helps a car roll smoothly and can feel springy and snug in a pretend story nest.",
        )
    ],
}
KNOWLEDGE_ORDER = ["garage", "adoption", "magic", "dragon", "moth", "toad", "care", "toolbox", "lantern", "tire"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    creature_cfg: Creature = f["creature_cfg"]
    hiding: HidingPlace = f["hiding_cfg"]
    outcome = f["outcome"]
    if outcome == "adopted":
        end = "ends with a careful adoption and a magical new home in the garage"
    else:
        end = "ends with a kind near-adoption where trust is not ready yet"
    return [
        'Write a tall-tale story for a 3-to-5-year-old set in a garage that includes the words "sigh", "murky", and "adoption".',
        f"Tell a magical garage story where {child.id} hears a sigh from {hiding.phrase}, finds {creature_cfg.label}, and learns that adoption means making a safe home.",
        f"Write a child-facing tall tale with Magic in a garage, a murky hiding place, and a tiny creature that {end}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    grownup: Entity = f["grownup"]
    creature_cfg: Creature = f["creature_cfg"]
    hiding: HidingPlace = f["hiding_cfg"]
    comfort: Comfort = f["comfort_cfg"]
    home: Home = f["home_cfg"]
    outcome = f["outcome"]
    pred = f["predicted"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {grownup.label_word}, and {creature_cfg.label} in the garage. The story begins when they hear a lonely sigh from a murky hiding place.",
        ),
        (
            f"Where did {child.id} find the magical creature?",
            f"{child.id} found it in {hiding.phrase}. That spot looked murky and hidden, which is why the little creature seemed scared and alone.",
        ),
        (
            f"Why did {child.id} want adoption right away?",
            f"{child.id} was amazed by the creature's Magic and wanted to keep it at once. But the grown-up explained that adoption starts with care, not with grabbing.",
        ),
        (
            f"What did {child.id} do to help the creature?",
            f"{child.id} used {comfort.phrase} and then made {home.phrase}. Cleaning and building the nook helped the creature feel safer because it was no longer dirty, cold, or unsettled.",
        ),
        (
            "How did the grown-up know what might happen next?",
            f"{grownup.label_word.capitalize()} looked at the creature and guessed what care could do. {grownup.pronoun().capitalize()} knew that if they helped quickly enough, the creature might {'stay' if pred['adopted'] else 'trust them a little but still leave'} because fear and comfort were pushing against each other.",
        ),
    ]
    if outcome == "adopted":
        qa.append(
            (
                "Did the adoption happen?",
                f"Yes. The creature stayed in the new nook, and the grown-up said that was the right way for adoption to begin. It stayed because the care they gave was bigger than its fear.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the garage changed by Magic and kindness. The child had a new friend, and the shining rafters showed that something real had changed.",
            )
        )
    else:
        qa.append(
            (
                "Did the adoption happen that day?",
                f"Not yet. The creature thanked {child.id} but flew or hopped away because it was still too frightened. The care mattered, though, and the ready-made nook showed that {child.id} had learned what adoption requires.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with hope instead of ownership. {child.id} kept the little home ready in the garage, because trust can grow later when kindness is steady.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    creature_cfg: Creature = f["creature_cfg"]
    comfort: Comfort = f["comfort_cfg"]
    home: Home = f["home_cfg"]
    tags = {"garage", "adoption", "magic", "care"}
    if "dragon" in creature_cfg.tags:
        tags.add("dragon")
    if "moth" in creature_cfg.tags:
        tags.add("moth")
    if "toad" in creature_cfg.tags:
        tags.add("toad")
    if home.id == "toolbox_nest":
        tags.add("toolbox")
    if comfort.id == "lantern_hum" or home.id == "lantern_shelf":
        tags.add("lantern")
    if home.id == "tire_bed":
        tags.add("tire")
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:9} ({ent.type:13}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    if "care_score" in world.facts and "fear_score" in world.facts:
        lines.append(
            f"  care_score={world.facts['care_score']} fear_score={world.facts['fear_score']}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
% Validity: the creature must plausibly be found there, and the chosen comfort
% and home must be the ones that match its needs.
valid(C,Hid,Com,Home) :-
    creature(C), hiding(Hid), comfort(Com), home(Home),
    found_here(C,Hid),
    comfort_need(C,N1), comfort_kind(Com,N1),
    home_need(C,N2), home_kind(Home,N2).

% Outcome: adopted when care is at least as big as fear.
fear(F) :- chosen_hiding(H), severity(H,S), chosen_creature(C), skittish(C,K), delay(D), F = S + K + D.
care(CA) :- chosen_comfort(Com), soothe(Com,S1), chosen_home(Home), stability(Home,S2), CA = S1 + S2.
adopted :- valid_story, care(CA), fear(F), CA >= F.
valid_story :- chosen_creature(C), chosen_hiding(H), chosen_comfort(Com), chosen_home(Home), valid(C,H,Com,Home).
outcome(adopted) :- valid_story, adopted.
outcome(visited) :- valid_story, not adopted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, creature in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        lines.append(asp.fact("comfort_need", cid, creature.comfort_need))
        lines.append(asp.fact("home_need", cid, creature.home_need))
        lines.append(asp.fact("skittish", cid, creature.skittishness))
    for hid, hiding in HIDING_PLACES.items():
        lines.append(asp.fact("hiding", hid))
        lines.append(asp.fact("severity", hid, hiding.severity))
        for cid in sorted(hiding.found_here):
            lines.append(asp.fact("found_here", cid, hid))
    for comfort_id, comfort in COMFORTS.items():
        lines.append(asp.fact("comfort", comfort_id))
        lines.append(asp.fact("comfort_kind", comfort_id, comfort.need_tag))
        lines.append(asp.fact("soothe", comfort_id, comfort.soothe))
    for home_id, home in HOMES.items():
        lines.append(asp.fact("home", home_id))
        lines.append(asp.fact("home_kind", home_id, home.need_tag))
        lines.append(asp.fact("stability", home_id, home.stability))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_creature", params.creature),
        asp.fact("chosen_hiding", params.hiding),
        asp.fact("chosen_comfort", params.comfort),
        asp.fact("chosen_home", params.home),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale garage Magic storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--hiding", choices=HIDING_PLACES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--home", choices=HOMES)
    ap.add_argument("--grownup", choices=["grandfather", "grandmother", "father", "mother"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the child delays before helping")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.creature and args.hiding and args.comfort and args.home:
        creature = CREATURES[args.creature]
        hiding = HIDING_PLACES[args.hiding]
        comfort = COMFORTS[args.comfort]
        home = HOMES[args.home]
        if not valid_combo(creature, hiding, comfort, home):
            raise StoryError(explain_rejection(creature, hiding, comfort, home))

    combos = [
        combo for combo in valid_combos()
        if (args.creature is None or combo[0] == args.creature)
        and (args.hiding is None or combo[1] == args.hiding)
        and (args.comfort is None or combo[2] == args.comfort)
        and (args.home is None or combo[3] == args.home)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    creature_id, hiding_id, comfort_id, home_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grownup = args.grownup or rng.choice(["grandfather", "grandmother", "father", "mother"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])
    return StoryParams(
        creature=creature_id,
        hiding=hiding_id,
        comfort=comfort_id,
        home=home_id,
        child_name=name,
        child_gender=gender,
        grownup=grownup,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        creature = CREATURES[params.creature]
        hiding = HIDING_PLACES[params.hiding]
        comfort = COMFORTS[params.comfort]
        home = HOMES[params.home]
    except KeyError as exc:
        raise StoryError(f"(Unknown parameter choice: {exc.args[0]})") from None
    if not valid_combo(creature, hiding, comfort, home):
        raise StoryError(explain_rejection(creature, hiding, comfort, home))
    world = tell(
        creature_cfg=creature,
        hiding=hiding,
        comfort=comfort,
        home=home,
        child_name=params.child_name,
        child_gender=params.child_gender,
        grownup_type=params.grownup,
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


CURATED = [
    StoryParams(
        creature="wrench_dragon",
        hiding="oil_pan",
        comfort="polishing_cloth",
        home="toolbox_nest",
        child_name="Nora",
        child_gender="girl",
        grownup="grandfather",
        trait="curious",
        delay=0,
    ),
    StoryParams(
        creature="lamp_moth",
        hiding="paint_bucket",
        comfort="lantern_hum",
        home="lantern_shelf",
        child_name="Eli",
        child_gender="boy",
        grownup="grandmother",
        trait="steady",
        delay=1,
    ),
    StoryParams(
        creature="tire_toad",
        hiding="tire_stack",
        comfort="wool_rag",
        home="tire_bed",
        child_name="Ruby",
        child_gender="girl",
        grownup="father",
        trait="kind",
        delay=0,
    ),
    StoryParams(
        creature="wrench_dragon",
        hiding="paint_bucket",
        comfort="polishing_cloth",
        home="toolbox_nest",
        child_name="Max",
        child_gender="boy",
        grownup="mother",
        trait="hopeful",
        delay=2,
    ),
    StoryParams(
        creature="lamp_moth",
        hiding="tire_stack",
        comfort="lantern_hum",
        home="lantern_shelf",
        child_name="June",
        child_gender="girl",
        grownup="grandfather",
        trait="careful",
        delay=2,
    ),
]


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
    for seed in range(80):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        ao = asp_outcome(params)
        po = outcome_of(params)
        if ao != po:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (creature, hiding, comfort, home) combos:\n")
        for creature, hiding, comfort, home in combos:
            print(f"  {creature:14} {hiding:12} {comfort:16} {home}")
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
            header = (
                f"### {sample.params.child_name}: {sample.params.creature} in {sample.params.hiding} "
                f"({outcome_of(sample.params)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
