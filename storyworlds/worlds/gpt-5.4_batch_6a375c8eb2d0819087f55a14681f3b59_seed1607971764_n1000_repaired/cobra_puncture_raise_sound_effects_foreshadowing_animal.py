#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cobra_puncture_raise_sound_effects_foreshadowing_animal.py
======================================================================================

A standalone story world for a small Animal Story domain built from the seed
words "cobra", "puncture", and "raise", with Sound Effects and Foreshadowing.

Premise
-------
Two young animals want to make a little whistle from a dry natural object.
One child wants to puncture it beside a warm hiding place that belongs to a
cobra. The warning signs arrive first: the grass whispers, birds go quiet,
and the story foreshadows danger before the snake appears. A wiser companion
or a quick elder keeps the children safe, and the ending image proves they
learn to make things in a safer place.

Run it
------
    python storyworlds/worlds/gpt-5.4/cobra_puncture_raise_sound_effects_foreshadowing_animal.py
    python storyworlds/worlds/gpt-5.4/cobra_puncture_raise_sound_effects_foreshadowing_animal.py --object coconut
    python storyworlds/worlds/gpt-5.4/cobra_puncture_raise_sound_effects_foreshadowing_animal.py --helper turtle
    python storyworlds/worlds/gpt-5.4/cobra_puncture_raise_sound_effects_foreshadowing_animal.py --all
    python storyworlds/worlds/gpt-5.4/cobra_puncture_raise_sound_effects_foreshadowing_animal.py --qa --json
    python storyworlds/worlds/gpt-5.4/cobra_puncture_raise_sound_effects_foreshadowing_animal.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "watchful", "thoughtful", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    puncturable: bool = False
    risky_hide: bool = False
    # physical and emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "meerkat_girl", "mongoose_girl", "rabbit_girl", "monkey_girl"}
        male = {"boy", "father", "uncle", "meerkat_boy", "mongoose_boy", "rabbit_boy", "monkey_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class ChildKind:
    id: str
    species: str
    pair_word: str
    home_line: str
    move_sound: str
    raise_part: str
    lookout: str
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    puncture_tool: str
    music_voice: str
    puncturable: bool = True
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
class ShelterCfg:
    id: str
    label: str
    the: str
    sign_sound: str
    quiet_line: str
    danger: int = 2
    risky: bool = True
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
class HelperCfg:
    id: str
    label: str
    type: str
    sense: int
    power: int
    arrive_sound: str
    rescue_text: str
    safe_puncture: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "cautioner"}]

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


