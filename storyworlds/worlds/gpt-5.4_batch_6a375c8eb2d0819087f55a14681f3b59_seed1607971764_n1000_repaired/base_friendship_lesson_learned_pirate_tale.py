#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/base_friendship_lesson_learned_pirate_tale.py
========================================================================

A standalone story world for a tiny pirate-style tale about friendship, a
pretend base, and a lesson learned. Two children make a pirate hideout and find
some treasure. One child makes a selfish choice that hurts the friendship. The
world model tracks both the physical play space and the children's feelings, so
the middle turn and ending come from simulated state instead of noun swapping.

The core pattern is:

    make a pirate base
    find treasure
    one child excludes the other
    the base-play stops feeling joyful
    the selfish child sees the hurt and repairs the friendship
    the game becomes shared again

Run it
------
    python storyworlds/worlds/gpt-5.4/base_friendship_lesson_learned_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/base_friendship_lesson_learned_pirate_tale.py --base blanket_fort
    python storyworlds/worlds/gpt-5.4/base_friendship_lesson_learned_pirate_tale.py --mistake lock_out
    python storyworlds/worlds/gpt-5.4/base_friendship_lesson_learned_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/base_friendship_lesson_learned_pirate_tale.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/base_friendship_lesson_learned_pirate_tale.py --qa --json
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
KIND_MIN = 2


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class BaseKind:
    id: str
    label: str
    phrase: str
    place: str
    build_line: str
    inside_line: str
    open_level: int
    sturdiness: int
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
    find_line: str
    count_word: str
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
class Mistake:
    id: str
    label: str
    sense: int
    needs_open_at_most: int
    line: str
    hurt_line: str
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


@dataclass
class Repair:
    id: str
    label: str
    helps_lock_out: bool
    helps_claim_all: bool
    action_line: str
    ending_line: str
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
        return [e for e in self.entities.values() if e.role in {"instigator", "friend"}]

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


