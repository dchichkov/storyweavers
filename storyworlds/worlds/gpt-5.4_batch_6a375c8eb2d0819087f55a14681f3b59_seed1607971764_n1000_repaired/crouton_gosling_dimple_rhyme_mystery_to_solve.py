#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crouton_gosling_dimple_rhyme_mystery_to_solve.py
============================================================================

A standalone story world for a nursery-rhyme-like mystery: a child with a bright
little dimple loses a crouton at a waterside snack, blames a gosling too fast,
and learns to solve the mystery gently before feeding dry human food to a baby
bird.

The domain is intentionally small and constrained:

- A place affords only certain culprits and helpers.
- The mystery is solved from world state, not by swapping nouns into one paragraph.
- The cautionary turn depends on the child's investigation choice:
    * ask_first      -> calm, near-miss ending
    * test_crouton   -> a brief scare: the gosling dislikes the hard dry bite
- Every ending proves a change: the child stops blaming, uses clues, and offers
  proper soft food with a grown-up's help.

Run it
------
    python storyworlds/worlds/gpt-5.4/crouton_gosling_dimple_rhyme_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/crouton_gosling_dimple_rhyme_mystery_to_solve.py --place pond --culprit crow
    python storyworlds/worlds/gpt-5.4/crouton_gosling_dimple_rhyme_mystery_to_solve.py --investigation test_crouton
    python storyworlds/worlds/gpt-5.4/crouton_gosling_dimple_rhyme_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/crouton_gosling_dimple_rhyme_mystery_to_solve.py --qa --json
    python storyworlds/worlds/gpt-5.4/crouton_gosling_dimple_rhyme_mystery_to_solve.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandma", "baker", "gardener"}
        male = {"boy", "father", "man", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"gosling", "crow", "squirrel"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandma": "grandma",
            "grandpa": "grandpa",
            "gardener": "gardener",
            "baker": "baker",
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
class Place:
    id: str
    label: str
    scene: str
    water_name: str
    rhyme_tag: str
    culprit_ids: set[str] = field(default_factory=set)
    helper_ids: set[str] = field(default_factory=set)
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
class Culprit:
    id: str
    label: str
    type: str
    clue_text: str
    reveal_text: str
    stash_text: str
    rhyme_line: str
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
class Helper:
    id: str
    type: str
    arrival: str
    safe_food: str
    explain: str
    water_help: str
    ending_line: str
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
class Investigation:
    id: str
    sense: int
    label: str
    cautionary: bool
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
    def __init__(self, place: Place) -> None:
        self.place = place
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


def _r_missing_worry(world: World) -> list[str]:
    child = world.get("child")
    crouton = world.get("crouton")
    if crouton.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    child.memes["mystery"] += 1
    return ["__mystery__"]


def _r_blame_unease(world: World) -> list[str]:
    child = world.get("child")
    gosling = world.get("gosling")
    if child.memes["blame_gosling"] < THRESHOLD:
        return []
    sig = ("blame_unease",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gosling.memes["unease"] += 1
    return []


def _r_hard_bite(world: World) -> list[str]:
    gosling = world.get("gosling")
    if gosling.meters["hard_bite"] < THRESHOLD:
        return []
    sig = ("hard_bite_startle",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gosling.memes["startle"] += 1
    world.get("child").memes["guilt"] += 1
    return ["__scare__"]


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="blame_unease", tag="social", apply=_r_blame_unease),
    Rule(name="hard_bite", tag="physical", apply=_r_hard_bite),
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


def culprit_possible(place: Place, culprit: Culprit) -> bool:
    return culprit.id in place.culprit_ids


def helper_possible(place: Place, helper: Helper) -> bool:
    return helper.id in place.helper_ids


def sensible_investigations() -> list[Investigation]:
    return [i for i in INVESTIGATIONS.values() if i.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for culprit_id, culprit in CULPRITS.items():
            if not culprit_possible(place, culprit):
                continue
            for helper_id, helper in HELPERS.items():
                if helper_possible(place, helper):
                    combos.append((place_id, culprit_id, helper_id))
    return sorted(combos)


def predict_gosling_reaction(world: World) -> dict:
    sim = world.copy()
    gosling = sim.get("gosling")
    gosling.meters["hard_bite"] += 1
    propagate(sim, narrate=False)
    return {
        "startled": gosling.memes["startle"] >= THRESHOLD,
        "guilt": sim.get("child").memes["guilt"] >= THRESHOLD,
    }


def open_rhyme(world: World, child: Entity, place: Place) -> None:
    child.memes["joy"] += 1
    world.say(
        f"By {place.label}, one silver noon, {child.id} hummed a bobbing tune. "
        f"A sunny dimple dipped and shone, and lunch lay on a checkered stone."
    )
    world.say(
        f"In a little cup of soup so bright, one golden crouton caught the light. "
        f"The reeds bent low, the ripples crooned, and all the air felt gently tuned."
    )


def lose_crouton(world: World, culprit: Culprit) -> None:
    crouton = world.get("crouton")
    crouton.meters["missing"] += 1
    world.facts["clue_text"] = culprit.clue_text
    propagate(world, narrate=False)
    world.say(
        "But when the child looked down to sup, the crouton was gone from the cup. "
        "Not in the spoon, not by the napkin, not where the little crumbs had been."
    )


def first_clue(world: World, culprit: Culprit) -> None:
    child = world.get("child")
    child.memes["curiosity"] += 1
    world.say(
        f"{culprit.clue_text} {child.id} blinked once, then twice, and whispered, "
        f'"Who took my crouton? That is not nice."'
    )


def blame_gosling(world: World, child: Entity, gosling: Entity) -> None:
    child.memes["blame_gosling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Near the bank stood a fuzzy gosling, soft and yellow, small and waddling. "
        f'"Was it you?" asked {child.id} in a hurry. The gosling blinked with baby worry.'
    )


def ask_first(world: World, child: Entity, helper: Entity) -> None:
    child.memes["restraint"] += 1
    child.memes["kindness"] += 1
    world.say(
        f"But {child.id} kept both hands still and called for {helper.label_word} up the hill. "
        f'"Before I guess and before I pout, please help me find what this is about."'
    )


def test_with_crouton(world: World, child: Entity, gosling: Entity) -> None:
    child.memes["impulse"] += 1
    world.say(
        f"But {child.id} thought, \"I will make sure. A second crouton will tell what is true.\" "
        f"The child held out the dry little square toward the gosling standing there."
    )
    pred = predict_gosling_reaction(world)
    world.facts["predicted_startle"] = pred["startled"]
    gosling.meters["hard_bite"] += 1
    propagate(world, narrate=False)
    world.say(
        "The gosling pecked a tiny bite, then shook its beak in quick surprise. "
        "The dry hard piece was rough, not sweet, and not a proper baby treat."
    )


def helper_arrives(world: World, helper: Entity, helper_cfg: Helper) -> None:
    world.say(helper_cfg.arrival)


def caution(world: World, helper: Entity, helper_cfg: Helper, child: Entity, gosling: Entity,
            investigation: Investigation) -> None:
    child.memes["lesson"] += 1
    child.memes["kindness"] += 1
    if investigation.cautionary:
        gosling.meters["hard_bite"] = 0.0
        gosling.memes["startle"] = 0.0
        world.say(
            f'"Easy now," said the {helper.label_word}. "{helper_cfg.explain}" '
            f'{helper.pronoun("subject").capitalize()} offered a sip of water, and the gosling settled.'
        )
    else:
        world.say(
            f'The {helper.label_word} knelt nearby and said, "{helper_cfg.explain}"'
        )


def solve_mystery(world: World, culprit: Culprit) -> None:
    child = world.get("child")
    child.memes["wonder"] += 1
    world.say(
        f"Then they looked for signs with patient eyes. {culprit.reveal_text} "
        f"{culprit.stash_text}"
    )
    world.say(culprit.rhyme_line)


def apologize(world: World, child: Entity, gosling: Entity) -> None:
    child.memes["guilt"] = max(child.memes["guilt"], 0.0)
    child.memes["relief"] += 1
    child.memes["fairness"] += 1
    gosling.memes["unease"] = 0.0
    gosling.memes["trust"] += 1
    world.say(
        f'{child.id} knelt down by the water and said, "Dear gosling, I was too quick with my guess. '
        f'I should look for clues before I blame." The gosling gave a peep and tucked its head with less distress.'
    )


def safe_feed(world: World, helper: Entity, helper_cfg: Helper, child: Entity, gosling: Entity,
              place: Place) -> None:
    child.memes["joy"] += 1
    child.memes["care"] += 1
    gosling.memes["joy"] += 1
    gosling.meters["fed_soft_food"] += 1
    world.say(
        f'Soon the {helper.label_word} brought {helper_cfg.safe_food}. '
        f'"This is kinder for a baby bird," {helper.pronoun()} said.'
    )
    world.say(
        f"{child.id} scattered the soft little bites by {place.water_name}, and the gosling nibbled them with tidy delight."
    )
    world.say(helper_cfg.ending_line)


def ending_image(world: World, child: Entity, place: Place) -> None:
    world.say(
        f"So by {place.label}, as daylight dimmed, the solved-up mystery softly rhymed. "
        f"{child.id}'s dimple shone again, now wiser than it shone back then."
    )


def tell(place: Place, culprit: Culprit, helper_cfg: Helper, investigation: Investigation,
         child_name: str = "Mina", child_type: str = "girl", parent_type: str = "mother") -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        traits=["curious", "kind"],
        attrs={"has_dimple": True},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.type,
        role="helper",
        attrs={},
    ))
    gosling = world.add(Entity(
        id="gosling",
        kind="character",
        type="gosling",
        label="gosling",
        role="gosling",
        attrs={"baby": True},
    ))
    crouton = world.add(Entity(
        id="crouton",
        kind="thing",
        type="food",
        label="crouton",
        role="missing_food",
        attrs={"dry": True},
    ))

    world.facts.update(
        place=place,
        culprit=culprit,
        helper_cfg=helper_cfg,
        investigation=investigation,
        clue_text=culprit.clue_text,
    )

    open_rhyme(world, child, place)
    world.para()
    lose_crouton(world, culprit)
    first_clue(world, culprit)
    blame_gosling(world, child, gosling)

    world.para()
    if investigation.id == "ask_first":
        ask_first(world, child, helper)
    else:
        test_with_crouton(world, child, gosling)

    helper_arrives(world, helper, helper_cfg)
    caution(world, helper, helper_cfg, child, gosling, investigation)

    world.para()
    solve_mystery(world, culprit)
    apologize(world, child, gosling)
    safe_feed(world, helper, helper_cfg, child, gosling, place)

    world.para()
    ending_image(world, child, place)

    outcome = "scare" if investigation.cautionary else "calm"
    world.facts.update(
        child=child,
        helper=helper,
        gosling=gosling,
        crouton=crouton,
        outcome=outcome,
        blamed=child.memes["blame_gosling"] >= THRESHOLD,
        startled=investigation.cautionary,
        mystery_solved=True,
        safe_food=helper_cfg.safe_food,
        lesson=child.memes["lesson"] >= THRESHOLD,
    )
    return world


PLACES = {
    "pond": Place(
        id="pond",
        label="the lily pond",
        scene="a round pond with reeds and stones",
        water_name="the pond edge",
        rhyme_tag="pond",
        culprit_ids={"crow", "breeze"},
        helper_ids={"gardener", "grandma"},
        tags={"pond", "water"},
    ),
    "brook": Place(
        id="brook",
        label="the singing brook",
        scene="a small brook with willow roots",
        water_name="the brook bend",
        rhyme_tag="brook",
        culprit_ids={"breeze", "squirrel"},
        helper_ids={"grandpa", "gardener"},
        tags={"brook", "water"},
    ),
    "bakery_garden": Place(
        id="bakery_garden",
        label="the bakery garden",
        scene="a fenced garden behind a warm bakery door",
        water_name="the bird basin",
        rhyme_tag="garden",
        culprit_ids={"crow", "squirrel"},
        helper_ids={"baker", "grandma"},
        tags={"garden", "bakery"},
    ),
}

CULPRITS = {
    "crow": Culprit(
        id="crow",
        label="crow",
        type="crow",
        clue_text="On the stone lay one black feather and three neat soup crumbs",
        reveal_text="Up on the gate sat a glossy crow with the missing crouton in its beak",
        stash_text="A few more square crumbs waited in a flowerpot below.",
        rhyme_line="So crow, not gosling, had made the dash; the thief was fond of crunchy stash.",
        tags={"crow", "clue"},
    ),
    "squirrel": Culprit(
        id="squirrel",
        label="squirrel",
        type="squirrel",
        clue_text="By the bench were quick brown scratches and a tiny trail of crumbs",
        reveal_text="Under the bench a squirrel sat up, holding the missing crouton in both paws",
        stash_text="Beside it lay acorn shells and one brave parsley leaf.",
        rhyme_line="So squirrel, not gosling, had nibbled sly; the tail told more than the first wild try.",
        tags={"squirrel", "clue"},
    ),
    "breeze": Culprit(
        id="breeze",
        label="breeze",
        type="breeze",
        clue_text="The napkin corner fluttered, and a line of crumbs led into the reeds",
        reveal_text="There in the reeds the crouton rested, tipped from the cup by a skipping breeze",
        stash_text="It had landed dry on a broad green leaf.",
        rhyme_line="So breeze, not gosling, had whisked it away; the wind had stolen the crunchy square that day.",
        tags={"wind", "clue"},
    ),
}

HELPERS = {
    "gardener": Helper(
        id="gardener",
        type="gardener",
        arrival="Down the path came the gardener with muddy boots and a calm green grin.",
        safe_food="a little tin of thawed peas",
        explain="A gosling should not have a dry crouton. Hard salty people-food can upset a baby bird.",
        water_help="The gardener poured a small sip of clean water in a saucer.",
        ending_line="Peep by peep and nibble by nibble, the trouble grew little and the kindness grew big.",
        tags={"peas", "birds"},
    ),
    "grandma": Helper(
        id="grandma",
        type="grandma",
        arrival="From the picnic rug came Grandma, humming as if she knew the rhyme already.",
        safe_food="a palmful of soft oats and greens",
        explain="Dry crouton is not for a gosling. Baby birds do best with soft proper food.",
        water_help="Grandma set down a saucer of water and stroked the air, not the bird.",
        ending_line="The gosling ate the soft bites neatly, and Grandma said the best guesses walk on gentle feet.",
        tags={"oats", "birds"},
    ),
    "grandpa": Helper(
        id="grandpa",
        type="grandpa",
        arrival="From the willow shade came Grandpa with a basket and a patient look.",
        safe_food="a few torn lettuce leaves",
        explain="A crouton is too hard and too salty for a gosling. Better to ask first and feed what helps.",
        water_help="Grandpa tipped a capful of water into a smooth flat stone cup.",
        ending_line="Soon the gosling was calm again, and Grandpa said clues are better friends than blame.",
        tags={"lettuce", "birds"},
    ),
    "baker": Helper(
        id="baker",
        type="baker",
        arrival="Out from the bakery door came the baker, flour on the apron and kindness in the eyes.",
        safe_food="a dish of softened grain mash",
        explain="Even though I bake bread, a dry crouton is not the right bite for a gosling. Soft bird food is safer.",
        water_help="The baker fetched a little bowl of water from the bird basin.",
        ending_line="Steam from the bakery curled above them while the gosling ate softly and the mystery turned sweet.",
        tags={"grain", "birds"},
    ),
}

INVESTIGATIONS = {
    "ask_first": Investigation(
        id="ask_first",
        sense=3,
        label="ask a grown-up before testing",
        cautionary=False,
        tags={"ask_first", "gentle"},
    ),
    "test_crouton": Investigation(
        id="test_crouton",
        sense=2,
        label="test the guess by offering a crouton",
        cautionary=True,
        tags={"cautionary", "feed_wrong_food"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ruby", "Tess", "Wren", "Mabel", "Ivy"]
BOY_NAMES = ["Owen", "Milo", "Toby", "Finn", "Jude", "Arlo", "Theo", "Ned"]


@dataclass
class StoryParams:
    place: str
    culprit: str
    helper: str
    investigation: str
    child_name: str
    child_type: str
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
    "gosling": [(
        "What is a gosling?",
        "A gosling is a baby goose. It is small, fuzzy, and still learning what food is safe to eat."
    )],
    "crouton": [(
        "What is a crouton?",
        "A crouton is a little toasted cube of bread, often put on soup or salad. It is dry and crunchy."
    )],
    "clues": [(
        "What is a clue?",
        "A clue is a sign that helps you solve a mystery. A feather, a crumb trail, or a moved napkin can all be clues."
    )],
    "birds": [(
        "Why should you ask before feeding a wild baby bird?",
        "Different birds need different food, and people-food is not always safe for them. A grown-up can help choose something gentle and proper."
    )],
    "peas": [(
        "Why are soft peas easier for a baby bird than a dry crouton?",
        "Soft peas are easier to peck and swallow than a hard dry cube. They are gentler on a little beak and throat."
    )],
    "oats": [(
        "Why are soft oats easier to eat than crunchy bread?",
        "Soft oats are not sharp or scratchy like a hard dry bite can be. That makes them easier to eat."
    )],
    "lettuce": [(
        "What does lettuce feel like to chew?",
        "Lettuce is soft and leafy. It bends easily, so it is gentler than a hard crunchy cube."
    )],
    "grain": [(
        "What is softened grain mash?",
        "Softened grain mash is grain mixed with water until it is soft. That makes it easier to eat than a dry piece of bread."
    )],
    "fairness": [(
        "Why is it important not to blame too quickly?",
        "If you blame too quickly, you can be unkind to someone who did nothing wrong. Looking for clues helps you be fair."
    )],
}
KNOWLEDGE_ORDER = ["gosling", "crouton", "clues", "birds", "peas", "oats", "lettuce", "grain", "fairness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    culprit = f["culprit"]
    inv = f["investigation"]
    return [
        'Write a nursery-rhyme-style mystery for a 3-to-5-year-old that uses the words "crouton", "gosling", and "dimple".',
        f"Tell a gentle rhyme where a child loses a crouton by {place.label}, blames a gosling too quickly, and follows clues to learn that the real culprit was {culprit.label}.",
        f"Write a cautionary little mystery in bouncing rhyme where the child chooses to {inv.label}, learns how to treat a baby bird kindly, and ends with a solved puzzle and a wiser smile.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    gosling = f["gosling"]
    place = f["place"]
    culprit = f["culprit"]
    inv = f["investigation"]
    helper_cfg = f["helper_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child with a sunny dimple, a little gosling by {place.label}, and the {helper.label_word} who helps solve the mystery."
        ),
        (
            "What was the mystery?",
            f"The mystery was that a crouton vanished from the soup cup. {child.id} had to figure out where it went and who really moved it."
        ),
        (
            f"Why did {child.id} first think the gosling took the crouton?",
            f"{child.id} saw the gosling near the water right after the crouton went missing, so the guess came too fast. The missing snack and the first strange clue made the child hurry to blame before checking carefully."
        ),
        (
            "How was the mystery solved?",
            f"They slowed down and followed clues instead of just guessing. That is how they discovered that {culprit.label} had really moved the crouton."
        ),
    ]
    if inv.cautionary:
        qa.append((
            "What happened when the child tested the guess with a crouton?",
            f"The gosling pecked at the dry crouton and did not like the hard bite. That small scare showed that a crouton was not the right food for a baby bird."
        ))
        qa.append((
            f"What did the {helper.label_word} do to help?",
            f"The {helper.label_word} stopped the test, explained why dry people-food was a bad idea, and helped with proper soft food instead. Then the child could care for the gosling kindly after the mistake."
        ))
    else:
        qa.append((
            f"Why was asking the {helper.label_word} first a good choice?",
            f"It kept the child from testing a risky guess on the gosling. Asking first gave them help with both the mystery and the safe way to treat a baby bird."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with the mystery solved, an apology to the gosling, and soft food shared the right way by the water. {child.id}'s dimple shone again because the child had become gentler and wiser."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"gosling", "crouton", "clues", "birds", "fairness"}
    safe = f["helper_cfg"].safe_food
    if "peas" in safe:
        tags.add("peas")
    if "oats" in safe:
        tags.add("oats")
    if "lettuce" in safe:
        tags.add("lettuce")
    if "grain" in safe:
        tags.add("grain")
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="pond",
        culprit="crow",
        helper="gardener",
        investigation="ask_first",
        child_name="Mina",
        child_type="girl",
    ),
    StoryParams(
        place="brook",
        culprit="squirrel",
        helper="grandpa",
        investigation="test_crouton",
        child_name="Owen",
        child_type="boy",
    ),
    StoryParams(
        place="bakery_garden",
        culprit="crow",
        helper="baker",
        investigation="ask_first",
        child_name="Ruby",
        child_type="girl",
    ),
    StoryParams(
        place="pond",
        culprit="breeze",
        helper="grandma",
        investigation="test_crouton",
        child_name="Theo",
        child_type="boy",
    ),
    StoryParams(
        place="brook",
        culprit="breeze",
        helper="gardener",
        investigation="ask_first",
        child_name="Ivy",
        child_type="girl",
    ),
]


def explain_rejection(place: Place, culprit: Culprit, helper: Optional[Helper] = None) -> str:
    if not culprit_possible(place, culprit):
        options = ", ".join(sorted(place.culprit_ids))
        return (
            f"(No story: {culprit.label} does not fit {place.label}. "
            f"Try a culprit used there, such as: {options}.)"
        )
    if helper is not None and not helper_possible(place, helper):
        options = ", ".join(sorted(place.helper_ids))
        return (
            f"(No story: the {helper.id} is not the helper for {place.label}. "
            f"Try one of: {options}.)"
        )
    return "(No story: that combination is not supported here.)"


def outcome_of(params: StoryParams) -> str:
    inv = INVESTIGATIONS[params.investigation]
    return "scare" if inv.cautionary else "calm"


ASP_RULES = r"""
% --- compatible story gate --------------------------------------------------
valid(Place, Culprit, Helper) :-
    place(Place), culprit(Culprit), helper(Helper),
    culprit_in(Place, Culprit), helper_in(Place, Helper).

% --- ending model -----------------------------------------------------------
scare :- chosen_investigation(test_crouton).
calm  :- chosen_investigation(ask_first).
outcome(scare) :- scare.
outcome(calm)  :- calm.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for culprit_id in sorted(place.culprit_ids):
            lines.append(asp.fact("culprit_in", place_id, culprit_id))
        for helper_id in sorted(place.helper_ids):
            lines.append(asp.fact("helper_in", place_id, helper_id))
    for culprit_id in CULPRITS:
        lines.append(asp.fact("culprit", culprit_id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    for inv_id in INVESTIGATIONS:
        lines.append(asp.fact("investigation", inv_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("chosen_investigation", params.investigation)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
    for seed in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme mystery world: a missing crouton, a gosling, and a gentle caution."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--investigation", choices=INVESTIGATIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.culprit:
        place = PLACES[args.place]
        culprit = CULPRITS[args.culprit]
        if not culprit_possible(place, culprit):
            raise StoryError(explain_rejection(place, culprit))
    if args.place and args.helper:
        place = PLACES[args.place]
        helper = HELPERS[args.helper]
        if not helper_possible(place, helper):
            culprit = CULPRITS[args.culprit] if args.culprit else next(iter(CULPRITS.values()))
            raise StoryError(explain_rejection(place, culprit, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, culprit, helper = rng.choice(sorted(combos))
    investigation = args.investigation or rng.choice(sorted(INVESTIGATIONS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    return StoryParams(
        place=place,
        culprit=culprit,
        helper=helper,
        investigation=investigation,
        child_name=child_name,
        child_type=child_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.investigation not in INVESTIGATIONS:
        raise StoryError(f"(Unknown investigation: {params.investigation})")

    place = PLACES[params.place]
    culprit = CULPRITS[params.culprit]
    helper = HELPERS[params.helper]
    investigation = INVESTIGATIONS[params.investigation]

    if not culprit_possible(place, culprit):
        raise StoryError(explain_rejection(place, culprit))
    if not helper_possible(place, helper):
        raise StoryError(explain_rejection(place, culprit, helper))

    world = tell(
        place=place,
        culprit=culprit,
        helper_cfg=helper,
        investigation=investigation,
        child_name=params.child_name,
        child_type=params.child_type,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, culprit, helper) combos:\n")
        for place, culprit, helper in combos:
            print(f"  {place:14} {culprit:9} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
                f"### {p.child_name}: {p.place}, {p.culprit}, {p.helper}, "
                f"{p.investigation} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
