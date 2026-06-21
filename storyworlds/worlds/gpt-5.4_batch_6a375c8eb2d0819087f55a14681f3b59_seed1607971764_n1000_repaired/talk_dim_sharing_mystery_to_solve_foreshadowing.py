#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/talk_dim_sharing_mystery_to_solve_foreshadowing.py
==============================================================================

A standalone story world for a small myth-shaped tale about a village mystery:
food vanishes from a twilight shrine, two children follow a clue, and the
mystery is solved not by grabbing but by sharing.

This world is built around three seed features:

* Sharing
* Mystery to Solve
* Foreshadowing

It also includes the seed word "talk-dim" as an old twilight word in the tale's
mythic setting.

Run it
------
    python storyworlds/worlds/gpt-5.4/talk_dim_sharing_mystery_to_solve_foreshadowing.py
    python storyworlds/worlds/gpt-5.4/talk_dim_sharing_mystery_to_solve_foreshadowing.py --place reed_bank --offering pear_slice --clue wet_tracks
    python storyworlds/worlds/gpt-5.4/talk_dim_sharing_mystery_to_solve_foreshadowing.py --place cedar_shrine --clue wet_tracks
    python storyworlds/worlds/gpt-5.4/talk_dim_sharing_mystery_to_solve_foreshadowing.py --all
    python storyworlds/worlds/gpt-5.4/talk_dim_sharing_mystery_to_solve_foreshadowing.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/talk_dim_sharing_mystery_to_solve_foreshadowing.py --verify
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
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    visible: bool = True
    # physical and emotional dimensions
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