def _r_hurt_breaks_play(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("instigator")
    b = world.get("friend")
    base = world.get("base")
    if b.memes["left_out"] >= THRESHOLD:
        sig = ("play_falls",)
        if sig not in world.fired:
            world.fired.add(sig)
            base.meters["fun"] -= 1
            a.memes["uneasy"] += 1
            b.memes["sad"] += 1
            out.append("__hurt__")
    return out


def _r_shared_fix(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("instigator")
    b = world.get("friend")
    base = world.get("base")
    treasure = world.get("treasure")
    if treasure.meters["shared"] >= THRESHOLD and a.memes["sorry"] >= THRESHOLD:
        sig = ("shared_fix",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["joy"] += 1
            b.memes["joy"] += 1
            a.memes["uneasy"] = 0.0
            b.memes["sad"] = 0.0
            b.memes["left_out"] = 0.0
            a.memes["friendship"] += 1
            b.memes["friendship"] += 1
            base.meters["fun"] += 2
            out.append("__repaired__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hurt_breaks_play", tag="social", apply=_r_hurt_breaks_play),
    Rule(name="shared_fix", tag="social", apply=_r_shared_fix),
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


def supports_mistake(base_kind: BaseKind, mistake: Mistake) -> bool:
    return base_kind.open_level <= mistake.needs_open_at_most


def repair_matches(mistake: Mistake, repair: Repair) -> bool:
    if mistake.id == "lock_out":
        return repair.helps_lock_out
    return repair.helps_claim_all


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for base_id, base_kind in BASES.items():
        for mistake_id, mistake in MISTAKES.items():
            if not supports_mistake(base_kind, mistake):
                continue
            for repair_id, repair in REPAIRS.items():
                if repair_matches(mistake, repair) and repair_kind(repair) >= KIND_MIN:
                    combos.append((base_id, mistake_id, repair_id))
    return combos


def repair_kind(repair: Repair) -> int:
    return 2 if repair.id in {"apology_share", "invite_and_split", "rebuild_together"} else 0


def predict_hurt(world: World, mistake: Mistake) -> dict:
    sim = world.copy()
    apply_mistake(sim, mistake, narrate=False)
    return {
        "left_out": sim.get("friend").memes["left_out"] >= THRESHOLD,
        "fun": sim.get("base").meters["fun"],
    }


def opening(world: World, a: Entity, b: Entity, base_kind: BaseKind) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["friendship"] += 1
    world.say(
        f"One bright afternoon, {a.id} and {b.id} decided to be pirates together. "
        f"They made {base_kind.phrase} at {base_kind.place} and called it their pirate base."
    )
    world.say(base_kind.build_line)
    world.say(base_kind.inside_line)


def discover_treasure(world: World, a: Entity, b: Entity, treasure: Treasure) -> None:
    world.get("treasure").meters["found"] += 1
    world.say(
        f"While they searched for secret loot, {a.id} spotted {treasure.find_line}. "
        f'"Treasure!" {a.id} cried. {b.id} clapped and hurried over.'
    )


def warn_heart(world: World, a: Entity, b: Entity, mistake: Mistake) -> None:
    pred = predict_hurt(world, mistake)
    world.facts["predicted_left_out"] = pred["left_out"]
    world.facts["predicted_fun"] = pred["fun"]
    if mistake.id == "lock_out":
        world.say(
            f'{b.id} slowed by the doorway. "{a.id}, a pirate base is more fun when we both fit," '
            f'{b.pronoun()} said.'
        )
    else:
        world.say(
            f'{b.id} looked at the treasure and then at {a.id}. '
            f'"Real friends share the treasure map," {b.pronoun()} said softly.'
        )


def apply_mistake(world: World, mistake: Mistake, narrate: bool = True) -> None:
    a = world.get("instigator")
    b = world.get("friend")
    base = world.get("base")
    treasure = world.get("treasure")
    a.memes["greed"] += 1
    b.memes["left_out"] += 1
    if mistake.id == "lock_out":
        base.meters["open"] = 0.0
    else:
        treasure.meters["shared"] = 0.0
    propagate(world, narrate=narrate)
    if narrate:
        world.say(mistake.line)
        world.say(mistake.hurt_line)


def notice_hurt(world: World, a: Entity, b: Entity, base_kind: BaseKind, treasure: Treasure) -> None:
    world.say(
        f"Then the pirate base did not feel bright anymore. {a.id} looked at {b.id}'s face and saw "
        f"that the game had gone quiet."
    )
    if world.get("base").meters["fun"] < THRESHOLD:
        world.say(
            f"The {base_kind.label} was still standing, and the {treasure.label} was still there, "
            f"but lonely play felt smaller than shared play."
        )


def apply_repair(world: World, repair: Repair, treasure: Treasure, base_kind: BaseKind) -> None:
    a = world.get("instigator")
    b = world.get("friend")
    base = world.get("base")
    a.memes["sorry"] += 1
    base.meters["open"] = 1.0
    treasure.meters["shared"] = 1.0
    world.say(repair.action_line.format(a=a.id, b=b.id, treasure=treasure.label, base=base_kind.label))
    propagate(world, narrate=False)
    world.say(
        f'{b.id} looked surprised, then smiled a little. "{repair.ending_line}"'
    )


def ending(world: World, a: Entity, b: Entity, base_kind: BaseKind, treasure: Treasure, mistake: Mistake) -> None:
    world.say(
        f"Soon the two friends were back inside their pirate base, shoulder to shoulder, "
        f"counting the {treasure.count_word} treasure together."
    )
    world.say(
        f"They learned that {mistake.lesson} Friendship made the best treasure of all."
    )
    if base_kind.id == "blanket_fort":
        world.say("The blanket roof glowed gold in the late light, and their shared whispers sounded brave and warm.")
    elif base_kind.id == "sand_cove":
        world.say("The little sand walls held their tiny shells in a neat row, and two happy pirate captains watched the waves.")
    else:
        world.say("The crate walls of the hideout looked grand again, because a base feels strongest when friends build it together.")


def tell(
    *,
    base_kind: BaseKind,
    treasure: Treasure,
    mistake: Mistake,
    repair: Repair,
    instigator_name: str,
    instigator_gender: str,
    friend_name: str,
    friend_gender: str,
    parent_type: str,
    friend_trait: str,
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator_name,
        role="instigator",
        traits=["bold"],
        attrs={"name": instigator_name},
    ))
    b = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=[friend_trait],
        attrs={"name": friend_name},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        attrs={"name": {"mother": "Mom", "father": "Dad"}[parent_type]},
    ))
    base = world.add(Entity(
        id="base",
        kind="thing",
        type="base",
        label=base_kind.label,
        attrs={"place": base_kind.place},
    ))
    treasure_ent = world.add(Entity(
        id="treasure",
        kind="thing",
        type="treasure",
        label=treasure.label,
    ))

    base.meters["sturdy"] = float(base_kind.sturdiness)
    base.meters["open"] = 1.0
    base.meters["fun"] = 2.0
    treasure_ent.meters["found"] = 0.0
    treasure_ent.meters["shared"] = 1.0
    a.memes["joy"] = 0.0
    b.memes["joy"] = 0.0
    a.memes["friendship"] = 0.0
    b.memes["friendship"] = 0.0
    a.memes["greed"] = 0.0
    a.memes["uneasy"] = 0.0
    a.memes["sorry"] = 0.0
    b.memes["left_out"] = 0.0
    b.memes["sad"] = 0.0

    opening(world, a, b, base_kind)
    discover_treasure(world, a, b, treasure)

    world.para()
    warn_heart(world, a, b, mistake)
    apply_mistake(world, mistake, narrate=True)

    world.para()
    notice_hurt(world, a, b, base_kind, treasure)
    apply_repair(world, repair, treasure, base_kind)

    world.para()
    ending(world, a, b, base_kind, treasure, mistake)

    world.facts.update(
        instigator=a,
        friend=b,
        parent=parent,
        base_cfg=base_kind,
        treasure_cfg=treasure,
        mistake=mistake,
        repair=repair,
        base=base,
        treasure=treasure_ent,
        lesson_learned=a.memes["sorry"] >= THRESHOLD and treasure_ent.meters["shared"] >= THRESHOLD,
        friendship_restored=b.memes["friendship"] >= THRESHOLD,
    )
    return world


