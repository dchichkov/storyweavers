#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/feel_gerund_ranch_reconciliation_ghost_story.py
===========================================================================

A small storyworld about two children at a moonlit ranch who have stopped
speaking after a quarrel. A gentle ghostly sign leads them toward a missing
keepsake, but the haunting only settles when they also mend what is broken
between them.

The domain is intentionally narrow: the world prefers a few coherent ghost-story
variants over a wide pile of weak combinations. The physical state tracks where
the keepsake is, whether the ghost is restless, and whether the children are
working together; the emotional state tracks hurt, guilt, fear, trust, and
peace. The prose is rendered from that changing state.

Run it
------
    python storyworlds/worlds/gpt-5.4/feel_gerund_ranch_reconciliation_ghost_story.py
    python storyworlds/worlds/gpt-5.4/feel_gerund_ranch_reconciliation_ghost_story.py --quarrel sharp_words --keepsake bell
    python storyworlds/worlds/gpt-5.4/feel_gerund_ranch_reconciliation_ghost_story.py --peace dare_the_ghost
    python storyworlds/worlds/gpt-5.4/feel_gerund_ranch_reconciliation_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/feel_gerund_ranch_reconciliation_ghost_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/feel_gerund_ranch_reconciliation_ghost_story.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandfather": "grandpa",
            "grandmother": "grandma",
            "father": "dad",
            "mother": "mom",
        }.get(self.type, self.type)
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
class RanchPlace:
    id: str
    label: str
    approach: str
    detail: str
    hook: str
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
class Keepsake:
    id: str
    label: str
    phrase: str
    owner_name: str
    owner_role: str
    home_place: str
    material: str
    found_spot: str
    return_spot: str
    memory_line: str
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
class GhostSign:
    id: str
    place: str
    sound: str
    shimmer: str
    fear_line: str
    comfort_line: str
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
class Quarrel:
    id: str
    label: str
    kind: str
    opening: str
    hurt_line: str
    blame_text: str
    remedy_tags: set[str] = field(default_factory=set)
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
class PeaceAct:
    id: str
    sense: int
    remedy_tags: set[str]
    apology_line: str
    together_line: str
    resolution_line: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        return [e for e in self.entities.values() if e.role in {"older", "younger"}]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
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


def _r_restless_ghost(world: World) -> list[str]:
    ghost = world.get("ghost")
    keepsake = world.get("keepsake")
    kids = world.kids()
    if keepsake.attrs.get("place") != keepsake.attrs.get("home_place"):
        sig = ("restless",)
        if sig not in world.fired:
            world.fired.add(sig)
            ghost.meters["restless"] += 1
    if any(k.memes["hurt"] >= THRESHOLD for k in kids) and ghost.meters["restless"] >= THRESHOLD:
        sig = ("haunt_grows",)
        if sig not in world.fired:
            world.fired.add(sig)
            ghost.meters["sadness"] += 1
            for kid in kids:
                kid.memes["fear"] += 1
            return ["__ghost__"]
    return []


