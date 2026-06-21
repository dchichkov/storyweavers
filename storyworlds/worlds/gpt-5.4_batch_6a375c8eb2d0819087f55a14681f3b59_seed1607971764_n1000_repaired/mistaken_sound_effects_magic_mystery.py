#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mistaken_sound_effects_magic_mystery.py
==================================================================

A standalone storyworld for a tiny "mistaken magical mystery" domain.

A child and a helper are in a magical place when an important little object goes
missing. Strange sound effects begin in the shadows. The child makes a mistaken
guess about who or what caused the trouble, but the world model keeps track of
the real moving source, the clues it leaves, and whether the chosen reveal spell
is strong enough to solve the mystery quickly. If not, a calm grown-up steps in.

Run it
------
    python storyworlds/worlds/gpt-5.4/mistaken_sound_effects_magic_mystery.py
    python storyworlds/worlds/gpt-5.4/mistaken_sound_effects_magic_mystery.py --place tower --source broom --suspect ghost
    python storyworlds/worlds/gpt-5.4/mistaken_sound_effects_magic_mystery.py --reveal shout_guess
    python storyworlds/worlds/gpt-5.4/mistaken_sound_effects_magic_mystery.py --all
    python storyworlds/worlds/gpt-5.4/mistaken_sound_effects_magic_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mistaken_sound_effects_magic_mystery.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/mistaken_sound_effects_magic_mystery.py --asp
    python storyworlds/worlds/gpt-5.4/mistaken_sound_effects_magic_mystery.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "witch", "librarian"}
        male = {"boy", "father", "man", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"librarian": "librarian", "mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    missing_item: str
    missing_phrase: str
    purpose: str
    caretaker_type: str
    caretaker_label: str
    afford_sources: set[str] = field(default_factory=set)
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
class Source:
    id: str
    label: str
    phrase: str
    sound: str
    sound_line: str
    movement: str
    clue: str
    carry_text: str
    reveal_text: str
    skittish: int
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
class Suspect:
    id: str
    label: str
    phrase: str
    theory: str
    overlap_tags: set[str] = field(default_factory=set)
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
class Reveal:
    id: str
    sense: int
    power: int
    label: str
    cast_text: str
    success_text: str
    fail_text: str
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


@dataclass
class StoryParams:
    place: str
    source: str
    suspect: str
    reveal: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    helper_trait: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "clue_text": "",
            "predicted_overlap": False,
            "predicted_sound": "",
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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    if source.meters["moving"] < THRESHOLD:
        return out
    sig = ("noise", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    source.meters["noisy"] += 1
    for eid in ("child", "helper"):
        ent = world.get(eid)
        ent.memes["curiosity"] += 1
        ent.memes["fear"] += 1
    out.append("__noise__")
    return out


def _r_missing(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    item = world.get("missing_item")
    if source.meters["moving"] < THRESHOLD or item.meters["attached"] < THRESHOLD:
        return out
    sig = ("missing", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["missing"] += 1
    out.append("__missing__")
    return out


def _r_revealed(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    item = world.get("missing_item")
    if source.meters["glowing"] < THRESHOLD:
        return out
    sig = ("revealed", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    source.meters["revealed"] += 1
    item.meters["found"] += 1
    item.meters["missing"] = 0.0
    for eid in ("child", "helper"):
        ent = world.get(eid)
        ent.memes["fear"] = 0.0
        ent.memes["relief"] += 1
    out.append("__revealed__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise", tag="physical", apply=_r_noise),
    Rule(name="missing", tag="physical", apply=_r_missing),
    Rule(name="revealed", tag="physical", apply=_r_revealed),
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


PLACES = {
    "tower": Place(
        id="tower",
        label="the moon tower",
        scene="the tallest room in the magic school, full of round windows and old shelves",
        missing_item="star key",
        missing_phrase="the little silver star key",
        purpose="open the star cupboard for lantern paper",
        caretaker_type="librarian",
        caretaker_label="the night librarian",
        afford_sources={"window_chimes", "broom"},
        tags={"tower", "library", "magic"},
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="the glass greenhouse",
        scene="a warm glass room where moonflowers curled around brass pots",
        missing_item="dew bell",
        missing_phrase="the tiny dew bell",
        purpose="wake the moonflowers for the evening show",
        caretaker_type="librarian",
        caretaker_label="the garden keeper",
        afford_sources={"window_chimes", "cat"},
        tags={"greenhouse", "plants", "magic"},
    ),
    "attic": Place(
        id="attic",
        label="the attic workshop",
        scene="a dusty workroom above the hall, packed with trunks and practice wands",
        missing_item="comet ribbon",
        missing_phrase="the blue comet ribbon",
        purpose="tie the prize parcel for the midnight fair",
        caretaker_type="librarian",
        caretaker_label="the supply keeper",
        afford_sources={"broom", "cat"},
        tags={"attic", "workshop", "magic"},
    ),
}

SOURCES = {
    "window_chimes": Source(
        id="window_chimes",
        label="enchanted window chimes",
        phrase="a string of enchanted window chimes",
        sound="ting-ting... whooo",
        sound_line="Ting-ting! Whooo...",
        movement="twisting in the window draft",
        clue="a line of silver dust by the window latch",
        carry_text="The missing item had snagged on the ribbon tied to the chimes.",
        reveal_text="the chimes came into view, trembling in the draft with the missing item looped over one bright ribbon",
        skittish=1,
        tags={"windy", "whispery", "shiny"},
    ),
    "broom": Source(
        id="broom",
        label="practice broom",
        phrase="a practice broom with a twitchy straw tail",
        sound="thump-swish... tap",
        sound_line="Thump-swish! Tap-tap!",
        movement="bumping into a trunk and swishing around in the dark",
        clue="a few gold straws on the floor",
        carry_text="The missing item had caught on the broom handle when it jumped awake.",
        reveal_text="the broom lurched out from behind a trunk, and the missing item glittered from its handle",
        skittish=2,
        tags={"thumpy", "sneaky", "stolen_looking"},
    ),
    "cat": Source(
        id="cat",
        label="spell-cat",
        phrase="a soft gray spell-cat with moonlit whiskers",
        sound="pat-pat... jingle",
        sound_line="Pat-pat! Jingle-jingle!",
        movement="slipping between boxes with something shiny in its mouth",
        clue="small paw prints in spilled blue dust",
        carry_text="The missing item had been carried off in a playful game.",
        reveal_text="the spell-cat blinked from under a stool, and the missing item dangled safely from its collar",
        skittish=1,
        tags={"patter", "sneaky", "pet"},
    ),
}

SUSPECTS = {
    "ghost": Suspect(
        id="ghost",
        label="ghost",
        phrase="a whispery ghost",
        theory="Something pale and floaty must be hiding in the dark.",
        overlap_tags={"windy", "whispery", "shiny"},
        tags={"ghost", "mystery"},
    ),
    "goblin": Suspect(
        id="goblin",
        label="goblin",
        phrase="a sneaky goblin",
        theory="Maybe a little goblin grabbed the missing thing and ran.",
        overlap_tags={"thumpy", "sneaky", "stolen_looking"},
        tags={"goblin", "mystery"},
    ),
    "cat": Suspect(
        id="cat",
        label="cat",
        phrase="the school cat",
        theory="Maybe the school cat batted it away just to play.",
        overlap_tags={"patter", "pet", "sneaky"},
        tags={"cat", "mystery"},
    ),
}

REVEALS = {
    "lantern_spell": Reveal(
        id="lantern_spell",
        sense=3,
        power=3,
        label="lantern spell",
        cast_text='"{Glow, and gently show},"',
        success_text="A warm lantern bubble floated ahead and lit the right hiding place at once.",
        fail_text="A warm lantern bubble glowed, but the moving shape darted deeper into the dark.",
        qa_text="used a lantern spell to light the shadows and show the hiding place",
        tags={"lantern", "magic"},
    ),
    "listening_charm": Reveal(
        id="listening_charm",
        sense=3,
        power=2,
        label="listening charm",
        cast_text='"{Hush and ring, tell what sings},"',
        success_text="The listening charm gathered the sound into one bright thread and led them straight to it.",
        fail_text="The listening charm caught the sound for a moment, but it skipped away before they could see clearly.",
        qa_text="used a listening charm to follow the sound to its source",
        tags={"listening", "magic"},
    ),
    "sparkle_net": Reveal(
        id="sparkle_net",
        sense=2,
        power=1,
        label="sparkle net",
        cast_text='"{Spark and stay},"',
        success_text="A soft net of sparkles settled over the corner and held the rustling shape still long enough to see it.",
        fail_text="A little sparkle net flashed out, but it was too weak and slid right off the moving thing.",
        qa_text="cast a sparkle net to stop the moving thing for a moment",
        tags={"sparkles", "magic"},
    ),
    "shout_guess": Reveal(
        id="shout_guess",
        sense=1,
        power=0,
        label="shout and point",
        cast_text='"There you are!"',
        success_text="The shout worked by luck this time.",
        fail_text="The shout only made the shadows jump and the mystery feel bigger.",
        qa_text="shouted into the dark and guessed without checking",
        tags={"guessing"},
    ),
}

GIRL_NAMES = ["Mira", "Nell", "Ivy", "Pia", "Luna", "Tara", "Wren", "Dora"]
BOY_NAMES = ["Oren", "Finn", "Leo", "Milo", "Jasper", "Toby", "Nico", "Evan"]
HELPER_TRAITS = ["careful", "patient", "steady", "clever", "quiet"]


def suspect_plausible(source: Source, suspect: Suspect) -> bool:
    return bool(source.tags & suspect.overlap_tags)


def sensible_reveals() -> list[Reveal]:
    return [r for r in REVEALS.values() if r.sense >= SENSE_MIN]


def reveal_threshold(source: Source, delay: int) -> int:
    return source.skittish + delay


def quick_solve(reveal: Reveal, source: Source, delay: int) -> bool:
    return reveal.power >= reveal_threshold(source, delay)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for source_id in sorted(place.afford_sources):
            source = SOURCES[source_id]
            for suspect_id, suspect in SUSPECTS.items():
                if suspect_plausible(source, suspect):
                    combos.append((place_id, source_id, suspect_id))
    return combos


def predict_theory(world: World, suspect: Suspect) -> dict:
    sim = world.copy()
    source = sim.get("source")
    source.meters["moving"] += 1
    propagate(sim, narrate=False)
    overlap = suspect_plausible(SOURCES[sim.facts["source_cfg"].id], suspect)
    return {
        "makes_noise": source.meters["noisy"] >= THRESHOLD,
        "missing": sim.get("missing_item").meters["missing"] >= THRESHOLD,
        "overlap": overlap,
        "sound": sim.facts["source_cfg"].sound,
    }


def introduce(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"After supper, {child.id} and {helper.id} climbed into {place.label}, "
        f"{place.scene}."
    )
    world.say(
        f"They needed {place.missing_phrase} to {place.purpose}, and the room looked "
        f"full of corners where a small mystery might hide."
    )


def discover_missing(world: World, child: Entity, place: Place) -> None:
    item = world.get("missing_item")
    item.meters["attached"] = 1.0
    world.say(
        f"But when {child.id} reached for the hook by the door, {place.missing_phrase} "
        f"was gone."
    )
    child.memes["worry"] += 1


def first_sound(world: World, child: Entity, helper: Entity, source_cfg: Source) -> None:
    source = world.get("source")
    source.meters["moving"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the dark answered with a sound: {source_cfg.sound_line} Something was "
        f"{source_cfg.movement}."
    )
    if helper.memes["curiosity"] >= THRESHOLD:
        world.say(f"{helper.id} stopped and listened instead of running away.")


def mistaken_guess(world: World, child: Entity, helper: Entity, suspect: Suspect) -> None:
    pred = predict_theory(world, suspect)
    world.facts["predicted_overlap"] = pred["overlap"]
    world.facts["predicted_sound"] = pred["sound"]
    child.memes["fear"] += 1
    child.memes["certainty"] += 1
    extra = " It sounded real enough to make the mistaken guess feel convincing."
    world.say(
        f'"Did you hear that?" whispered {child.id}. "{suspect.phrase.capitalize()}!" '
        f"{suspect.theory}{extra}"
    )
    if helper.attrs.get("trait") in {"patient", "careful", "steady"}:
        world.say(
            f'{helper.id} shook {helper.pronoun("possessive")} head. '
            f'"Maybe. But mysteries are better with clues than guesses."'
        )


def inspect_clue(world: World, helper: Entity, source_cfg: Source) -> None:
    helper.memes["focus"] += 1
    world.facts["clue_text"] = source_cfg.clue
    world.say(
        f"{helper.id} crouched down and found {source_cfg.clue}. That clue did not "
        f"match the first frightened idea."
    )


def cast_reveal(world: World, child: Entity, helper: Entity, reveal_cfg: Reveal) -> None:
    helper.memes["bravery"] += 1
    world.say(
        f'{helper.id} lifted a wand and said {reveal_cfg.cast_text} {reveal_cfg.success_text if reveal_cfg.power >= 2 else "A tiny shimmer ran across the room."}'
    )
    world.facts["revealer"] = helper


def reveal_success(world: World, child: Entity, helper: Entity, place: Place,
                   source_cfg: Source, reveal_cfg: Reveal) -> None:
    source = world.get("source")
    source.meters["glowing"] += 1
    propagate(world, narrate=False)
    item = world.get("missing_item")
    world.say(
        f"{reveal_cfg.success_text} In the light, {source_cfg.reveal_text}."
    )
    world.say(
        f'{child.id} blinked. "So it was not {world.facts["suspect_cfg"].phrase} at all."'
    )
    world.say(
        f"{source_cfg.carry_text} {child.id} took back {place.missing_phrase}, and the "
        f"whole room stopped feeling haunted."
    )
    item.memes["safe"] += 1


def reveal_fail_and_help(world: World, child: Entity, helper: Entity, caretaker: Entity,
                         place: Place, source_cfg: Source, reveal_cfg: Reveal) -> None:
    world.say(reveal_cfg.fail_text)
    world.say(
        f"The sound bounced away again -- {source_cfg.sound_line} -- and this time "
        f"{child.id} grabbed {helper.id}'s sleeve."
    )
    child.memes["fear"] += 1
    helper.memes["care"] += 1
    world.say(
        f'{child.id} took a breath and called for {caretaker.label}. That turned out to '
        f'be the bravest spell of all.'
    )
    source = world.get("source")
    source.meters["glowing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{caretaker.label.capitalize()} arrived with a broad moonbeam charm, and at once "
        f"{source_cfg.reveal_text}."
    )
    world.say(
        f"{source_cfg.carry_text} {caretaker.label.capitalize()} handed back "
        f"{place.missing_phrase} and reminded them that a mystery should be solved "
        f"before anyone is blamed."
    )


def closing(world: World, child: Entity, helper: Entity, place: Place) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"At last they used {place.missing_phrase} to {place.purpose}, and the room's "
        f"strange noises sounded different now."
    )
    world.say(
        f'What had first seemed spooky now sounded almost funny -- little mystery noises, '
        f'not monster noises. {child.id} laughed softly at the mistaken guess, and '
        f"{helper.id} laughed too."
    )


def tell(place: Place, source_cfg: Source, suspect: Suspect, reveal_cfg: Reveal,
         child_name: str = "Mira", child_gender: str = "girl",
         helper_name: str = "Oren", helper_gender: str = "boy",
         helper_trait: str = "patient", delay: int = 0) -> World:
    world = World(place)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={},
    ))
    child.id = child_name
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_gender,
        label=helper_name,
        role="helper",
        attrs={"trait": helper_trait},
    ))
    helper.id = helper_name
    caretaker = world.add(Entity(
        id="caretaker",
        kind="character",
        type=place.caretaker_type,
        label=place.caretaker_label,
        role="caretaker",
        attrs={},
    ))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type="source",
        label=source_cfg.label,
        attrs={},
        tags=set(source_cfg.tags),
    ))
    item = world.add(Entity(
        id="missing_item",
        kind="thing",
        type="item",
        label=place.missing_item,
        attrs={},
    ))

    child.memes["fear"] = 0.0
    child.memes["worry"] = 0.0
    helper.memes["fear"] = 0.0
    helper.memes["curiosity"] = 0.0
    helper.memes["focus"] = 0.0
    source.meters["moving"] = 0.0
    source.meters["noisy"] = 0.0
    source.meters["glowing"] = 0.0
    source.meters["revealed"] = 0.0
    item.meters["attached"] = 0.0
    item.meters["missing"] = 0.0
    item.meters["found"] = 0.0

    world.facts.update(
        place=place,
        source_cfg=source_cfg,
        suspect_cfg=suspect,
        reveal_cfg=reveal_cfg,
        child=child,
        helper=helper,
        caretaker=caretaker,
        delay=delay,
    )

    introduce(world, child, helper, place)
    discover_missing(world, child, place)

    world.para()
    first_sound(world, child, helper, source_cfg)
    mistaken_guess(world, child, helper, suspect)
    inspect_clue(world, helper, source_cfg)

    world.para()
    cast_reveal(world, child, helper, reveal_cfg)
    solved_quickly = quick_solve(reveal_cfg, source_cfg, delay)
    if solved_quickly:
        reveal_success(world, child, helper, place, source_cfg, reveal_cfg)
        outcome = "quick_reveal"
    else:
        reveal_fail_and_help(world, child, helper, caretaker, place, source_cfg, reveal_cfg)
        outcome = "grownup_help"

    world.para()
    closing(world, child, helper, place)

    world.facts.update(
        solved_quickly=solved_quickly,
        outcome=outcome,
        missing_found=world.get("missing_item").meters["found"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost in a story?",
            "A ghost in a story is an imaginary spooky figure people pretend might be around. In real life, strange sounds usually have an ordinary cause you can look for."
        )
    ],
    "goblin": [
        (
            "What is a goblin in a story?",
            "A goblin is a make-believe little troublemaker in many stories. Story goblins are fun for mysteries because they make characters wonder who caused a mess."
        )
    ],
    "cat": [
        (
            "Why do cats make mystery sounds?",
            "Cats can pad softly, jump onto things, and jingle tags or collars. That means they can sound spooky before you know where they are."
        )
    ],
    "lantern": [
        (
            "What does a lantern help you do?",
            "A lantern helps you see into dark corners. Better light often turns a scary mystery into an easy answer."
        )
    ],
    "listening": [
        (
            "Why is listening important in a mystery?",
            "Listening helps you notice where a sound really comes from. When you listen carefully, you make fewer mistaken guesses."
        )
    ],
    "sparkles": [
        (
            "What can sparkles show in a magic story?",
            "Sparkles can mark a path or outline a hidden thing. They are useful because they make invisible movement easier to see."
        )
    ],
    "magic": [
        (
            "What is magic in a story?",
            "Magic in a story is a special power that can make light, sounds, or moving objects. It lets small mysteries feel surprising and bright."
        )
    ],
    "mystery": [
        (
            "How do you solve a mystery?",
            "You look for clues, listen carefully, and check what really happened. Good mystery solving means you do not blame someone before you know the truth."
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "magic", "ghost", "goblin", "cat", "lantern", "listening", "sparkles"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    suspect = f["suspect_cfg"]
    reveal = f["reveal_cfg"]
    if f["outcome"] == "quick_reveal":
        return [
            f'Write a short mystery for a 3-to-5-year-old that includes the word "mistaken" and uses sound effects and magic in {place.label}.',
            f"Tell a gentle magical mystery where {child.id} hears a spooky sound, makes a mistaken guess about {suspect.label}, and {helper.id} solves it with a {reveal.label}.",
            f"Write a child-facing mystery story in which a missing little object, strange noises, and one careful clue lead to a warm, happy answer."
        ]
    return [
        f'Write a short mystery for a 3-to-5-year-old that includes the word "mistaken" and uses sound effects and magic in {place.label}.',
        f"Tell a magical mystery where {child.id} makes a mistaken guess after hearing spooky noises, and a calm grown-up helps {helper.id} finish solving it.",
        f"Write a gentle mystery story where clues matter more than guessing, and the ending proves that the scary sound had a real cause."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    caretaker = f["caretaker"]
    place = f["place"]
    source_cfg = f["source_cfg"]
    suspect = f["suspect_cfg"]
    reveal = f["reveal_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery at the beginning?",
            f"The mystery was that {place.missing_phrase} was missing just when the children needed it. That missing item made every sound in the room feel important."
        ),
        (
            f"Why did {child.id} make a mistaken guess?",
            f"{child.id} heard {source_cfg.sound} in the dark and felt frightened, so {child.pronoun('subject')} guessed it must be {suspect.phrase}. The room was shadowy, and the first sound came before the clue did."
        ),
        (
            f"What clue helped {helper.id} think more carefully?",
            f"{helper.id} found {f['clue_text']}. That clue pointed toward the real moving thing instead of the first scary idea."
        ),
    ]
    if f["outcome"] == "quick_reveal":
        qa.append(
            (
                f"How did {helper.id} solve the mystery?",
                f"{helper.id} {reveal.qa_text}. The spell worked quickly enough to show that the real source was {source_cfg.label}, and that is how they got {place.missing_phrase} back."
            )
        )
    else:
        qa.append(
            (
                f"Why did they call {caretaker.label}?",
                f"The first spell was too weak, so the sound skipped away and the mystery stayed dark. Calling {caretaker.label} helped because a calm grown-up could light the whole hiding place and stop the guessing."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the mystery solved and {place.missing_phrase} safely back where it belonged. The strange sound was not a monster at all, so the room felt friendly again."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"magic", "mystery"} | set(f["suspect_cfg"].tags) | set(f["reveal_cfg"].tags)
    if f["source_cfg"].id == "cat":
        tags.add("cat")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="tower",
        source="window_chimes",
        suspect="ghost",
        reveal="listening_charm",
        child_name="Mira",
        child_gender="girl",
        helper_name="Oren",
        helper_gender="boy",
        helper_trait="patient",
        delay=0,
    ),
    StoryParams(
        place="attic",
        source="broom",
        suspect="goblin",
        reveal="sparkle_net",
        child_name="Nell",
        child_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        helper_trait="careful",
        delay=1,
    ),
    StoryParams(
        place="greenhouse",
        source="cat",
        suspect="cat",
        reveal="lantern_spell",
        child_name="Ivy",
        child_gender="girl",
        helper_name="Leo",
        helper_gender="boy",
        helper_trait="steady",
        delay=0,
    ),
    StoryParams(
        place="attic",
        source="cat",
        suspect="cat",
        reveal="sparkle_net",
        child_name="Tara",
        child_gender="girl",
        helper_name="Milo",
        helper_gender="boy",
        helper_trait="quiet",
        delay=1,
    ),
    StoryParams(
        place="tower",
        source="broom",
        suspect="goblin",
        reveal="lantern_spell",
        child_name="Luna",
        child_gender="girl",
        helper_name="Jasper",
        helper_gender="boy",
        helper_trait="clever",
        delay=0,
    ),
]


def explain_rejection(place: Optional[Place] = None, source: Optional[Source] = None,
                      suspect: Optional[Suspect] = None, reveal: Optional[Reveal] = None) -> str:
    if reveal is not None and reveal.sense < SENSE_MIN:
        sensible = ", ".join(sorted(r.id for r in sensible_reveals()))
        return (
            f"(Refusing reveal '{reveal.id}': it scores too low on common sense "
            f"(sense={reveal.sense} < {SENSE_MIN}). A mystery should use clues or a "
            f"careful spell, not random shouting. Try: {sensible}.)"
        )
    if place is not None and source is not None and source.id not in place.afford_sources:
        return (
            f"(No story: {place.label} does not plausibly contain {source.phrase} in this "
            f"world, so the sound source would feel arbitrary.)"
        )
    if source is not None and suspect is not None and not suspect_plausible(source, suspect):
        return (
            f"(No story: {suspect.phrase} does not fit the clues left by {source.label}. "
            f"A mistaken guess still needs some clue overlap to feel believable.)"
        )
    return "(No valid combination matches the given options.)"


def outcome_of(params: StoryParams) -> str:
    return "quick_reveal" if quick_solve(REVEALS[params.reveal], SOURCES[params.source], params.delay) else "grownup_help"


ASP_RULES = r"""
% --- gate --------------------------------------------------------------
afforded(P,S) :- place(P), source(S), place_has(P,S).
plausible(S,Sp) :- source(S), suspect(Sp), overlap(S,Tag), suspect_tag(Sp,Tag).
valid(P,S,Sp) :- afforded(P,S), plausible(S,Sp).

sensible_reveal(R) :- reveal(R), sense(R,N), sense_min(M), N >= M.

% --- outcome -----------------------------------------------------------
threshold(Sk + D) :- chosen_source(S), skittish(S,Sk), delay(D).
quick_reveal :- chosen_reveal(R), power(R,P), threshold(T), P >= T.
outcome(quick_reveal) :- quick_reveal.
outcome(grownup_help) :- not quick_reveal.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for source_id in sorted(place.afford_sources):
            lines.append(asp.fact("place_has", place_id, source_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("skittish", source_id, source.skittish))
        for tag in sorted(source.tags):
            lines.append(asp.fact("overlap", source_id, tag))
    for suspect_id, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", suspect_id))
        for tag in sorted(suspect.overlap_tags):
            lines.append(asp.fact("suspect_tag", suspect_id, tag))
    for reveal_id, reveal in REVEALS.items():
        lines.append(asp.fact("reveal", reveal_id))
        lines.append(asp.fact("sense", reveal_id, reveal.sense))
        lines.append(asp.fact("power", reveal_id, reveal.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_reveals() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_reveal/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_reveal"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_source", params.source),
        asp.fact("chosen_reveal", params.reveal),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mistaken magical mystery driven by sound clues."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the moving thing keeps skittering before the reveal")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.reveal is not None and REVEALS[args.reveal].sense < SENSE_MIN:
        raise StoryError(explain_rejection(reveal=REVEALS[args.reveal]))
    if args.place is not None and args.source is not None:
        place = PLACES[args.place]
        source = SOURCES[args.source]
        if source.id not in place.afford_sources:
            raise StoryError(explain_rejection(place=place, source=source))
    if args.source is not None and args.suspect is not None:
        source = SOURCES[args.source]
        suspect = SUSPECTS[args.suspect]
        if not suspect_plausible(source, suspect):
            raise StoryError(explain_rejection(source=source, suspect=suspect))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.suspect is None or combo[2] == args.suspect)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id, suspect_id = rng.choice(sorted(combos))
    reveal_id = args.reveal or rng.choice(sorted(r.id for r in sensible_reveals()))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if child_gender == "girl" else rng.choice(["girl", "boy"])
    child_name = _pick_name(rng, child_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=child_name)
    helper_trait = rng.choice(HELPER_TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        place=place_id,
        source=source_id,
        suspect=suspect_id,
        reveal=reveal_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_trait=helper_trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        source_cfg = SOURCES[params.source]
        suspect = SUSPECTS[params.suspect]
        reveal_cfg = REVEALS[params.reveal]
    except KeyError as err:
        raise StoryError(f"(Unknown story parameter: {err.args[0]})") from None

    if source_cfg.id not in place.afford_sources:
        raise StoryError(explain_rejection(place=place, source=source_cfg))
    if not suspect_plausible(source_cfg, suspect):
        raise StoryError(explain_rejection(source=source_cfg, suspect=suspect))
    if reveal_cfg.sense < SENSE_MIN:
        raise StoryError(explain_rejection(reveal=reveal_cfg))

    world = tell(
        place=place,
        source_cfg=source_cfg,
        suspect=suspect,
        reveal_cfg=reveal_cfg,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        helper_trait=params.helper_trait,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_reveals = {r.id for r in sensible_reveals()}
    asp_reveals = set(asp_sensible_reveals())
    if py_reveals == asp_reveals:
        print(f"OK: sensible reveals match ({sorted(py_reveals)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible reveals: clingo={sorted(asp_reveals)} python={sorted(py_reveals)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(p)
    mismatches = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
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
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible_reveal/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible reveals: {', '.join(asp_sensible_reveals())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, source, suspect) combos:\n")
        for place, source, suspect in combos:
            print(f"  {place:10} {source:14} {suspect}")
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
            header = f"### {p.child_name} & {p.helper_name}: {p.source} in {p.place} (suspect: {p.suspect}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
