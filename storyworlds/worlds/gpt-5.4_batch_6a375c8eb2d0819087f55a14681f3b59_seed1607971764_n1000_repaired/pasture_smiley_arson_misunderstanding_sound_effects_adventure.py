#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pasture_smiley_arson_misunderstanding_sound_effects_adventure.py
=============================================================================================

A standalone story world for a small adventure on a pasture: two children go
looking for Smiley, a missing farm animal, hear alarming sound effects, and one
child misunderstands a smoky scene as "arson." The misunderstanding drives the
tension; the world then proves whether there is no fire at all, a small fire
that is sensibly contained, or a singed patch left behind when help is too late.

The domain is intentionally narrow and reasoned:
- the adventure always begins with a search across a pasture
- the word "smiley" appears as the missing animal's name
- the word "arson" appears as the child's mistaken fear
- sound effects matter: clinks, hisses, crackles, and bangs drive the turn
- a Python reasonableness gate and an ASP twin agree on valid combinations

Run it
------
    python storyworlds/worlds/gpt-5.4/pasture_smiley_arson_misunderstanding_sound_effects_adventure.py
    python storyworlds/worlds/gpt-5.4/pasture_smiley_arson_misunderstanding_sound_effects_adventure.py --all
    python storyworlds/worlds/gpt-5.4/pasture_smiley_arson_misunderstanding_sound_effects_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/pasture_smiley_arson_misunderstanding_sound_effects_adventure.py --json
    python storyworlds/worlds/gpt-5.4/pasture_smiley_arson_misunderstanding_sound_effects_adventure.py --asp
    python storyworlds/worlds/gpt-5.4/pasture_smiley_arson_misunderstanding_sound_effects_adventure.py --verify
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
SENSE_MIN = 3


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
        female = {"girl", "mother", "woman", "shepherdess"}
        male = {"boy", "father", "man", "shepherd"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class SearchTarget:
    id: str
    animal: str
    phrase: str
    hoof: str
    call_sound: str
    hide_spot: str
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
class Pasture:
    id: str
    phrase: str
    grass: str
    dampness: int
    detail: str
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
class Cause:
    id: str
    label: str
    sound: str
    sound_effect: str
    smoke: bool
    actual_fire: bool
    base_severity: int
    place: str
    explanation: str
    accident_text: str
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
class Response:
    id: str
    sense: int
    power: int
    no_fire_only: bool
    text: str
    fail: str
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
        return [e for e in self.entities.values() if e.role in {"leader", "partner"}]

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


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    patch = world.get("patch")
    if source.meters["burning"] >= THRESHOLD:
        sig = ("danger", "source")
        if sig not in world.fired:
            world.fired.add(sig)
            patch.meters["danger"] += 1
            patch.meters["smoke"] += source.meters["smoke"]
            for kid in world.kids():
                kid.memes["fear"] += 1
            out.append("__danger__")
    return out


def _r_find_smiley(world: World) -> list[str]:
    out: list[str] = []
    smiley = world.get("smiley")
    if smiley.memes["called"] >= THRESHOLD and smiley.memes["heard_bell"] >= THRESHOLD:
        sig = ("found", "smiley")
        if sig not in world.fired:
            world.fired.add(sig)
            smiley.meters["found"] += 1
            for kid in world.kids():
                kid.memes["relief"] += 1
            out.append("__found__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="danger", tag="physical", apply=_r_danger),
    Rule(name="find_smiley", tag="social", apply=_r_find_smiley),
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


def severity_for(cause: Cause, pasture: Pasture, delay: int) -> int:
    if not cause.actual_fire:
        return 0
    return max(1, cause.base_severity + pasture.dampness + delay)


def is_contained(response: Response, cause: Cause, pasture: Pasture, delay: int) -> bool:
    if not cause.actual_fire:
        return True
    return response.power >= severity_for(cause, pasture, delay)


def hazard_combo(target_id: str, cause_id: str, pasture_id: str) -> bool:
    target = TARGETS[target_id]
    cause = CAUSES[cause_id]
    pasture = PASTURES[pasture_id]
    if target.id not in {"lamb", "calf", "goat"}:
        return False
    if cause.id == "kettle":
        return True
    if cause.id == "lantern":
        return True
    if cause.id == "wagon_brake":
        return True
    return pasture.id == "dry_meadow"


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def explain_combo(target: SearchTarget, cause: Cause, pasture: Pasture) -> str:
    return (
        f"(No story: {target.phrase} in {pasture.phrase} does not make a grounded "
        f"misunderstanding with {cause.label}. Pick a listed cause that can honestly "
        f"produce the scary sounds or smoke that make the child blurt out 'arson'.)"
    )


def explain_response(response: Response, cause: Cause) -> str:
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response.id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). Try a safer response like "
            f"{', '.join(sorted(r.id for r in sensible_responses()))}.)"
        )
    if cause.actual_fire and response.no_fire_only:
        return (
            f"(No story: '{response.id}' only fits a false alarm, but {cause.label} "
            f"can start a real grass fire.)"
        )
    if (not cause.actual_fire) and (not response.no_fire_only):
        return (
            f"(No story: {cause.label} is only a misunderstanding here, so no fire "
            f"needs to be put out. Use the calm explanation response instead.)"
        )
    return "(No story: the chosen response does not fit this cause.)"