def _r_reconciliation(world: World) -> list[str]:
    a = world.get("older")
    b = world.get("younger")
    ghost = world.get("ghost")
    keepsake = world.get("keepsake")
    if (
        keepsake.attrs.get("place") == keepsake.attrs.get("home_place")
        and a.memes["trust"] >= THRESHOLD
        and b.memes["trust"] >= THRESHOLD
    ):
        sig = ("reconciled",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["peace"] += 1
            b.memes["peace"] += 1
            ghost.meters["restless"] = 0.0
            ghost.meters["peace"] += 1
            return ["__settled__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="restless_ghost", tag="physical", apply=_r_restless_ghost),
    Rule(name="reconciliation", tag="social", apply=_r_reconciliation),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            made = rule.apply(world)
            if made:
                changed = True
                out.extend(x for x in made if not x.startswith("__"))
    if narrate:
        for line in out:
            world.say(line)
    return out


def sensible_peace_acts() -> list[PeaceAct]:
    return [p for p in PEACE_ACTS.values() if p.sense >= SENSE_MIN]


def act_matches(quarrel: Quarrel, peace: PeaceAct) -> bool:
    return bool(quarrel.remedy_tags & peace.remedy_tags)


def sign_matches(sign: GhostSign, keepsake: Keepsake) -> bool:
    return sign.place == keepsake.home_place


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for qid, quarrel in QUARRELS.items():
        for sid, sign in SIGNS.items():
            for pid, peace in PEACE_ACTS.items():
                if peace.sense < SENSE_MIN:
                    continue
                for kid, keepsake in KEEPSAKES.items():
                    if sign_matches(sign, keepsake) and act_matches(quarrel, peace):
                        combos.append((qid, sid, kid, pid))
    return combos


def explain_peace_rejection(peace_id: str) -> str:
    peace = PEACE_ACTS[peace_id]
    better = ", ".join(sorted(p.id for p in sensible_peace_acts()))
    return (
        f"(Refusing peace act '{peace_id}': it scores too low on common sense "
        f"(sense={peace.sense} < {SENSE_MIN}). A quiet ghost on a ranch is not made "
        f"safer by taunting it. Try one of: {better}.)"
    )


def explain_combo_rejection(quarrel: Quarrel, sign: GhostSign, keepsake: Keepsake, peace: PeaceAct) -> str:
    if not sign_matches(sign, keepsake):
        place = PLACES[keepsake.home_place]
        return (
            f"(No story: {sign.id} belongs at {PLACES[sign.place].label}, but "
            f"{keepsake.label} belongs at {place.label}. The haunting and the keepsake "
            f"must point to the same place.)"
        )
    if not act_matches(quarrel, peace):
        return (
            f"(No story: {peace.id} does not truly mend the quarrel '{quarrel.id}'. "
            f"The ending needs a real reconciliation, not just spooky walking around.)"
        )
    return "(No story: this combination is not coherent.)"


def outcome_of(params: "StoryParams") -> str:
    peace = PEACE_ACTS[params.peace]
    quarrel = QUARRELS[params.quarrel]
    sign = SIGNS[params.sign]
    keepsake = KEEPSAKES[params.keepsake]
    if peace.sense < SENSE_MIN:
        return "restless"
    if sign_matches(sign, keepsake) and act_matches(quarrel, peace):
        return "settled"
    return "restless"


def predict_settling(world: World) -> dict:
    sim = world.copy()
    a = sim.get("older")
    b = sim.get("younger")
    keepsake = sim.get("keepsake")
    keepsake.attrs["place"] = keepsake.attrs["home_place"]
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    propagate(sim, narrate=False)
    ghost = sim.get("ghost")
    return {
        "settled": ghost.meters["peace"] >= THRESHOLD and ghost.meters["restless"] < THRESHOLD,
        "fear": sum(k.memes["fear"] for k in sim.kids()),
    }


def introduce(world: World, older: Entity, younger: Entity, grandpa: Entity, place: RanchPlace, quarrel: Quarrel) -> None:
    world.say(
        f"On Grand{grandpa.label_word[5:]}'s ranch, the evening light stretched long across "
        f"{place.approach}. {place.detail}"
    )
    world.say(
        f"{older.id} and {younger.id} had been together all afternoon, but by supper they were not "
        f"walking side by side anymore."
    )
    world.say(quarrel.opening)
    world.say(
        f"The odd feel-gerund of moving around each other without speaking made the whole ranch seem quieter."
    )


def send_errand(world: World, older: Entity, younger: Entity, grandpa: Entity, place: RanchPlace) -> None:
    world.say(
        f"After the dishes were stacked, {grandpa.label_word.capitalize()} asked them to fetch a blanket from "
        f"{place.label}. Neither one wanted to answer first, so they went together under the silver moon."
    )


def approach_haunting(world: World, older: Entity, younger: Entity, place: RanchPlace, sign: GhostSign) -> None:
    older.memes["fear"] += 1
    younger.memes["fear"] += 1
    world.say(
        f"When they reached {place.label}, {sign.sound}. Then {sign.shimmer}."
    )
    world.say(sign.fear_line)


def notice_missing_keepsake(world: World, older: Entity, younger: Entity, keepsake: Keepsake, sign: GhostSign) -> None:
    ghost = world.get("ghost")
    prop = world.get("keepsake")
    propagate(world, narrate=False)
    world.say(
        f"On the wall there should have been {keepsake.phrase} that had belonged to {keepsake.owner_name}, "
        f"but the hook stood empty."
    )
    world.say(
        f'"Maybe that is why the place feels so sad," {younger.id} whispered. '
        f'{sign.comfort_line}'
    )
    world.facts["ghost_restless_before"] = ghost.meters["restless"]
    world.facts["keepsake_missing_before"] = prop.attrs.get("place") != prop.attrs.get("home_place")


def find_keepsake(world: World, older: Entity, younger: Entity, keepsake: Keepsake) -> None:
    prop = world.get("keepsake")
    prop.attrs["found"] = keepsake.found_spot
    older.memes["pity"] += 1
    younger.memes["pity"] += 1
    world.say(
        f"They looked around together at last, and {older.id} spotted something {keepsake.material} glinting "
        f"{keepsake.found_spot}."
    )
    world.say(
        f"It was {keepsake.phrase}. The moon made it shine as if it had been waiting to be found."
    )


def make_peace(world: World, older: Entity, younger: Entity, quarrel: Quarrel, peace: PeaceAct) -> None:
    older.memes["guilt"] += 1
    younger.memes["guilt"] += 1
    older.memes["hurt"] = max(0.0, older.memes["hurt"] - 1)
    younger.memes["hurt"] = max(0.0, younger.memes["hurt"] - 1)
    older.memes["trust"] += 1
    younger.memes["trust"] += 1
    older.memes["cooperation"] += 1
    younger.memes["cooperation"] += 1
    world.say(peace.apology_line.replace("{older}", older.id).replace("{younger}", younger.id))
    world.say(peace.together_line.replace("{older}", older.id).replace("{younger}", younger.id))
    if quarrel.kind == "sharp_words":
        world.say(quarrel.hurt_line)
    elif quarrel.kind == "broken_promise":
        world.say(
            f"{older.id} could hear, now that the anger had thinned out, how lonely {younger.id} had felt."
        )
    else:
        world.say(
            f"The truth at last sounded smaller than the silence they had carried around all evening."
        )


def return_keepsake(world: World, older: Entity, younger: Entity, keepsake: Keepsake) -> None:
    prop = world.get("keepsake")
    prop.attrs["place"] = prop.attrs["home_place"]
    prop.meters["returned"] += 1
    world.say(
        f"Very gently, the two of them carried the keepsake back to {keepsake.return_spot}."
    )
    world.say(keepsake.memory_line)


def settle_ghost(world: World, older: Entity, younger: Entity, keepsake: Keepsake) -> None:
    ghost = world.get("ghost")
    pred = predict_settling(world)
    propagate(world, narrate=False)
    world.facts["predicted_settled"] = pred["settled"]
    world.say(
        f"At once the cold little shiver in the air softened. A pale shape, no scarier than moonlight on mist, "
        f"seemed to lift one hand in thanks."
    )
    if ghost.meters["peace"] >= THRESHOLD:
        world.say(
            f"Then the ghost of {keepsake.owner_name} faded like breath on a window, and the quiet no longer felt lonely."
        )
    world.say(
        f"{older.id} and {younger.id} stood close enough for their sleeves to touch, and neither one stepped away."
    )


def ending(world: World, older: Entity, younger: Entity, grandpa: Entity, place: RanchPlace) -> None:
    older.memes["relief"] += 1
    younger.memes["relief"] += 1
    world.say(
        f"When they walked back from {place.label}, they were carrying the blanket together instead of dragging it from opposite corners."
    )
    world.say(
        f"{grandpa.label_word.capitalize()} looked up from the porch and smiled when he saw them side by side."
    )
    world.say(
        f"Later, the ranch lay under the stars, wide and still, and the old place sounded like a home again."
    )


def tell(
    *,
    place: RanchPlace,
    keepsake: Keepsake,
    sign: GhostSign,
    quarrel: Quarrel,
    peace: PeaceAct,
    older_name: str,
    older_gender: str,
    younger_name: str,
    younger_gender: str,
    grandparent_type: str,
) -> World:
    world = World()
    older = world.add(Entity(id="older", kind="character", type=older_gender, label=older_name, role="older"))
    younger = world.add(Entity(id="younger", kind="character", type=younger_gender, label=younger_name, role="younger"))
    grandpa = world.add(
        Entity(id="grand", kind="character", type=grandparent_type, label="the grandparent", role="grandparent")
    )
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            label=f"the ghost of {keepsake.owner_name}",
            role="ghost",
            attrs={"owner_name": keepsake.owner_name, "owner_role": keepsake.owner_role},
        )
    )
    keepsake_ent = world.add(
        Entity(
            id="keepsake",
            kind="thing",
            type="keepsake",
            label=keepsake.label,
            role="keepsake",
            attrs={
                "home_place": keepsake.home_place,
                "place": "missing",
                "found": "",
            },
        )
    )

    older.memes["hurt"] = 1.0
    younger.memes["hurt"] = 1.0
    older.memes["trust"] = 0.0
    younger.memes["trust"] = 0.0
    older.memes["fear"] = 0.0
    younger.memes["fear"] = 0.0
    older.memes["cooperation"] = 0.0
    younger.memes["cooperation"] = 0.0
    ghost.meters["restless"] = 0.0
    ghost.meters["sadness"] = 0.0
    ghost.meters["peace"] = 0.0
    keepsake_ent.meters["returned"] = 0.0

    world.facts.update(
        place=place,
        keepsake_cfg=keepsake,
        sign=sign,
        quarrel=quarrel,
        peace=peace,
        older=older,
        younger=younger,
        grand=grandpa,
    )

    introduce(world, older, younger, grandpa, place, quarrel)
    send_errand(world, older, younger, grandpa, place)

    world.para()
    approach_haunting(world, older, younger, place, sign)
    notice_missing_keepsake(world, older, younger, keepsake, sign)
    find_keepsake(world, older, younger, keepsake)

    world.para()
    make_peace(world, older, younger, quarrel, peace)
    return_keepsake(world, older, younger, keepsake)
    settle_ghost(world, older, younger, keepsake)

    world.para()
    ending(world, older, younger, grandpa, place)

    world.facts.update(
        outcome="settled" if ghost.meters["peace"] >= THRESHOLD else "restless",
        reconciled=older.memes["peace"] >= THRESHOLD and younger.memes["peace"] >= THRESHOLD,
        returned=keepsake_ent.meters["returned"] >= THRESHOLD,
        ghost_peace=ghost.meters["peace"],
    )
    return world