BASES = {
    "blanket_fort": BaseKind(
        id="blanket_fort",
        label="blanket fort",
        phrase="a blanket fort under the dining table",
        place="the family room",
        build_line="A striped sheet became a sail, two chairs became masts, and a wooden spoon served as the captain's oar.",
        inside_line="Inside, the fort felt like a hidden ship's cabin where only whispers and giggles were allowed.",
        open_level=1,
        sturdiness=2,
        tags={"fort", "home"},
    ),
    "sand_cove": BaseKind(
        id="sand_cove",
        label="sand cove",
        phrase="a low sand-cove base beside a driftwood log",
        place="the beach",
        build_line="They patted up the walls with wet sand and planted a feather in the top like a pirate flag.",
        inside_line="The cove was wide enough for two captains to crouch in and watch the shining water.",
        open_level=2,
        sturdiness=1,
        tags={"beach", "sand"},
    ),
    "crate_hideout": BaseKind(
        id="crate_hideout",
        label="crate hideout",
        phrase="a hideout base from old crates and a big blue tarp",
        place="the backyard",
        build_line="The crates made rough walls, the tarp flapped like a sail, and a chalk X marked the secret door.",
        inside_line="From inside, it looked like a pirate stronghold with room for maps, treasure, and two muddy knees.",
        open_level=1,
        sturdiness=3,
        tags={"yard", "hideout"},
    ),
}

TREASURES = {
    "shells": Treasure(
        id="shells",
        label="shells",
        phrase="a handful of pearly shells",
        find_line="a handful of pearly shells tucked near a flowerpot",
        count_word="shells",
        tags={"shell"},
    ),
    "buttons": Treasure(
        id="buttons",
        label="gold buttons",
        phrase="a small tin of gold buttons",
        find_line="a small tin of gold buttons shining under a cushion",
        count_word="gold buttons",
        tags={"button"},
    ),
    "glass_gems": Treasure(
        id="glass_gems",
        label="glass gems",
        phrase="some round glass gems",
        find_line="some round glass gems glimmering in the sunlight",
        count_word="glass gems",
        tags={"gem"},
    ),
}