def _r_signs_raise_fear(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("ominous_signs", 0) < 1:
        return out
    for kid in world.kids():
        sig = ("fear", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["unease"] += 1
    out.append("__signs__")
    return out


def _r_cobra_danger(world: World) -> list[str]:
    out: list[str] = []
    cobra = world.entities.get("cobra")
    if cobra is None or cobra.meters["raised"] < THRESHOLD:
        return out
    sig = ("cobra_danger", "cobra")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("place").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__cobra__")
    return out


CAUSAL_RULES = [
    Rule(name="signs_raise_fear", tag="emotional", apply=_r_signs_raise_fear),
    Rule(name="cobra_danger", tag="physical", apply=_r_cobra_danger),
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
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(obj: ObjectCfg, shelter: ShelterCfg) -> bool:
    return obj.puncturable and shelter.risky


def sensible_helpers() -> list[HelperCfg]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def cobra_severity(shelter: ShelterCfg, delay: int) -> int:
    return shelter.danger + delay


def is_contained(helper: HelperCfg, shelter: ShelterCfg, delay: int) -> bool:
    return helper.power >= cobra_severity(shelter, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > hero_age
    authority = initial_caution(trait) + 1.0 + (3.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_cobra(world: World) -> dict:
    sim = world.copy()
    sim.facts["ominous_signs"] = 1
    propagate(sim, narrate=False)
    _raise_cobra(sim, narrate=False)
    return {
        "danger": sim.get("place").meters["danger"],
        "fear": sum(k.memes["fear"] for k in sim.kids()),
    }


def _raise_cobra(world: World, narrate: bool = True) -> None:
    cobra = world.get("cobra")
    cobra.meters["raised"] += 1
    cobra.meters["nearby"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, cautioner: Entity, kind: ChildKind) -> None:
    hero.memes["joy"] += 1
    cautioner.memes["joy"] += 1
    world.say(
        f"At the edge of the warm grassland, {hero.id} and {cautioner.id} were two little "
        f"{kind.pair_word} who loved making games out of ordinary things. {kind.home_line}"
    )
    world.say(
        f'"Listen," said {hero.id}. "{kind.move_sound}! Even our feet sound like music today."'
    )


def find_object(world: World, hero: Entity, obj: ObjectCfg) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"Under an acacia tree they found {obj.phrase}. It was light and dry, and {hero.id} "
        f"imagined it singing in a small {obj.music_voice} voice."
    )


def wish_to_make_music(world: World, hero: Entity, obj: ObjectCfg, shelter: ShelterCfg) -> None:
    world.say(
        f'"If I puncture {obj.label} with {obj.puncture_tool}, it can become a whistle," '
        f"{hero.id} said. The flattest stone nearby rested beside {shelter.the}, "
        f"so that place looked easy to work."
    )


def foreshadow(world: World, cautioner: Entity, kind: ChildKind, shelter: ShelterCfg) -> None:
    world.facts["ominous_signs"] = 1
    propagate(world, narrate=False)
    world.say(
        f"But before they came close, the grass went {shelter.sign_sound}. "
        f"{shelter.quiet_line}"
    )
    world.say(
        f"{cautioner.id} stopped and began to raise {cautioner.pronoun('possessive')} "
        f"{kind.raise_part}. {kind.lookout}"
    )


def warn(world: World, hero: Entity, cautioner: Entity, obj: ObjectCfg, shelter: ShelterCfg) -> None:
    pred = predict_cobra(world)
    world.facts["predicted_danger"] = pred["danger"]
    cautioner.memes["caution"] += 1
    extra = ""
    if cautioner.memes["caution"] >= 6:
        extra = f" {cautioner.id} was almost whispering now, because the warning felt real."
    world.say(
        f'"Please do not puncture {obj.label} there," said {cautioner.id}. '
        f'"That warm shadow looks like cobra place. If something raises its hood from '
        f"{shelter.the}, we will be too close.\"{extra}"
    )


def back_down(world: World, hero: Entity, cautioner: Entity, elder: Entity, obj: ObjectCfg) -> None:
    hero.memes["relief"] += 1
    cautioner.memes["relief"] += 1
    hero.memes["bravery"] = 0.0
    world.say(
        f'{hero.id} looked at the dry shell, then at {cautioner.id}\'s worried face. '
        f'"You are right," {hero.pronoun()} said. "I do not want a whistle badly enough to '
        f"stand over a snake hole.\""
    )
    world.say(
        f"They carried {obj.label} to {elder.label}, who knew safer ways to make small things sing."
    )


def defy(world: World, hero: Entity, cautioner: Entity, obj: ObjectCfg) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"Just one tiny poke," {hero.id} said. "{obj.puncture_tool.capitalize()}... tik, tik... and then we are done."'
    )
    world.say(
        f"But the wish to hear the new whistle was pulling harder than the warning."
    )


def attempt_puncture(world: World, hero: Entity, obj: ObjectCfg, shelter: ShelterCfg) -> None:
    obj_ent = world.get("object")
    obj_ent.meters["pierced"] += 1
    obj_ent.meters["at_shelter"] += 1
    world.say(
        f"{hero.id} set {obj.label} on the stone and touched it with {obj.puncture_tool}. "
        f"Tik. Tik. The sound was small, but beside {shelter.the} it felt too loud."
    )


def cobra_appears(world: World, shelter: ShelterCfg) -> None:
    _raise_cobra(world, narrate=False)
    world.say(
        f"Then came a sharp sound from the shadow: {shelter.sign_sound}! "
        f"From {shelter.the}, a cobra began to raise its hood."
    )


def alarm(world: World, cautioner: Entity, elder: Entity) -> None:
    cautioner.memes["fear"] += 1
    world.say(f'"Cobra!" cried {cautioner.id}. "{elder.label_word.capitalize()}, help!"')


def rescue(world: World, elder: Entity, helper: HelperCfg, hero: Entity, cautioner: Entity) -> None:
    world.get("place").meters["danger"] = 0.0
    world.get("cobra").meters["raised"] = 0.0
    world.say(
        f"{helper.arrive_sound} came {elder.label}, and {elder.pronoun()} {helper.rescue_text}."
    )
    world.say(
        f"{hero.id} and {cautioner.id} scrambled onto a tall stump while the cobra slid back into the dark."
    )


def lesson(world: World, elder: Entity, hero: Entity, cautioner: Entity, obj: ObjectCfg, shelter: ShelterCfg) -> None:
    for kid in (hero, cautioner):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'{elder.label_word.capitalize()} wrapped a wing around them both and spoke softly. '
        f'"A warm hole can hide more than silence. When the world gives warnings, you must listen before you puncture anything."'
    )
    world.say(
        f'"We will," whispered {hero.id}. {cautioner.id} nodded and kept well away from {shelter.the}.'
    )


def safe_finish(world: World, elder: Entity, helper: HelperCfg, hero: Entity, cautioner: Entity, obj: ObjectCfg) -> None:
    for kid in (hero, cautioner):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"Later, far from the grass hole, {elder.label} {helper.safe_puncture}."
    )
    world.say(
        f'Soon a bright note floated out -- "peep-peep!" -- and both little friends laughed. '
        f"This time the music rose from a safe place, and that made it sweeter."
    )


def rescue_fail(world: World, elder: Entity, helper: HelperCfg, obj: ObjectCfg) -> None:
    world.get("place").meters["danger"] += 1
    world.get("object").meters["lost"] += 1
    world.say(
        f"{helper.arrive_sound} came {elder.label}, but {elder.pronoun()} was a breath too late to save the little craft."
    )
    world.say(
        f"The cobra struck the dry {obj.label} instead -- tack! -- and sent it rolling into the weeds."
    )


def escape_loss(world: World, elder: Entity, hero: Entity, cautioner: Entity) -> None:
    for kid in (hero, cautioner):
        kid.memes["fear"] += 1
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"{elder.label_word.capitalize()} hurried the children up a fallen log and kept them there until the cobra slipped away."
    )
    world.say(
        f"No one was hurt, but the whistle-to-be was gone. The quiet that followed felt bigger than any song."
    )