PLACES = {
    "stable_loft": RanchPlace(
        id="stable_loft",
        label="the stable loft",
        approach="the corrals and the leaning stable",
        detail="Hay smelled sweet in the dark, and the horses shifted softly in their stalls.",
        hook="an old nail above the tack chest",
        tags={"stable", "ranch"},
    ),
    "windmill_shed": RanchPlace(
        id="windmill_shed",
        label="the windmill shed",
        approach="the pump house and the creaking windmill",
        detail="The blades turned slow as sleepy hands, and the boards answered with long wooden sighs.",
        hook="a peg by the water barrel",
        tags={"windmill", "ranch"},
    ),
    "porch_room": RanchPlace(
        id="porch_room",
        label="the screen porch room",
        approach="the lantern porch and the room beside it",
        detail="The screen door clicked in the breeze, and a rocker waited near the window as if someone had just risen from it.",
        hook="the carved chair back",
        tags={"porch", "ranch"},
    ),
}

KEEPSAKES = {
    "bell": Keepsake(
        id="bell",
        label="silver bell",
        phrase="a small silver bell on a leather thong",
        owner_name="Old Rosa",
        owner_role="horse trainer",
        home_place="stable_loft",
        material="silver",
        found_spot="under a drift of hay beside the tack chest",
        return_spot="the old nail above the tack chest",
        memory_line="Grandpa once said Old Rosa rang that bell before dawn so the horses would know her kind voice was near.",
        tags={"bell", "horse", "keepsake"},
    ),
    "bandanna": Keepsake(
        id="bandanna",
        label="red bandanna",
        phrase="a faded red bandanna stitched with tiny white stars",
        owner_name="Mister Vale",
        owner_role="night rider",
        home_place="windmill_shed",
        material="red cloth",
        found_spot="behind the water barrel where the moon reached in a thin stripe",
        return_spot="the peg by the water barrel",
        memory_line="People said Mister Vale tied that bandanna there after every late ride, so the ranch would know he had come home safe.",
        tags={"bandanna", "cloth", "keepsake"},
    ),
    "shawl_pin": Keepsake(
        id="shawl_pin",
        label="shawl pin",
        phrase="a moon-shaped shawl pin with a pearl in the middle",
        owner_name="Grandma June",
        owner_role="story keeper",
        home_place="porch_room",
        material="pearl",
        found_spot="under the old rocker where one white gleam kept winking",
        return_spot="the carved chair back",
        memory_line="Everyone on the ranch knew Grandma June used that pin when she told stories on windy nights, wrapping her shawl tight and smiling at every child on the steps.",
        tags={"shawl", "porch", "keepsake"},
    ),
}