def predict_scene(world: World, cause: Cause, pasture: Pasture) -> dict:
    sim = world.copy()
    source = sim.get("source")
    source.meters["smoke"] = 1.0 if cause.smoke else 0.0
    if cause.actual_fire:
        source.meters["burning"] = float(severity_for(cause, pasture, 0))
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("patch").meters["danger"],
        "smoke": source.meters["smoke"],
        "burning": source.meters["burning"],
    }


def open_adventure(world: World, a: Entity, b: Entity, parent: Entity,
                   target: SearchTarget, pasture: Pasture) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["brave"] += 1
    world.say(
        f"On a bright morning, {a.id} and {b.id} set off on an adventure across "
        f"{pasture.phrase}. {pasture.detail}"
    )
    world.say(
        f"They were looking for Smiley, {target.phrase}, who had wandered away "
        f"toward {target.hide_spot}. {a.id} carried a little map, and {b.id} carried "
        f"a bell to ring if they found a clue."
    )
    world.say(
        f'"Adventure scouts!" {a.id} whispered. "{parent.label_word.capitalize()} said '
        f'Smiley might answer to {target.call_sound}."'
    )


def clue(world: World, a: Entity, b: Entity, target: SearchTarget) -> None:
    world.say(
        f"Near the gate they found {target.hoof}, and beside it lay a pebble with a "
        f"smiley face drawn on it in chalk."
    )
    world.say(
        f'"A smiley clue!" {b.id} said. The two of them hurried on, feeling as if they '
        f"were following a secret trail."
    )


def hear_scene(world: World, a: Entity, b: Entity, cause: Cause, pasture: Pasture) -> None:
    pred = predict_scene(world, cause, pasture)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_smoke"] = pred["smoke"]
    source = world.get("source")
    source.meters["smoke"] = 1.0 if cause.smoke else 0.0
    world.say(
        f"Then, from beyond a low rise, came a strange sound: {cause.sound_effect}!"
    )
    world.say(
        f'"Did you hear that?" {a.id} asked. {cause.sound}'
    )
    if cause.smoke:
        world.say(
            f"A thin ribbon of smoke curled up near {cause.place}, and the children "
            f"froze in the grass."
        )


def misunderstanding(world: World, a: Entity, b: Entity, cause: Cause) -> None:
    a.memes["confusion"] += 1
    b.memes["confusion"] += 1
    world.say(
        f'{b.id} grabbed {a.id}\'s sleeve. "Is that arson?" {b.pronoun()} whispered. '
        f'"I heard that word when the fire truck came to school."'
    )
    if cause.smoke:
        world.say(
            f"{a.id} did not know for sure. Smoke plus a sharp noise sounded big and "
            f"dangerous in the middle of the adventure."
        )
    else:
        world.say(
            f"{a.id} did not know for sure. The bang had sounded so sudden that the whole "
            f"pasture felt different for a moment."
        )


