#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/genie_facial_magic_mystery.py
=======================================================

A standalone story world about a child, a genie, and a small magical mystery.

Reference seed:
    Write a story that includes the following words and narrative instruments.
    Words: genie, facial
    Features: Magic
    Style: Mystery

This world turns that seed into a tiny simulation domain: two children are
mixing a bedtime facial mask with magical ingredients when a small genie appears
and warns that one glowing ingredient has gone missing. The children must follow
state-grounded clues through a cozy place, search with a helper tool, and solve
the mystery before the mask can shine.

The world enforces simple reasonableness constraints:
- a missing ingredient must physically fit the hiding place,
- the hiding place must show the kind of clue that ingredient leaves,
- and the chosen helper must actually be able to detect that clue.

Run it
------
    python storyworlds/worlds/gpt-5.4/genie_facial_magic_mystery.py
    python storyworlds/worlds/gpt-5.4/genie_facial_magic_mystery.py --place bath_shop --missing moon_pearl
    python storyworlds/worlds/gpt-5.4/genie_facial_magic_mystery.py --hideout brass_teacup --helper velvet_fan
    python storyworlds/worlds/gpt-5.4/genie_facial_magic_mystery.py --all
    python storyworlds/worlds/gpt-5.4/genie_facial_magic_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/genie_facial_magic_mystery.py --asp
    python storyworlds/worlds/gpt-5.4/genie_facial_magic_mystery.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    shape: str = ""
    trail: str = ""
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
    opening: str
    detail: str
    hideouts: set[str] = field(default_factory=set)
    vessels: set[str] = field(default_factory=set)
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
class Vessel:
    id: str
    label: str
    phrase: str
    release: str
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
class MissingItem:
    id: str
    label: str
    phrase: str
    shape: str
    trail: str
    glow: str
    scent_line: str
    lesson: str
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
class Hideout:
    id: str
    label: str
    phrase: str
    fits: set[str] = field(default_factory=set)
    shows: set[str] = field(default_factory=set)
    difficulty: int = 0
    clue_text: str = ""
    find_text: str = ""
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
class Helper:
    id: str
    label: str
    phrase: str
    detects: set[str] = field(default_factory=set)
    power: int = 0
    action_text: str = ""
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


PLACES = {
    "bath_shop": Place(
        id="bath_shop",
        label="the little bath shop",
        opening="After closing time, the little bath shop felt full of soft shadows and good smells.",
        detail="Shelves of soap and jars of herbs stood around a marble mixing table.",
        hideouts={"velvet_drawer", "brass_teacup", "towel_basket"},
        vessels={"opal_bottle", "mirror_lamp"},
    ),
    "glass_house": Place(
        id="glass_house",
        label="the warm glass house",
        opening="At dusk, the warm glass house glowed green and gold around the workbench.",
        detail="Leaves tapped softly on the panes, and bowls of petals rested beside the sink.",
        hideouts={"brass_teacup", "curtain_fold", "towel_basket"},
        vessels={"opal_bottle", "shell_jar"},
    ),
    "attic_vanity": Place(
        id="attic_vanity",
        label="the attic vanity room",
        opening="Rain whispered on the roof above the attic vanity room.",
        detail="An old mirror, a comb, and a row of silver jars waited on the long table.",
        hideouts={"velvet_drawer", "curtain_fold", "brass_teacup"},
        vessels={"mirror_lamp", "shell_jar"},
    ),
}

VESSELS = {
    "opal_bottle": Vessel(
        id="opal_bottle",
        label="opal bottle",
        phrase="a cloudy opal bottle",
        release="A curl of blue light slipped out of the bottle and folded itself into a tiny genie with bright worried eyes.",
    ),
    "mirror_lamp": Vessel(
        id="mirror_lamp",
        label="mirror lamp",
        phrase="an old mirror lamp",
        release="The lamp flickered three times, and a tiny genie rose from the glass as if moonlight had learned how to bow.",
    ),
    "shell_jar": Vessel(
        id="shell_jar",
        label="shell jar",
        phrase="a pearly shell jar",
        release="The jar gave a small musical ping, and a tiny genie spiraled up in silver mist from inside it.",
    ),
}