SIGNS = {
    "hoofbeats": GhostSign(
        id="hoofbeats",
        place="stable_loft",
        sound="three soft hoofbeats tapped overhead, though every horse below was standing still",
        shimmer="a pale lantern-glow slipped over the loft rail and hovered by the empty hook",
        fear_line='"Did you hear that?" the older child breathed, and both of them forgot to be cross for one startled moment.',
        comfort_line="The glow did not rush at them. It waited, sad and patient, as if asking for help instead of trying to scare them.",
        tags={"ghost", "hoofbeats"},
    ),
    "windmill_song": GhostSign(
        id="windmill_song",
        place="windmill_shed",
        sound="the windmill began humming a tune too sweet and steady to be only wind",
        shimmer="a ribbon of pale light curled around the peg by the barrel",
        fear_line='The younger child grabbed the older one\'s sleeve before remembering they had been pretending not to need each other.',
        comfort_line="The humming sounded lonely more than mean, like someone waiting to be remembered.",
        tags={"ghost", "windmill"},
    ),
    "rocker_creak": GhostSign(
        id="rocker_creak",
        place="porch_room",
        sound="the old rocker gave one slow creak all by itself",
        shimmer="moonlight thickened in the chair until it almost looked like a sitting person made of pearl smoke",
        fear_line='Both children stood very still, because the room felt full of someone gentle and missing.',
        comfort_line="Nothing in the room felt angry. It felt like a story that had been interrupted in the middle.",
        tags={"ghost", "rocker"},
    ),
}