def call_for_help(world: World, a: Entity, b: Entity, parent: Entity,
                  target: SearchTarget) -> None:
    for kid in (a, b):
        kid.memes["care"] += 1
    smiley = world.get("smiley")
    smiley.memes["called"] += 1
    world.say(
        f'"{parent.label_word.upper()}!" both children shouted, and then {a.id} cupped '
        f"{a.pronoun('possessive')} hands and called, \"Smiley! {target.call_sound}!\""
    )


def real_fire(world: World, cause: Cause, pasture: Pasture, delay: int) -> None:
    source = world.get("source")
    patch = world.get("patch")
    source.meters["smoke"] = 1.0 if cause.smoke else 0.0
    source.meters["burning"] = float(severity_for(cause, pasture, delay))
    source.meters["severity"] = float(severity_for(cause, pasture, delay))
    patch.meters["dryness"] = float(max(0, pasture.dampness))
    propagate(world, narrate=False)
    world.say(
        f"When they looked over the rise, they saw what had happened: {cause.accident_text}"
    )


def false_alarm(world: World, parent: Entity, cause: Cause) -> None:
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"{parent.label_word.capitalize()} was already there by {cause.place}, and "
        f"{parent.pronoun()} lifted a hand so they would slow down."
    )
    world.say(
        f'"Easy now," {parent.pronoun()} said. "{cause.explanation}"'
    )
    world.say(
        f"The sound had been startling, but there was no fire racing through the grass "
        f"at all."
    )


def contain_fire(world: World, parent: Entity, response: Response,
                 cause: Cause, pasture: Pasture, delay: int) -> None:
    source = world.get("source")
    patch = world.get("patch")
    source.meters["burning"] = 0.0
    patch.meters["danger"] = 0.0
    patch.meters["singed"] += 1
    body = response.text.replace("{place}", cause.place).replace("{grass}", pasture.grass)
    world.say(
        f"{parent.label_word.capitalize()} came running with a steady face and {body}."
    )
    world.say(
        "The little flames gave one last crackle -- snap-snap! -- and then they were gone."
    )


def fire_too_late(world: World, parent: Entity, response: Response,
                  cause: Cause, pasture: Pasture, delay: int) -> None:
    patch = world.get("patch")
    patch.meters["singed"] += 2
    patch.meters["danger"] = 0.0
    body = response.fail.replace("{place}", cause.place).replace("{grass}", pasture.grass)
    world.say(
        f"{parent.label_word.capitalize()} hurried in and {body}."
    )
    world.say(
        f"The fire did stop before it reached the far fence, but it left a black, singed "
        f"patch in the {pasture.grass}."
    )


def explain_not_arson(world: World, parent: Entity, cause: Cause, actual_fire: bool) -> None:
    for kid in world.kids():
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
    if actual_fire:
        world.say(
            f'{parent.label_word.capitalize()} knelt beside the children. "You were right to call '
            f'for me," {parent.pronoun()} said. "But this was not arson. Arson means setting a fire '
            f'on purpose. This was an accident, and accidents still need fast, careful help."'
        )
    else:
        world.say(
            f'{parent.label_word.capitalize()} knelt beside the children. "Arson is when someone sets '
            f'a fire on purpose," {parent.pronoun()} said gently. "This was only a noisy bit of farm work, '
            f'and you did the right thing by asking instead of guessing."'
        )


def ring_bell_and_find(world: World, a: Entity, b: Entity, target: SearchTarget,
                       parent: Entity) -> None:
    smiley = world.get("smiley")
    smiley.memes["heard_bell"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {b.id} rang the bell -- ding-ding! -- and from behind the thistles came "
        f"{target.call_sound}."
    )
    world.say(
        f"Out stepped Smiley at last, nibbling calmly as if the whole adventure had been part of a game."
    )
    world.say(
        f"{a.id} laughed, {b.id} hugged Smiley's neck, and {parent.label_word} led them all home across "
        f"the pasture under the wide gold sky."
    )