MISSING_ITEMS = {
    "moon_pearl": MissingItem(
        id="moon_pearl",
        label="moon pearl",
        phrase="the moon pearl",
        shape="round",
        trail="glitter",
        glow="silver",
        scent_line="It left tiny silver dust wherever it bumped and rolled.",
        lesson="Even little magical things should be put back in their place.",
        tags={"glitter", "pearl", "magic"},
    ),
    "rose_drop": MissingItem(
        id="rose_drop",
        label="rose drop",
        phrase="the rose drop",
        shape="tiny",
        trail="rose_scent",
        glow="pink",
        scent_line="Where it went, the air kept a sweet rosy smell.",
        lesson="A careful nose can solve a mystery when eyes miss it.",
        tags={"rose", "scent", "magic"},
    ),
    "mint_star": MissingItem(
        id="mint_star",
        label="mint star leaf",
        phrase="the mint star leaf",
        shape="flat",
        trail="mint_scent",
        glow="green",
        scent_line="It always carried a cool mint smell, as if a breeze had touched it.",
        lesson="A calm pause can help you notice the clue that was there all along.",
        tags={"mint", "scent", "magic"},
    ),
}

HIDEOUTS = {
    "velvet_drawer": Hideout(
        id="velvet_drawer",
        label="velvet drawer",
        phrase="a velvet-lined drawer",
        fits={"round", "flat", "tiny"},
        shows={"glitter"},
        difficulty=0,
        clue_text="a line of silver specks on the drawer handle",
        find_text="nestled in the velvet corner",
    ),
    "brass_teacup": Hideout(
        id="brass_teacup",
        label="brass teacup",
        phrase="a little brass teacup",
        fits={"round", "tiny"},
        shows={"glitter", "rose_scent"},
        difficulty=1,
        clue_text="a bright ring at the bottom of a brass teacup",
        find_text="resting inside the cup",
    ),
    "towel_basket": Hideout(
        id="towel_basket",
        label="towel basket",
        phrase="a basket of folded towels",
        fits={"flat", "tiny"},
        shows={"rose_scent", "mint_scent"},
        difficulty=1,
        clue_text="a soft smell hiding in the folded towels",
        find_text="tucked between two towels",
    ),
    "curtain_fold": Hideout(
        id="curtain_fold",
        label="curtain fold",
        phrase="the deep fold of a curtain",
        fits={"flat", "tiny"},
        shows={"mint_scent", "glitter"},
        difficulty=2,
        clue_text="one curtain edge trembling with a cool strange smell",
        find_text="caught in the curtain fold",
    ),
}

HELPERS = {
    "silver_lens": Helper(
        id="silver_lens",
        label="silver lens",
        phrase="a silver lens",
        detects={"glitter"},
        power=1,
        action_text="held up the silver lens until every sparkle grew as big as a pebble",
        tags={"lens", "glitter"},
    ),
    "velvet_fan": Helper(
        id="velvet_fan",
        label="velvet fan",
        phrase="a velvet fan",
        detects={"rose_scent", "mint_scent"},
        power=1,
        action_text="waved the velvet fan and watched where the scented air curled",
        tags={"fan", "scent"},
    ),
    "whisper_comb": Helper(
        id="whisper_comb",
        label="whisper comb",
        phrase="a whisper comb",
        detects={"glitter", "rose_scent", "mint_scent"},
        power=2,
        action_text="brushed the air with the whisper comb and listened for the clue to hum back",
        tags={"comb", "magic"},
    ),
}

GIRL_NAMES = ["Lina", "Mina", "Ava", "Nora", "Zoe", "Ella", "Maya", "Ivy"]
BOY_NAMES = ["Oli", "Ben", "Noah", "Eli", "Leo", "Max", "Theo", "Finn"]
TRAITS = ["careful", "curious", "patient", "quiet", "thoughtful", "bright"]