QUARRELS = {
    "sharp_words": Quarrel(
        id="sharp_words",
        label="mean words",
        kind="sharp_words",
        opening='"You always make everything your way," the younger child had snapped, and the older child had snapped back even harder.',
        hurt_line="The mean words sounded even uglier now that the night had gone quiet around them.",
        blame_text="They had hurt each other with sharp words.",
        remedy_tags={"apology", "gentle_words"},
        tags={"argument", "words"},
    ),
    "broken_promise": Quarrel(
        id="broken_promise",
        label="broken promise",
        kind="broken_promise",
        opening="The older child had promised to help brush the pony after supper, then run off to play, leaving the younger child to do the waiting alone.",
        hurt_line="A promise can be quiet when it breaks, but it still leaves a sore place.",
        blame_text="One had felt forgotten after a broken promise.",
        remedy_tags={"apology", "help_together"},
        tags={"promise", "help"},
    ),
    "borrowed_without_asking": Quarrel(
        id="borrowed_without_asking",
        label="borrowed without asking",
        kind="borrowed_without_asking",
        opening="The younger child had borrowed something special without asking, and the older child had answered with more anger than the mistake deserved.",
        hurt_line="Secrets and shouting had turned one small mistake into a big lonely silence.",
        blame_text="The trouble began with taking something without asking and answering it badly.",
        remedy_tags={"apology", "return", "truth"},
        tags={"borrowing", "truth"},
    ),
}

PEACE_ACTS = {
    "honest_apology": PeaceAct(
        id="honest_apology",
        sense=3,
        remedy_tags={"apology", "gentle_words"},
        apology_line='"I was wrong to talk to you that way," {older} said first. "{younger}, I made the dark feel bigger than it was."',
        together_line='{younger} let out a shaky breath. "I was wrong too," {younger} said. "Let\'s fix this together."',
        resolution_line="They chose the brave thing: telling the truth and being kind again.",
        qa_text="They apologized honestly and spoke kindly again.",
        tags={"apology"},
    ),
    "apology_and_help": PeaceAct(
        id="apology_and_help",
        sense=3,
        remedy_tags={"apology", "help_together"},
        apology_line='"I should have come back when I promised," {older} admitted. "You should not have had to wait by yourself."',
        together_line='"Then help me now," {younger} said, and {older} nodded at once.',
        resolution_line="The promise was not repaired by words alone, so they finished the hard part side by side.",
        qa_text="They apologized and then helped each other right away.",
        tags={"apology", "help"},
    ),
    "return_and_apologize": PeaceAct(
        id="return_and_apologize",
        sense=3,
        remedy_tags={"apology", "return", "truth"},
        apology_line='"I should have told the truth sooner," {younger} whispered. "And I should have listened before getting so mad," {older} answered.',
        together_line="This time neither child pulled away. They held the keepsake with four careful hands.",
        resolution_line="Returning what was taken mattered, and so did telling the truth about it.",
        qa_text="They told the truth, returned what had been mishandled, and apologized.",
        tags={"return", "truth"},
    ),
    "dare_the_ghost": PeaceAct(
        id="dare_the_ghost",
        sense=1,
        remedy_tags={"noise"},
        apology_line='"Bet it cannot catch us," one child said, trying to laugh.',
        together_line="They stomped the floorboards and made the night rougher instead of gentler.",
        resolution_line="Taunting a sad ghost is not a wise way to mend hearts.",
        qa_text="They tried to taunt the ghost.",
        tags={"taunt"},
    ),
}