MISTAKES = {
    "lock_out": Mistake(
        id="lock_out",
        label="lock out the friend",
        sense=2,
        needs_open_at_most=1,
        line='"This part is only for me," {a} said, pulling the flap close and guarding the pirate base by {a_pos}self.'.replace("{a_pos}", "him"),
        hurt_line="Outside the doorway, the other pirate did not argue. The quiet hurt more than a shout.",
        lesson="a base is not a good base if it shuts a friend out. ",
        tags={"friendship", "sharing"},
    ),
    "claim_all": Mistake(
        id="claim_all",
        label="claim all the treasure",
        sense=2,
        needs_open_at_most=2,
        line='"I found it, so all the treasure is mine," {a} said, sweeping the pile close.',
        hurt_line="The other pirate's smile fell away, because even pretend treasure can make a real lonely feeling.",
        lesson="treasure is smaller when one friend grabs it all. ",
        tags={"friendship", "sharing"},
    ),
}

REPAIRS = {
    "apology_share": Repair(
        id="apology_share",
        label="apologize and share",
        helps_lock_out=True,
        helps_claim_all=True,
        action_line='"I am sorry," {a} said. "{b}, come in. We can split the {treasure} and make room for both of us."',
        ending_line="Then let us be a two-captain crew",
        qa_text="apologized, invited the friend back in, and split the treasure",
        tags={"apology", "sharing"},
    ),
    "invite_and_split": Repair(
        id="invite_and_split",
        label="make a shared captain's corner",
        helps_lock_out=True,
        helps_claim_all=True,
        action_line='{a} scooted over, lifted the flap wide, and said, "There is space in this {base} for both of us. You can help count the {treasure} with me."',
        ending_line="That is better. Pirate friends count together",
        qa_text="opened the base, made space, and shared the treasure counting",
        tags={"sharing", "together"},
    ),
    "rebuild_together": Repair(
        id="rebuild_together",
        label="rebuild together",
        helps_lock_out=True,
        helps_claim_all=False,
        action_line='{a} let go of the flap and said, "I was being mean. Will you help me make the {base} bigger and then share the {treasure}?"',
        ending_line="Yes. A bigger base is for both friends",
        qa_text="admitted the mistake, rebuilt the base together, and then shared the treasure",
        tags={"repair", "friendship"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Ruby"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Eli"]
TRAITS = ["kind", "patient", "gentle", "thoughtful", "steady"]

KNOWLEDGE = {
    "base": [(
        "What is a base in a pretend pirate game?",
        "A base is the special place where the pirates keep their things and make their plans. In a game, it can be a fort, a hideout, or any little safe spot they build together."
    )],
    "friendship": [(
        "What makes a good friend during play?",
        "A good friend makes room for you, listens to you, and shares the fun. Games feel better when everyone is included."
    )],
    "sharing": [(
        "Why is sharing important when children play together?",
        "Sharing helps everyone feel welcome and calm. When one child keeps everything, the game can stop feeling fun."
    )],
    "apology": [(
        "What does an apology do?",
        "An apology shows that someone knows they caused hurt and wants to make things better. It helps trust start to come back."
    )],
    "pirate": [(
        "What do pirates in pretend play usually look for?",
        "Pretend pirates often look for treasure, maps, and secret hideouts. In stories, those things make the game feel adventurous."
    )],
    "shell": [(
        "Why might shells feel like treasure to children?",
        "Shells can shine, swirl, and feel special in your hand. Children often pretend they are treasure because they look rare and beautiful."
    )],
    "button": [(
        "Why can shiny buttons become pretend treasure?",
        "Shiny buttons catch the light and look a little like gold coins. That makes them easy to imagine as treasure in a pirate game."
    )],
    "gem": [(
        "Why do glass gems look magical in stories?",
        "Glass gems sparkle and glow when light hits them. That sparkle makes them feel like something from a treasure chest."
    )],
}
KNOWLEDGE_ORDER = ["base", "pirate", "friendship", "sharing", "apology", "shell", "button", "gem"]


@dataclass
class StoryParams:
    base: str
    treasure: str
    mistake: str
    repair: str
    instigator: str
    instigator_gender: str
    friend: str
    friend_gender: str
    parent: str
    trait: str
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
        base="blanket_fort",
        treasure="buttons",
        mistake="lock_out",
        repair="apology_share",
        instigator="Tom",
        instigator_gender="boy",
        friend="Lily",
        friend_gender="girl",
        parent="mother",
        trait="kind",
    ),
    StoryParams(
        base="sand_cove",
        treasure="shells",
        mistake="claim_all",
        repair="invite_and_split",
        instigator="Mia",
        instigator_gender="girl",
        friend="Ben",
        friend_gender="boy",
        parent="father",
        trait="patient",
    ),
    StoryParams(
        base="crate_hideout",
        treasure="glass_gems",
        mistake="lock_out",
        repair="rebuild_together",
        instigator="Max",
        instigator_gender="boy",
        friend="Zoe",
        friend_gender="girl",
        parent="mother",
        trait="gentle",
    ),
]


