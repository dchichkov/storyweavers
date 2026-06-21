#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sweater_utmost_sound_effects_twist_pirate_tale.py
============================================================================

A standalone story world about two children playing pirates, a hideout that
starts making spooky sounds, and a twist: the "sea monster" is really a scared
pet tangled in a sweater. The world model prefers careful, sensible help over
rough poking or yanking, and the ending proves what changed when the children
choose utmost care.

Run it
------
    python storyworlds/worlds/gpt-5.4/sweater_utmost_sound_effects_twist_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/sweater_utmost_sound_effects_twist_pirate_tale.py --theme pirates --hideout basket --pet kitten
    python storyworlds/worlds/gpt-5.4/sweater_utmost_sound_effects_twist_pirate_tale.py --hideout crate --pet puppy
    python storyworlds/worlds/gpt-5.4/sweater_utmost_sound_effects_twist_pirate_tale.py --response yank
    python storyworlds/worlds/gpt-5.4/sweater_utmost_sound_effects_twist_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/sweater_utmost_sound_effects_twist_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/sweater_utmost_sound_effects_twist_pirate_tale.py --verify
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
SENSE_MIN = 2


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
    size: int = 0
    # physical + emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Theme:
    id: str
    scene: str
    rig: str
    titles: tuple[str, str]
    mission: str
    ending: str
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