# ---------------------------------------------------------------------------
# World container
# ---------------------------------------------------------------------------
class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "place": place,
            "clue_found": False,
            "detour": False,
            "mystery_started": False,
            "repaired": False,
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_missing_dulls(world: World) -> list[str]:
    bowl = world.get("bowl")
    ingredient = world.get("missing")
    if ingredient.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_dulls", ingredient.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bowl.meters["glow"] = 0.0
    bowl.meters["dull"] += 1
    bowl.memes["mystery"] += 1
    for actor in world.characters():
        if actor.role in {"child", "friend"}:
            actor.memes["worry"] += 1
            actor.memes["curiosity"] += 1
    world.facts["mystery_started"] = True
    return ["__mystery__"]


def _r_clue_raises_hope(world: World) -> list[str]:
    if not world.facts.get("clue_found"):
        return []
    sig = ("clue_hope",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for actor in world.characters():
        if actor.role in {"child", "friend"}:
            actor.memes["hope"] += 1
            actor.memes["curiosity"] += 1
    return []


def _r_return_repairs(world: World) -> list[str]:
    bowl = world.get("bowl")
    ingredient = world.get("missing")
    if ingredient.meters["returned"] < THRESHOLD:
        return []
    sig = ("return_repairs", ingredient.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bowl.meters["glow"] += 2
    bowl.meters["dull"] = 0.0
    for actor in world.characters():
        if actor.role in {"child", "friend"}:
            actor.memes["worry"] = 0.0
            actor.memes["relief"] += 1
            actor.memes["joy"] += 1
        if actor.role == "genie":
            actor.memes["trust"] += 1
            actor.memes["relief"] += 1
    world.facts["repaired"] = True
    return []


CAUSAL_RULES = [
    Rule(name="missing_dulls", tag="physical", apply=_r_missing_dulls),
    Rule(name="clue_hope", tag="emotional", apply=_r_clue_raises_hope),
    Rule(name="return_repairs", tag="physical", apply=_r_return_repairs),
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


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_place_vessel(place_id: str, vessel_id: str) -> bool:
    return vessel_id in PLACES[place_id].vessels


def valid_hiding(missing_id: str, hideout_id: str, helper_id: str, place_id: str) -> bool:
    missing = MISSING_ITEMS[missing_id]
    hideout = HIDEOUTS[hideout_id]
    helper = HELPERS[helper_id]
    place = PLACES[place_id]
    return (
        hideout_id in place.hideouts
        and missing.shape in hideout.fits
        and missing.trail in hideout.shows
        and missing.trail in helper.detects
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in sorted(PLACES):
        for missing_id in sorted(MISSING_ITEMS):
            for hideout_id in sorted(HIDEOUTS):
                for helper_id in sorted(HELPERS):
                    if valid_hiding(missing_id, hideout_id, helper_id, place_id):
                        combos.append((place_id, missing_id, hideout_id, helper_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    helper = HELPERS[params.helper]
    hideout = HIDEOUTS[params.hideout]
    return "direct" if helper.power >= hideout.difficulty else "detour"


def explain_rejection(place_id: str, missing_id: str, hideout_id: str, helper_id: str) -> str:
    place = PLACES[place_id]
    missing = MISSING_ITEMS[missing_id]
    hideout = HIDEOUTS[hideout_id]
    helper = HELPERS[helper_id]
    if hideout_id not in place.hideouts:
        return (
            f"(No story: {hideout.phrase} is not part of {place.label}, so the mystery "
            f"has nowhere honest to lead.)"
        )
    if missing.shape not in hideout.fits:
        return (
            f"(No story: {missing.phrase} would not sensibly fit in {hideout.phrase}. "
            f"The hiding place must physically suit the missing object.)"
        )
    if missing.trail not in hideout.shows:
        return (
            f"(No story: {hideout.phrase} would not show the clue left by {missing.phrase}. "
            f"A mystery needs a clue the children could really notice.)"
        )
    if missing.trail not in helper.detects:
        return (
            f"(No story: {helper.phrase} cannot detect the kind of clue {missing.phrase} leaves. "
            f"The chosen helper has to help for real.)"
        )
    return "(No story: this combination does not make a reasonable mystery.)"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_fix(world: World) -> dict:
    sim = world.copy()
    sim.get("missing").meters["returned"] += 1
    propagate(sim, narrate=False)
    bowl = sim.get("bowl")
    return {
        "glows": bowl.meters["glow"] >= THRESHOLD,
        "repaired": sim.facts.get("repaired", False),
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def setup_scene(world: World, child: Entity, friend: Entity, place: Place, vessel: Vessel) -> None:
    for actor in (child, friend):
        actor.memes["joy"] += 1
        actor.memes["curiosity"] += 1
    world.say(place.opening)
    world.say(place.detail)
    world.say(
        f'{child.id} and {friend.id} stood by the bowl, ready to mix a sleepy moon facial before bed.'
    )
    world.say(
        f'Beside the bowl sat {vessel.phrase}, dusty and quiet, as if it had been waiting to hear a secret.'
    )


def stir_mask(world: World, child: Entity, friend: Entity) -> None:
    bowl = world.get("bowl")
    bowl.meters["glow"] += 1
    world.say(
        f'{child.id} stirred the silver cream while {friend.id} counted three spoonfuls of cloud-soft foam.'
    )
    world.say("For a blink, the mixture glimmered like a tiny moon in a cup.")


def summon_genie(world: World, genie: Entity, vessel: Vessel) -> None:
    genie.memes["worry"] += 1
    world.say(vessel.release)
    world.say(
        f'"Please do not be frightened," said the genie. "I only come when a bit of small magic has gone missing."'
    )


def discover_loss(world: World, genie: Entity, missing: MissingItem) -> None:
    ing = world.get("missing")
    ing.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f'The genie floated over the bowl and frowned. "It should be glowing {missing.glow} by now, but {missing.phrase} is gone."'
    )
    world.say(
        f'"Without it, the facial will stay dull, and the bedtime charm will not wake."'
    )
    world.say(missing.scent_line)
    if world.facts.get("mystery_started"):
        world.say("A hush fell over the room, the kind that made every small object feel full of clues.")


def choose_helper(world: World, child: Entity, friend: Entity, helper: Helper) -> None:
    tool = world.get("helper")
    tool.attrs["active"] = True
    world.say(
        f'{friend.id} picked up {helper.phrase}, and {child.id} nodded as if the mystery had just become a game they could win.'
    )
    world.say(f"{friend.id} {helper.action_text}.")


def follow_first_clue(world: World, child: Entity, friend: Entity, missing: MissingItem, hideout: Hideout, helper: Helper) -> None:
    world.facts["clue_found"] = True
    propagate(world, narrate=False)
    world.say(
        f'Soon they noticed {hideout.clue_text}. It matched the trail from {missing.phrase}.'
    )
    if helper.power >= hideout.difficulty:
        world.say(
            f'"There," whispered {child.id}. "The clue is pointing straight at {hideout.phrase}."'
        )
    else:
        world.say(
            f'The clue led them part of the way, but not all the way. The room still kept one secret tucked behind another.'
        )


def detour(world: World, child: Entity, friend: Entity, genie: Entity, hideout: Hideout) -> None:
    world.facts["detour"] = True
    child.memes["worry"] += 1
    friend.memes["worry"] += 1
    genie.memes["trust"] += 1
    world.say(
        f'{child.id} checked the wrong shelf first, and {friend.id} looked under the mixing cloth, but neither place held anything magical.'
    )
    world.say(
        f'Then the genie went very still. "Listen," {genie.pronoun()} said softly. "One curtain is breathing colder than the others."'
    )
    world.say(
        f'That made them look again, slower this time, until their eyes came back to {hideout.phrase}.'
    )


def recover_item(world: World, child: Entity, friend: Entity, missing: MissingItem, hideout: Hideout) -> None:
    ing = world.get("missing")
    ing.meters["missing"] = 0.0
    ing.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Inside {hideout.phrase}, they found {missing.phrase}, {hideout.find_text}.'
    )
    world.say(
        f'{friend.id} cupped it gently, and {child.id} laughed the careful laugh that comes after being worried.'
    )


def repair_mask(world: World, child: Entity, genie: Entity, missing: MissingItem) -> None:
    bowl = world.get("bowl")
    pred = predict_fix(world)
    if not pred["glows"]:
        raise StoryError("(Internal story error: returning the missing magic should repair the bowl.)")
    world.say(
        f'{child.id} dropped {missing.phrase} back into the bowl. At once the cream turned {missing.glow} and shone against the spoon.'
    )
    world.say(
        f'The genie clapped tiny glowing hands. "The spell is whole again. A solved mystery always makes the best kind of Magic."'
    )
    if bowl.meters["glow"] >= 2:
        world.say("The room no longer felt worried. It felt bright and certain.")


def ending(world: World, child: Entity, friend: Entity, genie: Entity, missing: MissingItem) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    genie.memes["relief"] += 1
    world.say(
        f'They dabbed the shining facial on their cheeks in two tiny moon-shaped swirls, and the mirror showed them glowing softly back.'
    )
    world.say(
        f'"Next time," said {friend.id}, "we put {missing.phrase} away before it can wander."'
    )
    world.say(
        f'The genie bowed, slipped back into the lamplight, and left the mystery behind as only a memory of silver air and solved secrets.'
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    vessel: Vessel,
    missing: Missing,
    hideout: Hideout,
    helper: Helper,
    child_name: str,
    child_gender: str,
    friend_name: str,
    friend_gender: str,
    parent_type: ParentType,
    trait: str,
    place=None,
) -> World:
    world = World(place)

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=["steady"],
    ))
    genie = world.add(Entity(
        id="Genie",
        kind="character",
        type="genie",
        role="genie",
        label="the genie",
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    bowl = world.add(Entity(
        id="bowl",
        type="bowl",
        label="mixing bowl",
    ))
    ing = world.add(Entity(
        id="missing",
        type="ingredient",
        label=missing.label,
        shape=missing.shape,
        trail=missing.trail,
    ))
    tool = world.add(Entity(
        id="helper",
        type="tool",
        label=helper.label,
        attrs={"active": False},
    ))
    spot = world.add(Entity(
        id="hideout",
        type="hideout",
        label=hideout.label,
        attrs={"difficulty": hideout.difficulty},
    ))

    world.facts.update({
        "child": child,
        "friend": friend,
        "genie": genie,
        "parent": parent,
        "vessel": vessel,
        "missing_cfg": missing,
        "hideout_cfg": hideout,
        "helper_cfg": helper,
        "helper_power": helper.power,
        "difficulty": hideout.difficulty,
    })

    setup_scene(world, child, friend, place, vessel)
    stir_mask(world, child, friend)

    world.para()
    summon_genie(world, genie, vessel)
    discover_loss(world, genie, missing)

    world.para()
    choose_helper(world, child, friend, helper)
    follow_first_clue(world, child, friend, missing, hideout, helper)

    if helper.power < hideout.difficulty:
        detour(world, child, friend, genie, hideout)

    world.para()
    recover_item(world, child, friend, missing, hideout)
    repair_mask(world, child, genie, missing)

    world.para()
    ending(world, child, friend, genie, missing)
    world.facts["outcome"] = outcome_of(StoryParams(
        place=place.id,
        missing=missing.id,
        hideout=hideout.id,
        helper=helper.id,
        vessel=vessel.id,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent_type,
        trait=trait,
        seed=None,
    ))
    return world


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
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
    "genie": [(
        "What is a genie?",
        "A genie is a magical being from storybooks who can appear in a lamp, bottle, or jar. In many stories, a genie uses magic to help or warn people."
    )],
    "facial": [(
        "What is a facial?",
        "A facial is something gentle you put on your face for a little while and then wipe or wash away. In this story it is a soft pretend bedtime cream, not medicine."
    )],
    "glitter": [(
        "Why can glitter be a clue?",
        "Glitter is bright and easy to notice, so if something shiny leaves it behind, you can follow the sparkles. That makes it useful in a mystery."
    )],
    "rose": [(
        "How can a smell help solve a mystery?",
        "A smell can tell you where something has been even when you cannot see it. If the smell stays in one place, that place may be hiding the missing thing."
    )],
    "mint": [(
        "Why is mint smell easy to notice?",
        "Mint smells cool and fresh, so it stands out from other smells in a room. That makes it a strong clue if something magical smells like mint."
    )],
    "lens": [(
        "What does a lens help you do?",
        "A lens makes tiny things look bigger. That can help you notice clues you might have missed."
    )],
    "fan": [(
        "How can a fan help with a smell clue?",
        "A fan moves the air around. When air moves, a smell can drift and show you where it is strongest."
    )],
    "magic": [(
        "What does magic mean in a story?",
        "Magic means something wondrous happens that ordinary life cannot do by itself. In stories, magic often makes hidden things glow, move, or speak."
    )],
}
KNOWLEDGE_ORDER = ["genie", "facial", "glitter", "rose", "mint", "lens", "fan", "magic"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    missing = f["missing_cfg"]
    place = f["place"]
    outcome = f["outcome"]
    if outcome == "detour":
        return [
            f'Write a cozy Magic mystery for a 3-to-5-year-old that includes the words "genie" and "facial". Set it in {place.label} and make a missing magical ingredient the center of the mystery.',
            f"Tell a gentle mystery where {child.id} and {friend.id} are mixing a bedtime facial when a genie appears and warns that {missing.phrase} is missing. Let the first clue help, but not quite enough, before the children solve it.",
            f'Write a child-facing mystery story with a tiny genie, a glowing facial bowl, one wrong guess, and a happy ending where the missing magic is found and returned.',
        ]
    return [
        f'Write a cozy Magic mystery for a 3-to-5-year-old that includes the words "genie" and "facial". Set it in {place.label} and make a missing magical ingredient the center of the mystery.',
        f"Tell a gentle mystery where {child.id} and {friend.id} are mixing a bedtime facial when a genie appears and warns that {missing.phrase} is missing, and the children solve the clue neatly.",
        f'Write a simple mystery story with a tiny genie, a magical clue, and a bright ending that proves the problem was fixed.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    genie = f["genie"]
    missing = f["missing_cfg"]
    hideout = f["hideout_cfg"]
    helper = f["helper_cfg"]
    place = f["place"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {friend.id}, who were mixing a magical bedtime facial, and a tiny genie who came to warn them. The mystery starts because a small but important ingredient is missing."
        ),
        (
            "What problem did the genie notice?",
            f'The genie noticed that {missing.phrase} was gone, so the bowl would not glow the way it should. Without that missing piece, the spell could not finish waking up.'
        ),
        (
            f"Why did {child.id} and {friend.id} use {helper.phrase}?",
            f"They used {helper.phrase} to notice the kind of clue {missing.phrase} leaves behind. The helper mattered because a mystery is easier to solve when your tool matches the clue."
        ),
        (
            "Where did the clue lead them?",
            f'The clue led them toward {hideout.phrase}. That place made sense because it could really hide the missing magic and still show its trail.'
        ),
    ]
    if outcome == "detour":
        qa.append((
            "Did they solve the mystery right away?",
            f"No. Their first clue helped, but it did not tell them everything, so they checked the wrong place before the genie helped them notice one colder, truer sign. Slowing down let them see the real hiding place at last."
        ))
    else:
        qa.append((
            "Did they solve the mystery quickly or after a wrong turn?",
            f"They solved it quickly. Their helper was strong enough for that hiding place, so the first clue pointed them the right way."
        ))
    qa.append((
        f"What changed after they found {missing.phrase}?",
        f'They put {missing.phrase} back into the bowl, and the facial began to glow {missing.glow}. That bright change proved the mystery was solved and the magic was whole again.'
    ))
    qa.append((
        f"How did the story end in {place.label}?",
        f'The children dabbed the shining facial onto their cheeks, and the genie left behind only a memory of silver air. The ending image shows that the room has changed from worried and puzzling to calm and magical.'
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    missing = f["missing_cfg"]
    helper = f["helper_cfg"]
    tags = {"genie", "facial", "magic"}
    if missing.trail == "glitter":
        tags.add("glitter")
    if missing.trail == "rose_scent":
        tags.add("rose")
    if missing.trail == "mint_scent":
        tags.add("mint")
    if helper.id == "silver_lens":
        tags.add("lens")
    if helper.id == "velvet_fan":
        tags.add("fan")
    if helper.id == "whisper_comb":
        tags.add("magic")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.shape:
            bits.append(f"shape={ent.shape}")
        if ent.trail:
            bits.append(f"trail={ent.trail}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} clue_found={world.facts.get('clue_found')} detour={world.facts.get('detour')} repaired={world.facts.get('repaired')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    missing: str
    hideout: str
    helper: str
    vessel: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="bath_shop",
        missing="moon_pearl",
        hideout="velvet_drawer",
        helper="silver_lens",
        vessel="opal_bottle",
        child_name="Lina",
        child_gender="girl",
        friend_name="Oli",
        friend_gender="boy",
        parent="mother",
        trait="careful",
        seed=None,
    ),
    StoryParams(
        place="glass_house",
        missing="rose_drop",
        hideout="brass_teacup",
        helper="velvet_fan",
        vessel="shell_jar",
        child_name="Ben",
        child_gender="boy",
        friend_name="Maya",
        friend_gender="girl",
        parent="father",
        trait="curious",
        seed=None,
    ),
    StoryParams(
        place="attic_vanity",
        missing="mint_star",
        hideout="curtain_fold",
        helper="velvet_fan",
        vessel="mirror_lamp",
        child_name="Nora",
        child_gender="girl",
        friend_name="Leo",
        friend_gender="boy",
        parent="mother",
        trait="quiet",
        seed=None,
    ),
    StoryParams(
        place="glass_house",
        missing="mint_star",
        hideout="towel_basket",
        helper="whisper_comb",
        vessel="opal_bottle",
        child_name="Ivy",
        child_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        parent="father",
        trait="thoughtful",
        seed=None,
    ),
    StoryParams(
        place="attic_vanity",
        missing="moon_pearl",
        hideout="brass_teacup",
        helper="whisper_comb",
        vessel="shell_jar",
        child_name="Ava",
        child_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        parent="mother",
        trait="bright",
        seed=None,
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Place, Missing, Hideout, Helper) :-
    place(Place), missing(Missing), hideout(Hideout), helper(Helper),
    in_place(Place, Hideout),
    shape(Missing, Shape), fits(Hideout, Shape),
    trail(Missing, Trail), shows(Hideout, Trail),
    detects(Helper, Trail).

direct(Helper, Hideout) :-
    helper_power(Helper, HP), hideout_difficulty(Hideout, D), HP >= D.

detour(Helper, Hideout) :-
    helper_power(Helper, HP), hideout_difficulty(Hideout, D), HP < D.

outcome(direct) :- chosen_helper(H), chosen_hideout(Hi), direct(H, Hi).
outcome(detour) :- chosen_helper(H), chosen_hideout(Hi), detour(H, Hi).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for hideout_id in sorted(place.hideouts):
            lines.append(asp.fact("in_place", place_id, hideout_id))
        for vessel_id in sorted(place.vessels):
            lines.append(asp.fact("place_vessel", place_id, vessel_id))
    for missing_id, missing in MISSING_ITEMS.items():
        lines.append(asp.fact("missing", missing_id))
        lines.append(asp.fact("shape", missing_id, missing.shape))
        lines.append(asp.fact("trail", missing_id, missing.trail))
    for hideout_id, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hideout_id))
        lines.append(asp.fact("hideout_difficulty", hideout_id, hideout.difficulty))
        for shape in sorted(hideout.fits):
            lines.append(asp.fact("fits", hideout_id, shape))
        for trail in sorted(hideout.shows):
            lines.append(asp.fact("shows", hideout_id, trail))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helper_power", helper_id, helper.power))
        for trail in sorted(helper.detects):
            lines.append(asp.fact("detects", helper_id, trail))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_hideout", params.hideout),
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

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"MISMATCH: resolve_params unexpectedly failed on seed {seed}.")
            break

    mismatches = []
    for params in cases:
        ao = asp_outcome(params)
        po = outcome_of(params)
        if ao != po:
            mismatches.append((params.place, params.missing, params.hideout, params.helper, ao, po))
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print("MISMATCH in outcomes:")
        for item in mismatches[:10]:
            print(" ", item)

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generate()/emit() passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a genie, a magical facial, and a cozy mystery. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--missing", choices=sorted(MISSING_ITEMS))
    ap.add_argument("--hideout", choices=sorted(HIDEOUTS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--vessel", choices=sorted(VESSELS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.vessel and not valid_place_vessel(args.place, args.vessel):
        raise StoryError(
            f"(No story: {VESSELS[args.vessel].phrase} does not belong naturally in {PLACES[args.place].label}.)"
        )

    if args.place and args.missing and args.hideout and args.helper:
        if not valid_hiding(args.missing, args.hideout, args.helper, args.place):
            raise StoryError(explain_rejection(args.place, args.missing, args.hideout, args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.missing is None or combo[1] == args.missing)
        and (args.hideout is None or combo[2] == args.hideout)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, missing_id, hideout_id, helper_id = rng.choice(sorted(combos))
    place = PLACES[place_id]

    if args.vessel:
        if not valid_place_vessel(place_id, args.vessel):
            raise StoryError(
                f"(No story: {VESSELS[args.vessel].phrase} does not belong naturally in {place.label}.)"
            )
        vessel_id = args.vessel
    else:
        vessel_id = rng.choice(sorted(place.vessels))

    child_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    child_name = _pick_name(rng, child_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=child_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        missing=missing_id,
        hideout=hideout_id,
        helper=helper_id,
        vessel=vessel_id,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    required = {
        "place": PLACES,
        "missing": MISSING_ITEMS,
        "hideout": HIDEOUTS,
        "helper": HELPERS,
        "vessel": VESSELS,
    }
    for field_name, registry in required.items():
        value = getattr(params, field_name)
        if value not in registry:
            raise StoryError(f"(No story: unknown {field_name} '{value}'.)")

    if not valid_hiding(params.missing, params.hideout, params.helper, params.place):
        raise StoryError(explain_rejection(params.place, params.missing, params.hideout, params.helper))
    if not valid_place_vessel(params.place, params.vessel):
        raise StoryError(
            f"(No story: {VESSELS[params.vessel].phrase} does not belong naturally in {PLACES[params.place].label}.)"
        )

    world = tell(
        place=PLACES[params.place],
        vessel=VESSELS[params.vessel],
        missing=MISSING_ITEMS[params.missing],
        hideout=HIDEOUTS[params.hideout],
        helper=HELPERS[params.helper],
        child_name=params.child_name,
        child_gender=params.child_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        trait=params.trait,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, missing, hideout, helper) combos:\n")
        for place, missing, hideout, helper in combos:
            outcome = outcome_of(StoryParams(
                place=place,
                missing=missing,
                hideout=hideout,
                helper=helper,
                vessel=sorted(PLACES[place].vessels)[0],
                child_name="Lina",
                child_gender="girl",
                friend_name="Oli",
                friend_gender="boy",
                parent="mother",
                trait="careful",
                seed=None,
            ))
            print(f"  {place:13} {missing:10} {hideout:14} {helper:12} [{outcome}]")
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
                f"### {p.child_name} & {p.friend_name}: {p.missing} in {p.hideout} "
                f"({p.place}, {p.helper}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