def end_safe(world: World, a: Entity, b: Entity, target: SearchTarget,
             parent: Entity, actual_fire: bool) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    if actual_fire:
        world.say(
            "On the way back, the children looked once more at the quiet ground and felt the difference "
            "between a scary guess and a true answer."
        )
    else:
        world.say(
            "On the way back, the children felt taller inside, because asking for the truth had turned a "
            "frightening moment back into an adventure."
        )
    world.say(
        f'That night, {b.id} drew a new smiley on the map where they had found Smiley, and {a.id} wrote, '
        f'"Listen first, then be brave."'
    )


def tell(target: SearchTarget, pasture: Pasture, cause: Cause, response: Response,
         leader_name: str = "Nora", leader_gender: str = "girl",
         partner_name: str = "Eli", partner_gender: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    a = world.add(Entity(
        id=leader_name,
        kind="character",
        type=leader_gender,
        role="leader",
        traits=["adventurous"],
        attrs={},
    ))
    b = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        traits=["careful"],
        attrs={},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="guide",
        label="the parent",
        attrs={},
    ))
    smiley = world.add(Entity(
        id="smiley",
        kind="thing",
        type=target.animal,
        role="target",
        label="Smiley",
        attrs={},
    ))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type="source",
        label=cause.label,
        attrs={},
    ))
    patch = world.add(Entity(
        id="patch",
        kind="thing",
        type="pasture",
        label=pasture.id,
        attrs={},
    ))

    source.meters["smoke"] = 0.0
    source.meters["burning"] = 0.0
    source.meters["severity"] = 0.0
    patch.meters["danger"] = 0.0
    patch.meters["smoke"] = 0.0
    patch.meters["singed"] = 0.0
    patch.meters["dryness"] = float(max(0, pasture.dampness))
    smiley.meters["found"] = 0.0
    smiley.memes["called"] = 0.0
    smiley.memes["heard_bell"] = 0.0
    for kid in (a, b):
        kid.memes["fear"] = 0.0
        kid.memes["relief"] = 0.0
        kid.memes["lesson"] = 0.0
        kid.memes["joy"] = 0.0
        kid.memes["brave"] = 0.0
        kid.memes["care"] = 0.0
        kid.memes["confusion"] = 0.0

    open_adventure(world, a, b, parent, target, pasture)
    clue(world, a, b, target)

    world.para()
    hear_scene(world, a, b, cause, pasture)
    misunderstanding(world, a, b, cause)
    call_for_help(world, a, b, parent, target)

    world.para()
    severity = severity_for(cause, pasture, delay)
    if cause.actual_fire:
        real_fire(world, cause, pasture, delay)
        contained = is_contained(response, cause, pasture, delay)
        if contained:
            contain_fire(world, parent, response, cause, pasture, delay)
        else:
            fire_too_late(world, parent, response, cause, pasture, delay)
        explain_not_arson(world, parent, cause, actual_fire=True)
        outcome = "contained" if contained else "singed"
    else:
        false_alarm(world, parent, cause)
        explain_not_arson(world, parent, cause, actual_fire=False)
        outcome = "explained"

    world.para()
    ring_bell_and_find(world, a, b, target, parent)
    end_safe(world, a, b, target, parent, actual_fire=cause.actual_fire)

    world.facts.update(
        leader=a,
        partner=b,
        parent=parent,
        smiley=smiley,
        target_cfg=target,
        pasture=pasture,
        cause=cause,
        response=response,
        delay=delay,
        severity=severity,
        actual_fire=cause.actual_fire,
        outcome=outcome,
        found=smiley.meters["found"] >= THRESHOLD,
        singed=world.get("patch").meters["singed"] >= THRESHOLD,
    )
    return world