def quiet_resolution(world: World, elder: Entity, hero: Entity, cautioner: Entity) -> None:
    world.say(
        f'When their breathing slowed, {elder.label} said, "Music can wait. Safety comes first."'
    )
    world.say(
        f"After that day, {hero.id} and {cautioner.id} never worked beside a dark ground hole again."
    )


def tell(
    kind: ChildKind,
    obj: ObjectCfg,
    shelter: ShelterCfg,
    helper: HelperCfg,
    hero_name: str = "Pip",
    hero_type: str = "mongoose_boy",
    cautioner_name: str = "Tala",
    cautioner_type: str = "mongoose_girl",
    elder_name: str = "Old Peck",
    relation: str = "siblings",
    trait: str = "watchful",
    delay: int = 0,
    hero_age: int = 5,
    cautioner_age: int = 6,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        age=hero_age,
        attrs={"relation": relation},
    ))
    cautioner = world.add(Entity(
        id=cautioner_name,
        kind="character",
        type=cautioner_type,
        label=cautioner_name,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=helper.type,
        label=elder_name,
        role="elder",
        attrs={"helper": helper.id},
    ))
    world.add(Entity(id="place", type="place", label="the clearing"))
    world.add(Entity(id="object", type="object", label=obj.label, puncturable=obj.puncturable))
    world.add(Entity(id="shelter", type="shelter", label=shelter.label, risky_hide=shelter.risky))
    world.add(Entity(id="cobra", kind="character", type="cobra", label="the cobra"))

    hero.memes["bravery"] = BRAVERY_INIT
    cautioner.memes["caution"] = initial_caution(trait)

    world.facts.update(
        predicted_danger=0,
        ominous_signs=0,
    )

    introduce(world, hero, cautioner, kind)
    find_object(world, hero, obj)

    world.para()
    wish_to_make_music(world, hero, obj, shelter)
    foreshadow(world, cautioner, kind, shelter)
    warn(world, hero, cautioner, obj, shelter)

    averted = would_avert(relation, hero_age, cautioner_age, trait)

    if averted:
        back_down(world, hero, cautioner, elder, obj)
        world.para()
        safe_finish(world, elder, helper, hero, cautioner, obj)
        contained = True
        severity = 0
    else:
        defy(world, hero, cautioner, obj)
        world.para()
        attempt_puncture(world, hero, obj, shelter)
        cobra_appears(world, shelter)
        alarm(world, cautioner, elder)
        severity = cobra_severity(shelter, delay)
        world.get("cobra").meters["severity"] = float(severity)
        contained = is_contained(helper, shelter, delay)

        world.para()
        if contained:
            rescue(world, elder, helper, hero, cautioner)
            lesson(world, elder, hero, cautioner, obj, shelter)
            world.para()
            safe_finish(world, elder, helper, hero, cautioner, obj)
        else:
            rescue_fail(world, elder, helper, obj)
            escape_loss(world, elder, hero, cautioner)
            quiet_resolution(world, elder, hero, cautioner)

    outcome = "averted" if averted else ("contained" if contained else "lost")
    world.facts.update(
        hero=hero,
        cautioner=cautioner,
        elder=elder,
        child_kind=kind,
        object_cfg=obj,
        shelter_cfg=shelter,
        helper_cfg=helper,
        relation=relation,
        outcome=outcome,
        severity=severity,
        delay=delay,
        threatened=not averted,
        safe_end=contained,
        whistle_made=outcome in {"averted", "contained"},
    )
    return world


