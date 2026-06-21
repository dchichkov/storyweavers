#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/editor_seaside_promenade_sharing_myth.py
===================================================================

A standalone story world about two children on a seaside promenade, a bright
gift from the shore, an editor who remembers an old sea-myth, and the question
of whether a treasure grows brighter when it is shared.

The world models a small social truth with a mythic gloss:
- some finds are single things and must be shared by taking turns;
- some finds are many things and can be divided fairly;
- a child may share at once after a warning, share only after an omen, or cling
  too hard and miss the blessing.

Run it
------
    python storyworlds/worlds/gpt-5.4/editor_seaside_promenade_sharing_myth.py
    python storyworlds/worlds/gpt-5.4/editor_seaside_promenade_sharing_myth.py --gift moon_shell --method split
    python storyworlds/worlds/gpt-5.4/editor_seaside_promenade_sharing_myth.py --all
    python storyworlds/worlds/gpt-5.4/editor_seaside_promenade_sharing_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/editor_seaside_promenade_sharing_myth.py --verify
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
GENEROSITY_INIT = 4.0
STINGY_TRAITS = {"possessive", "jealous", "fierce"}
OPEN_TRAITS = {"gentle", "kind", "thoughtful", "generous"}


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Gift:
    id: str
    label: str
    phrase: str
    amount_kind: str
    find_text: str
    cling_text: str
    shared_image: str
    missed_image: str
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
class ShareMethod:
    id: str
    label: str
    handles: set[str] = field(default_factory=set)
    action_text: str = ""
    qa_text: str = ""
    blessing_text: str = ""
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
class Omen:
    id: str
    strength: int
    text: str
    lesson: str
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
        return [e for e in self.entities.values() if e.role in {"finder", "friend"}]

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


