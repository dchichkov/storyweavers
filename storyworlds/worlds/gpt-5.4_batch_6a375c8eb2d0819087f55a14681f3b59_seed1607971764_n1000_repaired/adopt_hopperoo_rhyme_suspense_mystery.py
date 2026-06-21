#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/adopt_hopperoo_rhyme_suspense_mystery.py
===================================================================

A standalone story world for a gentle mystery: at an adoption fair, a shy
hopperoo slips away, a child follows a trail of clues and remembers a rhyming
care-card, and the family ends by choosing to adopt the little creature.

The world is constraint-checked. A story is only generated when:
- the venue can plausibly contain the chosen hideout,
- the hideout suits the chosen kind of hopperoo,
- and the comfort item is the one that would honestly calm that hopperoo.

Run it
------
    python storyworlds/worlds/gpt-5.4/adopt_hopperoo_rhyme_suspense_mystery.py
    python storyworlds/worlds/gpt-5.4/adopt_hopperoo_rhyme_suspense_mystery.py --venue library --hopperoo moon --hideout reading_nook
    python storyworlds/worlds/gpt-5.4/adopt_hopperoo_rhyme_suspense_mystery.py --comfort clover_bundle
    python storyworlds/worlds/gpt-5.4/adopt_hopperoo_rhyme_suspense_mystery.py --all
    python storyworlds/worlds/gpt-5.4/adopt_hopperoo_rhyme_suspense_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/adopt_hopperoo_rhyme_suspense_mystery.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/adopt_hopperoo_rhyme_suspense_mystery.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Venue:
    id: str
    label: str
    phrase: str
    mood: str
    affords: set[str] = field(default_factory=set)
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
class HopperooKind:
    id: str
    label: str
    phrase: str
    coat: str
    clue_sign: str
    comfort: str
    rhyme: str
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
    suspense: str
    clue: str
    exposed: bool = False
    venues: set[str] = field(default_factory=set)
    suits: set[str] = field(default_factory=set)
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
    action: str
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


class World:
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
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
        clone = World(self.venue)
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


def _r_cold(world: World) -> list[str]:
    out: list[str] = []
    hopperoo = world.get("hopperoo")
    hideout = world.facts["hideout_cfg"]
    delay = world.facts["delay"]
    if hopperoo.meters["hidden"] < THRESHOLD:
        return out
    if not hideout.exposed or delay <= 0:
        return out
    sig = ("cold", hideout.id, delay)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hopperoo.meters["cold"] += 1
    world.get("child").memes["worry"] += 1
    out.append("__cold__")
    return out


