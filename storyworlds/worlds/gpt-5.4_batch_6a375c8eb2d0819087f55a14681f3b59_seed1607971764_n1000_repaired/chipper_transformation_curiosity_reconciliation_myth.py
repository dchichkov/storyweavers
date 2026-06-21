#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/chipper_transformation_curiosity_reconciliation_myth.py
==================================================================================

A standalone storyworld for a tiny mythic domain: a chipper child grows too
curious about a sacred wonder, breaks a boundary, is transformed by a guardian
spirit, and must make a fitting act of reconciliation to be changed back.

The world model tracks:
- physical meters: glow, hush, feathers/scales/petals, blessing
- emotional memes: curiosity, shame, wonder, fear, forgiveness

The prose is driven by state and branching outcomes, not simple word swaps.
A Python reasonableness gate and an inline ASP twin agree on which parameter
combinations form plausible myths.

Run it
------
    python storyworlds/worlds/gpt-5.4/chipper_transformation_curiosity_reconciliation_myth.py
    python storyworlds/worlds/gpt-5.4/chipper_transformation_curiosity_reconciliation_myth.py --place moon_pool
    python storyworlds/worlds/gpt-5.4/chipper_transformation_curiosity_reconciliation_myth.py --amends torch_song
    python storyworlds/worlds/gpt-5.4/chipper_transformation_curiosity_reconciliation_myth.py --all
    python storyworlds/worlds/gpt-5.4/chipper_transformation_curiosity_reconciliation_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/chipper_transformation_curiosity_reconciliation_myth.py --json
    python storyworlds/worlds/gpt-5.4/chipper_transformation_curiosity_reconciliation_myth.py --verify
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
    role: str = ""
    owner: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "goddess"}
        male = {"boy", "man", "god", "father"}
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


@dataclass
class SacredPlace:
    id: str
    title: str
    scene: str
    guardian_name: str
    guardian_type: str
    element: str
    relic_label: str
    relic_phrase: str
    warning: str
    helper_label: str
    helper_hint: str
    ending_image: str
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
class ForbiddenAct:
    id: str
    verb: str
    approach: str
    question: str
    trespass: str
    lesson: str
    needs_touch: bool = True
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
class Form:
    id: str
    label: str
    body_change: str
    movement: str
    voice: str
    mood: str
    element: str
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
class Amends:
    id: str
    label: str
    action: str
    effect: str
    element: str
    gentle: bool = True
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