@dataclass
class Hideout:
    id: str
    label: str
    phrase: str
    place_text: str
    capacity: int
    snug: int
    dark_word: str
    open_text: str
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
class Pet:
    id: str
    label: str
    phrase: str
    sound: str
    noise: str
    size: int
    skittish: int
    cuddle_text: str
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
class Sweater:
    id: str
    label: str
    phrase: str
    color: str
    snag: int
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
class Response:
    id: str
    sense: int
    power: int
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
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_hidden_pet_rattles(world: World) -> list[str]:
    pet = world.get("pet")
    hideout = world.get("hideout")
    if pet.meters["hidden"] < THRESHOLD or pet.meters["tangled"] < THRESHOLD:
        return []
    sig = ("rattle", hideout.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hideout.meters["rattling"] += 1
    pet.memes["fear"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__rattle__"]


def _r_spooky_guess(world: World) -> list[str]:
    hideout = world.get("hideout")
    if hideout.meters["rattling"] < THRESHOLD:
        return []
    sig = ("imagine", hideout.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["monster_guess"] += 1
    return ["__monster__"]


def _r_relief_after_free(world: World) -> list[str]:
    pet = world.get("pet")
    if pet.meters["tangled"] >= THRESHOLD:
        return []
    sig = ("relief", pet.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pet.memes["fear"] = 0.0
    pet.memes["comfort"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["care"] += 1
        kid.memes["fear"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="hidden_pet_rattles", tag="physical", apply=_r_hidden_pet_rattles),
    Rule(name="spooky_guess", tag="emotional", apply=_r_spooky_guess),
    Rule(name="relief_after_free", tag="emotional", apply=_r_relief_after_free),
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
        for line in produced:
            world.say(line)
    return produced


def pet_fits(hideout: Hideout, pet: Pet) -> bool:
    return pet.size <= hideout.capacity


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def entanglement_severity(hideout: Hideout, pet: Pet, sweater: Sweater, delay: int) -> int:
    return hideout.snug + pet.skittish + sweater.snag + delay - 1


def is_gentle_success(response: Response, hideout: Hideout, pet: Pet, sweater: Sweater,
                      delay: int) -> bool:
    return response.power >= entanglement_severity(hideout, pet, sweater, delay)


def explain_rejection(hideout: Hideout, pet: Pet) -> str:
    return (
        f"(No story: {pet.phrase.capitalize()} would not plausibly fit inside "
        f"{hideout.phrase}. Pick a roomier hideout or a smaller pet.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). A careful pirate story should choose "
        f"a calmer rescue. Try: {better}.)"
    )


def predict_scramble(world: World, response: Response) -> dict:
    sim = world.copy()
    hideout_cfg = sim.facts["hideout_cfg"]
    pet_cfg = sim.facts["pet_cfg"]
    sweater_cfg = sim.facts["sweater_cfg"]
    delay = sim.facts["delay"]
    if is_gentle_success(response, hideout_cfg, pet_cfg, sweater_cfg, delay):
        return {"scramble": False, "fear": sim.get("pet").memes["fear"]}
    sim.get("pet").memes["fear"] += 2
    sim.get("pet").meters["darting"] += 1
    return {"scramble": True, "fear": sim.get("pet").memes["fear"]}


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    cap_a, cap_b = theme.titles
    world.say(
        f"On a breezy afternoon, {a.id} and {b.id} turned the living room into "
        f"{theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{cap_a} {a.id} and {cap_b} {b.id}!" {a.id} cried. '
        f'"Today we find {theme.mission}!"'
    )


def set_dark_target(world: World, b: Entity, hideout: Hideout) -> None:
    world.say(
        f"At the far side of the room sat {hideout.phrase} {hideout.place_text}. "
        f"It looked dark enough to hide a whole pirate secret."
    )
    world.say(f'{b.id} pointed at it. "That must be the {hideout.dark_word}," {b.pronoun()} whispered.')


def start_trouble(world: World) -> None:
    propagate(world, narrate=False)


def spooky_sounds(world: World, hideout: Hideout, pet: Pet) -> None:
    world.say(
        f"Then came the sounds. {pet.noise}! {pet.sound.capitalize()}! "
        f"The {hideout.label} gave a shaky bump all by itself."
    )


def guess_monster(world: World, a: Entity, theme: Theme) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} jumped back, then tried to puff up like the bravest {theme.id[:-1] if theme.id.endswith("s") else "pirate"} on the sea. '
        f'"A cave beast!" {a.pronoun().capitalize()} gasped. "Or maybe a treasure-guarding sea monster!"'
    )


def warn_utmost(world: World, b: Entity, a: Entity, response: Response, parent: Entity) -> None:
    pred = predict_scramble(world, response)
    world.facts["predicted_scramble"] = pred["scramble"]
    b.memes["care"] += 1
    line = (
        f'{b.id} grabbed {a.id}\'s sleeve. "No poking," {b.pronoun()} said. '
        f'"We need utmost care. Whatever is inside sounds scared, not mean."'
    )
    if pred["scramble"]:
        line += (
            f" {b.pronoun().capitalize()} knew that if someone yanked too fast, "
            f"the hidden creature would only panic and dash harder."
        )
    else:
        line += (
            f" {b.pronoun().capitalize()} thought a calm grown-up could help without making things worse."
        )
    world.say(line)
    world.say(f'"Let\'s call {parent.label_word}," {b.id} said.')


def call_parent(world: World, parent: Entity) -> None:
    world.say(f'"{parent.label_word.upper()}!" both children called.')


def rescue_gently(world: World, parent: Entity, response: Response,
                  hideout: Hideout, pet: Pet, sweater: Sweater) -> None:
    pet_ent = world.get("pet")
    pet_ent.meters["tangled"] = 0.0
    pet_ent.meters["hidden"] = 0.0
    world.get("hideout").meters["rattling"] = 0.0
    body = response.text.format(
        hideout=hideout.label,
        pet=pet.label,
        sweater=sweater.label,
    )
    world.say(
        f"{parent.label_word.capitalize()} came quickly and {body}."
    )
    propagate(world, narrate=False)
    world.say(
        f'Out peeped {pet.phrase}, blinking hard with {sweater.phrase} looped around {pet.pronoun("possessive")} middle.'
    )
    world.say(
        f'"It was not a monster at all," {a_or_an(parent.label_word)} {parent.label_word} said with a soft smile. '
        f'"It was {pet.phrase} stuck in a sweater."'
    )


def rescue_scramble(world: World, parent: Entity, response: Response,
                    hideout: Hideout, pet: Pet, sweater: Sweater) -> None:
    pet_ent = world.get("pet")
    pet_ent.meters["hidden"] = 0.0
    pet_ent.meters["darting"] += 1
    pet_ent.memes["fear"] += 2
    body = response.fail.format(
        hideout=hideout.label,
        pet=pet.label,
        sweater=sweater.label,
    )
    world.say(
        f"{parent.label_word.capitalize()} hurried over and {body}."
    )
    world.say(
        f"Whoosh! Out burst {pet.phrase} with the {sweater.label} still bunched around {pet.pronoun('possessive')} back like a crooked pirate cape."
    )
    world.say(
        f"The room was so surprising that {a_or_an(pet.label)} {pet.label} skittered behind the sofa before anyone could laugh."
    )


def chase_with_care(world: World, parent: Entity, a: Entity, b: Entity, pet: Pet, sweater: Sweater) -> None:
    pet_ent = world.get("pet")
    pet_ent.meters["tangled"] = 0.0
    pet_ent.meters["darting"] = 0.0
    pet_ent.memes["fear"] = 0.0
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["care"] += 1
    world.say(
        f"{a.id} and {b.id} did not chase wildly. They crouched low, spoke softly, and let {parent.label_word} ease the {sweater.label} free at last."
    )
    world.say(
        f"Soon {pet.phrase} was safe, if a little ruffled, and the crooked cape slipped down to the rug."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, pet: Pet) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f"Then {parent.label_word.capitalize()} hugged them close. "
        f'"You were right to stop and call me," {parent.pronoun()} said. '
        f'"When something is frightened, brave helpers use utmost gentleness."'
    )
    world.say(
        f"{b.id} nodded first. {a.id} nodded too, much smaller now that the mystery had a whiskered face."
    )
    world.say(
        f"{pet.phrase.capitalize()} leaned into the cuddle, proving that quiet hands worked better than pirate bluster."
    )


def bright_ending(world: World, a: Entity, b: Entity, theme: Theme, pet: Pet, sweater: Sweater) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"After that, the children folded the {sweater.label} and tied it to a chair with clothespins, making a fine pirate sail instead of a snare."
    )
    world.say(
        f'{pet.phrase.capitalize()} curled beneath it, purring like a tiny ship engine: "{pet.sound}... {pet.sound}..."'
    )
    world.say(
        f"And the {theme.id} sailed on again, wiser than before, with their treasure guarded by kindness."
    )


def cautious_ending(world: World, a: Entity, b: Entity, theme: Theme, pet: Pet, sweater: Sweater) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"Later, when everyone had calmed down, {a.id} spread the {sweater.label} flat on the rug and said it would make a better map than a cape."
    )
    world.say(
        f"{b.id} smoothed one corner while {pet.phrase} sat on the middle of it as if guarding buried gold."
    )
    world.say(
        f"From then on, whenever a mystery thumped in their pirate ship, the crew remembered to begin with quiet voices and utmost care."
    )