def _r_emerge(world: World) -> list[str]:
    out: list[str] = []
    hopperoo = world.get("hopperoo")
    if hopperoo.meters["hidden"] < THRESHOLD:
        return out
    if hopperoo.meters["comfort_match"] < THRESHOLD:
        return out
    sig = ("emerge", world.facts["hopperoo_cfg"].id, world.facts["hideout_cfg"].id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hopperoo.meters["hidden"] = 0.0
    hopperoo.meters["found"] += 1
    hopperoo.memes["trust"] += 1
    world.get("child").memes["relief"] += 1
    out.append("__emerge__")
    return out


def _r_adopt(world: World) -> list[str]:
    out: list[str] = []
    hopperoo = world.get("hopperoo")
    if hopperoo.meters["found"] < THRESHOLD or hopperoo.memes["trust"] < THRESHOLD:
        return out
    sig = ("adopt", hopperoo.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hopperoo.meters["adopted"] += 1
    hopperoo.memes["belonging"] += 1
    world.get("child").memes["belonging"] += 1
    out.append("__adopt__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="cold", tag="physical", apply=_r_cold),
    Rule(name="emerge", tag="social", apply=_r_emerge),
    Rule(name="adopt", tag="social", apply=_r_adopt),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def valid_combo(venue_id: str, hopperoo_id: str, hideout_id: str, comfort_id: str) -> bool:
    if venue_id not in VENUES or hopperoo_id not in HOPPEROOS or hideout_id not in HIDEOUTS or comfort_id not in COMFORTS:
        return False
    venue = VENUES[venue_id]
    hopperoo = HOPPEROOS[hopperoo_id]
    hideout = HIDEOUTS[hideout_id]
    return (
        hideout_id in venue.affords
        and venue_id in hideout.venues
        and hopperoo_id in hideout.suits
        and comfort_id == hopperoo.comfort
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for venue_id in sorted(VENUES):
        for hopperoo_id in sorted(HOPPEROOS):
            for hideout_id in sorted(HIDEOUTS):
                comfort_id = HOPPEROOS[hopperoo_id].comfort
                if valid_combo(venue_id, hopperoo_id, hideout_id, comfort_id):
                    combos.append((venue_id, hopperoo_id, hideout_id, comfort_id))
    return combos


def story_outcome(hideout: Hideout, delay: int) -> str:
    return "chilled" if hideout.exposed and delay > 0 else "cozy"


def predict_search(venue: Venue, hopperoo_cfg: HopperooKind, hideout_cfg: Hideout,
                   comfort_cfg: Comfort, delay: int) -> dict:
    sim = World(venue)
    child = sim.add(Entity(id="child", kind="character", type="girl", label="the child"))
    sim.add(Entity(id="hopperoo", type="hopperoo", label=hopperoo_cfg.label))
    sim.facts["hideout_cfg"] = hideout_cfg
    sim.facts["hopperoo_cfg"] = hopperoo_cfg
    sim.facts["comfort_cfg"] = comfort_cfg
    sim.facts["delay"] = delay
    sim.get("hopperoo").meters["hidden"] = 1.0
    child.memes["worry"] = 0.0
    propagate(sim, narrate=False)
    sim.get("hopperoo").meters["comfort_match"] = 1.0 if comfort_cfg.id == hopperoo_cfg.comfort else 0.0
    propagate(sim, narrate=False)
    return {
        "cold": sim.get("hopperoo").meters["cold"] >= THRESHOLD,
        "found": sim.get("hopperoo").meters["found"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, parent: Entity, volunteer: Entity,
              hopperoo_cfg: HopperooKind) -> None:
    child.memes["hope"] += 1
    world.say(
        f"On a dusky afternoon, {child.id} went with {child.pronoun('possessive')} "
        f"{parent.label_word} to {world.venue.phrase}, where a rescue volunteer was "
        f"helping families adopt gentle little animals."
    )
    world.say(
        f"The room felt like a mystery book with the pages half-turned: "
        f"{world.venue.mood}."
    )
    world.say(
        f"At the smallest basket sat {hopperoo_cfg.phrase}, {hopperoo_cfg.coat}. "
        f'{volunteer.id} smiled and whispered, "This is a {hopperoo_cfg.label}."'
    )


def rhyme_card(world: World, volunteer: Entity, hopperoo_cfg: HopperooKind) -> None:
    world.say(
        f"{volunteer.id} lifted the care card tied to the basket and read it aloud "
        f"like a secret poem: \"{hopperoo_cfg.rhyme}\""
    )


def vanish(world: World, child: Entity, parent: Entity, hopperoo_cfg: HopperooKind) -> None:
    hopperoo = world.get("hopperoo")
    hopperoo.meters["hidden"] = 1.0
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    world.say(
        f"Then someone opened a side door, a draft slid across the floor, and the "
        f"basket gave a tiny wobble. When {child.id} looked back, the "
        f"{hopperoo_cfg.label} was gone."
    )
    world.say(
        f'"Where did it go?" {child.id} asked. Even {parent.label_word} lowered '
        f"{parent.pronoun('possessive')} voice, as if the answer might be hiding in the dark."
    )


def inspect_clue(world: World, child: Entity, hideout_cfg: Hideout, hopperoo_cfg: HopperooKind,
                 comfort_cfg: Comfort) -> None:
    pred = predict_search(world.venue, hopperoo_cfg, hideout_cfg, comfort_cfg, world.facts["delay"])
    world.facts["predicted_cold"] = pred["cold"]
    world.say(
        f"Near the empty basket lay {hopperoo_cfg.clue_sign}. A little farther on, "
        f"{hideout_cfg.clue}."
    )
    world.say(
        f"{child.id} remembered the rhyme and followed the trail slowly, one careful "
        f"step at a time."
    )


def suspense_search(world: World, child: Entity, hideout_cfg: Hideout) -> None:
    world.say(
        f"The trail led toward {hideout_cfg.phrase}. {hideout_cfg.suspense}"
    )
    if hideout_cfg.exposed:
        world.say(
            "The air there felt cooler, and the mystery suddenly seemed more urgent."
        )


def offer_comfort(world: World, child: Entity, comfort_cfg: Comfort, hideout_cfg: Hideout) -> None:
    hopperoo = world.get("hopperoo")
    hopperoo.meters["comfort_match"] = 1.0
    child.memes["kindness"] += 1
    world.say(
        f"{child.id} did not grab or shout. Instead, {child.pronoun()} {comfort_cfg.action} "
        f"near {hideout_cfg.label} and waited."
    )
    propagate(world, narrate=False)


def reveal(world: World, child: Entity, hopperoo_cfg: HopperooKind, hideout_cfg: Hideout) -> None:
    hopperoo = world.get("hopperoo")
    if hopperoo.meters["found"] < THRESHOLD:
        raise StoryError("(Story failed: the hopperoo never came out.)")
    if hopperoo.meters["cold"] >= THRESHOLD:
        world.say(
            f"For one breath, nothing moved. Then two bright eyes blinked from the shadows, "
            f"and the {hopperoo_cfg.label} gave a soft hop into the open. Its whiskers trembled, "
            f"and {child.id} could see it had been getting chilly out there."
        )
    else:
        world.say(
            f"For one breath, nothing moved. Then two bright eyes blinked from the shadows, "
            f"and the {hopperoo_cfg.label} gave a soft hop into the open."
        )
    world.say(
        f"It came from {hideout_cfg.label} not because anyone chased it, but because "
        f"someone had finally offered the one gentle thing it trusted."
    )


def warm_if_needed(world: World, child: Entity, parent: Entity, comfort_cfg: Comfort) -> None:
    hopperoo = world.get("hopperoo")
    if hopperoo.meters["cold"] < THRESHOLD:
        return
    hopperoo.meters["cold"] = 0.0
    hopperoo.memes["calm"] += 1
    world.say(
        f"{parent.label_word.capitalize()} wrapped the little creature in {comfort_cfg.phrase}, "
        f"and {child.id} stroked its tiny back until the shiver went out of it."
    )


def adopt_scene(world: World, child: Entity, parent: Entity, volunteer: Entity,
                hopperoo_cfg: HopperooKind) -> None:
    propagate(world, narrate=False)
    hopperoo = world.get("hopperoo")
    if hopperoo.meters["adopted"] < THRESHOLD:
        raise StoryError("(Story failed: adoption state did not complete.)")
    world.say(
        f'{volunteer.id} let out a relieved laugh. "You found the little {hopperoo_cfg.label}," '
        f"{volunteer.pronoun()} said. \"And you found it the right way.\""
    )
    world.say(
        f"When {child.id} asked whether anyone had chosen this hopperoo yet, "
        f"{volunteer.id} shook {volunteer.pronoun('possessive')} head."
    )
    world.say(
        f"{parent.label_word.capitalize()} looked at the hopperoo, then at {child.id}. "
        f'"Shall we adopt it?" {parent.pronoun()} asked.'
    )
    world.say(
        f"{child.id} nodded so fast that the mystery turned into joy. The hopperoo "
        f"pressed close against {child.pronoun('possessive')} sleeve as if it had "
        f"been waiting for that answer."
    )


def ending_image(world: World, child: Entity, hopperoo_cfg: HopperooKind) -> None:
    if world.facts["outcome"] == "chilled":
        world.say(
            f"By the time they stepped into the evening, the once-hidden {hopperoo_cfg.label} "
            f"was warm in its new basket, and {child.id} kept softly repeating the rhyme that "
            f"had brought it home."
        )
    else:
        world.say(
            f"By the time they stepped into the evening, the once-hidden {hopperoo_cfg.label} "
            f"was tucked into its new basket, and {child.id} kept softly repeating the rhyme "
            f"that had solved the mystery."
        )


def tell(venue: Venue, hopperoo_cfg: HopperooKind, hideout_cfg: Hideout, comfort_cfg: Comfort,
         child_name: str = "Mina", child_gender: str = "girl", parent_type: str = "mother",
         volunteer_name: str = "Mrs. Vale", delay: int = 0) -> World:
    world = World(venue)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        attrs={},
    ))
    volunteer = world.add(Entity(
        id=volunteer_name,
        kind="character",
        type="woman",
        label=volunteer_name,
        role="volunteer",
        attrs={},
    ))
    hopperoo = world.add(Entity(
        id="hopperoo",
        type="hopperoo",
        label=hopperoo_cfg.label,
        phrase=hopperoo_cfg.phrase,
        role="pet",
        attrs={"comfort": hopperoo_cfg.comfort},
    ))

    child.memes["worry"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["kindness"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["belonging"] = 0.0
    hopperoo.meters["hidden"] = 0.0
    hopperoo.meters["comfort_match"] = 0.0
    hopperoo.meters["found"] = 0.0
    hopperoo.meters["cold"] = 0.0
    hopperoo.meters["adopted"] = 0.0
    hopperoo.memes["trust"] = 0.0
    hopperoo.memes["belonging"] = 0.0
    hopperoo.memes["calm"] = 0.0

    world.facts["venue"] = venue
    world.facts["hopperoo_cfg"] = hopperoo_cfg
    world.facts["hideout_cfg"] = hideout_cfg
    world.facts["comfort_cfg"] = comfort_cfg
    world.facts["delay"] = delay
    world.facts["outcome"] = story_outcome(hideout_cfg, delay)

    introduce(world, child, parent, volunteer, hopperoo_cfg)
    rhyme_card(world, volunteer, hopperoo_cfg)

    world.para()
    vanish(world, child, parent, hopperoo_cfg)
    inspect_clue(world, child, hideout_cfg, hopperoo_cfg, comfort_cfg)
    suspense_search(world, child, hideout_cfg)

    propagate(world, narrate=False)

    world.para()
    offer_comfort(world, child, comfort_cfg, hideout_cfg)
    reveal(world, child, hopperoo_cfg, hideout_cfg)
    warm_if_needed(world, child, parent, comfort_cfg)

    world.para()
    adopt_scene(world, child, parent, volunteer, hopperoo_cfg)
    ending_image(world, child, hopperoo_cfg)

    world.facts.update(
        child=child,
        parent=parent,
        volunteer=volunteer,
        hopperoo=hopperoo,
        found=hopperoo.meters["found"] >= THRESHOLD,
        adopted=hopperoo.meters["adopted"] >= THRESHOLD,
    )
    return world


VENUES = {
    "library": Venue(
        id="library",
        label="library",
        phrase="the library's evening adoption fair",
        mood="lamplight pooled between tall shelves, and every cart cast a long quiet shadow",
        affords={"reading_nook", "coat_cubby"},
    ),
    "greenhouse": Venue(
        id="greenhouse",
        label="greenhouse",
        phrase="the greenhouse adoption fair",
        mood="glass panes clicked overhead, and leaf-shadows trembled over the stone path",
        affords={"fern_bench", "potting_shelf"},
    ),
    "town_hall": Venue(
        id="town_hall",
        label="town hall",
        phrase="the town hall adoption fair",
        mood="paper lanterns glowed over folding tables, and the long curtain by the entry fluttered whenever the door sighed open",
        affords={"boot_rack", "wagon"},
    ),
}

HOPPEROOS = {
    "moon": HopperooKind(
        id="moon",
        label="moon hopperoo",
        phrase="a moon hopperoo",
        coat="with silver-gray fur and round ears like little commas",
        clue_sign="a pinch of silver paper stars",
        comfort="paper_star_lantern",
        rhyme="If corners dim and shadows swoop, hold up a star for one shy hop-loop.",
        tags={"hopperoo", "lantern", "mystery"},
    ),
    "moss": HopperooKind(
        id="moss",
        label="moss hopperoo",
        phrase="a moss hopperoo",
        coat="with green-flecked fur and paws soft as velvet leaves",
        clue_sign="three bitten clover stems",
        comfort="clover_bundle",
        rhyme="When leaves lie still and whispers blow, bring clover where the cool ferns grow.",
        tags={"hopperoo", "clover", "mystery"},
    ),
    "puddle": HopperooKind(
        id="puddle",
        label="puddle hopperoo",
        phrase="a puddle hopperoo",
        coat="with speckled paws and a damp little nose",
        clue_sign="a dotted trail of dark wet prints",
        comfort="warm_towel",
        rhyme="If raindrop paws go swish-swish through, a warm dry towel will call me to you.",
        tags={"hopperoo", "towel", "mystery"},
    ),
}

HIDEOUTS = {
    "reading_nook": Hideout(
        id="reading_nook",
        label="the reading nook",
        phrase="the reading nook behind a crescent-moon beanbag",
        suspense="The blanket there made a small cave, and something inside gave the faintest rustle.",
        clue="a bent bookmark pointed toward the reading nook",
        exposed=False,
        venues={"library"},
        suits={"moon"},
        tags={"books", "quiet"},
    ),
    "coat_cubby": Hideout(
        id="coat_cubby",
        label="the coat cubby",
        phrase="the coat cubby beside the front desk",
        suspense="One dangling scarf swayed even though nobody had brushed past it.",
        clue="a silver star clung to the edge of the cubby",
        exposed=True,
        venues={"library"},
        suits={"moon"},
        tags={"coats", "draft"},
    ),
    "fern_bench": Hideout(
        id="fern_bench",
        label="the fern bench",
        phrase="the fern bench where fronds spilled almost to the floor",
        suspense="The fronds trembled once, then went still, as if the plants were trying to keep a secret.",
        clue="a trail of nibbled clover led between the pots",
        exposed=False,
        venues={"greenhouse"},
        suits={"moss"},
        tags={"plants"},
    ),
    "potting_shelf": Hideout(
        id="potting_shelf",
        label="the potting shelf",
        phrase="the low potting shelf by the misting cans",
        suspense="A wooden tray gave a tiny scrape from somewhere behind the seed packets.",
        clue="loose soil was pattered with neat little half-moon tracks",
        exposed=True,
        venues={"greenhouse"},
        suits={"moss"},
        tags={"soil"},
    ),
    "boot_rack": Hideout(
        id="boot_rack",
        label="the boot rack",
        phrase="the boot rack near the rainy entry",
        suspense="A lace twitched once in the dark gap beneath the bench.",
        clue="the wet pawprints stopped beside the boot rack",
        exposed=True,
        venues={"town_hall"},
        suits={"puddle"},
        tags={"boots"},
    ),
    "wagon": Hideout(
        id="wagon",
        label="the red wagon",
        phrase="the red wagon parked behind a table of pet bowls",
        suspense="Its blanket was mounded in the middle, though no wind was blowing there.",
        clue="a tiny damp nose-print shone on the side of the wagon",
        exposed=False,
        venues={"town_hall"},
        suits={"puddle"},
        tags={"wagon"},
    ),
}

COMFORTS = {
    "paper_star_lantern": Comfort(
        id="paper_star_lantern",
        label="paper star lantern",
        phrase="the paper star lantern",
        action="set the paper star lantern on the floor so its glow fell softly",
        tags={"lantern", "light"},
    ),
    "clover_bundle": Comfort(
        id="clover_bundle",
        label="bundle of clover",
        phrase="the bundle of clover",
        action="laid the bundle of clover down gently",
        tags={"clover", "plant"},
    ),
    "warm_towel": Comfort(
        id="warm_towel",
        label="warm towel",
        phrase="the warm towel",
        action="folded the warm towel into a little nest",
        tags={"towel", "warmth"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Tessa", "June", "Wren", "Ella"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Ben", "Finn", "Eli", "Noah", "Jasper"]
VOLUNTEER_NAMES = ["Mrs. Vale", "Ms. Rowan", "Auntie Fern"]
TRAITS = ["patient", "careful", "gentle", "curious"]


@dataclass
class StoryParams:
    venue: str
    hopperoo: str
    hideout: str
    comfort: str
    child_name: str
    child_gender: str
    parent: str
    volunteer_name: str
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


CURATED = [
    StoryParams(
        venue="library",
        hopperoo="moon",
        hideout="reading_nook",
        comfort="paper_star_lantern",
        child_name="Mina",
        child_gender="girl",
        parent="mother",
        volunteer_name="Mrs. Vale",
        trait="patient",
        delay=0,
    ),
    StoryParams(
        venue="greenhouse",
        hopperoo="moss",
        hideout="fern_bench",
        comfort="clover_bundle",
        child_name="Theo",
        child_gender="boy",
        parent="father",
        volunteer_name="Ms. Rowan",
        trait="gentle",
        delay=0,
    ),
    StoryParams(
        venue="town_hall",
        hopperoo="puddle",
        hideout="boot_rack",
        comfort="warm_towel",
        child_name="June",
        child_gender="girl",
        parent="mother",
        volunteer_name="Auntie Fern",
        trait="careful",
        delay=1,
    ),
    StoryParams(
        venue="library",
        hopperoo="moon",
        hideout="coat_cubby",
        comfort="paper_star_lantern",
        child_name="Eli",
        child_gender="boy",
        parent="father",
        volunteer_name="Mrs. Vale",
        trait="curious",
        delay=1,
    ),
    StoryParams(
        venue="town_hall",
        hopperoo="puddle",
        hideout="wagon",
        comfort="warm_towel",
        child_name="Lila",
        child_gender="girl",
        parent="mother",
        volunteer_name="Ms. Rowan",
        trait="patient",
        delay=0,
    ),
]


KNOWLEDGE = {
    "adopt": [
        (
            "What does adopt mean?",
            "To adopt an animal means you welcome it into your family and promise to care for it every day. It gets a safe home, food, and love."
        )
    ],
    "hopperoo": [
        (
            "What is a hopperoo in this story world?",
            "A hopperoo is a tiny hopping rescue pet with a shy nature and special comforts that help it feel safe. Different hopperoos trust different gentle things."
        )
    ],
    "mystery": [
        (
            "What makes something feel like a mystery?",
            "A mystery begins when you do not know the answer yet and must follow clues to find it. Quiet places, careful looking, and one hidden fact can make a story feel mysterious."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme uses words with matching ending sounds, like 'still' and 'hill' or 'slow' and 'glow.' Rhymes can help people remember important things."
        )
    ],
    "lantern": [
        (
            "Why can a soft lantern help a shy animal?",
            "A soft lantern gives light without sudden grabbing or loud noise. That can make a nervous animal feel safer about coming out."
        )
    ],
    "clover": [
        (
            "Why would clover calm a small animal?",
            "A familiar smell can help a frightened animal trust a place again. If clover is something it likes, the scent tells it that gentle care is nearby."
        )
    ],
    "towel": [
        (
            "Why does a warm towel help after a chilly or wet wait?",
            "A warm towel gives heat and comfort. That helps a small body stop shivering and feel safe."
        )
    ],
}
KNOWLEDGE_ORDER = ["adopt", "hopperoo", "mystery", "rhyme", "lantern", "clover", "towel"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hopperoo_cfg = f["hopperoo_cfg"]
    hideout_cfg = f["hideout_cfg"]
    comfort_cfg = f["comfort_cfg"]
    child = f["child"]
    return [
        f'Write a gentle mystery for a 3-to-5-year-old that includes the words "adopt" and "hopperoo" and uses rhyme as an important clue.',
        f"Tell a suspenseful but child-safe story where {child.id} follows clues to find a missing {hopperoo_cfg.label} hiding in {hideout_cfg.label}, then helps the family adopt it.",
        f"Write a short mystery in which a rhyming care-card leads a child to calm a shy hopperoo with {comfort_cfg.phrase} and bring it home.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    volunteer = f["volunteer"]
    hopperoo = f["hopperoo"]
    hopperoo_cfg = f["hopperoo_cfg"]
    hideout_cfg = f["hideout_cfg"]
    comfort_cfg = f["comfort_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {parent.label_word}, {volunteer.id}, and a shy {hopperoo_cfg.label} at an adoption fair."
        ),
        (
            f"What mystery had to be solved?",
            f"The mystery was where the missing hopperoo had gone after it slipped away from its basket. {child.id} had to follow clues instead of guessing."
        ),
        (
            f"How did the rhyme help {child.id}?",
            f"The rhyme told {child.pronoun('object')} what gentle comfort the hopperoo trusted. Because {child.id} remembered that clue, {child.pronoun()} could offer the right thing instead of scaring it."
        ),
        (
            f"Why did the hopperoo come out of {hideout_cfg.label}?",
            f"It came out because {child.id} used {comfort_cfg.phrase}, which matched what that hopperoo needed to feel safe. The child waited quietly, so the little animal chose to trust {child.pronoun('object')}."
        ),
    ]
    if f["outcome"] == "chilled":
        qa.append(
            (
                "Was there any danger while the hopperoo was missing?",
                f"Yes, a small one. The hideout was a cooler, more open place, so the hopperoo had started to get chilly while it stayed hidden. That is why the warm care afterward mattered."
            )
        )
    else:
        qa.append(
            (
                "What made the search feel suspenseful but safe?",
                f"The hideout was dark and quiet, and each clue led deeper into the mystery. But the grown-ups stayed close, and {child.id} moved carefully, so the search never became dangerous."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the family deciding to adopt the hopperoo. The last image shows the once-hidden little creature resting in its new basket on the way home."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"adopt", "hopperoo", "mystery", "rhyme"}
    comfort_cfg = world.facts["comfort_cfg"]
    if comfort_cfg.id == "paper_star_lantern":
        tags.add("lantern")
    if comfort_cfg.id == "clover_bundle":
        tags.add("clover")
    if comfort_cfg.id == "warm_towel":
        tags.add("towel")
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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(
        f"  outcome={world.facts.get('outcome')} predicted_cold={world.facts.get('predicted_cold')}"
    )
    return "\n".join(lines)


def explain_rejection(venue_id: str, hopperoo_id: str, hideout_id: str, comfort_id: str) -> str:
    if venue_id in VENUES and hideout_id in HIDEOUTS:
        venue = VENUES[venue_id]
        hideout = HIDEOUTS[hideout_id]
        if hideout_id not in venue.affords or venue_id not in hideout.venues:
            return (
                f"(No story: {hideout.label} does not belong in {venue.label}, so the mystery would feel fake. "
                f"Pick a hideout that the venue really affords.)"
            )
    if hopperoo_id in HOPPEROOS and hideout_id in HIDEOUTS:
        hopperoo_cfg = HOPPEROOS[hopperoo_id]
        hideout = HIDEOUTS[hideout_id]
        if hopperoo_id not in hideout.suits:
            return (
                f"(No story: a {hopperoo_cfg.label} would not sensibly hide in {hideout.label}. "
                f"The clue trail and comfort logic would not match.)"
            )
    if hopperoo_id in HOPPEROOS and comfort_id in COMFORTS:
        hopperoo_cfg = HOPPEROOS[hopperoo_id]
        comfort_cfg = COMFORTS[comfort_id]
        if comfort_id != hopperoo_cfg.comfort:
            needed = COMFORTS[hopperoo_cfg.comfort].label
            return (
                f"(No story: {comfort_cfg.label} would not be the honest way to calm a {hopperoo_cfg.label}. "
                f"Try the comfort it actually trusts: {needed}.)"
            )
    return "(No story: the chosen options do not make a reasonable hopperoo mystery.)"


ASP_RULES = r"""
valid(V,H,P,C) :- venue(V), hopperoo(H), hideout(P), comfort(C),
                  affords(V,P), hideout_in(P,V), suits(P,H), calms(C,H).

chilled :- chosen_hideout(P), exposed(P), delay(D), D > 0.
outcome(chilled) :- chilled.
outcome(cozy) :- not chilled.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for venue_id, venue in VENUES.items():
        lines.append(asp.fact("venue", venue_id))
        for hideout_id in sorted(venue.affords):
            lines.append(asp.fact("affords", venue_id, hideout_id))
    for hopperoo_id, hopperoo_cfg in HOPPEROOS.items():
        lines.append(asp.fact("hopperoo", hopperoo_id))
        lines.append(asp.fact("calms", hopperoo_cfg.comfort, hopperoo_id))
    for hideout_id, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hideout_id))
        for venue_id in sorted(hideout.venues):
            lines.append(asp.fact("hideout_in", hideout_id, venue_id))
        for hopperoo_id in sorted(hideout.suits):
            lines.append(asp.fact("suits", hideout_id, hopperoo_id))
        if hideout.exposed:
            lines.append(asp.fact("exposed", hideout_id))
    for comfort_id in COMFORTS:
        lines.append(asp.fact("comfort", comfort_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join(
        [
            asp.fact("chosen_hideout", params.hideout),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != story_outcome(HIDEOUTS[params.hideout], params.delay):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification surface
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a rhyming hopperoo mystery that ends in adoption. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--hopperoo", choices=HOPPEROOS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the little mystery lasts before the clue is solved")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.venue and args.hopperoo and args.hideout and args.comfort:
        if not valid_combo(args.venue, args.hopperoo, args.hideout, args.comfort):
            raise StoryError(explain_rejection(args.venue, args.hopperoo, args.hideout, args.comfort))

    combos = [
        combo for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.hopperoo is None or combo[1] == args.hopperoo)
        and (args.hideout is None or combo[2] == args.hideout)
        and (args.comfort is None or combo[3] == args.comfort)
    ]
    if not combos:
        venue_id = args.venue or next(iter(VENUES))
        hopperoo_id = args.hopperoo or next(iter(HOPPEROOS))
        hideout_id = args.hideout or next(iter(HIDEOUTS))
        comfort_id = args.comfort or HOPPEROOS[hopperoo_id].comfort
        raise StoryError(explain_rejection(venue_id, hopperoo_id, hideout_id, comfort_id))

    venue_id, hopperoo_id, hideout_id, comfort_id = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    volunteer_name = rng.choice(VOLUNTEER_NAMES)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        venue=venue_id,
        hopperoo=hopperoo_id,
        hideout=hideout_id,
        comfort=comfort_id,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent,
        volunteer_name=volunteer_name,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.venue not in VENUES:
        raise StoryError(f"(Unknown venue: {params.venue})")
    if params.hopperoo not in HOPPEROOS:
        raise StoryError(f"(Unknown hopperoo: {params.hopperoo})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.comfort not in COMFORTS:
        raise StoryError(f"(Unknown comfort: {params.comfort})")
    if not valid_combo(params.venue, params.hopperoo, params.hideout, params.comfort):
        raise StoryError(explain_rejection(params.venue, params.hopperoo, params.hideout, params.comfort))

    world = tell(
        venue=VENUES[params.venue],
        hopperoo_cfg=HOPPEROOS[params.hopperoo],
        hideout_cfg=HIDEOUTS[params.hideout],
        comfort_cfg=COMFORTS[params.comfort],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        volunteer_name=params.volunteer_name,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, hopperoo, hideout, comfort) combos:\n")
        for venue_id, hopperoo_id, hideout_id, comfort_id in combos:
            print(f"  {venue_id:10} {hopperoo_id:8} {hideout_id:13} {comfort_id}")
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
            header = f"### {p.child_name}: {p.hopperoo} hopperoo at {p.venue} ({p.hideout}, {story_outcome(HIDEOUTS[p.hideout], p.delay)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