# ---------------------------------------------------------------------------
# Domain registries
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
    phrase: str
    image: str
    old_word_line: str
    creature: str
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
class Offering:
    id: str
    label: str
    phrase: str
    scent: str
    share_line: str
    liked_by: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    phrase: str
    hint_line: str
    reveals: str
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
class CreatureKind:
    id: str
    label: str
    phrase: str
    hiding_line: str
    thanks_line: str
    gift: str
    habitat: str
    likes: set[str] = field(default_factory=set)
    clue: str = ""
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
class Treasure:
    id: str
    label: str
    phrase: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def _r_hungry_search(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    if creature.meters["hunger"] < THRESHOLD:
        return out
    if creature.meters["seen_clue"] < THRESHOLD:
        sig = ("search", creature.id)
        if sig not in world.fired:
            world.fired.add(sig)
            creature.meters["left_clue"] += 1
            world.get("clue").meters["present"] += 1
            out.append("__clue__")
    return out


def _r_share_builds_trust(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    creature = world.get("creature")
    offering = world.get("offering")
    if child.meters["shared"] < THRESHOLD:
        return out
    if offering.attrs.get("offering_id") not in creature.attrs.get("likes", set()):
        return out
    sig = ("trust", child.id, creature.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.memes["trust"] += 1
    child.memes["kindness"] += 1
    out.append("__trust__")
    return out


def _r_trust_reveals(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    if creature.memes["trust"] < THRESHOLD or creature.visible:
        return out
    sig = ("reveal", creature.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.visible = True
    creature.meters["revealed"] += 1
    out.append("__reveal__")
    return out


def _r_reveal_gift(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    treasure = world.get("treasure")
    child = world.get("child")
    if creature.meters["revealed"] < THRESHOLD:
        return out
    sig = ("gift", creature.id, treasure.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    treasure.meters["given"] += 1
    child.memes["wonder"] += 1
    out.append("__gift__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hungry_search", tag="physical", apply=_r_hungry_search),
    Rule(name="share_builds_trust", tag="social", apply=_r_share_builds_trust),
    Rule(name="trust_reveals", tag="social", apply=_r_trust_reveals),
    Rule(name="reveal_gift", tag="physical", apply=_r_reveal_gift),
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
# Constraint helpers
# ---------------------------------------------------------------------------
def valid_combo(place_id: str, offering_id: str, clue_id: str) -> bool:
    if place_id not in PLACES or offering_id not in OFFERINGS or clue_id not in CLUES:
        return False
    place = PLACES[place_id]
    creature = CREATURES[place.creature]
    clue_ok = creature.clue == clue_id
    offering_ok = offering_id in creature.likes
    habitat_ok = creature.habitat == place_id
    return clue_ok and offering_ok and habitat_ok


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id in sorted(PLACES):
        for offering_id in sorted(OFFERINGS):
            for clue_id in sorted(CLUES):
                if valid_combo(place_id, offering_id, clue_id):
                    out.append((place_id, offering_id, clue_id))
    return out


def explain_rejection(place_id: str, offering_id: str, clue_id: str) -> str:
    if place_id not in PLACES:
        return f"(No story: unknown place '{place_id}'.)"
    place = PLACES[place_id]
    creature = CREATURES[place.creature]
    if clue_id in CLUES and creature.clue != clue_id:
        expected = CLUES[creature.clue].label
        got = CLUES[clue_id].label
        return (
            f"(No story: {got} does not fit the hidden creature at {place.label}. "
            f"The foreshadowing clue there should be {expected}.)"
        )
    if offering_id in OFFERINGS and offering_id not in creature.likes:
        return (
            f"(No story: the hidden {creature.label} at {place.label} would not come "
            f"out for {OFFERINGS[offering_id].label}. The offered food must be one it trusts.)"
        )
    return "(No story: this combination does not make a coherent mystery.)"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_solving(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["shared"] += 1
    propagate(sim, narrate=False)
    return {
        "will_reveal": sim.get("creature").meters["revealed"] >= THRESHOLD,
        "will_receive_gift": sim.get("treasure").meters["given"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, elder: Entity, place: Place) -> None:
    world.say(
        f"In the old days, when evening bells were answered by frogs and reeds, "
        f"{child.id} lived with {elder.id} beside {place.phrase}. {place.image}"
    )
    world.say(place.old_word_line)
    child.memes["wonder"] += 1


def shrine_mystery(world: World, child: Entity, elder: Entity, offering: Offering, place: Place) -> None:
    world.say(
        f"Each dusk, {elder.id} set {offering.phrase} on the flat stone there, "
        f"for travelers, birds, or any quiet hungry thing. Yet each morning the food was gone."
    )
    world.say(
        f'"No crumb stays, and no one is ever seen," {child.id} whispered. '
        f'The little mystery made {child.pronoun("possessive")} heart beat fast.'
    )
    child.memes["curiosity"] += 1
    world.facts["mystery"] = True


def foreshadow(world: World, clue: Clue) -> None:
    world.say(clue.hint_line)
    world.get("clue").meters["present"] += 1
    world.get("creature").meters["seen_clue"] += 1


def keep_watch(world: World, child: Entity, elder: Entity) -> None:
    world.say(
        f"That night, instead of hurrying home, {child.id} and {elder.id} waited "
        f"behind a stone lantern and watched the dark grow silver at the edges."
    )
    child.memes["patience"] += 1
    elder.memes["patience"] += 1


def worry_and_choice(world: World, child: Entity, offering: Offering) -> None:
    pred = predict_solving(world)
    world.facts["predicted_reveal"] = pred["will_reveal"]
    world.facts["predicted_gift"] = pred["will_receive_gift"]
    world.say(
        f"When the night grew still, {child.id} held the last {offering.label} close. "
        f'"If I keep it for myself, maybe the thief will stay hidden forever," {child.pronoun()} thought.'
    )
    world.say(
        f"Then {child.pronoun().capitalize()} remembered how the elders said the world opens more easily to an open hand."
    )
    child.memes["greed"] += 0.5


def share(world: World, child: Entity, offering: Offering) -> None:
    child.meters["shared"] += 1
    world.get("offering").meters["shared_piece"] += 1
    world.say(
        f"So {child.id} broke {offering.phrase} in two and laid the sweeter half upon the stone. "
        f'{offering.share_line}'
    )
    propagate(world, narrate=False)
    child.memes["greed"] = 0.0


def reveal(world: World, creature_cfg: CreatureKind, clue: Clue) -> None:
    creature = world.get("creature")
    if creature.meters["revealed"] < THRESHOLD:
        raise StoryError("(Internal story error: the creature never revealed itself.)")
    world.say(
        f"At once the clue made sense. {clue.phrase} stirred, and from the shadows came {creature_cfg.phrase}. "
        f"{creature_cfg.hiding_line}"
    )
    world.say(creature_cfg.thanks_line)


def gift(world: World, treasure_cfg: Treasure, child: Entity, place: Place) -> None:
    if world.get("treasure").meters["given"] < THRESHOLD:
        raise StoryError("(Internal story error: the gift was never given.)")
    world.say(
        f"In thanks, the little being left {treasure_cfg.phrase} in {child.id}'s palms. "
        f"{treasure_cfg.ending_line}"
    )
    world.say(
        f"After that, {child.id} never set food on the stone without leaving a fair share, "
        f"and the people of {place.label} said the dusk there felt kinder."
    )


def tell(
    place: Place,
    offering: Offering,
    clue: Clue,
    *,
    child_name: str = "Nia",
    child_gender: str = "girl",
    elder_name: str = "Tarin",
    elder_gender: str = "boy",
    relation: str = "brother",
    seed: Optional[int] = None,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={"relation": relation},
    ))
    elder = world.add(Entity(
        id=elder_name,
        kind="character",
        type=elder_gender,
        label=elder_name,
        role="elder",
        attrs={"relation": relation},
    ))
    creature_cfg = CREATURES[place.creature]
    treasure_cfg = TREASURES[creature_cfg.gift]
    creature = world.add(Entity(
        id="creature",
        kind="thing",
        type="spirit",
        label=creature_cfg.label,
        visible=False,
        attrs={"creature_id": creature_cfg.id, "likes": set(creature_cfg.likes), "clue": creature_cfg.clue},
    ))
    offering_ent = world.add(Entity(
        id="offering",
        kind="thing",
        type="food",
        label=offering.label,
        attrs={"offering_id": offering.id},
    ))
    clue_ent = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue.label,
        attrs={"clue_id": clue.id},
    ))
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type="treasure",
        label=treasure_cfg.label,
        attrs={"treasure_id": treasure_cfg.id},
    ))

    # Initialize rule-read values before any propagation.
    creature.meters["hunger"] = 1.0
    creature.meters["seen_clue"] = 0.0
    creature.meters["left_clue"] = 0.0
    creature.meters["revealed"] = 0.0
    creature.memes["trust"] = 0.0
    child.meters["shared"] = 0.0
    child.memes["kindness"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["wonder"] = 0.0
    child.memes["greed"] = 0.0
    elder.memes["patience"] = 0.0
    clue_ent.meters["present"] = 0.0
    treasure.meters["given"] = 0.0
    offering_ent.meters["shared_piece"] = 0.0

    world.facts.update(
        place=place,
        offering_cfg=offering,
        clue_cfg=clue,
        creature_cfg=creature_cfg,
        treasure_cfg=treasure_cfg,
        child=child,
        elder=elder,
        relation=relation,
        seed=seed,
    )

    introduce(world, child, elder, place)
    shrine_mystery(world, child, elder, offering, place)

    world.para()
    foreshadow(world, clue)
    keep_watch(world, child, elder)
    worry_and_choice(world, child, offering)

    world.para()
    share(world, child, offering)
    reveal(world, creature_cfg, clue)
    gift(world, treasure_cfg, child, place)

    world.facts.update(
        solved=creature.meters["revealed"] >= THRESHOLD,
        shared=child.meters["shared"] >= THRESHOLD,
        gift_given=treasure.meters["given"] >= THRESHOLD,
        clue_present=clue_ent.meters["present"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "cedar_shrine": Place(
        id="cedar_shrine",
        label="the Cedar Shrine",
        phrase="the Cedar Shrine at the foot of the hill",
        image="Three cedars leaned over the mossy roof as if they were listening to prayers.",
        old_word_line='The grandmothers called that hour "talk-dim," the moment when even stones seemed ready to whisper back.',
        creature="moss_tortoise",
        tags={"shrine", "cedar", "twilight"},
    ),
    "reed_bank": Place(
        id="reed_bank",
        label="the Reed Bank",
        phrase="the Reed Bank where the river bent like a sleeping snake",
        image="Reeds bowed over black water, and little fish made rings under the moon.",
        old_word_line='The fishers called it "talk-dim," because the reeds rubbed together there and sounded like secret voices.',
        creature="river_otter",
        tags={"river", "reed", "twilight"},
    ),
    "moon_steps": Place(
        id="moon_steps",
        label="the Moon Steps",
        phrase="the Moon Steps carved above the valley spring",
        image="Old white stones climbed toward the sky, and each step held a pool of fading light.",
        old_word_line='The herdsmen used the old word "talk-dim" for that pale hour when the hills muttered before night.',
        creature="cloud_fox",
        tags={"mountain", "moon", "twilight"},
    ),
}

OFFERINGS = {
    "sesame_cake": Offering(
        id="sesame_cake",
        label="sesame cake",
        phrase="a round sesame cake",
        scent="warm and nutty",
        share_line="Its warm, nutty smell drifted softly into the dark.",
        liked_by={"moss_tortoise"},
        tags={"cake", "sharing"},
    ),
    "pear_slice": Offering(
        id="pear_slice",
        label="pear slice",
        phrase="a moon-bright slice of pear",
        scent="sweet and cool",
        share_line="Sweet juice shone on the stone like a little crescent moon.",
        liked_by={"river_otter"},
        tags={"pear", "sharing"},
    ),
    "plum_bun": Offering(
        id="plum_bun",
        label="plum bun",
        phrase="a soft plum bun",
        scent="sweet and dark",
        share_line="A purple drop of plum jam slipped down the stone and glimmered like dusk.",
        liked_by={"cloud_fox"},
        tags={"bun", "sharing"},
    ),
}

CLUES = {
    "moss_crumbs": Clue(
        id="moss_crumbs",
        label="moss crumbs",
        phrase="a trail of soft green moss crumbs",
        hint_line="In the morning, a trail of soft green moss crumbs lay on the stone, though no moss grew there at all.",
        reveals="moss_tortoise",
        tags={"moss", "clue"},
    ),
    "wet_tracks": Clue(
        id="wet_tracks",
        label="wet tracks",
        phrase="a string of wet little tracks",
        hint_line="By dawn, the stone shone with a string of wet little tracks, as if river water had walked there on tiny feet.",
        reveals="river_otter",
        tags={"water", "clue"},
    ),
    "silver_fur": Clue(
        id="silver_fur",
        label="silver fur",
        phrase="one thread of silver fur",
        hint_line="Caught in a crack of the step was one thread of silver fur, bright as moonlight and gone when touched.",
        reveals="cloud_fox",
        tags={"fur", "clue"},
    ),
}

CREATURES = {
    "moss_tortoise": CreatureKind(
        id="moss_tortoise",
        label="moss tortoise",
        phrase="a tiny moss tortoise no bigger than a teacup",
        hiding_line="Its shell carried living moss, and two shy lantern-eyes blinked from under the green.",
        thanks_line='"I only borrowed what was left for no one," it said in a voice like bark rubbed by rain. "But a shared bite is a true gift."',
        gift="cedar_seed",
        habitat="cedar_shrine",
        likes={"sesame_cake"},
        clue="moss_crumbs",
        tags={"tortoise", "forest", "spirit"},
    ),
    "river_otter": CreatureKind(
        id="river_otter",
        label="river otter spirit",
        phrase="a small river otter spirit with whiskers bright with spray",
        hiding_line="Water beaded on its fur, but none of it fell to the ground.",
        thanks_line='"I was hungry and ashamed to ask," it murmured. "Your shared pear tasted of kindness."',
        gift="river_shell",
        habitat="reed_bank",
        likes={"pear_slice"},
        clue="wet_tracks",
        tags={"otter", "river", "spirit"},
    ),
    "cloud_fox": CreatureKind(
        id="cloud_fox",
        label="cloud fox",
        phrase="a cloud fox kit with moon-pale paws",
        hiding_line="Its tail looked like a strand of fog that had learned to curl and breathe.",
        thanks_line='"Many wait with traps," it whispered. "You waited with half of your supper. So I may answer you plainly."',
        gift="moon_bead",
        habitat="moon_steps",
        likes={"plum_bun"},
        clue="silver_fur",
        tags={"fox", "mountain", "spirit"},
    ),
}

TREASURES = {
    "cedar_seed": Treasure(
        id="cedar_seed",
        label="cedar seed",
        phrase="a cedar seed warm as if it held a summer noon inside",
        ending_line="They planted it beside the shrine, and in the years to come the tree grew straight and fragrant, a sign that kindness had taken root.",
        tags={"seed", "gift"},
    ),
    "river_shell": Treasure(
        id="river_shell",
        label="river shell",
        phrase="a spiral river shell that sang when held to the ear",
        ending_line="Whenever the river ran high, the shell sang first, and the village children knew to tie their boats well.",
        tags={"shell", "gift"},
    ),
    "moon_bead": Treasure(
        id="moon_bead",
        label="moon bead",
        phrase="a pale moon bead that glowed whenever someone spoke truthfully",
        ending_line="It hung by the doorway after that, and lies always seemed too small to live beneath its light.",
        tags={"bead", "gift"},
    ),
}

GIRL_NAMES = ["Nia", "Luma", "Sena", "Mira", "Tali", "Ira"]
BOY_NAMES = ["Tarin", "Rian", "Keto", "Maro", "Sorin", "Pavel"]
RELATIONS = ["brother", "sister", "cousin", "friend"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    offering: str
    clue: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_gender: str
    relation: str
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
    "sharing": [
        (
            "Why can sharing solve a problem better than grabbing?",
            "Sharing can show another person or creature that you are safe and kind. When fear softens, it becomes easier to tell the truth and solve the real problem."
        )
    ],
    "clue": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that points toward an answer. It helps you notice what happened, even before you see everything clearly."
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is an early hint that something important will happen later. A strange track or shining thread can quietly prepare you for the mystery's answer."
        )
    ],
    "otter": [
        (
            "What is an otter?",
            "An otter is a playful river animal with fur, whiskers, and strong feet for swimming. It likes water and often slips in and out of streams very quietly."
        )
    ],
    "fox": [
        (
            "What is a fox known for in old tales?",
            "In old tales, a fox is often quick, careful, and hard to catch. Writers use foxes in mysteries because they can seem clever and hidden."
        )
    ],
    "tortoise": [
        (
            "What is a tortoise?",
            "A tortoise is a slow animal with a hard shell on its back. In stories, a tortoise can feel old, patient, and wise."
        )
    ],
    "shell": [
        (
            "What is a shell?",
            "A shell is a hard covering made by some water animals. People sometimes keep pretty shells because they sound or look special."
        )
    ],
    "seed": [
        (
            "What does a seed become?",
            "A seed can grow into a plant or a tree when it has soil, water, and time. Small gifts can become big living things."
        )
    ],
    "moon": [
        (
            "Why do old stories use moonlight so often?",
            "Moonlight makes ordinary places look strange and quiet, so it fits mystery stories well. It can make a clue seem small and magical at the same time."
        )
    ],
}
KNOWLEDGE_ORDER = ["sharing", "clue", "foreshadowing", "tortoise", "otter", "fox", "shell", "seed", "moon"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    offering = f["offering_cfg"]
    clue = f["clue_cfg"]
    creature = f["creature_cfg"]
    return [
        f'Write a short mythic story for a 3-to-5-year-old that includes the word "talk-dim" and a small mystery at {place.label}.',
        f"Tell a gentle mystery where food keeps disappearing, a clue like {clue.label} foreshadows the answer, and a child solves the problem by sharing {offering.label}.",
        f"Write a child-facing myth where a hidden {creature.label} is not caught by force but invited out by kindness."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    place = f["place"]
    offering = f["offering_cfg"]
    clue = f["clue_cfg"]
    creature = f["creature_cfg"]
    treasure = f["treasure_cfg"]
    relation = f["relation"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {elder.id} near {place.label}. They were trying to learn who had been taking the food from the stone."
        ),
        (
            "What was the mystery?",
            f"The mystery was that {offering.phrase} kept vanishing from the stone each night. The missing food made the children wonder whether a thief, a bird, or something magical was visiting."
        ),
        (
            "What clue came first?",
            f"The first clue was {clue.phrase}. That small sign mattered because it hinted at the hidden visitor before anyone could see it."
        ),
        (
            f"How did {child.id} solve the mystery?",
            f"{child.id} solved it by sharing part of the {offering.label} instead of hiding it away. The open-handed choice helped the shy creature trust {child.pronoun('object')} enough to come out."
        ),
    ]
    if f.get("solved"):
        qa.append((
            "Who was taking the food?",
            f"It was {creature.phrase}. The earlier clue fit that creature exactly, which is why the mystery suddenly made sense when it appeared."
        ))
    if f.get("gift_given"):
        qa.append((
            f"What did {child.id} receive at the end?",
            f"{child.pronoun('subject').capitalize()} received {treasure.phrase}. The gift showed that kindness had changed the meeting from a fearful mystery into a friendship."
        ))
    qa.append((
        f"Why was sharing important in this story?",
        f"Sharing was important because it turned suspicion into trust. Instead of catching the hidden being like an enemy, {child.id} treated it like a hungry neighbor."
    ))
    if relation in {"brother", "sister", "cousin", "friend"}:
        qa.append((
            f"What were {child.id} and {elder.id} doing together?",
            f"They were keeping watch together and trying to understand the clue. Working side by side made the mystery feel brave instead of lonely."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    creature = f["creature_cfg"]
    treasure = f["treasure_cfg"]
    tags: set[str] = {"sharing", "clue", "foreshadowing", "moon"}
    if creature.id == "moss_tortoise":
        tags.add("tortoise")
    elif creature.id == "river_otter":
        tags.add("otter")
    elif creature.id == "cloud_fox":
        tags.add("fox")
    if treasure.id == "river_shell":
        tags.add("shell")
    if treasure.id == "cedar_seed":
        tags.add("seed")

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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {}
            for k, v in ent.attrs.items():
                if isinstance(v, set):
                    shown[k] = sorted(v)
                elif v:
                    shown[k] = v
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        bits.append(f"visible={ent.visible}")
        lines.append(f"  {ent.id:9} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% coherent combinations
valid(P,O,C) :- place(P), offering(O), clue(C),
                creature_at(P,K), likes(K,O), clue_of(K,C), habitat(K,P).

% outcome model for this world
shared        :- choose_share.
trust         :- shared, chosen_place(P), creature_at(P,K), chosen_offering(O), likes(K,O).
revealed      :- trust.
gift_given    :- revealed.

#show valid/3.
#show shared/0.
#show trust/0.
#show revealed/0.
#show gift_given/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in sorted(PLACES):
        lines.append(asp.fact("place", pid))
    for oid in sorted(OFFERINGS):
        lines.append(asp.fact("offering", oid))
    for cid in sorted(CLUES):
        lines.append(asp.fact("clue", cid))
    for kid, creature in CREATURES.items():
        lines.append(asp.fact("creature", kid))
        lines.append(asp.fact("habitat", kid, creature.habitat))
        lines.append(asp.fact("clue_of", kid, creature.clue))
        for oid in sorted(creature.likes):
            lines.append(asp.fact("likes", kid, oid))
    for pid, place in PLACES.items():
        lines.append(asp.fact("creature_at", pid, place.creature))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> dict[str, bool]:
    import asp

    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_offering", params.offering),
        "choose_share.",
    ])
    model = asp.one_model(asp_program(extra))
    return {
        "shared": bool(asp.atoms(model, "shared")),
        "trust": bool(asp.atoms(model, "trust")),
        "revealed": bool(asp.atoms(model, "revealed")),
        "gift_given": bool(asp.atoms(model, "gift_given")),
    }


# ---------------------------------------------------------------------------
# Parser / resolve / generate
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="cedar_shrine",
        offering="sesame_cake",
        clue="moss_crumbs",
        child_name="Nia",
        child_gender="girl",
        elder_name="Tarin",
        elder_gender="boy",
        relation="brother",
        seed=None,
    ),
    StoryParams(
        place="reed_bank",
        offering="pear_slice",
        clue="wet_tracks",
        child_name="Mira",
        child_gender="girl",
        elder_name="Rian",
        elder_gender="boy",
        relation="cousin",
        seed=None,
    ),
    StoryParams(
        place="moon_steps",
        offering="plum_bun",
        clue="silver_fur",
        child_name="Luma",
        child_gender="girl",
        elder_name="Sorin",
        elder_gender="boy",
        relation="friend",
        seed=None,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic mystery storyworld: a vanished offering, a clue, and a problem solved by sharing."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--offering", choices=sorted(OFFERINGS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-gender", choices=["girl", "boy"])
    ap.add_argument("--relation", choices=sorted(RELATIONS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.offering and args.clue:
        if not valid_combo(args.place, args.offering, args.clue):
            raise StoryError(explain_rejection(args.place, args.offering, args.clue))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.offering is None or combo[1] == args.offering)
        and (args.clue is None or combo[2] == args.clue)
    ]
    if not combos:
        place_id = args.place or next(iter(PLACES))
        offering_id = args.offering or next(iter(OFFERINGS))
        clue_id = args.clue or next(iter(CLUES))
        if args.place or args.offering or args.clue:
            raise StoryError(explain_rejection(place_id, offering_id, clue_id))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, offering_id, clue_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    elder_name = args.elder_name or _pick_name(rng, elder_gender, avoid=child_name)
    relation = args.relation or rng.choice(RELATIONS)
    return StoryParams(
        place=place_id,
        offering=offering_id,
        clue=clue_id,
        child_name=child_name,
        child_gender=child_gender,
        elder_name=elder_name,
        elder_gender=elder_gender,
        relation=relation,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    required = {
        "place": params.place,
        "offering": params.offering,
        "clue": params.clue,
    }
    for field_name, value in required.items():
        if not value:
            raise StoryError(f"(No story: missing required parameter '{field_name}'.)")
    if not valid_combo(params.place, params.offering, params.clue):
        raise StoryError(explain_rejection(params.place, params.offering, params.clue))

    world = tell(
        PLACES[params.place],
        OFFERINGS[params.offering],
        CLUES[params.clue],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_name=params.elder_name,
        elder_gender=params.elder_gender,
        relation=params.relation,
        seed=params.seed,
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


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------
def outcome_of(params: StoryParams) -> dict[str, bool]:
    sample = generate(params)
    world = sample.world
    if world is None:
        raise StoryError("(Internal story error: missing world for verification.)")
    return {
        "shared": bool(world.facts.get("shared")),
        "revealed": bool(world.facts.get("solved")),
        "gift_given": bool(world.facts.get("gift_given")),
    }


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: valid combo gate matches ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    for params in CURATED:
        try:
            py = outcome_of(params)
            cl = asp_outcome(params)
        except Exception as err:
            print(f"FAIL: verification crashed on {params}: {err}")
            return 1
        if not py["shared"] or not py["revealed"] or not py["gift_given"]:
            print(f"FAIL: generated outcome missing expected story beats for {params}.")
            return 1
        if not cl["shared"] or not cl["revealed"] or not cl["gift_given"]:
            print(f"FAIL: ASP outcome missing expected story beats for {params}.")
            return 1
    print(f"OK: ASP outcome agrees with curated generated stories ({len(CURATED)} cases).")

    smoke_args = build_parser().parse_args([])
    try:
        smoke_params = resolve_params(smoke_args, random.Random(123))
        smoke_params.seed = 123
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        emit(smoke_sample, trace=False, qa=False, header="")
    except Exception as err:
        print(f"FAIL: normal generation smoke test crashed: {err}")
        return 1

    print("OK: normal generation smoke test passed.")
    return rc


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, offering, clue) combinations:\n")
        for place_id, offering_id, clue_id in combos:
            print(f"  {place_id:12} {offering_id:12} {clue_id}")
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
            header = f"### {p.child_name}: {p.place}, {p.offering}, {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
