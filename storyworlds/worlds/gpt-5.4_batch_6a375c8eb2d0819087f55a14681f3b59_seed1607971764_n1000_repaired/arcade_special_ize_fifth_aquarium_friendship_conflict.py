#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/arcade_special_ize_fifth_aquarium_friendship_conflict.py
===================================================================================

A standalone story world about two children at an aquarium who discover a lost
arcade prize token beside the fifth tank. One child wants to keep the shiny
token and use it at the aquarium arcade. The other wants to solve the mystery
fairly. Their conflict turns on ownership and trust, and the resolution comes
through sharing the search and returning the token to the child who lost it.

The seed asked for:
- the words "arcade", "special-ize", and "fifth"
- setting: aquarium
- features: Friendship, Conflict, Sharing
- style: Mystery

This world models a small, concrete mystery:
    a token is found -> a friendship strain appears over what to do with it ->
    clues and a helper lead to the rightful owner -> the children share the
    moment and end with a better game than the selfish one they first imagined.

Run it
------
    python storyworlds/worlds/gpt-5.4/arcade_special_ize_fifth_aquarium_friendship_conflict.py
    python storyworlds/worlds/gpt-5.4/arcade_special_ize_fifth_aquarium_friendship_conflict.py --zone jellyfish --keeper return_desk
    python storyworlds/worlds/gpt-5.4/arcade_special_ize_fifth_aquarium_friendship_conflict.py --clue none
    python storyworlds/worlds/gpt-5.4/arcade_special_ize_fifth_aquarium_friendship_conflict.py --all --qa
    python storyworlds/worlds/gpt-5.4/arcade_special_ize_fifth_aquarium_friendship_conflict.py --verify
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
FAIR_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    owner: str = ""
    visible: bool = True
    portable: bool = False
    # physical + emotional axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "staff_woman"}
        male = {"boy", "father", "man", "staff_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "staff_woman": "guide",
            "staff_man": "guide",
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
class Zone:
    id: str
    label: str
    exhibit: str
    glow: str
    sound: str
    ordinal: str
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
class LostItem:
    id: str
    label: str
    phrase: str
    use: str
    color: str
    portable: bool = True
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
    text: str
    owner_hint: str
    strength: int
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
class KeeperPlan:
    id: str
    fairness: int
    success: bool
    action_text: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.history = list(self.history)
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


def _r_conflict(world: World) -> list[str]:
    finder = world.get("finder")
    friend = world.get("friend")
    item = world.get("item")
    if item.owner:
        return []
    if finder.memes["keep_wish"] < THRESHOLD or friend.memes["fairness"] < THRESHOLD:
        return []
    sig = ("conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    finder.memes["conflict"] += 1
    friend.memes["conflict"] += 1
    world.get("bond").meters["strain"] += 1
    return ["__conflict__"]


def _r_clarity(world: World) -> list[str]:
    item = world.get("item")
    if item.owner:
        return []
    if world.facts.get("clue_strength", 0) < 1:
        return []
    sig = ("clarity",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("friend").memes["certainty"] += 1
    return []


def _r_returned_heals(world: World) -> list[str]:
    item = world.get("item")
    if not item.owner:
        return []
    sig = ("returned", item.owner)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    finder = world.get("finder")
    friend = world.get("friend")
    owner = world.get("owner")
    bond = world.get("bond")
    bond.meters["strain"] = 0.0
    bond.meters["trust"] += 1
    finder.memes["guilt"] = 0.0
    finder.memes["relief"] += 1
    friend.memes["relief"] += 1
    owner.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="clarity", tag="mystery", apply=_r_clarity),
    Rule(name="returned_heals", tag="social", apply=_r_returned_heals),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def item_can_be_lost(item: LostItem, zone: Zone) -> bool:
    return item.portable and "aquarium" in zone.tags


def sensible_plans() -> list[KeeperPlan]:
    return [p for p in PLANS.values() if p.fairness >= FAIR_MIN and p.success]


def best_plan() -> KeeperPlan:
    return max(PLANS.values(), key=lambda p: p.fairness)


def plan_works(plan: KeeperPlan, clue: Clue) -> bool:
    return plan.success and clue.strength >= 1


def explain_zone_failure(item: LostItem, zone: Zone) -> str:
    return (
        f"(No story: {item.label} could be lost at the aquarium, but {zone.label} "
        f"doesn't fit the aquarium mystery frame used in this world.)"
    )


def explain_plan(plan_id: str) -> str:
    plan = PLANS[plan_id]
    better = " / ".join(sorted(p.id for p in sensible_plans()))
    return (
        f"(Refusing plan '{plan_id}': it is too unfair or ineffective "
        f"(fairness={plan.fairness} < {FAIR_MIN} or it cannot resolve the mystery). "
        f"Try: {better}.)"
    )


def predict_owner_found(world: World, clue_id: str, plan_id: str) -> dict:
    sim = world.copy()
    clue = CLUES[clue_id]
    plan = PLANS[plan_id]
    sim.facts["clue_strength"] = clue.strength
    if plan_works(plan, clue):
        sim.get("item").owner = sim.get("owner").id
    propagate(sim, narrate=False)
    return {
        "owner_found": bool(sim.get("item").owner),
        "trust": sim.get("bond").meters["trust"],
    }


def opening(world: World, finder: Entity, friend: Entity, zone: Zone) -> None:
    finder.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f"On a bright afternoon, {finder.id} and {friend.id} walked through the aquarium "
        f"with their noses almost touching the glass. They had already counted four big tanks, "
        f"and the {zone.ordinal} one glowed with {zone.glow} while {zone.sound}."
    )
    world.say(
        f"The sign beside it called the room {zone.label}, and everything inside looked a little "
        f"like a secret."
    )


def discovery(world: World, finder: Entity, friend: Entity, item: LostItem, zone: Zone) -> None:
    item.meters["found"] += 1
    finder.memes["excitement"] += 1
    world.say(
        f"Right by the rail near the {zone.exhibit}, {finder.id} spotted {item.phrase}. "
        f"It was {item.color} and smooth, and it looked important."
    )
    world.say(
        f'"It must go to the arcade upstairs," {finder.id} whispered. '
        f'"Maybe this is a lucky token."'
    )


def temptation(world: World, finder: Entity, friend: Entity, item: LostItem) -> None:
    finder.memes["keep_wish"] += 1
    world.say(
        f"{finder.id} curled {finder.pronoun('possessive')} fingers around the {item.label}. "
        f'"We could special-ize our whole visit," {finder.pronoun()} said. '
        f'"One game for me and one for you, and no one would even know."'
    )


def objection(world: World, friend: Entity, finder: Entity, item: LostItem, clue: Clue) -> None:
    friend.memes["fairness"] += 1
    world.facts["clue_strength"] = clue.strength
    propagate(world, narrate=False)
    extra = ""
    if clue.id != "none":
        extra = f" {friend.id} pointed to {clue.text}."
    world.say(
        f'{friend.id} did not smile back. "Someone might be looking for that {item.label}," '
        f'{friend.pronoun()} said.{extra} "A mystery is not a prize if it belongs to somebody else."'
    )


def quarrel(world: World, finder: Entity, friend: Entity) -> None:
    if world.get("bond").meters["strain"] >= THRESHOLD:
        finder.memes["guilt"] += 1
        world.say(
            f'"But we found it," {finder.id} said, and for the first time that day the two friends '
            f"stood still instead of walking together."
        )
        world.say(
            f"The blue light from the tank rippled over their shoes while the argument sat between them, "
            f"small and sharp."
        )


def seek_help(world: World, helper: Entity, finder: Entity, friend: Entity, plan: KeeperPlan, clue: Clue) -> None:
    pred = predict_owner_found(world, clue.id, plan.id)
    world.facts["predicted_owner_found"] = pred["owner_found"]
    helper.memes["calm"] += 1
    world.say(
        f"At last {friend.id} tugged {finder.id} toward a nearby guide in a silver aquarium vest. "
        f'The guide listened, nodded once, and said, "Let us solve the mystery the fair way."'
    )


def execute_plan(world: World, helper: Entity, owner: Entity, item: Entity, plan: KeeperPlan, clue: Clue) -> bool:
    if plan_works(plan, clue):
        item.owner = owner.id
        world.facts["owner_found"] = True
        propagate(world, narrate=False)
        world.say(plan.action_text)
        return True
    world.facts["owner_found"] = False
    world.say(plan.fail_text)
    return False


def reunion(world: World, owner: Entity, item_cfg: LostItem) -> None:
    owner.memes["relief"] += 1
    world.say(
        f"A smaller child in a striped shirt came hurrying over and held up a paper cup of fish pellets. "
        f'"My {item_cfg.label}! I dropped it when the rays splashed," {owner.id} cried.'
    )
    world.say(
        f"{owner.id} hugged the shiny {item_cfg.label} to {owner.pronoun('possessive')} chest as if it had been "
        f"a tiny moon that finally came back."
    )


def apology(world: World, finder: Entity, friend: Entity) -> None:
    finder.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    world.say(
        f'{finder.id} looked at {friend.id} and let out a slow breath. '
        f'"You were right," {finder.pronoun()} said. "I was thinking about a game, not about the person who lost it."'
    )
    world.say(
        f'{friend.id} bumped shoulders with {finder.pronoun("object")}. '
        f'"We solved it together," {friend.pronoun()} said.'
    )


def sharing_end(world: World, finder: Entity, friend: Entity, owner: Entity, zone: Zone) -> None:
    world.get("bond").meters["sharing"] += 1
    finder.memes["joy"] += 1
    friend.memes["joy"] += 1
    owner.memes["joy"] += 1
    world.say(
        f"The little child offered them each a fish-shaped sticker from the guide's pocket, "
        f"and the two friends shared a laugh over how much trouble one small token had caused."
    )
    world.say(
        f"When they moved on from the {zone.exhibit}, they walked shoulder to shoulder again. "
        f"The mystery was over, but their friendship felt brighter than the glowing tank."
    )


def unresolved_end(world: World, finder: Entity, friend: Entity, helper: Entity, zone: Zone) -> None:
    world.say(
        f"The guide took the {world.get('item').label} to the lost-and-found desk anyway. "
        f'"If someone asks for it, we will have it ready," {helper.pronoun()} said.'
    )
    world.say(
        f"{finder.id} and {friend.id} watched the fifth tank in silence for a moment, then went on more slowly. "
        f"They had not solved the mystery all the way, but they had still chosen not to keep what was not theirs."
    )


def tell(
    zone: Zone,
    item_cfg: LostItem,
    clue: Clue,
    plan: KeeperPlan,
    finder_name: str = "Mira",
    finder_gender: str = "girl",
    friend_name: str = "Owen",
    friend_gender: str = "boy",
    owner_name: str = "Tess",
    owner_gender: str = "girl",
    helper_type: str = "staff_woman",
    parent_type: str = "mother",
) -> World:
    world = World()
    finder = world.add(Entity(
        id=finder_name,
        kind="character",
        type=finder_gender,
        role="finder",
        attrs={"parent_type": parent_type},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        attrs={"parent_type": parent_type},
    ))
    owner = world.add(Entity(
        id=owner_name,
        kind="character",
        type=owner_gender,
        role="owner",
    ))
    helper = world.add(Entity(
        id="Guide",
        kind="character",
        type=helper_type,
        role="helper",
        label="the guide",
    ))
    bond = world.add(Entity(
        id="bond",
        type="friendship",
        label="friendship",
    ))
    item = world.add(Entity(
        id="item",
        type="token",
        label=item_cfg.label,
        portable=item_cfg.portable,
    ))

    # initialize state read by rules before any propagation
    bond.meters["strain"] = 0.0
    bond.meters["trust"] = 0.0
    bond.meters["sharing"] = 0.0
    finder.memes["keep_wish"] = 0.0
    friend.memes["fairness"] = 0.0
    friend.memes["certainty"] = 0.0
    finder.memes["guilt"] = 0.0
    world.facts["clue_strength"] = 0
    world.facts["owner_found"] = False
    world.facts["predicted_owner_found"] = False

    opening(world, finder, friend, zone)
    discovery(world, finder, friend, item_cfg, zone)

    world.para()
    temptation(world, finder, friend, item_cfg)
    objection(world, friend, finder, item_cfg, clue)
    quarrel(world, finder, friend)

    world.para()
    seek_help(world, helper, finder, friend, plan, clue)
    success = execute_plan(world, helper, owner, item, plan, clue)

    world.para()
    if success:
        reunion(world, owner, item_cfg)
        apology(world, finder, friend)
        sharing_end(world, finder, friend, owner, zone)
        outcome = "returned"
    else:
        unresolved_end(world, finder, friend, helper, zone)
        outcome = "desk"

    world.facts.update(
        zone=zone,
        item_cfg=item_cfg,
        clue=clue,
        plan=plan,
        finder=finder,
        friend=friend,
        owner=owner,
        helper=helper,
        outcome=outcome,
        conflict=bond.meters["strain"] >= THRESHOLD or finder.memes["guilt"] >= THRESHOLD,
        shared=bond.meters["sharing"] >= THRESHOLD,
        item_returned=bool(item.owner),
        tank_ordinal=zone.ordinal,
    )
    return world


ZONES = {
    "jellyfish": Zone(
        id="jellyfish",
        label="the Moon Glow Hall",
        exhibit="jellyfish tank",
        glow="soft blue light",
        sound="the filter hummed like a secret machine",
        ordinal="fifth",
        tags={"aquarium", "mystery", "glow"},
    ),
    "rays": Zone(
        id="rays",
        label="the Ripple Room",
        exhibit="ray pool",
        glow="silver-green light",
        sound="water tapped the glass in tiny beats",
        ordinal="fifth",
        tags={"aquarium", "mystery", "splash"},
    ),
    "seahorses": Zone(
        id="seahorses",
        label="the Kelp Corner",
        exhibit="seahorse tank",
        glow="green-gold light",
        sound="the pumps sighed softly behind the wall",
        ordinal="fifth",
        tags={"aquarium", "mystery", "quiet"},
    ),
}

ITEMS = {
    "star_token": LostItem(
        id="star_token",
        label="token",
        phrase="a star-stamped brass token on the floor",
        use="for the aquarium arcade",
        color="golden",
        portable=True,
        tags={"token", "arcade"},
    ),
    "shell_token": LostItem(
        id="shell_token",
        label="token",
        phrase="a shell-etched silver token tucked beside the rail",
        use="for the aquarium arcade",
        color="silver",
        portable=True,
        tags={"token", "arcade"},
    ),
    "whale_coin": LostItem(
        id="whale_coin",
        label="coin",
        phrase="a whale-marked game coin resting by a bench leg",
        use="for the aquarium arcade",
        color="blue and bright",
        portable=True,
        tags={"token", "arcade"},
    ),
}

CLUES = {
    "sticker": Clue(
        id="sticker",
        text="a damp sticker shaped like a smiling stingray stuck to one side",
        owner_hint="a child from the ray-touch station",
        strength=2,
        tags={"clue", "ray"},
    ),
    "pellets": Clue(
        id="pellets",
        text="a tiny paper fish-food cup lying beside it",
        owner_hint="a child who had been feeding fish",
        strength=2,
        tags={"clue", "fish"},
    ),
    "none": Clue(
        id="none",
        text="nothing else at all",
        owner_hint="nobody clear",
        strength=0,
        tags={"uncertain"},
    ),
}

PLANS = {
    "return_desk": KeeperPlan(
        id="return_desk",
        fairness=3,
        success=True,
        action_text='The guide lifted the token high, asked a few nearby families, and then checked the desk where lost things were logged. A note about a missing arcade token had just been radioed in, so the guide called the waiting child over.',
        fail_text='The guide carried the token to the desk, but without any clue or matching report, nobody nearby could prove whose it was.',
        qa_text="They gave the token to the guide and used the lost-and-found desk to match it with the child who had reported it missing.",
        tags={"return", "desk", "sharing"},
    ),
    "ask_families": KeeperPlan(
        id="ask_families",
        fairness=2,
        success=True,
        action_text='The guide and the children asked the families near the fifth tank, and a worried child answered every detail of the lost token at once.',
        fail_text='They asked the nearby families, but without a useful clue the questions drifted and no one could be sure.',
        qa_text="They asked nearby families and listened for the child who could describe the token correctly.",
        tags={"return", "questions"},
    ),
    "keep_it": KeeperPlan(
        id="keep_it",
        fairness=0,
        success=False,
        action_text='',
        fail_text='Keeping the token would not solve the mystery at all; it would only hide who really lost it.',
        qa_text="Keeping it would have been unfair because the token belonged to someone else.",
        tags={"unfair"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Tess", "June", "Ava", "Nora", "Lucy", "Maya"]
BOY_NAMES = ["Owen", "Max", "Eli", "Finn", "Theo", "Leo", "Ben", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_plans():
        return combos
    for zid, zone in ZONES.items():
        for iid, item in ITEMS.items():
            if not item_can_be_lost(item, zone):
                continue
            for cid, clue in CLUES.items():
                if clue.strength >= 1:
                    combos.append((zid, iid, cid))
    return combos


@dataclass
class StoryParams:
    zone: str
    item: str
    clue: str
    plan: str
    finder: str
    finder_gender: str
    friend: str
    friend_gender: str
    owner: str
    owner_gender: str
    helper_type: str
    parent_type: str
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
    "aquarium": [
        (
            "What is an aquarium?",
            "An aquarium is a place where people can look at fish and other water animals in big tanks. The tanks let you see underwater creatures up close.",
        )
    ],
    "arcade": [
        (
            "What is an arcade?",
            "An arcade is a place with games people can play, often by using coins or tokens. Winning a turn does not make a lost token yours.",
        )
    ],
    "token": [
        (
            "What is a token?",
            "A token is a small piece, like a special coin, used for a machine or game. If you find one that somebody dropped, the kind thing is to help return it.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. In a mystery, clues help people find the true answer.",
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting other people join in good things instead of keeping everything for yourself. Sharing can help a friendship feel warm and fair.",
        )
    ],
    "friendship": [
        (
            "How can honesty help a friendship?",
            "Honesty helps friends trust each other. When friends choose the fair thing, their friendship often grows stronger.",
        )
    ],
}
KNOWLEDGE_ORDER = ["aquarium", "arcade", "token", "clue", "sharing", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    zone = f["zone"]
    finder = f["finder"]
    friend = f["friend"]
    item = f["item_cfg"]
    outcome = f["outcome"]
    if outcome == "returned":
        return [
            f'Write a gentle mystery story for a 3-to-5-year-old set in an aquarium that includes the words "arcade", "special-ize", and "fifth".',
            f"Tell a friendship story where {finder.id} and {friend.id} find a lost {item.label} by the fifth tank, argue about it, and then solve the mystery fairly together.",
            "Write a child-facing mystery about sharing, fairness, and returning a lost game token instead of keeping it.",
        ]
    return [
        f'Write a quiet aquarium mystery for a young child that includes the words "arcade", "special-ize", and "fifth".',
        f"Tell a story where {finder.id} and {friend.id} cannot fully solve the mystery of a lost {item.label}, but still choose the fair thing and leave it with the guide.",
        "Write a friendship story where a conflict over a found object ends with honesty, even before the owner is known.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    finder = f["finder"]
    friend = f["friend"]
    owner = f["owner"]
    zone = f["zone"]
    item = f["item_cfg"]
    clue = f["clue"]
    plan = f["plan"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {finder.id} and {friend.id}, at the aquarium. They find a lost {item.label} near the {zone.ordinal} tank and have to decide what is fair.",
        ),
        (
            f"Where did {finder.id} and {friend.id} find the lost {item.label}?",
            f"They found it near the {zone.exhibit} in the {zone.label}. That was the fifth tank they had counted on their walk through the aquarium.",
        ),
        (
            f"Why did {finder.id} and {friend.id} argue?",
            f"{finder.id} wanted to keep the {item.label} and use it at the arcade, but {friend.id} thought it might belong to someone else. Their conflict came from wanting different things: a game for now or fairness for the missing child.",
        ),
    ]
    if clue.id != "none":
        qa.append(
            (
                "What clue helped with the mystery?",
                f"The clue was {clue.text}. It mattered because it made the token seem connected to {clue.owner_hint}, so returning it became easier and more certain.",
            )
        )
    if f["outcome"] == "returned":
        qa.append(
            (
                "How was the mystery solved?",
                f"They asked the guide for help, and {plan.qa_text} That worked because the children chose to share the problem instead of hiding it.",
            )
        )
        qa.append(
            (
                f"How did {finder.id} change by the end?",
                f"{finder.id} stopped thinking only about the arcade game and started thinking about the child who had lost the token. After the token was returned, {finder.pronoun()} apologized and walked beside {friend.id} again.",
            )
        )
        qa.append(
            (
                f"How did the story end for {owner.id}?",
                f"{owner.id} got the lost {item.label} back and felt relieved. The ending shows that honesty helped three children at once: the owner, the finder, and the friend who spoke up.",
            )
        )
    else:
        qa.append(
            (
                "Did they keep the token?",
                f"No. They gave it to the guide instead of keeping it. Even without solving the mystery all the way, they chose the fair thing.",
            )
        )
        qa.append(
            (
                "How did the friendship change?",
                f"The argument became quieter once they agreed not to keep the token. They still felt a little unsure, but they were walking in the same direction again because they made the choice together.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"aquarium", "friendship", "sharing"}
    tags |= set(world.facts["item_cfg"].tags)
    if world.facts["clue"].strength >= 1:
        tags.add("clue")
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
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        zone="jellyfish",
        item="star_token",
        clue="sticker",
        plan="return_desk",
        finder="Mira",
        finder_gender="girl",
        friend="Owen",
        friend_gender="boy",
        owner="Tess",
        owner_gender="girl",
        helper_type="staff_woman",
        parent_type="mother",
    ),
    StoryParams(
        zone="rays",
        item="shell_token",
        clue="pellets",
        plan="ask_families",
        finder="June",
        finder_gender="girl",
        friend="Max",
        friend_gender="boy",
        owner="Nora",
        owner_gender="girl",
        helper_type="staff_man",
        parent_type="father",
    ),
    StoryParams(
        zone="seahorses",
        item="whale_coin",
        clue="none",
        plan="return_desk",
        finder="Eli",
        finder_gender="boy",
        friend="Lucy",
        friend_gender="girl",
        owner="Maya",
        owner_gender="girl",
        helper_type="staff_woman",
        parent_type="mother",
    ),
]


def outcome_of(params: StoryParams) -> str:
    clue = CLUES[params.clue]
    plan = PLANS[params.plan]
    return "returned" if plan_works(plan, clue) else "desk"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
lost_here(I, Z) :- item(I), zone(Z), portable(I), aquarium_zone(Z).
useful_clue(C)  :- clue(C), clue_strength(C, S), S >= 1.
fair_plan(P)    :- plan(P), fairness(P, F), fair_min(M), F >= M, succeeds(P).
valid(Z, I, C)  :- lost_here(I, Z), useful_clue(C).

% --- outcome ---------------------------------------------------------------
returned        :- chosen_plan(P), succeeds(P), chosen_clue(C), clue_strength(C, S), S >= 1.
outcome(returned) :- returned.
outcome(desk)     :- not returned.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for zid in ZONES:
        lines.append(asp.fact("zone", zid))
        lines.append(asp.fact("aquarium_zone", zid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.portable:
            lines.append(asp.fact("portable", iid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_strength", cid, clue.strength))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("fairness", pid, plan.fairness))
        if plan.success:
            lines.append(asp.fact("succeeds", pid))
    lines.append(asp.fact("fair_min", FAIR_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_fair_plans() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show fair_plan/1."))
    return sorted(p for (p,) in asp.atoms(model, "fair_plan"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_plan", params.plan),
        asp.fact("chosen_clue", params.clue),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    got = asp.atoms(model, "outcome")
    return got[0][0] if got else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small aquarium mystery about friendship, conflict, and sharing."
    )
    ap.add_argument("--zone", choices=ZONES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--helper-type", choices=["staff_woman", "staff_man"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
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


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.zone and args.item and not item_can_be_lost(ITEMS[args.item], ZONES[args.zone]):
        raise StoryError(explain_zone_failure(ITEMS[args.item], ZONES[args.zone]))
    if args.plan and PLANS[args.plan].fairness < FAIR_MIN:
        raise StoryError(explain_plan(args.plan))

    combos = [
        c for c in valid_combos()
        if (args.zone is None or c[0] == args.zone)
        and (args.item is None or c[1] == args.item)
        and (args.clue is None or c[2] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    zone, item, clue = rng.choice(sorted(combos))
    plan = args.plan or rng.choice(sorted(p.id for p in sensible_plans()))
    finder_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    owner_gender = rng.choice(["girl", "boy"])
    finder = _pick_name(rng, finder_gender, set())
    friend = _pick_name(rng, friend_gender, {finder})
    owner = _pick_name(rng, owner_gender, {finder, friend})
    helper_type = args.helper_type or rng.choice(["staff_woman", "staff_man"])
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    return StoryParams(
        zone=zone,
        item=item,
        clue=clue,
        plan=plan,
        finder=finder,
        finder_gender=finder_gender,
        friend=friend,
        friend_gender=friend_gender,
        owner=owner,
        owner_gender=owner_gender,
        helper_type=helper_type,
        parent_type=parent_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        zone = ZONES[params.zone]
        item = ITEMS[params.item]
        clue = CLUES[params.clue]
        plan = PLANS[params.plan]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if not item_can_be_lost(item, zone):
        raise StoryError(explain_zone_failure(item, zone))
    if plan.fairness < FAIR_MIN:
        raise StoryError(explain_plan(params.plan))

    world = tell(
        zone=zone,
        item_cfg=item,
        clue=clue,
        plan=plan,
        finder_name=params.finder,
        finder_gender=params.finder_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        owner_name=params.owner,
        owner_gender=params.owner_gender,
        helper_type=params.helper_type,
        parent_type=params.parent_type,
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
        print("MISMATCH in gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_fair = set(asp_fair_plans())
    p_fair = {p.id for p in sensible_plans()}
    if c_fair == p_fair:
        print(f"OK: fair plans match ({sorted(c_fair)}).")
    else:
        rc = 1
        print(f"MISMATCH in fair plans: clingo={sorted(c_fair)} python={sorted(p_fair)}")

    cases = list(CURATED)
    for s in range(50):
        try:
            args = build_parser().parse_args([])
            cases.append(resolve_params(args, random.Random(s)))
        except StoryError:
            continue
    mismatches = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    # smoke test ordinary generation
    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test produced empty story.)")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show fair_plan/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"fair plans: {', '.join(asp_fair_plans())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (zone, item, clue) combos:\n")
        for zone, item, clue in combos:
            print(f"  {zone:12} {item:11} {clue}")
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
            header = f"### {p.finder} & {p.friend}: {p.item} at {p.zone} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