def a_or_an(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def tell(theme: Theme, hideout: Hideout, pet: Pet, sweater: Sweater, response: Response,
         instigator: str = "Tom", instigator_gender: str = "boy",
         cautioner: str = "Lily", cautioner_gender: str = "girl",
         parent_type: str = "mother", trait: str = "careful", delay: int = 0) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        traits=["bold"],
        attrs={"trait": "bold"},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        traits=[trait],
        attrs={"trait": trait},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    hideout_ent = world.add(Entity(
        id="hideout",
        type="hideout",
        label=hideout.label,
        size=hideout.capacity,
    ))
    pet_ent = world.add(Entity(
        id="pet",
        type="pet",
        label=pet.label,
        size=pet.size,
    ))
    sweater_ent = world.add(Entity(
        id="sweater",
        type="sweater",
        label=sweater.label,
    ))

    a.memes["bravery"] = 1.0
    b.memes["care"] = 1.0
    pet_ent.meters["hidden"] = 1.0
    pet_ent.meters["tangled"] = 1.0
    pet_ent.memes["fear"] = float(pet.skittish)
    hideout_ent.meters["rattling"] = 0.0
    sweater_ent.meters["snag"] = float(sweater.snag)
    world.facts.update(
        theme=theme,
        hideout_cfg=hideout,
        pet_cfg=pet,
        sweater_cfg=sweater,
        response=response,
        delay=delay,
        instigator=a,
        cautioner=b,
        parent=parent,
        pet=pet_ent,
        hideout=hideout_ent,
        sweater=sweater_ent,
    )

    play_setup(world, a, b, theme)
    set_dark_target(world, b, hideout)

    world.para()
    start_trouble(world)
    spooky_sounds(world, hideout, pet)
    guess_monster(world, a, theme)
    warn_utmost(world, b, a, response, parent)
    call_parent(world, parent)

    world.para()
    success = is_gentle_success(response, hideout, pet, sweater, delay)
    severity = entanglement_severity(hideout, pet, sweater, delay)
    world.facts["severity"] = severity
    world.facts["success"] = success

    if success:
        rescue_gently(world, parent, response, hideout, pet, sweater)
        world.para()
        lesson(world, parent, a, b, pet)
        bright_ending(world, a, b, theme, pet, sweater)
        outcome = "gentle"
    else:
        rescue_scramble(world, parent, response, hideout, pet, sweater)
        world.para()
        chase_with_care(world, parent, a, b, pet, sweater)
        lesson(world, parent, a, b, pet)
        cautious_ending(world, a, b, theme, pet, sweater)
        outcome = "scramble"

    world.facts["outcome"] = outcome
    world.facts["revealed_pet"] = True
    world.facts["monster_wrong"] = True
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a storm-tossed pirate ship",
        rig="The sofa was the deck, two cushions were lifeboats, and a broom stood up as the tallest mast in the room.",
        titles=("Captain", "Lookout"),
        mission="the last hidden treasure map",
        ending="sailed on again",
    ),
    "raiders": Theme(
        id="raiders",
        scene="a raid on a moonlit harbor",
        rig="The coffee table was the dock, a blanket became the sea, and a cardboard box was stacked high as a cargo pier.",
        titles=("Captain", "Matey"),
        mission="the lantern chest from the harbor wall",
        ending="set sail once more",
    ),
    "corsairs": Theme(
        id="corsairs",
        scene="a corsair deck under a windy sky",
        rig="The rug was the sea, the armchair was the captain's rail, and a long spoon served as a silver spyglass.",
        titles=("Captain", "Scout"),
        mission="the secret chart of the northern cove",
        ending="crept onward together",
    ),
}