CHILD_KINDS = {
    "mongoose": ChildKind(
        id="mongoose",
        species="mongoose",
        pair_word="mongooses",
        home_line="Their burrow opened under a low bank, and every evening they chased the last gold stripes of sun.",
        move_sound="patter-patter",
        raise_part="tail",
        lookout="Her whiskers twitched. Something about the ground felt watchful.",
        tags={"mongoose"},
    ),
    "meerkat": ChildKind(
        id="meerkat",
        species="meerkat",
        pair_word="meerkats",
        home_line="Their sandy den faced the open plain, where little paws were always learning what the wind meant.",
        move_sound="scritch-scritch",
        raise_part="tail",
        lookout="His ears tipped forward. The stillness was wrong in a way he could not explain.",
        tags={"meerkat"},
    ),
    "rabbit": ChildKind(
        id="rabbit",
        species="rabbit",
        pair_word="rabbits",
        home_line="Their warren lay near sweet grass, and they liked to pretend every root and pebble was part of a grand invention.",
        move_sound="thump-thump",
        raise_part="ears",
        lookout="Her ears stood tall. Quiet could be a message too.",
        tags={"rabbit"},
    ),
}

OBJECTS = {
    "gourd": ObjectCfg(
        id="gourd",
        label="the dry gourd",
        phrase="a palm-sized dry gourd",
        puncture_tool="a thorn",
        music_voice="hollow",
        puncturable=True,
        tags={"gourd", "whistle"},
    ),
    "reed": ObjectCfg(
        id="reed",
        label="the reed stem",
        phrase="a fat reed stem, dried by the sun",
        puncture_tool="a sharp twig",
        music_voice="thin",
        puncturable=True,
        tags={"reed", "whistle"},
    ),
    "seedpod": ObjectCfg(
        id="seedpod",
        label="the seedpod",
        phrase="a hard brown seedpod with seeds rattling inside",
        puncture_tool="a thorn",
        music_voice="rattle",
        puncturable=True,
        tags={"seedpod", "whistle"},
    ),
    "coconut": ObjectCfg(
        id="coconut",
        label="the coconut shell",
        phrase="a thick little coconut shell",
        puncture_tool="a thorn",
        music_voice="deep",
        puncturable=False,
        tags={"coconut"},
    ),
}

SHELTERS = {
    "termite_mound": ShelterCfg(
        id="termite_mound",
        label="termite mound",
        the="the cracked side of the termite mound",
        sign_sound="ssss-ssss",
        quiet_line="Even the finches on the branches went quiet for a moment.",
        danger=2,
        risky=True,
        tags={"cobra", "warning_signs"},
    ),
    "log_hollow": ShelterCfg(
        id="log_hollow",
        label="log hollow",
        the="the warm hollow under the fallen log",
        sign_sound="hissss",
        quiet_line="The beetles seemed loud because the bigger bird sounds had stopped.",
        danger=2,
        risky=True,
        tags={"cobra", "warning_signs"},
    ),
    "rock_crack": ShelterCfg(
        id="rock_crack",
        label="rock crack",
        the="the shadowy crack beneath the sun-warmed rock",
        sign_sound="sssk",
        quiet_line="A lizard froze on the stone as if it knew the next sound would matter.",
        danger=3,
        risky=True,
        tags={"cobra", "warning_signs"},
    ),
    "open_stump": ShelterCfg(
        id="open_stump",
        label="open stump",
        the="the open stump in the bright field",
        sign_sound="puff",
        quiet_line="Birds kept chirping, and nothing in the grass seemed to hide.",
        danger=0,
        risky=False,
        tags={"safe_place"},
    ),
}

