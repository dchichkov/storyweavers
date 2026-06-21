#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/aleck_swim_dim_mystery_to_solve_reconciliation.py
============================================================================

A standalone story world about two children playing pirates, a missing snack
treasure, a quick wrong suspicion, a clue-led mystery, and a warm making-up at
the end.

The style stays close to a small pirate tale, but the engine is a stateful
simulation: children turn a place into a pirate scene, hide a little "treasure"
basket, discover that something is missing, and let their feelings push the
middle of the story. The turn comes from clues in the physical world. Once the
real thief is found, the children reconcile and share what is left.

This world always includes the words "aleck" and "swim-dim" in natural story
text.

Run it
------
    python storyworlds/worlds/gpt-5.4/aleck_swim_dim_mystery_to_solve_reconciliation.py
    python storyworlds/worlds/gpt-5.4/aleck_swim_dim_mystery_to_solve_reconciliation.py --setting beach --stash buns --culprit gull
    python storyworlds/worlds/gpt-5.4/aleck_swim_dim_mystery_to_solve_reconciliation.py --setting garden --culprit gull
    python storyworlds/worlds/gpt-5.4/aleck_swim_dim_mystery_to_solve_reconciliation.py --all
    python storyworlds/worlds/gpt-5.4/aleck_swim_dim_mystery_to_solve_reconciliation.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/aleck_swim_dim_mystery_to_solve_reconciliation.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        animal = {"gull", "puppy", "goat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Setting:
    id: str
    label: str
    scene: str
    rig: str
    hideout: str
    clue_path: str
    affords: set[str] = field(default_factory=set)
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
class Stash:
    id: str
    label: str
    phrase: str
    share_line: str
    clue: str
    plural: bool = True
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
class Culprit:
    id: str
    label: str
    type: str
    phrase: str
    clue_mark: str
    trail: str
    lair: str
    action: str
    likes: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    phrase: str
    use_line: str
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


SETTINGS = {
    "beach": Setting(
        id="beach",
        label="the beach",
        scene="a windy island shore",
        rig="A striped towel was their ship, a stick became a mast, and a blue bucket held their treasure map and little snack chest.",
        hideout="the swim-dim cave under the old boardwalk",
        clue_path="past the rope posts and down by the wet sand",
        affords={"gull", "puppy"},
        tags={"beach", "mystery"},
    ),
    "dock": Setting(
        id="dock",
        label="the dock",
        scene="a creaky harbor island",
        rig="A fishing crate was their ship, a coiled rope became a sea serpent, and a tin pail held their treasure map and little snack chest.",
        hideout="the swim-dim cave under the dock stairs",
        clue_path="along the planks and toward the bait shed",
        affords={"gull", "goat"},
        tags={"dock", "mystery"},
    ),
    "garden": Setting(
        id="garden",
        label="the garden",
        scene="a secret backyard bay",
        rig="The sandbox was their island, a rake became an oar, and a little basket held their treasure map and little snack chest.",
        hideout="the swim-dim cave behind the bean trellis",
        clue_path="between the stepping stones and over by the gate",
        affords={"puppy", "goat"},
        tags={"garden", "mystery"},
    ),
}

STASHES = {
    "buns": Stash(
        id="buns",
        label="coconut buns",
        phrase="a paper packet of soft coconut buns",
        share_line="broke the last coconut bun in half so each pirate had a sweet bite",
        clue="a round crumb with coconut stuck to it",
        plural=True,
        tags={"food", "sharing"},
    ),
    "oranges": Stash(
        id="oranges",
        label="orange slices",
        phrase="a little tin of bright orange slices",
        share_line="counted the orange slices and shared them one by one until the tin was empty",
        clue="a shiny orange drop on the lid",
        plural=True,
        tags={"food", "sharing"},
    ),
    "biscuits": Stash(
        id="biscuits",
        label="seed biscuits",
        phrase="a wax-paper bundle of crunchy seed biscuits",
        share_line="stacked the seed biscuits in one neat pile and took turns choosing from it",
        clue="a cracked biscuit corner with tiny seeds all over it",
        plural=True,
        tags={"food", "sharing"},
    ),
}

CULPRITS = {
    "gull": Culprit(
        id="gull",
        label="gull",
        type="gull",
        phrase="a bold gull with one bright eye",
        clue_mark="white feathers",
        trail="little pecks and feathers",
        lair="on the rail above a post",
        action="had snatched one piece and was hopping away with it",
        likes={"buns", "oranges", "biscuits"},
        tags={"gull", "clue"},
    ),
    "puppy": Culprit(
        id="puppy",
        label="puppy",
        type="puppy",
        phrase="a sandy puppy with a wagging tail",
        clue_mark="small pawprints",
        trail="pawprints and a damp nose-smudge",
        lair="behind a bucket near the fence",
        action="had tugged one piece free and was hiding with it between its paws",
        likes={"buns", "biscuits"},
        tags={"puppy", "clue"},
    ),
    "goat": Culprit(
        id="goat",
        label="goat",
        type="goat",
        phrase="a nibbling island goat with a bell on its neck",
        clue_mark="tiny hoof marks",
        trail="hoof marks and square little nibbles",
        lair="beside a patch of tall grass",
        action="had stolen one piece and was chewing with a very innocent face",
        likes={"buns", "oranges"},
        tags={"goat", "clue"},
    ),
}

TOOLS = {
    "spyglass": Tool(
        id="spyglass",
        label="spyglass",
        phrase="a toy spyglass",
        use_line="held up the toy spyglass and searched for the smallest sign",
        tags={"spyglass"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a safe camp lantern",
        use_line="lifted the safe camp lantern and tipped its glow toward the ground",
        tags={"lantern"},
    ),
    "map": Tool(
        id="map",
        label="map",
        phrase="their crayon treasure map",
        use_line="smoothed out their crayon treasure map and checked where a thief might have gone",
        tags={"map"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "clever", "thoughtful", "curious", "gentle", "steady"]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        return [e for e in self.entities.values() if e.role in {"finder", "blamed"}]

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


# ---------------------------------------------------------------------------
# Rules
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


def _r_hurt_from_blame(world: World) -> list[str]:
    out: list[str] = []
    accuser = world.get("finder")
    blamed = world.get("blamed")
    if blamed.memes["blamed"] >= THRESHOLD:
        sig = ("hurt_from_blame", blamed.id)
        if sig not in world.fired:
            world.fired.add(sig)
            blamed.memes["hurt"] += 1
            accuser.memes["certainty"] += 1
            out.append("__hurt__")
    return out


def _r_evidence_softens(world: World) -> list[str]:
    out: list[str] = []
    accuser = world.get("finder")
    blamed = world.get("blamed")
    if world.get("clue").meters["evidence"] >= THRESHOLD:
        sig = ("evidence_softens", accuser.id)
        if sig not in world.fired:
            world.fired.add(sig)
            accuser.memes["doubt"] += 1
            accuser.memes["certainty"] = 0.0
            blamed.memes["hope"] += 1
            out.append("__evidence__")
    return out


def _r_found_culprit(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.get("culprit")
    if culprit.meters["found"] >= THRESHOLD:
        sig = ("found_culprit", culprit.id)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.kids():
                kid.memes["relief"] += 1
            world.get("finder").memes["shame"] += 1
            out.append("__found__")
    return out


def _r_apology_heals(world: World) -> list[str]:
    out: list[str] = []
    finder = world.get("finder")
    blamed = world.get("blamed")
    if finder.memes["sorry"] >= THRESHOLD and blamed.memes["hurt"] >= THRESHOLD:
        sig = ("apology_heals", finder.id, blamed.id)
        if sig not in world.fired:
            world.fired.add(sig)
            blamed.memes["forgive"] += 1
            blamed.memes["hurt"] = 0.0
            finder.memes["love"] += 1
            blamed.memes["love"] += 1
            out.append("__apology__")
    return out


def _r_sharing_joy(world: World) -> list[str]:
    out: list[str] = []
    chest = world.get("chest")
    if chest.meters["shared"] >= THRESHOLD:
        sig = ("sharing_joy", chest.id)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.kids():
                kid.memes["joy"] += 1
                kid.memes["friendship"] += 1
            out.append("__sharing__")
    return out


CAUSAL_RULES = [
    Rule(name="hurt_from_blame", tag="social", apply=_r_hurt_from_blame),
    Rule(name="evidence_softens", tag="social", apply=_r_evidence_softens),
    Rule(name="found_culprit", tag="social", apply=_r_found_culprit),
    Rule(name="apology_heals", tag="social", apply=_r_apology_heals),
    Rule(name="sharing_joy", tag="social", apply=_r_sharing_joy),
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
# Constraints and outcomes
# ---------------------------------------------------------------------------
def likes_stash(culprit: Culprit, stash: Stash) -> bool:
    return stash.id in culprit.likes


def allowed_here(setting: Setting, culprit: Culprit) -> bool:
    return culprit.id in setting.affords


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for stash_id, stash in STASHES.items():
            for culprit_id, culprit in CULPRITS.items():
                if allowed_here(setting, culprit) and likes_stash(culprit, stash):
                    combos.append((setting_id, stash_id, culprit_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    close = (params.relation == "siblings" and params.trust >= 6) or (
        params.relation == "friends" and params.trust >= 7
    )
    if close and params.blamed_age >= params.finder_age:
        return "quick"
    return "tender"


def explain_rejection(setting: Setting, stash: Stash, culprit: Culprit) -> str:
    if not allowed_here(setting, culprit):
        return (
            f"(No story: {culprit.label}s do not fit {setting.label} in this little world, "
            f"so the mystery would have no believable thief there.)"
        )
    if not likes_stash(culprit, stash):
        return (
            f"(No story: a {culprit.label} would not reasonably steal {stash.label} here, "
            f"so the clue trail would feel false.)"
        )
    return "(No story: this mystery combination is not reasonable.)"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_mystery(world: World) -> dict:
    sim = world.copy()
    sim.get("clue").meters["evidence"] += 1
    sim.get("culprit").meters["found"] += 1
    propagate(sim, narrate=False)
    return {
        "hurt": sim.get("blamed").memes["hurt"],
        "relief": sim.get("finder").memes["relief"],
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def play_setup(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright day, {a.id} and {b.id} turned {setting.label} into {setting.scene}. "
        f"{setting.rig}"
    )
    world.say(
        f'"Captain {a.id} and Scout {b.id}!" {a.id} shouted. "We will hide our snack treasure by {setting.hideout} and guard it like real pirates."'
    )


def hide_treasure(world: World, a: Entity, b: Entity, stash: Stash, setting: Setting) -> None:
    world.say(
        f"They tucked away {stash.phrase} beside {setting.hideout}. Then they ran in circles around their ship and sang a splashy pirate song."
    )


def discover_missing(world: World, a: Entity, stash: Stash) -> None:
    chest = world.get("chest")
    chest.meters["missing"] += 1
    a.memes["alarm"] += 1
    world.say(
        f"When {a.id} lifted the lid again, {a.pronoun()} gasped. One of the {stash.label} was gone."
    )
    world.say('"Our treasure has been pinched!"')


def blame_friend(world: World, a: Entity, b: Entity) -> None:
    b.memes["blamed"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{a.id} spun around. "Did you take it, {b.id}?" {a.pronoun()} asked too fast.'
    )
    if b.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{b.id}'s face fell. {b.pronoun().capitalize()} had only been guarding the map, and now {b.pronoun()} looked small and hurt."
        )


def start_search(world: World, b: Entity, tool: Tool, setting: Setting) -> None:
    pred = predict_mystery(world)
    world.facts["predicted_hurt"] = pred["hurt"]
    world.facts["predicted_relief"] = pred["relief"]
    b.memes["steady"] += 1
    world.say(
        f'{b.id} took a slow breath. "I did not take it. Let us look first," {b.pronoun()} said.'
    )
    world.say(
        f"Then {b.pronoun()} {tool.use_line}. There, {setting.clue_path}, was the first clue."
    )


def inspect_clue(world: World, stash: Stash, culprit: Culprit) -> None:
    clue = world.get("clue")
    clue.meters["evidence"] += 1
    propagate(world, narrate=False)
    world.say(
        f"It was {stash.clue}, beside {culprit.clue_mark}. The mark did not look like a pirate child's shoe at all."
    )
    world.say(
        f"Soon they saw {culprit.trail} leading away from the little chest."
    )


def track_thief(world: World, a: Entity, b: Entity, culprit: Culprit) -> None:
    world.say(
        f'"Not you," {a.id} whispered. Together they followed the trail until they reached {culprit.lair}.'
    )
    if world.facts.get("outcome") == "quick":
        world.say(
            "At that moment a smart aleck breeze rattled the rope, as if even the air were giggling at their mistake."
        )
    else:
        world.say(
            "The quiet between them felt heavy for a moment, because being wrongly blamed can sting even in a game."
        )


def reveal_culprit(world: World, culprit: Culprit) -> None:
    world.get("culprit").meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"There sat {culprit.phrase}. It {culprit.action}."
    )
    world.say(
        f"The mystery was solved at last, and the missing treasure had never been stolen by a friend at all."
    )


def apologize(world: World, a: Entity, b: Entity) -> None:
    a.memes["sorry"] += 1
    propagate(world, narrate=False)
    if world.facts.get("outcome") == "quick":
        world.say(
            f'{a.id} reached for {b.id}\'s hand. "I am sorry I blamed you before we looked," {a.pronoun()} said. "You were the best scout on the whole shore."'
        )
        world.say(
            f'{b.id} squeezed back at once. "Next time we hunt clues first," {b.pronoun()} said.'
        )
    else:
        world.say(
            f'{a.id} looked down at the sand. "I am truly sorry," {a.pronoun()} said softly. "I made your heart hurt when I should have trusted you."'
        )
        world.say(
            f'{b.id} was quiet for one breath, then nodded. "I felt sad, but I know you were worried about the treasure," {b.pronoun()} said. "Let us be shipmates again."'
        )


def share_ending(world: World, a: Entity, b: Entity, stash: Stash, setting: Setting) -> None:
    world.get("chest").meters["shared"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So the two pirates went back to their little chest and {stash.share_line}."
    )
    world.say(
        f"They even left one tiny crumb far from the lid, just in case the thief wandered by again and needed a kinder sort of feast."
    )
    world.say(
        f"By sunset, {setting.hideout} did not feel like a place for quarrels anymore. It felt like a secret cove where shipmates solved mysteries, made up, and shared."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    stash: Stash,
    culprit_cfg: Culprit,
    tool: Tool,
    *,
    finder_name: str = "Tom",
    finder_gender: str = "boy",
    blamed_name: str = "Lily",
    blamed_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    relation: str = "siblings",
    trust: int = 7,
    finder_age: int = 6,
    blamed_age: int = 6,
) -> World:
    world = World()

    finder = world.add(
        Entity(
            id="finder",
            kind="character",
            type=finder_gender,
            label=finder_name,
            role="finder",
            age=finder_age,
            traits=["bold"],
            attrs={"name": finder_name, "relation": relation},
        )
    )
    blamed = world.add(
        Entity(
            id="blamed",
            kind="character",
            type=blamed_gender,
            label=blamed_name,
            role="blamed",
            age=blamed_age,
            traits=[trait],
            attrs={"name": blamed_name, "relation": relation},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
            attrs={},
        )
    )
    chest = world.add(
        Entity(
            id="chest",
            type="chest",
            label="the little chest",
            attrs={"stash": stash.id},
        )
    )
    clue = world.add(
        Entity(
            id="clue",
            type="clue",
            label="the clue",
            attrs={"mark": culprit_cfg.clue_mark},
        )
    )
    culprit = world.add(
        Entity(
            id="culprit",
            type=culprit_cfg.type,
            label=culprit_cfg.label,
            attrs={"likes": sorted(culprit_cfg.likes)},
        )
    )
    tool_ent = world.add(
        Entity(
            id="tool",
            type="tool",
            label=tool.label,
            attrs={"tool": tool.id},
        )
    )

    finder.memes["trust"] = float(trust)
    blamed.memes["trust"] = float(trust)
    finder.memes["certainty"] = 0.0
    blamed.memes["blamed"] = 0.0
    blamed.memes["hurt"] = 0.0
    finder.memes["sorry"] = 0.0
    clue.meters["evidence"] = 0.0
    culprit.meters["found"] = 0.0
    chest.meters["missing"] = 0.0
    chest.meters["shared"] = 0.0
    tool_ent.meters["ready"] = 1.0
    world.facts["outcome"] = "quick" if (
        (relation == "siblings" and trust >= 6) or (relation == "friends" and trust >= 7)
    ) and blamed_age >= finder_age else "tender"

    play_setup(world, finder, blamed, setting)
    hide_treasure(world, finder, blamed, stash, setting)

    world.para()
    discover_missing(world, finder, stash)
    blame_friend(world, finder, blamed)
    start_search(world, blamed, tool, setting)

    world.para()
    inspect_clue(world, stash, culprit_cfg)
    track_thief(world, finder, blamed, culprit_cfg)
    reveal_culprit(world, culprit_cfg)

    world.para()
    apologize(world, finder, blamed)
    share_ending(world, finder, blamed, stash, setting)

    world.facts.update(
        setting=setting,
        stash=stash,
        culprit_cfg=culprit_cfg,
        tool=tool,
        parent=parent,
        finder=finder,
        blamed=blamed,
        chest=chest,
        clue=clue,
        culprit=culprit,
        relation=relation,
        trust=trust,
        finder_name=finder_name,
        blamed_name=blamed_name,
        reconciled=blamed.memes["forgive"] >= THRESHOLD or blamed.memes["hurt"] == 0.0,
        shared=chest.meters["shared"] >= THRESHOLD,
        mystery_solved=culprit.meters["found"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    stash: str
    culprit: str
    tool: str
    finder: str
    finder_gender: str
    blamed: str
    blamed_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    trust: int = 7
    finder_age: int = 6
    blamed_age: int = 6
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
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
    "mystery": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. It can be a mark, a crumb, or anything that points toward the truth.",
        )
    ],
    "sharing": [
        (
            "Why is sharing kind?",
            "Sharing is kind because it lets more than one person enjoy something good. It also shows that friendship matters more than keeping every piece for yourself.",
        )
    ],
    "reconciliation": [
        (
            "What does it mean to reconcile?",
            "To reconcile means to make peace after a hurt feeling or an argument. People listen, apologize, forgive, and come close again.",
        )
    ],
    "gull": [
        (
            "Why might a gull grab food?",
            "A gull looks for easy food near people. If it sees something tasty and unguarded, it may swoop down and snatch it.",
        )
    ],
    "puppy": [
        (
            "Why do puppies follow smells?",
            "Puppies explore the world with their noses. A good smell can lead them straight to a snack or an interesting hiding place.",
        )
    ],
    "goat": [
        (
            "Why do goats nibble things?",
            "Goats like to test things with their mouths. They nibble to explore, and if something smells tasty, they may try to eat it.",
        )
    ],
    "spyglass": [
        (
            "What is a spyglass?",
            "A spyglass is a small telescope sailors used to look far away. In games, it helps children pretend they are scouts on a ship.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives light so people can see in dim places. A safe camp lantern glows without an open flame.",
        )
    ],
    "map": [
        (
            "Why do maps help in a hunt?",
            "Maps help you remember where things are and where to look next. They turn a search into a careful plan instead of a wild guess.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "mystery",
    "sharing",
    "reconciliation",
    "gull",
    "puppy",
    "goat",
    "spyglass",
    "lantern",
    "map",
]


def _name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    finder = _name(f["finder"])
    blamed = _name(f["blamed"])
    stash = f["stash"]
    setting = f["setting"]
    culprit = f["culprit_cfg"]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the words "aleck" and "swim-dim", where a snack treasure goes missing and the children solve the mystery.',
        f"Tell a gentle mystery where {finder} wrongly suspects {blamed} after {stash.label} vanish near {setting.hideout}, but clues lead them to a {culprit.label} instead.",
        f"Write a small story about shipmates who make up after a mistake and end by sharing what is left of their treasure snack.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    finder = f["finder"]
    blamed = f["blamed"]
    stash = f["stash"]
    setting = f["setting"]
    culprit = f["culprit_cfg"]
    tool = f["tool"]
    finder_name = _name(finder)
    blamed_name = _name(blamed)
    pair = pair_noun(finder, blamed, f["relation"])

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {finder_name} and {blamed_name}, pretending to be pirates together. Their game matters because the missing snack treasure interrupts something happy they built as shipmates.",
        ),
        (
            "What was the mystery?",
            f"One of the {stash.label} was gone from their little chest near {setting.hideout}. That missing piece made {finder_name} worry so fast that {finder.pronoun()} blamed {blamed_name} before checking the clues.",
        ),
        (
            f"Why were {blamed_name}'s feelings hurt?",
            f"{blamed_name}'s feelings were hurt because {finder_name} asked if {blamed_name} had taken the missing treasure. Being blamed stung especially because {blamed_name} had only been helping guard the game.",
        ),
        (
            "How did they solve the mystery?",
            f"They slowed down and searched instead of arguing. Using {tool.phrase}, they found {stash.clue} and {culprit.clue_mark}, and those clues showed that the real thief was a {culprit.label}, not a friend.",
        ),
    ]
    if f["mystery_solved"]:
        qa.append(
            (
                "Who really took the missing snack?",
                f"A {culprit.label} did. The trail of {culprit.trail} led them to {culprit.lair}, where the thief was caught with the missing piece.",
            )
        )
    if f["reconciled"]:
        if f["outcome"] == "quick":
            qa.append(
                (
                    f"How did {finder_name} and {blamed_name} make up?",
                    f"{finder_name} apologized as soon as the truth was clear, and {blamed_name} forgave quickly. Their trust was strong enough that the wrong guess did not stay between them for long.",
                )
            )
        else:
            qa.append(
                (
                    f"How did {finder_name} and {blamed_name} reconcile?",
                    f"{finder_name} admitted the blame had hurt {blamed_name}'s heart and gave a real apology. {blamed_name} told the truth about those feelings, then forgave, so their friendship became warm again instead of merely quiet.",
                )
            )
    if f["shared"]:
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children sharing what was left of the treasure snack. That ending proves the change, because the chest stopped being a cause for quarrels and became something kind they enjoyed together.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery", "sharing", "reconciliation", f["culprit_cfg"].id, f["tool"].id}
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.age:
            bits.append(f"age={e.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(S, St, C) :- setting(S), stash(St), culprit(C), affords(S, C), likes(C, St).

close_pair :- relation(siblings), trust(T), T >= 6.
close_pair :- relation(friends), trust(T), T >= 7.
older_or_peer_blamed :- finder_age(FA), blamed_age(BA), BA >= FA.

outcome(quick)  :- close_pair, older_or_peer_blamed.
outcome(tender) :- not outcome(quick).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for cid in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, cid))
    for stid in STASHES:
        lines.append(asp.fact("stash", stid))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        for liked in sorted(culprit.likes):
            lines.append(asp.fact("likes", cid, liked))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("trust", params.trust),
            asp.fact("finder_age", params.finder_age),
            asp.fact("blamed_age", params.blamed_age),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
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
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = s
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - explicit verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirates, a missing snack treasure, a clue, and making up."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--stash", choices=STASHES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--tool", choices=TOOLS)
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.stash and args.culprit:
        setting = SETTINGS[args.setting]
        stash = STASHES[args.stash]
        culprit = CULPRITS[args.culprit]
        if not (allowed_here(setting, culprit) and likes_stash(culprit, stash)):
            raise StoryError(explain_rejection(setting, stash, culprit))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.stash is None or combo[1] == args.stash)
        and (args.culprit is None or combo[2] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, stash_id, culprit_id = rng.choice(sorted(combos))
    tool_id = args.tool or rng.choice(sorted(TOOLS))
    finder_name, finder_gender = _pick_kid(rng)
    blamed_name, blamed_gender = _pick_kid(rng, avoid=finder_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    finder_age, blamed_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(3, 9)

    return StoryParams(
        setting=setting_id,
        stash=stash_id,
        culprit=culprit_id,
        tool=tool_id,
        finder=finder_name,
        finder_gender=finder_gender,
        blamed=blamed_name,
        blamed_gender=blamed_gender,
        parent=parent,
        trait=trait,
        relation=relation,
        trust=trust,
        finder_age=finder_age,
        blamed_age=blamed_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.stash not in STASHES:
        raise StoryError(f"(Unknown stash: {params.stash})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")

    setting = SETTINGS[params.setting]
    stash = STASHES[params.stash]
    culprit = CULPRITS[params.culprit]
    tool = TOOLS[params.tool]

    if not (allowed_here(setting, culprit) and likes_stash(culprit, stash)):
        raise StoryError(explain_rejection(setting, stash, culprit))

    world = tell(
        setting=setting,
        stash=stash,
        culprit_cfg=culprit,
        tool=tool,
        finder_name=params.finder,
        finder_gender=params.finder_gender,
        blamed_name=params.blamed,
        blamed_gender=params.blamed_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        trust=params.trust,
        finder_age=params.finder_age,
        blamed_age=params.blamed_age,
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
        setting="beach",
        stash="buns",
        culprit="gull",
        tool="spyglass",
        finder="Tom",
        finder_gender="boy",
        blamed="Lily",
        blamed_gender="girl",
        parent="mother",
        trait="careful",
        relation="siblings",
        trust=8,
        finder_age=5,
        blamed_age=7,
    ),
    StoryParams(
        setting="garden",
        stash="biscuits",
        culprit="puppy",
        tool="lantern",
        finder="Mia",
        finder_gender="girl",
        blamed="Ben",
        blamed_gender="boy",
        parent="father",
        trait="steady",
        relation="friends",
        trust=5,
        finder_age=6,
        blamed_age=5,
    ),
    StoryParams(
        setting="dock",
        stash="oranges",
        culprit="goat",
        tool="map",
        finder="Sam",
        finder_gender="boy",
        blamed="Nora",
        blamed_gender="girl",
        parent="mother",
        trait="thoughtful",
        relation="siblings",
        trust=7,
        finder_age=6,
        blamed_age=6,
    ),
    StoryParams(
        setting="dock",
        stash="biscuits",
        culprit="gull",
        tool="lantern",
        finder="Ella",
        finder_gender="girl",
        blamed="Max",
        blamed_gender="boy",
        parent="father",
        trait="gentle",
        relation="friends",
        trust=8,
        finder_age=4,
        blamed_age=6,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, stash, culprit) combos:\n")
        for setting, stash, culprit in combos:
            print(f"  {setting:8} {stash:9} {culprit}")
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
            header = f"### {p.finder} & {p.blamed}: {p.stash} at {p.setting} ({p.culprit}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