HIDEOUTS = {
    "basket": Hideout(
        id="basket",
        label="laundry basket",
        phrase="a tall laundry basket",
        place_text="beside the hallway door",
        capacity=1,
        snug=1,
        dark_word="shadow basket",
        open_text="lifted the lid a crack",
        tags={"basket", "laundry"},
    ),
    "hamper": Hideout(
        id="hamper",
        label="linen hamper",
        phrase="the round linen hamper",
        place_text="under the coat hooks",
        capacity=2,
        snug=2,
        dark_word="secret hold",
        open_text="opened the hamper slowly",
        tags={"hamper", "laundry"},
    ),
    "crate": Hideout(
        id="crate",
        label="blanket crate",
        phrase="a wooden blanket crate",
        place_text="under the window seat",
        capacity=2,
        snug=2,
        dark_word="captain's chest",
        open_text="raised the crate lid inch by inch",
        tags={"crate", "blanket"},
    ),
}

PETS = {
    "kitten": Pet(
        id="kitten",
        label="kitten",
        phrase="a little kitten",
        sound="mew",
        noise="Thump",
        size=1,
        skittish=1,
        cuddle_text="purred into the nearest arm",
        tags={"kitten", "pet"},
    ),
    "puppy": Pet(
        id="puppy",
        label="puppy",
        phrase="a floppy-eared puppy",
        sound="arf",
        noise="Bump",
        size=2,
        skittish=2,
        cuddle_text="licked a hand and trembled less",
        tags={"puppy", "pet"},
    ),
    "guinea_pig": Pet(
        id="guinea_pig",
        label="guinea pig",
        phrase="a round little guinea pig",
        sound="squeak",
        noise="Scritch",
        size=1,
        skittish=2,
        cuddle_text="made tiny happy cheeps in the towel",
        tags={"guinea_pig", "pet"},
    ),
}