HELPERS = {
    "woodpecker": HelperCfg(
        id="woodpecker",
        label="Old Peck the woodpecker",
        type="woodpecker",
        sense=3,
        power=3,
        arrive_sound="Tap-tap-tap!",
        rescue_text="swooped to a branch above the cobra and drummed so sharply that the snake turned away from the children",
        safe_puncture="held the gourd steady on a branch and pecked one neat little hole into it",
        qa_text="drummed from above and turned the cobra away, then made a neat hole safely",
        tags={"woodpecker", "bird_help"},
    ),
    "porcupine": HelperCfg(
        id="porcupine",
        label="Bram the porcupine",
        type="porcupine",
        sense=2,
        power=2,
        arrive_sound="Rattle-rattle!",
        rescue_text="shuffled between the children and the cobra, lifting a brave fan of quills until the snake chose to slide back",
        safe_puncture="used a dropped quill to make a careful hole while everyone stood in the sunny open",
        qa_text="stood between the children and the cobra with raised quills, then used a quill to make the hole safely",
        tags={"porcupine", "quills"},
    ),
    "turtle": HelperCfg(
        id="turtle",
        label="Mossback the turtle",
        type="turtle",
        sense=1,
        power=1,
        arrive_sound="Scrape... scrape...",
        rescue_text="hurried as fast as old turtle feet could go, but slow feet are not much help in a snake scare",
        safe_puncture="pushed at the shell for a long while and never made a clean hole",
        qa_text="tried to help, but was too slow to save the craft",
        tags={"turtle"},
    ),
}