TARGETS = {
    "lamb": SearchTarget(
        id="lamb",
        animal="lamb",
        phrase="a woolly lamb with one floppy ear",
        hoof="small split hoofprints",
        call_sound="baa-aa",
        hide_spot="the far side of the thistle hill",
        tags={"animal", "lamb"},
    ),
    "calf": SearchTarget(
        id="calf",
        animal="calf",
        phrase="a round-eyed calf with a white nose",
        hoof="soft, wide hoofprints",
        call_sound="moo-oo",
        hide_spot="the shady side of the water trough",
        tags={"animal", "calf"},
    ),
    "goat": SearchTarget(
        id="goat",
        animal="goat",
        phrase="a springy little goat with bright knees",
        hoof="tiny neat hoofprints",
        call_sound="maa-a",
        hide_spot="the rocks near the old fence",
        tags={"animal", "goat"},
    ),
}

PASTURES = {
    "green_hollow": Pasture(
        id="green_hollow",
        phrase="the green hollow pasture",
        grass="cool green grass",
        dampness=-1,
        detail="The grass still held little beads of dew, and the wind moved in soft waves over the field",
        tags={"pasture", "dew"},
    ),
    "sunny_field": Pasture(
        id="sunny_field",
        phrase="the sunny pasture",
        grass="yellow-green grass",
        dampness=0,
        detail="Buttercups nodded along the path, and an old wagon track curled through the middle like a trail on a treasure map",
        tags={"pasture", "sun"},
    ),
    "dry_meadow": Pasture(
        id="dry_meadow",
        phrase="the dry summer pasture",
        grass="dry straw-colored grass",
        dampness=1,
        detail="The ground was pale and rustly underfoot, and every step made the field whisper around their boots",
        tags={"pasture", "dry"},
    ),
}

CAUSES = {
    "kettle": Cause(
        id="kettle",
        label="the chuck-wagon kettle",
        sound="The lid went plink-plink while steam hissed around the rim",
        sound_effect="plink-plink, hissss",
        smoke=True,
        actual_fire=False,
        base_severity=0,
        place="the cookfire ring by the wagon",
        explanation="The kettle was only singing on a safe cookfire ring while lunch warmed",
        accident_text="",
        tags={"smoke", "kettle", "sound"},
    ),
    "lantern": Cause(
        id="lantern",
        label="a tipped lantern",
        sound="Glass had clinked against stone, and the flame was nibbling at the grass with a crackle-crackle sound",
        sound_effect="clink! crackle-crackle",
        smoke=True,
        actual_fire=True,
        base_severity=2,
        place="the old supply wagon",
        explanation="",
        accident_text="a lantern had tipped near the wagon, and a strip of grass was burning beside it",
        tags={"fire", "smoke", "lantern", "sound"},
    ),
    "wagon_brake": Cause(
        id="wagon_brake",
        label="the wagon brake",
        sound="A loose brake shoe had slammed the wheel with a loud bang and sent up a puff of dust",
        sound_effect="BANG-clang!",
        smoke=False,
        actual_fire=False,
        base_severity=0,
        place="the old wagon wheel",
        explanation="The wagon brake had only banged loose and kicked up dust; nothing was burning",
        accident_text="",
        tags={"wagon", "sound"},
    ),
}