SWEATERS = {
    "striped": Sweater(
        id="striped",
        label="striped sweater",
        phrase="a blue striped sweater",
        color="blue",
        snag=1,
        tags={"sweater", "clothes"},
    ),
    "cable": Sweater(
        id="cable",
        label="cable-knit sweater",
        phrase="a thick cable-knit sweater",
        color="cream",
        snag=2,
        tags={"sweater", "clothes"},
    ),
    "red": Sweater(
        id="red",
        label="red sweater",
        phrase="a bright red sweater",
        color="red",
        snag=1,
        tags={"sweater", "clothes"},
    ),
}

RESPONSES = {
    "flashlight_hands": Response(
        id="flashlight_hands",
        sense=4,
        power=4,
        text="knelt down, shone a flashlight into the {hideout}, and eased the {sweater} loose with slow, careful fingers",
        fail="knelt down and tried to work the {sweater} free, but the frightened {pet} twisted away before the knot could loosen",
        qa_text="used a flashlight and gentle hands to loosen the sweater",
        tags={"flashlight", "gentle_help"},
    ),
    "towel_lift": Response(
        id="towel_lift",
        sense=3,
        power=3,
        text="spread out a soft towel, opened the {hideout}, and wrapped the scared {pet} before slipping the {sweater} free",
        fail="opened the {hideout} with a towel ready, but the scared {pet} wriggled out before the sweater could be untangled",
        qa_text="used a towel to hold the pet calmly while removing the sweater",
        tags={"towel", "gentle_help"},
    ),
    "treat_trail": Response(
        id="treat_trail",
        sense=2,
        power=2,
        text="coaxed the hidden {pet} out with a treat and then worked the {sweater} loose bit by bit",
        fail="tried to lure the hidden {pet} with a treat, but the sweater stayed caught and the poor thing bolted",
        qa_text="coaxed the pet out first and loosened the sweater bit by bit",
        tags={"treat", "gentle_help"},
    ),
    "yank": Response(
        id="yank",
        sense=1,
        power=1,
        text="grabbed the sweater and yanked it at once",
        fail="grabbed for the sweater too fast and only made the hidden pet panic",
        qa_text="yanked the sweater",
        tags={"rough", "unsafe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "gentle", "thoughtful", "steady", "kind"]


@dataclass
class StoryParams:
    theme: str
    hideout: str
    pet: str
    sweater: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    if not sensible_responses():
        return combos
    for theme_id in THEMES:
        for hideout_id, hideout in HIDEOUTS.items():
            for pet_id, pet in PETS.items():
                if not pet_fits(hideout, pet):
                    continue
                for sweater_id in SWEATERS:
                    combos.append((theme_id, hideout_id, pet_id, sweater_id))
    return combos


KNOWLEDGE = {
    "kitten": [(
        "Why do kittens make little mew sounds?",
        "Kittens mew to call for help or attention. If a kitten is scared or stuck, the sound can become faster and sharper."
    )],
    "puppy": [(
        "Why might a puppy bark or arf indoors?",
        "A puppy may bark because it is excited, confused, or frightened. A scared puppy needs calm voices and gentle help."
    )],
    "guinea_pig": [(
        "Why do guinea pigs squeak?",
        "Guinea pigs squeak to communicate. They can squeak when they want attention or when something startles them."
    )],
    "sweater": [(
        "What is a sweater for?",
        "A sweater is soft clothing that helps keep a body warm. If it gets twisted around a small pet, though, it can be hard for the pet to move."
    )],
    "flashlight": [(
        "Why is a flashlight useful when something is hidden in the dark?",
        "A flashlight helps you see clearly without poking around. Good light makes careful helping easier and safer."
    )],
    "towel": [(
        "Why can a towel help with a scared pet?",
        "A soft towel can help a grown-up hold a wriggly pet gently. That keeps the pet from slipping or scratching while it is being helped."
    )],
    "treat": [(
        "Why might a treat help a nervous pet come closer?",
        "A treat can make a pet feel curious and a little braver. It works best when the pet is not too frightened."
    )],
    "pet": [(
        "What should you do if a pet is stuck?",
        "Tell a grown-up right away and stay calm. Quiet hands and gentle help are better than grabbing or yanking."
    )],
    "laundry": [(
        "Why do pets sometimes hide in baskets or hampers?",
        "Soft clothes can smell warm and safe, so a pet may crawl in to nap or hide. But tight spaces can make it easy to get tangled."
    )],
}
KNOWLEDGE_ORDER = ["pet", "sweater", "kitten", "puppy", "guinea_pig", "flashlight", "towel", "treat", "laundry"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    pet = f["pet_cfg"]
    hideout = f["hideout_cfg"]
    sweater = f["sweater_cfg"]
    theme = f["theme"]
    outcome = f["outcome"]
    base = (
        f'Write a pirate-style story for a 3-to-5-year-old where two children hear spooky sounds from {hideout.phrase} and discover a pet tangled in a {sweater.label}. '
        f'Include the words "sweater" and "utmost".'
    )
    if outcome == "gentle":
        return [
            base,
            f"Tell a twist story where {a.id} thinks a sea monster is hiding, but {b.id} insists on utmost care, and the scary noises turn out to be {pet.phrase}.",
            f"Write a child-facing pirate tale with sound effects, a false monster scare, and a calm grown-up rescue that ends with the children playing again more gently.",
        ]
    return [
        base,
        f"Tell a pirate tale where the first rescue is not enough and the hidden {pet.label} scrambles away, but everyone slows down, uses utmost care, and helps in the end.",
        f"Write a sound-effects story with a twist: the 'monster' is a scared pet in a sweater, and the children learn that quiet help works better than rushing.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    return "a brother and a sister"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    theme = f["theme"]
    hideout = f["hideout_cfg"]
    pet = f["pet_cfg"]
    sweater = f["sweater_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}, playing {theme.id}. It also includes their {parent.label_word}, who helps with the mystery."
        ),
        (
            "What did the children think was in the hideout at first?",
            f"They thought something like a sea monster or cave beast might be inside {hideout.phrase}. They guessed that because the hideout bumped and made spooky sounds."
        ),
        (
            "What was really making the sounds?",
            f"The sounds came from {pet.phrase} tangled in {sweater.phrase}. The twist is that the scary pirate mystery was really a frightened pet that needed help."
        ),
        (
            f"Why did {b.id} say they needed utmost care?",
            f"{b.id} could tell the sounds were scared sounds, not angry ones. {b.pronoun().capitalize()} wanted a calm grown-up to help so the hidden pet would not panic more."
        ),
    ]
    if outcome == "gentle":
        qa.append((
            f"How did {parent.label_word} help?",
            f"{parent.label_word.capitalize()} {response.qa_text}. That careful method let the pet come out safely instead of feeling more trapped."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the children turning the {sweater.label} into part of their pirate game instead of letting it trap anyone. The ending proves they changed because their play became gentler and kinder."
        ))
    else:
        qa.append((
            f"Did the first try work right away?",
            f"No. The first try made the scared {pet.label} bolt out still wearing part of the sweater, so everyone had to slow down even more. That second, calmer effort is what finally helped."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely after the children stopped rushing and helped with quiet voices. After that, they remembered to begin every mystery with utmost care."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    pet = f["pet_cfg"]
    hideout = f["hideout_cfg"]
    response = f["response"]
    tags: set[str] = {"sweater", "pet"}
    tags |= set(pet.tags)
    tags |= set(response.tags)
    if "laundry" in hideout.tags:
        tags.add("laundry")
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
        if e.size:
            bits.append(f"size={e.size}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        hideout="basket",
        pet="kitten",
        sweater="red",
        response="flashlight_hands",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
    ),
    StoryParams(
        theme="raiders",
        hideout="crate",
        pet="puppy",
        sweater="cable",
        response="towel_lift",
        instigator="Ben",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="father",
        trait="gentle",
        delay=0,
    ),
    StoryParams(
        theme="corsairs",
        hideout="hamper",
        pet="guinea_pig",
        sweater="striped",
        response="treat_trail",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        parent="mother",
        trait="thoughtful",
        delay=1,
    ),
    StoryParams(
        theme="pirates",
        hideout="crate",
        pet="puppy",
        sweater="cable",
        response="treat_trail",
        instigator="Eli",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="father",
        trait="steady",
        delay=2,
    ),
]


ASP_RULES = r"""
fits(H, P) :- capacity(H, C), pet_size(P, S), S <= C.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(T, H, P, Sw) :- theme(T), hideout(H), pet(P), sweater(Sw), fits(H, P).

severity(V) :- chosen_hideout(H), hideout_snug(H, HS),
               chosen_pet(P), pet_skittish(P, PS),
               chosen_sweater(Sw), sweater_snag(Sw, SS),
               delay(D), V = HS + PS + SS + D - 1.

success :- chosen_response(R), response_power(R, P), severity(V), P >= V.
outcome(gentle) :- success.
outcome(scramble) :- not success.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for hid, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        lines.append(asp.fact("capacity", hid, hideout.capacity))
        lines.append(asp.fact("hideout_snug", hid, hideout.snug))
    for pid, pet in PETS.items():
        lines.append(asp.fact("pet", pid))
        lines.append(asp.fact("pet_size", pid, pet.size))
        lines.append(asp.fact("pet_skittish", pid, pet.skittish))
    for sid, sweater in SWEATERS.items():
        lines.append(asp.fact("sweater", sid))
        lines.append(asp.fact("sweater_snag", sid, sweater.snag))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("response_power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_hideout", params.hideout),
        asp.fact("chosen_pet", params.pet),
        asp.fact("chosen_sweater", params.sweater),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    hideout = HIDEOUTS[params.hideout]
    pet = PETS[params.pet]
    sweater = SWEATERS[params.sweater]
    response = RESPONSES[params.response]
    return "gentle" if is_gentle_success(response, hideout, pet, sweater, params.delay) else "scramble"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: pirate play, spooky sounds, a sweater tangle, and a twist. Unspecified choices are randomized (seeded)."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--pet", choices=PETS)
    ap.add_argument("--sweater", choices=SWEATERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the pet stays tangled before help begins")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hideout and args.pet:
        if not pet_fits(HIDEOUTS[args.hideout], PETS[args.pet]):
            raise StoryError(explain_rejection(HIDEOUTS[args.hideout], PETS[args.pet]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.hideout is None or c[1] == args.hideout)
        and (args.pet is None or c[2] == args.pet)
        and (args.sweater is None or c[3] == args.sweater)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, hideout, pet, sweater = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        theme=theme,
        hideout=hideout,
        pet=pet,
        sweater=sweater,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.pet not in PETS:
        raise StoryError(f"(Unknown pet: {params.pet})")
    if params.sweater not in SWEATERS:
        raise StoryError(f"(Unknown sweater: {params.sweater})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if not pet_fits(HIDEOUTS[params.hideout], PETS[params.pet]):
        raise StoryError(explain_rejection(HIDEOUTS[params.hideout], PETS[params.pet]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        theme=THEMES[params.theme],
        hideout=HIDEOUTS[params.hideout],
        pet=PETS[params.pet],
        sweater=SWEATERS[params.sweater],
        response=RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(200):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(s)))
        except StoryError:
            continue
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
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, hideout, pet, sweater) combos:\n")
        for theme, hideout, pet, sweater in combos:
            print(f"  {theme:8} {hideout:8} {pet:11} {sweater}")
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
                f"### {p.instigator} & {p.cautioner}: {p.pet} in {p.hideout} "
                f"({p.theme}, {p.sweater}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