def _r_transformation(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["transformed"] < THRESHOLD:
        return []
    sig = ("transformation", world.facts["form"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    child.memes["wonder"] += 1
    spirit = world.get("guardian")
    spirit.meters["hush"] += 1
    return ["__transform__"]


def _r_reconciliation(world: World) -> list[str]:
    child = world.get("child")
    spirit = world.get("guardian")
    if child.memes["apology"] < THRESHOLD or child.meters["amends_done"] < THRESHOLD:
        return []
    sig = ("reconciled", world.facts["amends"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    spirit.memes["forgiveness"] += 1
    child.meters["restored"] += 1
    child.meters["blessing"] += 1
    child.meters["transformed"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    return ["__reconcile__"]


CAUSAL_RULES = [
    Rule(name="transformation", tag="mythic", apply=_r_transformation),
    Rule(name="reconciliation", tag="social", apply=_r_reconciliation),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(s for s in produced if not s.startswith("__"))
    if narrate:
        for line in out:
            world.say(line)
    return out


PLACES = {
    "moon_pool": SacredPlace(
        id="moon_pool",
        title="the Moon Pool",
        scene="a round pool hidden among reeds where the water held the moon even in daylight",
        guardian_name="Selu-of-the-Still-Water",
        guardian_type="goddess",
        element="water",
        relic_label="moon shell",
        relic_phrase="a silver moon shell resting on a black stone",
        warning="No child was to touch the shell before asking the pool whose face it borrowed.",
        helper_label="a heron",
        helper_hint="The heron knew the old manners of water and watched without splashing.",
        ending_image="the child's face shone in the water again, and even the reeds seemed to bow",
        tags={"moon", "water", "pool"},
    ),
    "sun_tree": SacredPlace(
        id="sun_tree",
        title="the Sun Tree",
        scene="a tall fig tree on a hill, its fruit warm as little lamps",
        guardian_name="Tama-of-the-High-Boughs",
        guardian_type="god",
        element="sun",
        relic_label="sun seed",
        relic_phrase="a golden seed sleeping in a nest of leaves",
        warning="No child was to crack the seed open before greeting the tree that ripened it.",
        helper_label="a swallow",
        helper_hint="The swallow had carried dawn songs from branch to branch for many summers.",
        ending_image="the fruit above glowed softly, and the hill looked friendly instead of stern",
        tags={"sun", "tree", "hill"},
    ),
    "echo_cave": SacredPlace(
        id="echo_cave",
        title="the Echo Cave",
        scene="a stone cave where every whisper came back polished and strange",
        guardian_name="Naro-of-the-Deep-Stone",
        guardian_type="god",
        element="stone",
        relic_label="echo pearl",
        relic_phrase="a pale echo pearl cupped in a ring of rock",
        warning="No child was to pry at the pearl before asking what promise the cave was keeping.",
        helper_label="a cave wren",
        helper_hint="The cave wren lived by careful sounds and knew when to be quiet.",
        ending_image="the cave gave back the child's true name, round and clear as a bell",
        tags={"stone", "cave", "echo"},
    ),
}

FORBIDDEN_ACTS = {
    "ask_too_close": ForbiddenAct(
        id="ask_too_close",
        verb="lean close and ask what secret was hidden inside",
        approach="crept close with bright eyes and a chipper hum",
        question='“What secret are you hiding from me?”',
        trespass="Curiosity carried small fingers past the line where wonder should have paused.",
        lesson="A mystery can be invited to speak, but it should not be snatched open.",
        needs_touch=True,
        tags={"curiosity", "question"},
    ),
    "lift_cover": ForbiddenAct(
        id="lift_cover",
        verb="lift the sacred thing to see beneath it",
        approach="knelt down, chipper and eager, certain that one quick look could do no harm",
        question='“If I look only once, who could it hurt?”',
        trespass="The old boundary broke not with a crash, but with one curious hand.",
        lesson="Sacred things are not rude because they are hidden; they are hidden because they are sacred.",
        needs_touch=True,
        tags={"curiosity", "touch"},
    ),
    "call_name": ForbiddenAct(
        id="call_name",
        verb="call the relic by a nickname and coax it to answer",
        approach="circled it with a chipper little song",
        question='“Come now, small wonder, tell me your true name.”',
        trespass="The child tried to make a holy thing playful before learning how to honor it.",
        lesson="Names that belong to spirits should be received with care, not tugged like ribbons.",
        needs_touch=False,
        tags={"curiosity", "name"},
    ),
}

FORMS = {
    "frog": Form(
        id="frog",
        label="frog",
        body_change="small green feet and a cool bright throat",
        movement="could only spring from stone to stone",
        voice="a thin croak",
        mood="the quick startled heart of a pond creature",
        element="water",
        tags={"frog", "water", "transformation"},
    ),
    "lark": Form(
        id="lark",
        label="lark",
        body_change="light wings and a breast full of trembling song",
        movement="kept hopping and fluttering before it understood the air",
        voice="a spray of notes instead of words",
        mood="the restless brightness of a bird at dawn",
        element="sun",
        tags={"bird", "song", "transformation"},
    ),
    "lizard": Form(
        id="lizard",
        label="lizard",
        body_change="small scales and careful feet that loved warm stone",
        movement="could only skitter along the cave wall",
        voice="a dry clicking hush",
        mood="the still alert patience of rock-creatures",
        element="stone",
        tags={"lizard", "stone", "transformation"},
    ),
}

AMENDS = {
    "dew_bowl": Amends(
        id="dew_bowl",
        label="a bowl of dawn dew",
        action="gathered dawn dew in both hands and tipped it back where the sacred shine had first rested",
        effect="The water settled, listened, and became clear enough to hold a promise again.",
        element="water",
        gentle=True,
        tags={"water", "gift", "apology"},
    ),
    "torch_song": Amends(
        id="torch_song",
        label="a torch song of thanks",
        action="stood facing the east and sang thanks until the first light touched every leaf",
        effect="The warm branches stopped rustling with anger and answered with a softer glow.",
        element="sun",
        gentle=True,
        tags={"sun", "song", "apology"},
    ),
    "pebble_circle": Amends(
        id="pebble_circle",
        label="a circle of polished pebbles",
        action="carried smooth pebbles one by one and laid them in a patient circle before the relic's stone seat",
        effect="The cave quieted, as if each pebble had mended one sharp piece of silence.",
        element="stone",
        gentle=True,
        tags={"stone", "gift", "apology"},
    ),
}

GIRL_NAMES = ["Ila", "Mira", "Neri", "Sora", "Tali", "Ari", "Luma", "Zia"]
BOY_NAMES = ["Tarin", "Kio", "Rami", "Solen", "Aren", "Bero", "Niko", "Eli"]
TRAITS = ["chipper", "kind", "quick", "bright", "patient", "nimble"]


def valid_combo(place_id: str, form_id: str, amends_id: str) -> bool:
    if place_id not in PLACES or form_id not in FORMS or amends_id not in AMENDS:
        return False
    place = PLACES[place_id]
    form = FORMS[form_id]
    amends = AMENDS[amends_id]
    return place.element == form.element == amends.element and amends.gentle


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in sorted(PLACES):
        for form_id in sorted(FORMS):
            for amends_id in sorted(AMENDS):
                if valid_combo(place_id, form_id, amends_id):
                    combos.append((place_id, form_id, amends_id))
    return combos


@dataclass
class StoryParams:
    place: str
    act: str
    form: str
    amends: str
    child_name: str
    child_gender: str
    child_trait: str
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


def explain_rejection(place_id: str, form_id: str, amends_id: str) -> str:
    if place_id not in PLACES or form_id not in FORMS or amends_id not in AMENDS:
        return "(No story: one of the requested ids is unknown to this myth world.)"
    place = PLACES[place_id]
    form = FORMS[form_id]
    amends = AMENDS[amends_id]
    if place.element != form.element:
        return (
            f"(No story: {place.title} belongs to {place.element}, so a {form.label} "
            f"transformation would feel out of place there. Pick a form shaped by the same sacred element.)"
        )
    if place.element != amends.element:
        return (
            f"(No story: {amends.label} reconciles with {amends.element}, but {place.title} "
            f"asks for a {place.element} apology. The amends must fit the offended spirit.)"
        )
    if not amends.gentle:
        return "(No story: reconciliation in this world must be gentle and fitting, not harsh.)"
    return "(No story: this combination does not make a coherent myth.)"


def introduce(world: World, child: Entity, place: SacredPlace) -> None:
    child.memes["curiosity"] += 1
    child.memes["joy"] += 1
    world.say(
        f"In the elder days, when streams remembered songs and caves remembered names, "
        f"there lived a {child.attrs['trait']} child named {child.id}."
    )
    world.say(
        f"{child.id} was so chipper that even chores sounded like tunes when {child.pronoun()} did them."
    )
    world.say(
        f"Beyond the village stood {place.title}, {place.scene}. There, people spoke softly, "
        f"because {place.guardian_name} kept watch."
    )


def warning(world: World, elder: Entity, place: SacredPlace) -> None:
    world.say(
        f"The elders always said, “{place.warning}”"
    )
    world.say(
        f"But warnings are often brightest to the ears that have not yet learned why they matter."
    )
    elder.memes["care"] += 1


def curiosity(world: World, child: Entity, place: SacredPlace, act: ForbiddenAct) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"One morning {child.id} wandered to {place.title}. There {child.pronoun()} found "
        f"{place.relic_phrase}."
    )
    world.say(
        f"{child.id} {act.approach}. {act.question}"
    )
    world.say(act.trespass)


def transgress(world: World, child: Entity, act: ForbiddenAct) -> None:
    child.memes["shame"] += 0.0
    if act.needs_touch:
        world.say(
            f"Then {child.pronoun()} reached out and did what {child.pronoun()} had been told not to do."
        )
    else:
        world.say(
            f"Then the teasing song slipped out once too often, and the sacred place answered."
        )


def transform(world: World, child: Entity, guardian: Entity, form: Form, place: SacredPlace) -> None:
    child.meters["transformed"] += 1
    child.meters["glow"] += 1
    child.attrs["current_form"] = form.label
    propagate(world, narrate=False)
    world.say(
        f"The air at once grew still. {guardian.id} rose from the holy place like a shape made of "
        f"{place.element} and memory."
    )
    world.say(
        f'“Little one,” said {guardian.id}, “curiosity is not a sin, but greed inside curiosity is.”'
    )
    world.say(
        f"At that word, {child.id}'s hands and feet changed into {form.body_change}. "
        f"In a blink, the child was a {form.label} and felt {form.mood}."
    )
    world.say(
        f"{child.pronoun().capitalize()} tried to speak, but only {form.voice} came out, and {child.pronoun()} {form.movement}."
    )


def helper_guidance(world: World, child: Entity, place: SacredPlace, helper: Entity, form: Form) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"By the edge of the sacred place waited {helper.label}. {place.helper_hint}"
    )
    world.say(
        f"The small helper did not laugh at the transformed child. Instead it seemed to say, "
        f"with eyes older than feathers, “A broken boundary is mended by honor, not by hiding.”"
    )
    world.say(
        f"{child.id} understood at last that being sorry was not enough unless sorrow learned a shape."
    )


def make_amends(world: World, child: Entity, guardian: Entity, amends: Amends) -> None:
    child.memes["apology"] += 1
    child.meters["amends_done"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So the little {world.facts['form'].label} worked patiently. {child.id} {amends.action}"
    )
    world.say(amends.effect)
    world.say(
        f'At last {child.pronoun()} bowed low and said the truest words {child.pronoun()} had ever learned: '
        f'“I was curious, but I forgot to be reverent. I ask forgiveness.”'
    )
    if guardian.memes["forgiveness"] >= THRESHOLD:
        world.say(
            f"{guardian.id} looked upon the child, and the sternness in the holy place loosened."
        )


def restore(world: World, child: Entity, guardian: Entity, place: SacredPlace, act: ForbiddenAct) -> None:
    if child.meters["restored"] < THRESHOLD:
        raise StoryError("(Story logic error: reconciliation did not restore the child.)")
    world.say(
        f'“Now you know the difference,” said {guardian.id}. “Wonder may ask, but first it must bow.”'
    )
    world.say(
        f"Then the sacred light flowed over {child.id}, and the strange shape melted away. "
        f"The child stood once more in human form, trembling but whole."
    )
    world.say(
        f"From that day on, {child.id} still asked many questions, yet never with grabbing hands or teasing boldness."
    )
    world.say(
        f"When younger children ran to {place.title}, {child.pronoun()} became the first to teach them gently: "
        f"{act.lesson}"
    )
    world.say(
        f"In this way curiosity and reverence were reconciled, and {place.ending_image}."
    )


def tell(
    place: SacredPlace,
    act: ForbiddenAct,
    form: Form,
    amends: Amends,
    child_name: str,
    child_gender: str,
    child_trait: str,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        attrs={"trait": child_trait, "current_form": "child"},
        tags={"child"},
    ))
    guardian = world.add(Entity(
        id=place.guardian_name,
        kind="character",
        type=place.guardian_type,
        role="guardian",
        label=place.guardian_name,
        tags={place.element, "guardian"},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="bird" if place.id != "echo_cave" else "wren",
        role="helper",
        label=place.helper_label,
        tags={"helper"},
    ))
    elder = world.add(Entity(
        id="elders",
        kind="character",
        type="people",
        role="elder",
        label="the elders",
        tags={"elders"},
    ))
    relic = world.add(Entity(
        id="relic",
        kind="thing",
        type="relic",
        label=place.relic_label,
        owner=place.guardian_name,
        tags={place.element, "relic"},
    ))
    world.facts.update(
        place=place,
        act=act,
        form=form,
        amends=amends,
        child=child,
        guardian=guardian,
        helper=helper,
        relic=relic,
    )

    introduce(world, child, place)
    warning(world, elder, place)
    world.para()
    curiosity(world, child, place, act)
    transgress(world, child, act)
    world.para()
    transform(world, child, guardian, form, place)
    helper_guidance(world, child, place, helper, form)
    world.para()
    make_amends(world, child, guardian, amends)
    restore(world, child, guardian, place, act)
    return world


KNOWLEDGE = {
    "myth": [
        (
            "What is a myth?",
            "A myth is an old kind of story that explains a lesson, a custom, or a wonder of the world. It often includes spirits, sacred places, or transformations."
        )
    ],
    "reverence": [
        (
            "What does reverence mean?",
            "Reverence means showing deep respect for something important or sacred. It is the feeling that makes you slow down, listen, and treat a thing carefully."
        )
    ],
    "apology": [
        (
            "What makes an apology feel true?",
            "A true apology says what was wrong and tries to mend the hurt. The words matter, but the caring action matters too."
        )
    ],
    "curiosity": [
        (
            "Is curiosity bad?",
            "No. Curiosity helps people learn. It becomes a problem only when wanting to know something makes a person ignore care, safety, or respect."
        )
    ],
    "transformation": [
        (
            "Why do myths use transformation?",
            "Transformation lets a story show a big inner lesson in an outer way. When a character changes shape, we can see that something inside them must change too."
        )
    ],
    "water": [
        (
            "Why do stories connect water with reflection?",
            "Water can hold a picture of the sky or a face, so it often stands for seeing clearly. In stories, clear water can mean clear understanding."
        )
    ],
    "sun": [
        (
            "Why is the sun often a symbol in stories?",
            "The sun gives light and warmth, so it often stands for truth, life, or understanding. A story may use sunlight to show that confusion is ending."
        )
    ],
    "stone": [
        (
            "Why is stone often linked with patience?",
            "Stone changes slowly and lasts a long time, so it can symbolize steadiness and patience. In a myth, stone can remind people to move carefully and keep promises."
        )
    ],
}
KNOWLEDGE_ORDER = ["myth", "curiosity", "transformation", "reverence", "apology", "water", "sun", "stone"]


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"]
    act = world.facts["act"]
    form = world.facts["form"]
    return [
        f'Write a short myth for young children about curiosity, transformation, and reconciliation. Include the word "chipper".',
        f"Tell a mythic story where a chipper child at {place.title} grows too curious, is turned into a {form.label}, and earns forgiveness through a fitting apology.",
        f"Write a gentle sacred tale in which the forbidden act is to {act.verb}, and the ending teaches that wonder should be respectful as well as brave.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    place = world.facts["place"]
    form = world.facts["form"]
    amends = world.facts["amends"]
    guardian = world.facts["guardian"]
    act = world.facts["act"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a chipper child named {child.id} who went to {place.title}. The story also follows {guardian.id}, the spirit who guarded that sacred place."
        ),
        (
            f"Why did {child.id} get into trouble?",
            f"{child.id} became too curious about {place.relic_phrase}. The trouble began when that curiosity crossed the holy boundary instead of pausing to ask with respect."
        ),
        (
            f"What happened after {child.id} broke the rule?",
            f"{guardian.id} transformed {child.id} into a {form.label}. The change made the lesson physical, because the child could no longer act or speak in the easy human way."
        ),
        (
            f"How did {child.id} make peace with {guardian.id}?",
            f"{child.id} worked patiently and offered {amends.label}. Then {child.pronoun().capitalize()} spoke a careful apology and admitted that curiosity had become disrespectful."
        ),
        (
            "How did the story end?",
            f"The guardian forgave the child and restored {child.id} to human form. After that, {child.pronoun()} still loved questions, but used them gently and taught younger children the same lesson."
        ),
        (
            f"What lesson did {child.id} learn about curiosity?",
            f"{child.id} learned that curiosity itself was not the wrong part. The wrong part was pushing past reverence, so the new wisdom was to ask first and handle sacred things with care."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"myth", "curiosity", "transformation", "reverence", "apology", world.facts["place"].element}
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
        lines.append(f"  {ent.id:14} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,F,A) :- place(P), form(F), amends(A), place_element(P,E), form_element(F,E), amends_element(A,E), gentle(A).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("place_element", place_id, place.element))
    for form_id, form in FORMS.items():
        lines.append(asp.fact("form", form_id))
        lines.append(asp.fact("form_element", form_id, form.element))
    for amends_id, amends in AMENDS.items():
        lines.append(asp.fact("amends", amends_id))
        lines.append(asp.fact("amends_element", amends_id, amends.element))
        if amends.gentle:
            lines.append(asp.fact("gentle", amends_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    base = ASP_RULES.replace("#show valid/3.", "")
    return f"{asp_facts()}\n{base}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic storyworld: a chipper child grows too curious, is transformed, and reconciles with a sacred guardian."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--act", choices=sorted(FORBIDDEN_ACTS))
    ap.add_argument("--form", choices=sorted(FORMS))
    ap.add_argument("--amends", choices=sorted(AMENDS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.form and args.amends and not valid_combo(args.place, args.form, args.amends):
        raise StoryError(explain_rejection(args.place, args.form, args.amends))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.form is None or combo[1] == args.form)
        and (args.amends is None or combo[2] == args.amends)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, form_id, amends_id = rng.choice(combos)
    act_id = args.act or rng.choice(sorted(FORBIDDEN_ACTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        child_name = args.name
    else:
        child_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        act=act_id,
        form=form_id,
        amends=amends_id,
        child_name=child_name,
        child_gender=gender,
        child_trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.act not in FORBIDDEN_ACTS:
        raise StoryError(f"(No story: unknown act '{params.act}'.)")
    if params.form not in FORMS:
        raise StoryError(f"(No story: unknown form '{params.form}'.)")
    if params.amends not in AMENDS:
        raise StoryError(f"(No story: unknown amends '{params.amends}'.)")
    if not valid_combo(params.place, params.form, params.amends):
        raise StoryError(explain_rejection(params.place, params.form, params.amends))

    world = tell(
        place=PLACES[params.place],
        act=FORBIDDEN_ACTS[params.act],
        form=FORMS[params.form],
        amends=AMENDS[params.amends],
        child_name=params.child_name,
        child_gender=params.child_gender,
        child_trait=params.child_trait,
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
        place="moon_pool",
        act="ask_too_close",
        form="frog",
        amends="dew_bowl",
        child_name="Mira",
        child_gender="girl",
        child_trait="chipper",
    ),
    StoryParams(
        place="sun_tree",
        act="call_name",
        form="lark",
        amends="torch_song",
        child_name="Solen",
        child_gender="boy",
        child_trait="bright",
    ),
    StoryParams(
        place="echo_cave",
        act="lift_cover",
        form="lizard",
        amends="pebble_circle",
        child_name="Neri",
        child_gender="girl",
        child_trait="nimble",
    ),
]


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid combo gate matches ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(5):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("(Smoke test failed: empty seeded story.)")
        except Exception as err:
            rc = 1
            print(f"SEEDED GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: seeded generation smoke tests passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, form, amends) combos:\n")
        for place_id, form_id, amends_id in combos:
            print(f"  {place_id:10} {form_id:8} {amends_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.place}, {p.form}, {p.amends}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