GIRL_NAMES = ["Tala", "Nia", "Miri", "Luma", "Pia", "Suri"]
BOY_NAMES = ["Pip", "Kito", "Rafi", "Milo", "Timo", "Zed"]
TRAITS = ["watchful", "careful", "thoughtful", "curious", "eager", "bold"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for kind_id in CHILD_KINDS:
        for obj_id, obj in OBJECTS.items():
            for shelter_id, shelter in SHELTERS.items():
                for helper_id, helper in HELPERS.items():
                    if hazard_at_risk(obj, shelter) and helper.sense >= SENSE_MIN:
                        combos.append((kind_id, obj_id, shelter_id, helper_id))
    return combos


@dataclass
class StoryParams:
    child_kind: str
    object: str
    shelter: str
    helper: str
    hero_name: str
    hero_type: str
    cautioner_name: str
    cautioner_type: str
    elder_name: str
    relation: str
    trait: str
    delay: int = 0
    hero_age: int = 5
    cautioner_age: int = 6
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
    "cobra": [(
        "What does a cobra do when it feels threatened?",
        "A cobra may raise its hood and hiss to warn others away. That warning means you should back away and leave it alone."
    )],
    "warning_signs": [(
        "Why can sudden quiet be a warning in the wild?",
        "Sometimes small birds and animals go quiet when something dangerous is nearby. The quiet can be a clue that everyone else has noticed a problem first."
    )],
    "gourd": [(
        "What is a gourd?",
        "A gourd is a hard-shelled fruit that can dry out and become light and hollow. People and animals in stories sometimes use dry gourds for little containers or instruments."
    )],
    "reed": [(
        "What is a reed?",
        "A reed is a tall plant that grows in wet places. When a reed dries, its stem can be light and hollow."
    )],
    "seedpod": [(
        "What is a seedpod?",
        "A seedpod is the part of a plant that holds seeds. Some dry seedpods rattle when the seeds bump around inside."
    )],
    "woodpecker": [(
        "How does a woodpecker make holes in wood?",
        "A woodpecker uses its strong beak to peck very quickly. Its head and neck are built to handle all that tapping."
    )],
    "porcupine": [(
        "What are porcupine quills for?",
        "Quills help protect a porcupine when something comes too close. They are not thrown like darts, but they make other animals think twice."
    )],
    "quills": [(
        "Can a sharp quill puncture something light?",
        "Yes, a sharp quill can puncture something thin or dry. That is why Bram could help make a careful little hole in the story."
    )],
    "whistle": [(
        "How does a whistle make a sound?",
        "Air moves through a small opening and begins to vibrate. That vibration makes the clear little note you hear."
    )],
}
KNOWLEDGE_ORDER = ["cobra", "warning_signs", "gourd", "reed", "seedpod", "woodpecker", "porcupine", "quills", "whistle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    cautioner = f["cautioner"]
    obj = f["object_cfg"]
    shelter = f["shelter_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write an Animal Story for ages 3 to 5 where two little {f["child_kind"].pair_word} find {obj.label} and want to make music, but warning signs near {shelter.the} stop them before a cobra appears. Include the words "cobra", "puncture", and "raise".',
            f"Tell a gentle foreshadowing story where {cautioner.id} notices the grass and birds changing first, warns {hero.id}, and they choose a safer place to work.",
            f'Write a child-facing story with sound effects like "tik-tik" and "peep-peep," where the characters listen to danger signs instead of poking at something risky.',
        ]
    if outcome == "contained":
        return [
            f'Write an Animal Story for ages 3 to 5 where a child tries to puncture {obj.label} near {shelter.the}, a cobra begins to raise its hood, and a wise elder keeps everyone safe.',
            f"Tell a short story with foreshadowing, sound effects, and a calm lesson: the warning signs come first, then the snake, then a rescue, and at the end the children still get their whistle in a safer place.",
            f'Write a story that includes "cobra", "puncture", and "raise" and ends with safe music instead of danger.',
        ]
    return [
        f'Write an Animal Story for ages 3 to 5 where a child ignores the warning signs beside {shelter.the}, a cobra appears, and the children escape but lose the little whistle they wanted to make.',
        f"Tell a cautionary animal tale with foreshadowing, rustling sound effects, and a gentle lesson about listening before you come close to a hidden place.",
        f'Write a story using the words "cobra", "puncture", and "raise" where nobody is hurt, but the children learn the hard way to work in a safer spot.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    cautioner = f["cautioner"]
    elder = f["elder"]
    obj = f["object_cfg"]
    shelter = f["shelter_cfg"]
    helper = f["helper_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {cautioner.id}, two little {f['child_kind'].pair_word}, and {elder.label} who helps them. They wanted to turn {obj.label} into a tiny whistle."
        ),
        (
            f"Why did {cautioner.id} feel worried before the cobra appeared?",
            f"{cautioner.id} noticed the warning signs first: the grass made a strange sound and the other creatures went quiet. Those clues made {cautioner.pronoun('object')} suspect that something dangerous was hiding near {shelter.the}."
        ),
        (
            f"What did {hero.id} want to do with {obj.label}?",
            f"{hero.id} wanted to puncture it and make a whistle. The dry shell seemed perfect for a little singing sound."
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"How was the danger stopped before it fully happened?",
            f"{hero.id} listened when {cautioner.id} warned {hero.pronoun('object')} and backed away from the hole. Because they left early, the risky moment ended before any cobra had to come out."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with {elder.label} helping them make the whistle in a safer place. The happy music at the end shows they learned to listen to warnings first."
        ))
    elif outcome == "contained":
        qa.append((
            f"How did {elder.label} help when the cobra raised its hood?",
            f"{elder.label} {helper.qa_text}. That gave the children time to scramble up to safety and wait for the danger to pass."
        ))
        qa.append((
            "What lesson did the children learn?",
            f"They learned not to work beside hidden warm holes just because a stone looks convenient. The warning signs mattered, and listening to them kept the day from turning worse."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a whistle singing from a safe place far away from the hole. The final peep-peep proves the children changed how they solved the problem."
        ))
    else:
        qa.append((
            "Did anyone get hurt?",
            "No one was hurt, because the elder got the children up to safety in time. But they lost the little craft they had hoped to make, which made the lesson feel real."
        ))
        qa.append((
            "Why was the ending sadder than the happy version?",
            f"The children escaped, but the cobra struck the little object and ruined their plan. They still learned to respect warning signs, yet they did not get music that day."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["object_cfg"].tags) | set(f["shelter_cfg"].tags) | set(f["helper_cfg"].tags)
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.puncturable:
            bits.append("puncturable=True")
        if e.risky_hide:
            bits.append("risky_hide=True")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  facts={{{', '.join(f'{k}={v!r}' for k, v in world.facts.items() if k in {'outcome', 'severity', 'delay', 'predicted_danger', 'ominous_signs'})}}}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        child_kind="mongoose",
        object="gourd",
        shelter="termite_mound",
        helper="woodpecker",
        hero_name="Pip",
        hero_type="mongoose_boy",
        cautioner_name="Tala",
        cautioner_type="mongoose_girl",
        elder_name="Old Peck the woodpecker",
        relation="siblings",
        trait="watchful",
        delay=0,
        hero_age=5,
        cautioner_age=7,
    ),
    StoryParams(
        child_kind="meerkat",
        object="reed",
        shelter="log_hollow",
        helper="porcupine",
        hero_name="Kito",
        hero_type="meerkat_boy",
        cautioner_name="Miri",
        cautioner_type="meerkat_girl",
        elder_name="Bram the porcupine",
        relation="friends",
        trait="careful",
        delay=0,
        hero_age=5,
        cautioner_age=5,
    ),
    StoryParams(
        child_kind="rabbit",
        object="seedpod",
        shelter="rock_crack",
        helper="porcupine",
        hero_name="Luma",
        hero_type="rabbit_girl",
        cautioner_name="Rafi",
        cautioner_type="rabbit_boy",
        elder_name="Bram the porcupine",
        relation="siblings",
        trait="curious",
        delay=1,
        hero_age=6,
        cautioner_age=4,
    ),
    StoryParams(
        child_kind="mongoose",
        object="gourd",
        shelter="rock_crack",
        helper="woodpecker",
        hero_name="Zed",
        hero_type="mongoose_boy",
        cautioner_name="Nia",
        cautioner_type="mongoose_girl",
        elder_name="Old Peck the woodpecker",
        relation="friends",
        trait="thoughtful",
        delay=1,
        hero_age=6,
        cautioner_age=6,
    ),
]