def explain_base_mistake(base_kind: BaseKind, mistake: Mistake) -> str:
    return (
        f"(No story: {mistake.label} does not fit a {base_kind.label}. "
        f"That base is too open for a believable shut-out scene.)"
    )


def explain_repair(mistake: Mistake, repair: Repair) -> str:
    return (
        f"(No story: the repair '{repair.id}' does not honestly solve the mistake "
        f"'{mistake.id}'. The ending needs a real friendship repair.)"
    )


def explain_kind(repair: Repair) -> str:
    return (
        f"(No story: the repair '{repair.id}' is too weak for this world "
        f"(kind={repair_kind(repair)} < {KIND_MIN}).)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["friend"]
    base_kind = f["base_cfg"]
    treasure = f["treasure_cfg"]
    mistake = f["mistake"]
    return [
        f'Write a short pirate-style story for a 3-to-5-year-old that includes the word "base" and ends with a friendship lesson.',
        f"Tell a gentle pirate tale where {a.label} and {b.label} build a {base_kind.label}, find {treasure.label}, and one child makes a selfish choice before learning to share.",
        f"Write a story about two pretend pirates whose game goes wrong when someone tries to {mistake.label}, but the ending shows that friendship matters more than treasure.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["friend"]
    base_kind = f["base_cfg"]
    treasure = f["treasure_cfg"]
    mistake = f["mistake"]
    repair = f["repair"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {a.label} and {b.label}, who pretended to be pirates together. They built a {base_kind.label} and turned their game into a little adventure."
        ),
        (
            "What was their pirate base like?",
            f"Their pirate base was {base_kind.phrase} at {base_kind.place}. That special hiding place made the game feel like a real pirate tale."
        ),
        (
            "What treasure did they find?",
            f"They found {treasure.phrase}. The treasure felt exciting, which is why the selfish choice mattered so much."
        ),
    ]
    if mistake.id == "lock_out":
        qa.append((
            f"How did {a.label} hurt {b.label}'s feelings?",
            f"{a.label} tried to keep the pirate base only for {a.pronoun('object')}self and shut {b.label} out. That made {b.label} feel left out, and the game stopped feeling happy."
        ))
    else:
        qa.append((
            f"How did {a.label} hurt {b.label}'s feelings?",
            f"{a.label} tried to keep all the treasure instead of sharing it. That made {b.label} feel lonely because pretend treasure still matters inside a friendship game."
        ))
    qa.append((
        "What made the selfish choice feel wrong?",
        f"The pirate base and the treasure were still there, but the fun dropped when one friend was left out. The quiet change in the game showed {a.label} that something important had been hurt."
    ))
    qa.append((
        f"How did {a.label} fix the problem?",
        f"{a.label} {repair.qa_text}. That repair worked because it gave friendship a real place in the game again."
    ))
    qa.append((
        "What lesson did the children learn?",
        f"They learned that {mistake.lesson.strip()} Friendship was worth more than pretend treasure. The ending proves the lesson because they played happily together again."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"base", "friendship", "pirate"}
    tags |= set(f["mistake"].tags)
    tags |= set(f["repair"].tags)
    tags |= set(f["treasure_cfg"].tags)
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
        if e.label:
            bits.append(f"label={e.label!r}")
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% Reasonable combinations.
supports(Base, Mistake) :- base(Base), mistake(Mistake), open_level(Base, O), needs_open_at_most(Mistake, N), O <= N.
repair_kind_ok(R) :- repair(R), repair_kind(R, K), kind_min(M), K >= M.
solves(M, R) :- mistake(M), repair(R), fixes(M, R).
valid(B, M, R) :- base(B), mistake(M), repair(R), supports(B, M), solves(M, R), repair_kind_ok(R).

% Outcome is always repaired for a valid combination in this world.
outcome(repaired) :- chosen_base(B), chosen_mistake(M), chosen_repair(R), valid(B, M, R).
#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for base_id, base_kind in BASES.items():
        lines.append(asp.fact("base", base_id))
        lines.append(asp.fact("open_level", base_id, base_kind.open_level))
    for mistake_id, mistake in MISTAKES.items():
        lines.append(asp.fact("mistake", mistake_id))
        lines.append(asp.fact("needs_open_at_most", mistake_id, mistake.needs_open_at_most))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("repair_kind", repair_id, repair_kind(repair)))
        if repair.helps_lock_out:
            lines.append(asp.fact("fixes", "lock_out", repair_id))
        if repair.helps_claim_all:
            lines.append(asp.fact("fixes", "claim_all", repair_id))
    lines.append(asp.fact("kind_min", KIND_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_base", params.base),
        asp.fact("chosen_mistake", params.mistake),
        asp.fact("chosen_repair", params.repair),
    ])
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    for params in CURATED:
        out = asp_outcome(params)
        if out != "repaired":
            rc = 1
            print(f"MISMATCH in outcome for curated params: {params} -> {out}")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### smoke")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate-style friendship story world with a pretend base and a lesson learned."
    )
    ap.add_argument("--base", choices=BASES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--mistake", choices=MISTAKES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (base, mistake, repair) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    pool = [n for n in names if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.base and args.mistake:
        base_kind = BASES[args.base]
        mistake = MISTAKES[args.mistake]
        if not supports_mistake(base_kind, mistake):
            raise StoryError(explain_base_mistake(base_kind, mistake))
    if args.mistake and args.repair:
        mistake = MISTAKES[args.mistake]
        repair = REPAIRS[args.repair]
        if not repair_matches(mistake, repair):
            raise StoryError(explain_repair(mistake, repair))
    if args.repair and repair_kind(REPAIRS[args.repair]) < KIND_MIN:
        raise StoryError(explain_kind(REPAIRS[args.repair]))

    combos = [
        combo for combo in valid_combos()
        if (args.base is None or combo[0] == args.base)
        and (args.mistake is None or combo[1] == args.mistake)
        and (args.repair is None or combo[2] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    base_id, mistake_id, repair_id = rng.choice(sorted(combos))
    treasure_id = args.treasure or rng.choice(sorted(TREASURES))
    instigator, instigator_gender = _pick_kid(rng)
    friend, friend_gender = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        base=base_id,
        treasure=treasure_id,
        mistake=mistake_id,
        repair=repair_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        friend=friend,
        friend_gender=friend_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.base not in BASES:
        raise StoryError(f"(Unknown base: {params.base})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if params.mistake not in MISTAKES:
        raise StoryError(f"(Unknown mistake: {params.mistake})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")

    base_kind = BASES[params.base]
    treasure = TREASURES[params.treasure]
    mistake = MISTAKES[params.mistake]
    repair = REPAIRS[params.repair]

    if not supports_mistake(base_kind, mistake):
        raise StoryError(explain_base_mistake(base_kind, mistake))
    if not repair_matches(mistake, repair):
        raise StoryError(explain_repair(mistake, repair))
    if repair_kind(repair) < KIND_MIN:
        raise StoryError(explain_kind(repair))

    world = tell(
        base_kind=base_kind,
        treasure=treasure,
        mistake=mistake,
        repair=repair,
        instigator_name=params.instigator,
        instigator_gender=params.instigator_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        friend_trait=params.trait,
    )

    story = world.render()
    inst = world.facts["instigator"].label
    fr = world.facts["friend"].label
    story = story.replace("instigator", inst).replace("friend", fr)
    story = story.replace("{a}", inst).replace("{b}", fr)

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (base, mistake, repair) combos:\n")
        for base_id, mistake_id, repair_id in combos:
            print(f"  {base_id:13} {mistake_id:10} {repair_id}")
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
            header = f"### {p.instigator} & {p.friend}: {p.base}, {p.mistake}, {p.repair}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