def _r_exclusion_hurts(world: World) -> list[str]:
    finder = world.get("finder")
    friend = world.get("friend")
    gift = world.get("gift")
    if finder.meters["holding"] < THRESHOLD or gift.meters["shared"] >= THRESHOLD:
        return []
    sig = ("hurt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["hurt"] += 1
    friend.memes["left_out"] += 1
    return ["__hurt__"]


def _r_sharing_blesses(world: World) -> list[str]:
    gift = world.get("gift")
    sea = world.get("sea")
    if gift.meters["shared"] < THRESHOLD:
        return []
    sig = ("bless",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sea.meters["blessing"] += 1
    gift.meters["gleam"] += 1
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["wonder"] += 1
    return ["__blessing__"]


CAUSAL_RULES = [
    Rule(name="exclusion_hurts", tag="social", apply=_r_exclusion_hurts),
    Rule(name="sharing_blesses", tag="mythic", apply=_r_sharing_blesses),
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


def method_fits(gift: Gift, method: ShareMethod) -> bool:
    return gift.amount_kind in method.handles


def initial_generosity(trait: str) -> float:
    if trait in OPEN_TRAITS:
        return 5.0
    if trait in STINGY_TRAITS:
        return 2.0
    return GENEROSITY_INIT


def should_share_on_warning(trait: str) -> bool:
    return initial_generosity(trait) + 1 > 4


def outcome_for(trait: str, omen: Omen) -> str:
    base = initial_generosity(trait)
    if base + 1 > 4:
        return "shared_after_warning"
    if base + 1 + omen.strength > 4:
        return "shared_after_omen"
    return "kept_all"


def predict_hurt(world: World) -> dict:
    sim = world.copy()
    sim.get("finder").meters["holding"] += 1
    propagate(sim, narrate=False)
    return {
        "friend_hurt": sim.get("friend").memes["hurt"] >= THRESHOLD,
        "left_out": sim.get("friend").memes["left_out"] >= THRESHOLD,
    }


def opening(world: World, finder: Entity, friend: Entity, gift: Gift) -> None:
    for kid in (finder, friend):
        kid.memes["delight"] += 1
    world.say(
        f"At the seaside promenade, where salt wind tugged at ribbons and the railings "
        f"shone with old spray, {finder.id} and {friend.id} walked slowly and watched "
        f"the tide leave its little secrets behind."
    )
    world.say(gift.find_text.format(finder=finder.id, friend=friend.id))
    world.say(
        f"For a breath, the morning felt like the beginning of one of the old stories."
    )


def claim(world: World, finder: Entity, gift: Gift) -> None:
    finder.meters["holding"] += 1
    finder.memes["greed"] += 1
    world.say(
        f"But then {finder.id} curled both hands around the {gift.label}. "
        f'"It is mine," {finder.pronoun()} said. {gift.cling_text}'
    )
    propagate(world, narrate=False)


def ask_to_share(world: World, friend: Entity, method: ShareMethod) -> None:
    world.say(
        f'{friend.id} stepped nearer. "Could we share it {method.label}?" '
        f"{friend.pronoun().capitalize()} asked."
    )
    if friend.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{friend.id}'s face had gone quiet, the way water goes quiet before a wave folds."
        )


def editor_warning(world: World, editor: Entity, finder: Entity, friend: Entity) -> None:
    pred = predict_hurt(world)
    world.facts["predicted_hurt"] = pred["friend_hurt"]
    finder.memes["pause"] += 1
    world.say(
        f"From the little bookstall by the lamps, an old editor looked up from a stack "
        f"of sea-tales. {editor.pronoun().capitalize()} had spent so many years mending "
        f"broken stories that people said {editor.pronoun()} could hear when a moment "
        f"was about to go wrong."
    )
    world.say(
        f'"In the oldest promenade myths," {editor.pronoun()} said, "the sea does not '
        f'keep bright gifts for a closed fist. When one child is shut out, the shine '
        f'grows lonely."'
    )
    if pred["friend_hurt"]:
        world.say(
            f"{editor.pronoun().capitalize()} glanced at {friend.id}. "
            f'"Look well. {friend.id} is already hurting."'
        )


def share_now(world: World, finder: Entity, friend: Entity, gift: Gift, method: ShareMethod) -> None:
    finder.meters["holding"] = 0.0
    gift.meters["shared"] += 1
    finder.memes["generosity"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"{finder.id} opened {finder.pronoun('possessive')} hands at once. "
        f"{method.action_text.format(finder=finder.id, friend=friend.id, gift=gift.label)}"
    )
    propagate(world, narrate=False)


def omen_arrives(world: World, omen: Omen) -> None:
    world.get("sea").meters["omen"] += 1
    world.say(omen.text)


def share_after_omen(world: World, finder: Entity, friend: Entity, gift: Gift, method: ShareMethod) -> None:
    finder.meters["holding"] = 0.0
    gift.meters["shared"] += 1
    finder.memes["shame"] += 1
    finder.memes["generosity"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"{finder.id} looked from the sea to {friend.id}, and then back to the treasure. "
        f'"I do not want the shine to go lonely," {finder.pronoun()} whispered.'
    )
    world.say(method.action_text.format(finder=finder.id, friend=friend.id, gift=gift.label))
    propagate(world, narrate=False)


def keep_all(world: World, finder: Entity, friend: Entity, gift: Gift, omen: Omen) -> None:
    finder.memes["stubborn"] += 1
    world.say(
        f"But {finder.id} tightened {finder.pronoun('possessive')} hands and turned away from the sea. "
        f'{finder.pronoun().capitalize()} pretended not to hear the old warning.'
    )
    world.say(
        f"{omen.lesson} {gift.missed_image}"
    )
    friend.memes["sadness"] += 1


def blessing(world: World, gift: Gift, method: ShareMethod) -> None:
    if world.get("gift").meters["shared"] < THRESHOLD:
        return
    world.say(method.blessing_text.format(gift=gift.label))
    world.say(gift.shared_image)


def ending_shared(world: World, finder: Entity, friend: Entity) -> None:
    world.say(
        f"After that, {finder.id} and {friend.id} did not walk like rivals hunting one bright thing. "
        f"They walked like two small keepers of the promenade, ready to pass wonder from hand to hand."
    )


def ending_missed(world: World, finder: Entity, friend: Entity) -> None:
    world.say(
        f"They still walked home together, but there was a space between them where the morning's magic had been. "
        f"Even the sea sounded farther away."
    )


GIFTS = {
    "moon_shell": Gift(
        id="moon_shell",
        label="moon shell",
        phrase="a moon-pale shell with a silver lip",
        amount_kind="single",
        find_text="{finder} spotted a moon-pale shell caught in a crack by the promenade steps and lifted it carefully before the next wash could claim it.",
        cling_text="The shell made a tiny sea-sound against the warm skin of the clenched palms.",
        shared_image="Then the shell whispered in turn to each ear, and both children laughed as if the tide had told them the same secret twice.",
        missed_image="By the time the gulls wheeled past the lamps, the shell in the fist looked only like an ordinary shell.",
        tags={"shell", "sea"},
    ),
    "sea_glass": Gift(
        id="sea_glass",
        label="sea glass",
        phrase="a little handful of green and blue sea glass",
        amount_kind="many",
        find_text="{finder} found a little nest of green and blue sea glass glimmering at the edge of the stones, each piece softened by patient waves.",
        cling_text="The smooth pieces clicked together like tiny cold bells.",
        shared_image="In two open palms the glass caught the sun so brightly that the paving stones seemed sprinkled with bits of calm water.",
        missed_image="The colors stayed pretty, but the handful looked smaller and duller than it had a moment before.",
        tags={"sea_glass", "sea"},
    ),
    "amber_pebbles": Gift(
        id="amber_pebbles",
        label="amber pebbles",
        phrase="three amber pebbles warm as trapped sunlight",
        amount_kind="many",
        find_text="{friend} was the first to gasp, but {finder} knelt and picked up three amber pebbles the tide had rolled into a bright line beside the railing.",
        cling_text="They glowed between the fingers like tiny pieces of sunset.",
        shared_image="Shared out between them, the pebbles looked less like loot and more like lanterns for a very small legend.",
        missed_image="Soon the pebbles looked like plain stones that happened to be the right color.",
        tags={"pebbles", "sea"},
    ),
    "whisper_conch": Gift(
        id="whisper_conch",
        label="whisper conch",
        phrase="a curled little conch no bigger than a plum",
        amount_kind="single",
        find_text="{finder} reached under a bench and drew out a curled little conch, still wet, as if the tide had hidden it there for a careful child.",
        cling_text="The conch held one cool bead of seawater in its throat.",
        shared_image="Each time it passed from one child to the other, the conch seemed to hold a deeper hush, like a story being read aloud the right way.",
        missed_image="The tiny bead of seawater slipped out and the conch's magic hush was gone.",
        tags={"conch", "sea"},
    ),
}

METHODS = {
    "turns": ShareMethod(
        id="turns",
        label="by taking turns",
        handles={"single"},
        action_text="{finder} offered the {gift} first, then promised that each would hold it for one hundred heartbeats before passing it on.",
        qa_text="They shared it by taking turns holding and admiring it.",
        blessing_text="A soft wave sounded against the sea wall, and the old shell-song seemed to grow clearer each time the {gift} changed hands.",
        tags={"taking_turns", "sharing"},
    ),
    "split": ShareMethod(
        id="split",
        label="by dividing it fairly",
        handles={"many"},
        action_text="{finder} knelt on the warm stones and divided the {gift} into two fair little heaps, watching carefully until both looked right.",
        qa_text="They shared it by dividing it into two fair parts.",
        blessing_text="A bright wash of light crossed the promenade, and each share of the {gift} looked richer for being chosen fairly.",
        tags={"dividing", "sharing"},
    ),
}

OMENS = {
    "gull_shadow": Omen(
        id="gull_shadow",
        strength=1,
        text="Just then a gull swept low across the promenade, and its shadow crossed the treasure so swiftly that the shine seemed to blink.",
        lesson="The editor closed the bookstall ledger and said, \"Even gulls know when brightness is being hoarded.\"",
        tags={"gull", "sea"},
    ),
    "foam_circle": Omen(
        id="foam_circle",
        strength=2,
        text="A curl of foam climbed higher than the last wave, reached the bottom stair, and left a white ring around the children's shoes like a warning drawn in milk.",
        lesson="The editor whispered, \"When the sea draws a circle, it is asking whether the gift will stay locked inside one pair of hands.\"",
        tags={"foam", "sea"},
    ),
    "bell_wind": Omen(
        id="bell_wind",
        strength=2,
        text="A wind came off the water and shook the little bell above the bookstall, though no other bell along the promenade moved.",
        lesson="The editor touched the old brass sound and murmured, \"That is the sea's small bell. It rings for closed hands.\"",
        tags={"wind", "sea"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Tessa", "Ayla", "Ivy", "Sana", "Poppy"]
BOY_NAMES = ["Leo", "Milo", "Tarin", "Nico", "Evan", "Jude", "Oren", "Finn"]
TRAITS = ["gentle", "kind", "thoughtful", "curious", "careful", "possessive", "jealous", "fierce"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for gid, gift in GIFTS.items():
        for mid, method in METHODS.items():
            if method_fits(gift, method):
                combos.append((gid, mid))
    return combos


@dataclass
class StoryParams:
    gift: str
    method: str
    omen: str
    finder: str
    finder_gender: str
    friend: str
    friend_gender: str
    trait: str
    editor_name: str = "Maris"
    editor_gender: str = "woman"
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


def tell(
    gift: Gift,
    method: ShareMethod,
    omen: Omen,
    finder_name: str = "Lina",
    finder_gender: str = "girl",
    friend_name: str = "Leo",
    friend_gender: str = "boy",
    trait: str = "thoughtful",
    editor_name: str = "Maris",
    editor_gender: str = "woman",
) -> World:
    world = World()
    finder = world.add(Entity(
        id="finder",
        kind="character",
        type=finder_gender,
        label=finder_name,
        role="finder",
        traits=[trait],
        attrs={"display": finder_name},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=["hopeful"],
        attrs={"display": friend_name},
    ))
    editor = world.add(Entity(
        id="editor",
        kind="character",
        type=editor_gender,
        label=editor_name,
        role="editor",
        traits=["wise"],
        attrs={"job": "editor"},
    ))
    sea = world.add(Entity(
        id="sea",
        kind="thing",
        type="sea",
        label="the sea",
        role="sea",
        attrs={},
    ))
    gift_ent = world.add(Entity(
        id="gift",
        kind="thing",
        type="gift",
        label=gift.label,
        role="gift",
        attrs={"amount_kind": gift.amount_kind},
    ))

    finder.meters["holding"] = 0.0
    gift_ent.meters["shared"] = 0.0
    gift_ent.meters["gleam"] = 0.0
    sea.meters["blessing"] = 0.0
    sea.meters["omen"] = 0.0
    friend.memes["hurt"] = 0.0
    friend.memes["left_out"] = 0.0

    opening(world, finder, friend, gift)
    world.para()
    claim(world, finder, gift)
    ask_to_share(world, friend, method)
    editor_warning(world, editor, finder, friend)

    outcome = outcome_for(trait, omen)
    world.para()
    if outcome == "shared_after_warning":
        share_now(world, finder, friend, gift, method)
        blessing(world, gift, method)
        ending_shared(world, finder, friend)
    elif outcome == "shared_after_omen":
        omen_arrives(world, omen)
        share_after_omen(world, finder, friend, gift, method)
        blessing(world, gift, method)
        ending_shared(world, finder, friend)
    else:
        omen_arrives(world, omen)
        keep_all(world, finder, friend, gift, omen)
        ending_missed(world, finder, friend)

    world.facts.update(
        finder=finder,
        friend=friend,
        editor=editor,
        gift_cfg=gift,
        method=method,
        omen=omen,
        outcome=outcome,
        shared=gift_ent.meters["shared"] >= THRESHOLD,
        blessing=sea.meters["blessing"] >= THRESHOLD,
        predicted_hurt=world.facts.get("predicted_hurt", False),
    )
    return world


KNOWLEDGE = {
    "sharing": [
        (
            "Why can sharing make a game feel better?",
            "Sharing lets more than one person belong in the happy moment. When everyone is included, the fun often lasts longer and feels warmer."
        )
    ],
    "taking_turns": [
        (
            "What does taking turns mean?",
            "Taking turns means one person uses or holds something first, and then passes it to the next person. It is a fair way to share one special thing."
        )
    ],
    "dividing": [
        (
            "What does it mean to divide something fairly?",
            "It means splitting something so each person gets a part that feels even and kind. Fair sharing helps people trust each other."
        )
    ],
    "shell": [
        (
            "What is a shell?",
            "A shell is the hard outer home some sea animals make. After the animal is gone, waves can wash the shell onto the shore."
        )
    ],
    "sea_glass": [
        (
            "What is sea glass?",
            "Sea glass is old glass that the sea has rolled and rubbed smooth for a long time. That is why it looks soft and frosted instead of sharp."
        )
    ],
    "pebbles": [
        (
            "What is a pebble?",
            "A pebble is a small smooth stone. Water can polish pebbles by tumbling them again and again."
        )
    ],
    "conch": [
        (
            "What is a conch?",
            "A conch is a kind of sea shell with a curled shape. Some people hold one to their ear because it seems to carry a deep rushing sound."
        )
    ],
    "gull": [
        (
            "What is a gull?",
            "A gull is a seaside bird with strong wings and a sharp call. You often see gulls circling over beaches and promenades."
        )
    ],
    "foam": [
        (
            "What is sea foam?",
            "Sea foam is a frothy white layer that waves can leave behind. It forms when air gets mixed into the water."
        )
    ],
    "wind": [
        (
            "Why does the sea feel windy?",
            "Air often moves strongly near the shore because warm and cool air shift above the land and water. That moving air is the wind you feel on your face."
        )
    ],
    "sea": [
        (
            "Why do things wash up by the sea?",
            "Waves and tides move shells, stones, and little objects along the shore. Then the water leaves some of them behind when it goes back."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "sharing", "taking_turns", "dividing", "shell", "sea_glass", "pebbles",
    "conch", "gull", "foam", "wind", "sea",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    finder = f["finder"]
    friend = f["friend"]
    gift = f["gift_cfg"]
    method = f["method"]
    outcome = f["outcome"]
    if outcome == "kept_all":
        return [
            f'Write a myth-like story for a 3-to-5-year-old set on a seaside promenade that includes the word "editor" and a child who finds {gift.phrase}.',
            f"Tell a promenade myth where {finder.label} refuses to share with {friend.label}, an editor warns about the sea's old law, and the magic goes dim.",
            f"Write a gentle cautionary tale about sharing where one bright seaside find should have been shared {method.label}, but the child clings too tightly."
        ]
    if outcome == "shared_after_omen":
        return [
            f'Write a myth-like story for a 3-to-5-year-old set on a seaside promenade that includes the word "editor" and ends with children sharing {gift.label}.',
            f"Tell a story where {finder.label} first says the treasure is only {finder.pronoun('possessive')}, then an omen from the sea helps {finder.pronoun('object')} choose kindness.",
            f"Write a simple mythic story about sharing {gift.label} {method.label}, with an editor by a bookstall who remembers the old sea stories."
        ]
    return [
        f'Write a myth-like story for a 3-to-5-year-old set on a seaside promenade that includes the word "editor" and teaches sharing.',
        f"Tell a gentle story where {finder.label} finds {gift.phrase}, a friend asks to share, and an editor's warning helps the child choose kindness at once.",
        f"Write a short story in a myth style where a seaside treasure is shared {method.label} and the ending proves the sea loves open hands."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    finder = f["finder"]
    friend = f["friend"]
    editor = f["editor"]
    gift = f["gift_cfg"]
    method = f["method"]
    omen = f["omen"]
    outcome = f["outcome"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {finder.label} and {friend.label}, two children walking on the seaside promenade, and {editor.label}, the old editor at the bookstall. The story follows what happens after they find {gift.phrase}."
        ),
        (
            f"What did {finder.label} find?",
            f"{finder.label} found {gift.phrase}. The treasure looked special because the sea had left it shining on the promenade."
        ),
        (
            f"Why were {friend.label}'s feelings hurt?",
            f"{friend.label}'s feelings were hurt because {finder.label} closed both hands around the {gift.label} and said it was only {finder.pronoun('possessive')}. That left {friend.label} outside the wonder instead of sharing it."
        ),
        (
            "What did the editor say?",
            f"The editor said that in the oldest promenade myths, bright gifts do not stay bright for a closed fist. {editor.pronoun().capitalize()} warned that when one child is shut out, the shine grows lonely."
        ),
    ]
    if outcome == "shared_after_warning":
        qa.append((
            f"How did {finder.label} share the treasure?",
            f"{finder.label} listened right after the warning and shared it {method.label}. {method.qa_text} so both children could belong in the same happy moment."
        ))
        qa.append((
            "How did the ending show that something changed?",
            f"The ending showed change because the sea seemed to bless the shared treasure, and both children walked on like keepers of one story instead of rivals. Sharing turned a grabbed thing into a shared wonder."
        ))
    elif outcome == "shared_after_omen":
        qa.append((
            f"What omen helped {finder.label} change {finder.pronoun('possessive')} mind?",
            f"{omen.text} That strange sign made the warning feel real, so {finder.label} stopped trying to keep everything."
        ))
        qa.append((
            f"Why did the treasure feel brighter after {finder.label} shared it?",
            f"It felt brighter because the sharing invited joy back into the moment. In the story's mythic logic, the sea blesses open hands and not lonely hoarding."
        ))
    else:
        qa.append((
            f"Did {finder.label} share the treasure in the end?",
            f"No. Even after the warning and the omen, {finder.label} kept the {gift.label} to {finder.pronoun('self') if False else 'themself'}."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the magic feeling smaller, not bigger. The children still walked home together, but the space between them proved that keeping everything had cost them the morning's wonder."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"sharing"} | set(world.facts["gift_cfg"].tags) | set(world.facts["method"].tags) | set(world.facts["omen"].tags)
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        gift="moon_shell",
        method="turns",
        omen="foam_circle",
        finder="Lina",
        finder_gender="girl",
        friend="Leo",
        friend_gender="boy",
        trait="gentle",
        editor_name="Maris",
        editor_gender="woman",
    ),
    StoryParams(
        gift="sea_glass",
        method="split",
        omen="gull_shadow",
        finder="Milo",
        finder_gender="boy",
        friend="Ivy",
        friend_gender="girl",
        trait="curious",
        editor_name="Maris",
        editor_gender="woman",
    ),
    StoryParams(
        gift="amber_pebbles",
        method="split",
        omen="bell_wind",
        finder="Nora",
        finder_gender="girl",
        friend="Finn",
        friend_gender="boy",
        trait="possessive",
        editor_name="Maris",
        editor_gender="woman",
    ),
    StoryParams(
        gift="whisper_conch",
        method="turns",
        omen="foam_circle",
        finder="Oren",
        finder_gender="boy",
        friend="Poppy",
        friend_gender="girl",
        trait="fierce",
        editor_name="Maris",
        editor_gender="woman",
    ),
]


def explain_rejection(gift: Gift, method: ShareMethod) -> str:
    if gift.amount_kind == "single":
        return (
            f"(No story: {gift.label} is one special thing, so sharing it by {method.label} "
            f"does not make sense here. Try a method for a single treasure, like taking turns.)"
        )
    return (
        f"(No story: {gift.label} is a little collection, so it should be shared by dividing it fairly, "
        f"not by a single-object method.)"
    )


ASP_RULES = r"""
gift_fits(G, M) :- gift(G), method(M), amount_kind(G, K), handles(M, K).

open_trait(T)   :- trait(T), open_kind(T).
stingy_trait(T) :- trait(T), stingy_kind(T).

base_generosity(5) :- open_trait(T).
base_generosity(2) :- stingy_trait(T).
base_generosity(4) :- trait(T), not open_trait(T), not stingy_trait(T).

share_on_warning :- base_generosity(B), B + 1 > 4.
share_after_omen :- not share_on_warning, base_generosity(B), chosen_omen(O), omen_strength(O, S), B + 1 + S > 4.
kept_all         :- not share_on_warning, not share_after_omen.

outcome(shared_after_warning) :- share_on_warning.
outcome(shared_after_omen)    :- share_after_omen.
outcome(kept_all)             :- kept_all.

valid(G, M) :- gift_fits(G, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("amount_kind", gid, gift.amount_kind))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        for kind in sorted(method.handles):
            lines.append(asp.fact("handles", mid, kind))
    for oid, omen in OMENS.items():
        lines.append(asp.fact("omen", oid))
        lines.append(asp.fact("omen_strength", oid, omen.strength))
    for trait in sorted(OPEN_TRAITS):
        lines.append(asp.fact("open_kind", trait))
    for trait in sorted(STINGY_TRAITS):
        lines.append(asp.fact("stingy_kind", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("trait", params.trait),
        asp.fact("chosen_omen", params.omen),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated empty story.")
    emit(sample, trace=False, qa=False, header="")


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
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_for(p.trait, OMENS[p.omen]))
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a seaside promenade myth about sharing, an editor, and a bright gift from the shore."
    )
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--finder")
    ap.add_argument("--friend")
    ap.add_argument("--finder-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    if args.gift and args.method:
        if not method_fits(GIFTS[args.gift], METHODS[args.method]):
            raise StoryError(explain_rejection(GIFTS[args.gift], METHODS[args.method]))

    combos = [
        combo for combo in valid_combos()
        if (args.gift is None or combo[0] == args.gift)
        and (args.method is None or combo[1] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    gift_id, method_id = rng.choice(sorted(combos))
    omen_id = args.omen or rng.choice(sorted(OMENS))
    trait = args.trait or rng.choice(TRAITS)
    finder_gender = args.finder_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    finder = args.finder or _pick_name(rng, finder_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=finder)

    return StoryParams(
        gift=gift_id,
        method=method_id,
        omen=omen_id,
        finder=finder,
        finder_gender=finder_gender,
        friend=friend,
        friend_gender=friend_gender,
        trait=trait,
        editor_name="Maris",
        editor_gender="woman",
    )


def generate(params: StoryParams) -> StorySample:
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.omen not in OMENS:
        raise StoryError(f"(Unknown omen: {params.omen})")
    if not method_fits(GIFTS[params.gift], METHODS[params.method]):
        raise StoryError(explain_rejection(GIFTS[params.gift], METHODS[params.method]))

    world = tell(
        gift=GIFTS[params.gift],
        method=METHODS[params.method],
        omen=OMENS[params.omen],
        finder_name=params.finder,
        finder_gender=params.finder_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        trait=params.trait,
        editor_name=params.editor_name,
        editor_gender=params.editor_gender,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (gift, method) combos:\n")
        for gift, method in combos:
            print(f"  {gift:14} {method}")
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
            header = f"### {p.finder} & {p.friend}: {p.gift} with {p.method} ({outcome_for(p.trait, OMENS[p.omen])})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