RESPONSES = {
    "explain": Response(
        id="explain",
        sense=4,
        power=0,
        no_fire_only=True,
        text="",
        fail="",
        qa_text="explained the sound and showed the children there was no dangerous fire",
        tags={"explain"},
    ),
    "wet_blanket": Response(
        id="wet_blanket",
        sense=4,
        power=3,
        no_fire_only=False,
        text="snatched up a wet blanket from {place} and pressed it over the flames until the {grass} stopped glowing",
        fail="threw the wet blanket over the flames, but the fire had already licked farther through the {grass} than one blanket could cover",
        qa_text="smothered the flames with a wet blanket",
        tags={"blanket", "fire"},
    ),
    "water_pail": Response(
        id="water_pail",
        sense=4,
        power=2,
        no_fire_only=False,
        text="grabbed a water pail from {place} and poured it low and steady over the flames",
        fail="poured a whole pail of water over the flames, but they had already spread through too much of the {grass}",
        qa_text="poured water over the fire until it went out",
        tags={"water", "fire"},
    ),
    "hat_wave": Response(
        id="hat_wave",
        sense=1,
        power=0,
        no_fire_only=False,
        text="waved a hat at the flames",
        fail="waved a hat at the flames, which only stirred them faster",
        qa_text="waved a hat at the flames",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Ava", "Mia", "Zoe", "Ella", "Maya", "Lucy"]
BOY_NAMES = ["Eli", "Tom", "Ben", "Max", "Finn", "Theo", "Jack", "Leo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for target_id in TARGETS:
        for cause_id in CAUSES:
            for pasture_id in PASTURES:
                if hazard_combo(target_id, cause_id, pasture_id):
                    combos.append((target_id, cause_id, pasture_id))
    return combos


@dataclass
class StoryParams:
    target: str
    cause: str
    pasture: str
    response: str
    leader: str
    leader_gender: str
    partner: str
    partner_gender: str
    parent: str
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


KNOWLEDGE = {
    "pasture": [
        (
            "What is a pasture?",
            "A pasture is a grassy field where farm animals can walk, graze, and rest."
        )
    ],
    "arson": [
        (
            "What does arson mean?",
            "Arson means setting a fire on purpose. If you are not sure what is happening, the safe thing is to ask a grown-up right away."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something means one thing, but it really means something else."
        )
    ],
    "lantern": [
        (
            "Why can a lantern be dangerous in dry grass?",
            "A lantern has a real flame or a very hot part, so if it tips into dry grass it can start a fire quickly."
        )
    ],
    "blanket": [
        (
            "How can a wet blanket help with a small fire?",
            "A wet blanket can cover a small fire and cut down the heat and air around it, which helps the flames go out."
        )
    ],
    "water": [
        (
            "Why does water help put out a small grass fire?",
            "Water cools the burning grass and can stop the flames from spreading farther."
        )
    ],
    "bell": [
        (
            "Why might a farm animal come to a bell?",
            "Animals learn familiar sounds. If they know a bell means food or company, they may come when they hear it."
        )
    ],
    "kettle": [
        (
            "Why does a kettle make hissing and clinking sounds?",
            "A kettle can hiss when steam pushes out, and the lid can clink when hot water bubbles underneath it."
        )
    ],
}
KNOWLEDGE_ORDER = ["pasture", "arson", "misunderstanding", "lantern", "blanket", "water", "bell", "kettle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    target = f["target_cfg"]
    cause = f["cause"]
    pasture = f["pasture"]
    outcome = f["outcome"]
    leader = f["leader"]
    partner = f["partner"]
    base = (
        f'Write a short adventure story for a 3-to-5-year-old set in a pasture, including '
        f'the words "smiley" and "arson," where two children hear scary sound effects while '
        f'looking for a missing {target.animal}.'
    )
    if outcome == "explained":
        return [
            base,
            f"Tell a gentle adventure where {leader.id} and {partner.id} mistake a noisy smoky farm scene for arson, but it turns out to be harmless and a grown-up explains the misunderstanding.",
            f'Write a story with sound effects and a misunderstanding that ends with the children finding Smiley and learning to ask for the truth instead of guessing.'
        ]
    if outcome == "contained":
        return [
            base,
            f"Tell an adventure where the children fear arson after hearing {cause.sound_effect}, but a grown-up quickly puts out a small accidental fire and explains the difference between an accident and a fire set on purpose.",
            f"Write a pasture rescue story where the misunderstanding leads the children to call for help fast, and that brave choice helps keep everyone safe."
        ]
    return [
        base,
        f"Tell an adventure where the children think they see arson, and although a grown-up stops the fire before it spreads too far, the pasture is left singed and the children learn why quick help matters.",
        f"Write a sound-filled farm story with a misunderstanding, a black patch of burned grass, and a safe ending where Smiley is still found."
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two children"
    if a.type == "girl" and b.type == "girl":
        return "two children"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["leader"]
    b = f["partner"]
    parent = f["parent"]
    target = f["target_cfg"]
    pasture = f["pasture"]
    cause = f["cause"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}, searching across {pasture.phrase} for Smiley the {target.animal}. Their adventure changes when a strange noise makes them worry something dangerous is happening."
        ),
        (
            "Why were the children out in the pasture?",
            f"They were trying to find Smiley, who had wandered away toward {target.hide_spot}. The missing animal turned their walk into a little adventure with clues and a map."
        ),
        (
            "Why did the children say the word arson?",
            f"They heard {cause.sound_effect} and, in some versions, saw smoke near {cause.place}. Those clues sounded so alarming that they misunderstood the scene and wondered if it was arson."
        ),
    ]
    if outcome == "explained":
        qa.append((
            "What was really making the scary sound?",
            f"It was {cause.label}. {parent.label_word.capitalize()} explained that nothing dangerous was spreading through the grass, so the children could trade fear for understanding."
        ))
    elif outcome == "contained":
        qa.append((
            f"How did {a.id}'s {parent.label_word} stop the fire?",
            f"{parent.label_word.capitalize()} {response.qa_text}. That fast, careful help kept the small fire from running across the pasture."
        ))
        qa.append((
            "Was it really arson?",
            "No. It was an accident, not a fire set on purpose. The grown-up explained the difference so the children understood the big word they had used."
        ))
    else:
        qa.append((
            "What happened to the pasture after the fire was stopped?",
            f"A black, singed patch was left in the {pasture.grass}. The children were safe, but they could see that even a small fire can leave a mark when help comes a little later."
        ))
        qa.append((
            "Was it really arson?",
            "No. The grown-up explained that arson means setting a fire on purpose, and this was an accident. The misunderstanding still helped the children do the right thing, because they called for help fast."
        ))
    qa.append((
        "How did the story end?",
        f"{b.id} rang the bell, Smiley came out, and the family walked home together. The ending shows that the adventure became calm again once the children stopped guessing and listened carefully."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"pasture", "arson", "misunderstanding", "bell"}
    cause = world.facts["cause"]
    response = world.facts["response"]
    if cause.id == "kettle":
        tags.add("kettle")
    if cause.id == "lantern":
        tags.add("lantern")
    if response.id == "wet_blanket":
        tags.add("blanket")
    if response.id == "water_pail":
        tags.add("water")
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        target="lamb",
        cause="kettle",
        pasture="sunny_field",
        response="explain",
        leader="Nora",
        leader_gender="girl",
        partner="Eli",
        partner_gender="boy",
        parent="mother",
        delay=0,
    ),
    StoryParams(
        target="goat",
        cause="lantern",
        pasture="green_hollow",
        response="water_pail",
        leader="Mia",
        leader_gender="girl",
        partner="Tom",
        partner_gender="boy",
        parent="father",
        delay=0,
    ),
    StoryParams(
        target="calf",
        cause="lantern",
        pasture="dry_meadow",
        response="water_pail",
        leader="Leo",
        leader_gender="boy",
        partner="Ava",
        partner_gender="girl",
        parent="mother",
        delay=1,
    ),
    StoryParams(
        target="lamb",
        cause="wagon_brake",
        pasture="green_hollow",
        response="explain",
        leader="Lucy",
        leader_gender="girl",
        partner="Finn",
        partner_gender="boy",
        parent="father",
        delay=0,
    ),
    StoryParams(
        target="goat",
        cause="lantern",
        pasture="sunny_field",
        response="wet_blanket",
        leader="Zoe",
        leader_gender="girl",
        partner="Max",
        partner_gender="boy",
        parent="mother",
        delay=0,
    ),
]


def outcome_of(params: StoryParams) -> str:
    cause = CAUSES[params.cause]
    pasture = PASTURES[params.pasture]
    response = RESPONSES[params.response]
    if not cause.actual_fire:
        return "explained"
    return "contained" if is_contained(response, cause, pasture, params.delay) else "singed"


ASP_RULES = r"""
valid(Target, Cause, Pasture) :- target(Target), cause(Cause), pasture(Pasture),
                                 plausible(Target, Cause, Pasture).

sensible(Response) :- response(Response), sense(Response, S), sense_min(M), S >= M.

severity(C, P, D, 0) :- actual_fire(C, 0), pasture(P), delay(D).
severity(C, P, D, V) :- actual_fire(C, 1), base_severity(C, B), dampness(P, K), delay(D), V = B + K + D, V > 0.
severity(C, P, D, 1) :- actual_fire(C, 1), base_severity(C, B), dampness(P, K), delay(D), B + K + D <= 0.

contained :- chosen_cause(C), chosen_pasture(P), delay(D), chosen_response(R),
             actual_fire(C, 1), severity(C, P, D, V), power(R, Pow), Pow >= V.

outcome(explained) :- chosen_cause(C), actual_fire(C, 0).
outcome(contained) :- chosen_cause(C), actual_fire(C, 1), contained.
outcome(singed) :- chosen_cause(C), actual_fire(C, 1), not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for target_id in TARGETS:
        lines.append(asp.fact("target", target_id))
    for pasture_id, pasture in PASTURES.items():
        lines.append(asp.fact("pasture", pasture_id))
        lines.append(asp.fact("dampness", pasture_id, pasture.dampness))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("actual_fire", cause_id, 1 if cause.actual_fire else 0))
        lines.append(asp.fact("base_severity", cause_id, cause.base_severity))
    for target_id, cause_id, pasture_id in valid_combos():
        lines.append(asp.fact("plausible", target_id, cause_id, pasture_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
        if response.no_fire_only:
            lines.append(asp.fact("no_fire_only", response_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_pasture", params.pasture),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    csense = set(asp_sensible())
    psense = {r.id for r in sensible_responses()}
    if csense == psense:
        print(f"OK: sensible responses match ({sorted(csense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(csense)} python={sorted(psense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve_params failure for seed {seed}.")
            break
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "Smiley" not in sample.story:
            raise StoryError("Smoke test story did not render expected adventure content.")
        print("OK: smoke test generate() rendered a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pasture adventure, a misunderstanding, and brave help."
    )
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--pasture", choices=PASTURES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra time before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and args.cause and args.pasture:
        if not hazard_combo(args.target, args.cause, args.pasture):
            raise StoryError(explain_combo(TARGETS[args.target], CAUSES[args.cause], PASTURES[args.pasture]))

    combos = [
        combo for combo in valid_combos()
        if (args.target is None or combo[0] == args.target)
        and (args.cause is None or combo[1] == args.cause)
        and (args.pasture is None or combo[2] == args.pasture)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    target_id, cause_id, pasture_id = rng.choice(sorted(combos))
    cause = CAUSES[cause_id]

    if args.response:
        response_id = args.response
        response = RESPONSES[response_id]
        if response.sense < SENSE_MIN or response.no_fire_only != (not cause.actual_fire):
            raise StoryError(explain_response(response, cause))
    else:
        if cause.actual_fire:
            response_id = rng.choice(sorted(r.id for r in sensible_responses() if not r.no_fire_only))
        else:
            response_id = "explain"

    leader, leader_gender = _pick_child(rng)
    partner, partner_gender = _pick_child(rng, avoid=leader)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else (rng.randint(0, 1) if cause.actual_fire else 0)

    return StoryParams(
        target=target_id,
        cause=cause_id,
        pasture=pasture_id,
        response=response_id,
        leader=leader,
        leader_gender=leader_gender,
        partner=partner,
        partner_gender=partner_gender,
        parent=parent,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.pasture not in PASTURES:
        raise StoryError(f"(Unknown pasture: {params.pasture})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    if not hazard_combo(params.target, params.cause, params.pasture):
        raise StoryError(explain_combo(TARGETS[params.target], CAUSES[params.cause], PASTURES[params.pasture]))

    cause = CAUSES[params.cause]
    response = RESPONSES[params.response]
    if response.sense < SENSE_MIN or response.no_fire_only != (not cause.actual_fire):
        raise StoryError(explain_response(response, cause))

    world = tell(
        target=TARGETS[params.target],
        pasture=PASTURES[params.pasture],
        cause=cause,
        response=response,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (target, cause, pasture) combos:\n")
        for target, cause, pasture in combos:
            print(f"  {target:6} {cause:11} {pasture}")
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
                f"### {p.leader} & {p.partner}: {p.target} / {p.cause} / {p.pasture} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