def explain_rejection(obj: ObjectCfg, shelter: ShelterCfg) -> str:
    if not obj.puncturable:
        return (
            f"(No story: {obj.label} is too thick for the little tool in this world. "
            f"The children need something they could honestly puncture, like a gourd or a reed.)"
        )
    if not shelter.risky:
        return (
            f"(No story: {shelter.the} is an open, safe place, so there is no believable cobra danger there. "
            f"This story needs a hidden warm shelter that could really hold a snake.)"
        )
    return "(No story: this combination has no believable cobra hazard.)"


def explain_helper(helper_id: str) -> str:
    helper = HELPERS[helper_id]
    better = ", ".join(sorted(h.id for h in sensible_helpers()))
    return (
        f"(Refusing helper '{helper_id}': it scores too low on common sense for a fast cobra scare "
        f"(sense={helper.sense} < {SENSE_MIN}). Try one of these safer helpers: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.hero_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_contained(HELPERS[params.helper], SHELTERS[params.shelter], params.delay) else "lost"


ASP_RULES = r"""
% reasonableness gate
hazard(O, S) :- puncturable(O), risky(S).
sensible(H)  :- helper(H), sense(H, N), sense_min(M), N >= M.
valid(K, O, S, H) :- child_kind(K), object(O), shelter(S), helper(H), hazard(O, S), sensible(H).

% outcome model
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), hero_age(HA), cautioner_age(CA), CA > HA.
bonus(3) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(Dg + Dl) :- chosen_shelter(S), danger(S, Dg), delay(Dl).
helper_power(P) :- chosen_helper(H), power(H, P).
contained :- helper_power(P), severity(Sv), P >= Sv.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(lost) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for kid in CHILD_KINDS:
        lines.append(asp.fact("child_kind", kid))
    for obj_id, obj in OBJECTS.items():
        lines.append(asp.fact("object", obj_id))
        if obj.puncturable:
            lines.append(asp.fact("puncturable", obj_id))
    for shelter_id, shelter in SHELTERS.items():
        lines.append(asp.fact("shelter", shelter_id))
        lines.append(asp.fact("danger", shelter_id, shelter.danger))
        if shelter.risky:
            lines.append(asp.fact("risky", shelter_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("sense", helper_id, helper.sense))
        lines.append(asp.fact("power", helper_id, helper.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(h for (h,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_shelter", params.shelter),
        asp.fact("chosen_helper", params.helper),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    python_gate = set(valid_combos())
    clingo_gate = set(asp_valid_combos())
    if python_gate == clingo_gate:
        print(f"OK: gate matches valid_combos() ({len(python_gate)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_gate - python_gate:
            print("  only in clingo:", sorted(clingo_gate - python_gate))
        if python_gate - clingo_gate:
            print("  only in python:", sorted(python_gate - clingo_gate))

    python_helpers = {h.id for h in sensible_helpers()}
    clingo_helpers = set(asp_sensible())
    if python_helpers == clingo_helpers:
        print(f"OK: sensible helpers match ({sorted(python_helpers)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible helpers: clingo={sorted(clingo_helpers)} python={sorted(python_helpers)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
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
        if not sample.story or "cobra" not in sample.story or "puncture" not in sample.story or "raise" not in sample.story:
            raise StoryError("Smoke test story missing required content.")
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: two young animals, a whistle, warning signs, and a cobra hazard."
    )
    ap.add_argument("--child-kind", choices=CHILD_KINDS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--shelter", choices=SHELTERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start before the elder arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_names(rng: random.Random) -> tuple[str, str, str, str]:
    hero_is_girl = rng.choice([True, False])
    if hero_is_girl:
        hero_name = rng.choice(GIRL_NAMES)
        hero_type = rng.choice(["mongoose_girl", "meerkat_girl", "rabbit_girl"])
        cautioner_name = rng.choice([n for n in BOY_NAMES + GIRL_NAMES if n != hero_name])
        cautioner_type = rng.choice(["mongoose_boy", "meerkat_boy", "rabbit_boy", "mongoose_girl", "meerkat_girl", "rabbit_girl"])
    else:
        hero_name = rng.choice(BOY_NAMES)
        hero_type = rng.choice(["mongoose_boy", "meerkat_boy", "rabbit_boy"])
        cautioner_name = rng.choice([n for n in BOY_NAMES + GIRL_NAMES if n != hero_name])
        cautioner_type = rng.choice(["mongoose_boy", "meerkat_boy", "rabbit_boy", "mongoose_girl", "meerkat_girl", "rabbit_girl"])
    elder_name = rng.choice([h.label for h in HELPERS.values()])
    return hero_name, hero_type, cautioner_name, cautioner_type


def _force_species_type(kind_id: str, raw_type: str) -> str:
    sex = "girl" if raw_type.endswith("_girl") else "boy"
    return f"{kind_id}_{sex}"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.object and args.shelter:
        obj = OBJECTS[args.object]
        shelter = SHELTERS[args.shelter]
        if not hazard_at_risk(obj, shelter):
            raise StoryError(explain_rejection(obj, shelter))
    if args.helper and HELPERS[args.helper].sense < SENSE_MIN:
        raise StoryError(explain_helper(args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.child_kind is None or combo[0] == args.child_kind)
        and (args.object is None or combo[1] == args.object)
        and (args.shelter is None or combo[2] == args.shelter)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    child_kind, object_id, shelter_id, helper_id = rng.choice(sorted(combos))
    relation = args.relation or rng.choice(["siblings", "friends"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    trait = rng.choice(TRAITS)
    hero_name, raw_hero_type, cautioner_name, raw_cautioner_type = _pick_names(rng)
    hero_type = _force_species_type(child_kind, raw_hero_type)
    cautioner_type = _force_species_type(child_kind, raw_cautioner_type)
    elder_name = HELPERS[helper_id].label
    hero_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        child_kind=child_kind,
        object=object_id,
        shelter=shelter_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_type=hero_type,
        cautioner_name=cautioner_name,
        cautioner_type=cautioner_type,
        elder_name=elder_name,
        relation=relation,
        trait=trait,
        delay=delay,
        hero_age=hero_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.child_kind not in CHILD_KINDS:
        raise StoryError(f"(Unknown child kind: {params.child_kind})")
    if params.object not in OBJECTS:
        raise StoryError(f"(Unknown object: {params.object})")
    if params.shelter not in SHELTERS:
        raise StoryError(f"(Unknown shelter: {params.shelter})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    kind = CHILD_KINDS[params.child_kind]
    obj = OBJECTS[params.object]
    shelter = SHELTERS[params.shelter]
    helper = HELPERS[params.helper]

    if not hazard_at_risk(obj, shelter):
        raise StoryError(explain_rejection(obj, shelter))
    if helper.sense < SENSE_MIN:
        raise StoryError(explain_helper(params.helper))

    world = tell(
        kind=kind,
        obj=obj,
        shelter=shelter,
        helper=helper,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        cautioner_name=params.cautioner_name,
        cautioner_type=params.cautioner_type,
        elder_name=params.elder_name,
        relation=params.relation,
        trait=params.trait,
        delay=params.delay,
        hero_age=params.hero_age,
        cautioner_age=params.cautioner_age,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible helpers: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (child_kind, object, shelter, helper) combos:\n")
        for child_kind, object_id, shelter_id, helper_id in combos:
            print(f"  {child_kind:9} {object_id:8} {shelter_id:14} {helper_id}")
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
            header = (
                f"### {p.hero_name} & {p.cautioner_name}: {p.object} near {p.shelter} "
                f"({p.child_kind}, {p.helper}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