GIRL_NAMES = ["Lila", "Nora", "Maya", "June", "Elsie", "Ruby", "Wren", "Clara"]
BOY_NAMES = ["Eli", "Toby", "Finn", "Silas", "Noah", "Cal", "Jesse", "Owen"]


@dataclass
class StoryParams:
    quarrel: str
    sign: str
    keepsake: str
    peace: str
    older_name: str
    older_gender: str
    younger_name: str
    younger_gender: str
    grandparent: str
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
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story with a spooky feeling and a spirit or haunting in it. In gentle ghost stories, the ghost is often sad or lonely instead of mean."
        )
    ],
    "ranch": [
        (
            "What is a ranch?",
            "A ranch is a big piece of land where people may raise horses or cattle and take care of barns, fences, and fields."
        )
    ],
    "bell": [
        (
            "Why would a ranch use a bell in a stable?",
            "A bell can help call animals or people, and its sound carries well. On a ranch, a familiar bell can also become part of a place's daily routine."
        )
    ],
    "windmill": [
        (
            "What does a windmill do on a ranch?",
            "A windmill uses moving air to turn its blades. On a ranch, that turning can help pump water from the ground."
        )
    ],
    "porch": [
        (
            "Why do porches creak?",
            "Wood swells and shrinks with weather and age, so old boards and chairs can creak when they move."
        )
    ],
    "apology": [
        (
            "What makes an apology real?",
            "A real apology says what was wrong and means it. It also tries to repair the hurt instead of only wishing the problem would go away."
        )
    ],
    "promise": [
        (
            "Why can a broken promise hurt feelings?",
            "A promise tells someone they can count on you. When it breaks, the other person can feel forgotten or unimportant."
        )
    ],
    "truth": [
        (
            "Why is telling the truth important after a mistake?",
            "Telling the truth helps people understand what really happened. It gives everyone a fair chance to fix the problem."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "ranch", "bell", "windmill", "porch", "apology", "promise", "truth"]


def generation_prompts(world: World) -> list[str]:
    quarrel = world.facts["quarrel"]
    keepsake = world.facts["keepsake_cfg"]
    place = world.facts["place"]
    older = world.facts["older"]
    younger = world.facts["younger"]
    return [
        (
            f'Write a gentle ghost story for a 3-to-5-year-old set on a ranch. '
            f'Include the word "feel-gerund" and let two children reconcile after a quarrel.'
        ),
        (
            f"Tell a moonlit ranch story where {older.label} and {younger.label} find {keepsake.phrase} at "
            f"{place.label}, and the haunting settles only when they mend a quarrel about {quarrel.label}."
        ),
        (
            f"Write a spooky-but-soft story with a ghostly sign, a missing keepsake, and an ending image that shows reconciliation instead of fear."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    older = world.facts["older"]
    younger = world.facts["younger"]
    place = world.facts["place"]
    keepsake = world.facts["keepsake_cfg"]
    sign = world.facts["sign"]
    quarrel = world.facts["quarrel"]
    peace = world.facts["peace"]
    grand = world.facts["grand"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {older.label} and {younger.label}, two children on their {grand.label_word}'s ranch. They begin the night hurt and quiet after a quarrel."
        ),
        (
            "Why did the ranch feel spooky?",
            f"It felt spooky because at {place.label} they heard {sign.sound} and saw {sign.shimmer}. The haunting seemed sad, which made the place eerie without feeling cruel."
        ),
        (
            f"What was missing at {place.label}?",
            f"{keepsake.phrase} was missing from its proper place. The empty hook made the children think the ghost was restless because something important had not been put back."
        ),
        (
            "How did the children find the keepsake?",
            f"They finally looked together instead of staying angry, and that is when they spotted it {keepsake.found_spot}. Working side by side changed the story, because the search only succeeded once they stopped acting alone."
        ),
        (
            "How did they make peace with each other?",
            f"{peace.qa_text} That mattered because the haunting was tied not only to the missing keepsake, but also to the hurt still sitting between them."
        ),
        (
            "Why did the ghost settle down?",
            f"The ghost settled after the keepsake was returned to {keepsake.return_spot} and the children reconciled. The ranch stopped feeling lonely because both the old object and the friendship were put right."
        ),
        (
            "How did the story end?",
            f"It ended with the children walking back together and their {grand.label_word} seeing them side by side. The final picture shows that the fear is gone and their quarrel is too."
        ),
    ]
    if quarrel.kind == "broken_promise":
        qa.append(
            (
                "Why was the broken promise important in the story?",
                f"The promise mattered because {younger.label} felt left alone, not merely annoyed. When {older.label} admitted that and helped right away, the apology became believable."
            )
        )
    elif quarrel.kind == "borrowed_without_asking":
        qa.append(
            (
                "Why did telling the truth help?",
                f"Telling the truth let both children see the mistake clearly instead of hiding behind anger and silence. Once the truth was spoken, returning the keepsake and forgiving each other became possible."
            )
        )
    else:
        qa.append(
            (
                "Why were the mean words a big problem?",
                f"Mean words can stay in a room even after voices go quiet. In the story, saying sorry changed the mood because it took that sharpness out of the night."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"ghost", "ranch"}
    keepsake = world.facts["keepsake_cfg"]
    quarrel = world.facts["quarrel"]
    if keepsake.id == "bell":
        tags.add("bell")
    if keepsake.home_place == "windmill_shed":
        tags.add("windmill")
    if keepsake.home_place == "porch_room":
        tags.add("porch")
    if "apology" in quarrel.remedy_tags:
        tags.add("apology")
    if quarrel.id == "broken_promise":
        tags.add("promise")
    if quarrel.id == "borrowed_without_asking":
        tags.add("truth")
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
        attrs = {k: v for k, v in e.attrs.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        bits_text = " ".join(bits)
        lines.append(f"  {e.id:8} ({e.type:12}) {bits_text}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quarrel="sharp_words",
        sign="hoofbeats",
        keepsake="bell",
        peace="honest_apology",
        older_name="Eli",
        older_gender="boy",
        younger_name="Ruby",
        younger_gender="girl",
        grandparent="grandfather",
    ),
    StoryParams(
        quarrel="broken_promise",
        sign="windmill_song",
        keepsake="bandanna",
        peace="apology_and_help",
        older_name="Nora",
        older_gender="girl",
        younger_name="Cal",
        younger_gender="boy",
        grandparent="grandmother",
    ),
    StoryParams(
        quarrel="borrowed_without_asking",
        sign="rocker_creak",
        keepsake="shawl_pin",
        peace="return_and_apologize",
        older_name="Silas",
        older_gender="boy",
        younger_name="June",
        younger_gender="girl",
        grandparent="grandmother",
    ),
]


ASP_RULES = r"""
sensible(P) :- peace(P), sense(P,S), sense_min(M), S >= M.
sign_matches(S,K) :- sign(S), keepsake(K), sign_place(S,Pl), home_place(K,Pl).
act_matches(Q,P) :- quarrel(Q), peace(P), needs(Q,T), fixes(P,T).
valid(Q,S,K,P) :- quarrel(Q), sign(S), keepsake(K), peace(P),
                  sensible(P), sign_matches(S,K), act_matches(Q,P).

outcome(settled) :- chosen_quarrel(Q), chosen_sign(S), chosen_keepsake(K), chosen_peace(P),
                    sensible(P), sign_matches(S,K), act_matches(Q,P).
outcome(restless) :- chosen_quarrel(Q), chosen_sign(S), chosen_keepsake(K), chosen_peace(P),
                     not outcome(settled).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for kid, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", kid))
        lines.append(asp.fact("home_place", kid, keepsake.home_place))
        for tag in sorted(keepsake.tags):
            lines.append(asp.fact("keepsake_tag", kid, tag))
    for sid, sign in SIGNS.items():
        lines.append(asp.fact("sign", sid))
        lines.append(asp.fact("sign_place", sid, sign.place))
    for qid, quarrel in QUARRELS.items():
        lines.append(asp.fact("quarrel", qid))
        for tag in sorted(quarrel.remedy_tags):
            lines.append(asp.fact("needs", qid, tag))
    for pid, peace in PEACE_ACTS.items():
        lines.append(asp.fact("peace", pid))
        lines.append(asp.fact("sense", pid, peace.sense))
        for tag in sorted(peace.remedy_tags):
            lines.append(asp.fact("fixes", pid, tag))
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
    return sorted(p for (p,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_quarrel", params.quarrel),
            asp.fact("chosen_sign", params.sign),
            asp.fact("chosen_keepsake", params.keepsake),
            asp.fact("chosen_peace", params.peace),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle ghost-story world on a ranch: two children, a missing keepsake, and reconciliation."
    )
    ap.add_argument("--quarrel", choices=QUARRELS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--peace", choices=PEACE_ACTS)
    ap.add_argument("--older-gender", choices=["girl", "boy"])
    ap.add_argument("--younger-gender", choices=["girl", "boy"])
    ap.add_argument("--older-name")
    ap.add_argument("--younger-name")
    ap.add_argument("--grandparent", choices=["grandfather", "grandmother"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.peace and PEACE_ACTS[args.peace].sense < SENSE_MIN:
        raise StoryError(explain_peace_rejection(args.peace))
    if args.quarrel and args.sign and args.keepsake and args.peace:
        quarrel = QUARRELS[args.quarrel]
        sign = SIGNS[args.sign]
        keepsake = KEEPSAKES[args.keepsake]
        peace = PEACE_ACTS[args.peace]
        if peace.sense < SENSE_MIN or not sign_matches(sign, keepsake) or not act_matches(quarrel, peace):
            raise StoryError(explain_combo_rejection(quarrel, sign, keepsake, peace))

    combos = [
        combo
        for combo in valid_combos()
        if (args.quarrel is None or combo[0] == args.quarrel)
        and (args.sign is None or combo[1] == args.sign)
        and (args.keepsake is None or combo[2] == args.keepsake)
        and (args.peace is None or combo[3] == args.peace)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quarrel, sign, keepsake, peace = rng.choice(sorted(combos))
    older_gender = args.older_gender or rng.choice(["girl", "boy"])
    younger_gender = args.younger_gender or rng.choice(["girl", "boy"])
    older_name = args.older_name or _pick_name(rng, older_gender)
    younger_name = args.younger_name or _pick_name(rng, younger_gender, avoid=older_name)
    grandparent = args.grandparent or rng.choice(["grandfather", "grandmother"])
    return StoryParams(
        quarrel=quarrel,
        sign=sign,
        keepsake=keepsake,
        peace=peace,
        older_name=older_name,
        older_gender=older_gender,
        younger_name=younger_name,
        younger_gender=younger_gender,
        grandparent=grandparent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quarrel not in QUARRELS:
        raise StoryError(f"(Unknown quarrel '{params.quarrel}'.)")
    if params.sign not in SIGNS:
        raise StoryError(f"(Unknown sign '{params.sign}'.)")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Unknown keepsake '{params.keepsake}'.)")
    if params.peace not in PEACE_ACTS:
        raise StoryError(f"(Unknown peace act '{params.peace}'.)")

    quarrel = QUARRELS[params.quarrel]
    sign = SIGNS[params.sign]
    keepsake = KEEPSAKES[params.keepsake]
    peace = PEACE_ACTS[params.peace]

    if peace.sense < SENSE_MIN:
        raise StoryError(explain_peace_rejection(params.peace))
    if not sign_matches(sign, keepsake) or not act_matches(quarrel, peace):
        raise StoryError(explain_combo_rejection(quarrel, sign, keepsake, peace))

    place = PLACES[keepsake.home_place]
    world = tell(
        place=place,
        keepsake=keepsake,
        sign=sign,
        quarrel=quarrel,
        peace=peace,
        older_name=params.older_name,
        older_gender=params.older_gender,
        younger_name=params.younger_name,
        younger_gender=params.younger_gender,
        grandparent_type=params.grandparent,
    )
    return StorySample(
        params=params,
        story=world.render().replace("older", params.older_name).replace("younger", params.younger_name),
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

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid_combos() matches clingo ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    python_sensible = {p.id for p in sensible_peace_acts()}
    clingo_sensible = set(asp_sensible())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible peace acts match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible peace acts: python={sorted(python_sensible)} clingo={sorted(clingo_sensible)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(25):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test story came out empty.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible peace acts: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quarrel, sign, keepsake, peace) combos:\n")
        for quarrel, sign, keepsake, peace in combos:
            print(f"  {quarrel:22} {sign:14} {keepsake:10} {peace}")
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
            header = f"### {p.older_name} & {p.younger_name}: {p.keepsake} at {KEEPSAKES[p.keepsake].home_place} ({p.quarrel}, {p.peace})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
