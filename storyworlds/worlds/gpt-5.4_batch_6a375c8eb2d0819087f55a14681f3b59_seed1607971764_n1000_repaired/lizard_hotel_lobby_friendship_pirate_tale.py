#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lizard_hotel_lobby_friendship_pirate_tale.py
=======================================================================

A standalone storyworld for a tiny pirate-flavored friendship tale set in a
hotel lobby. Two children turn the lobby into a pirate ship, spot a little
lizard, and must learn that friendship means helping a scared creature feel
safe instead of grabbing it for a game.

The domain is small and constraint-checked:

- A hiding spot has a physical access level and a "skittish" severity.
- A helper method must actually reach that spot and be sensible.
- The bold child may back down because of the friend's influence, or lunge and
  scare the lizard.
- If the lizard is scared, the chosen helper method may calmly contain and guide
  it outside, or be too weak and let it escape on its own.

Run it
------
    python storyworlds/worlds/gpt-5.4/lizard_hotel_lobby_friendship_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/lizard_hotel_lobby_friendship_pirate_tale.py --spot fern --helper shoebox_shelter
    python storyworlds/worlds/gpt-5.4/lizard_hotel_lobby_friendship_pirate_tale.py --helper bare_hands
    python storyworlds/worlds/gpt-5.4/lizard_hotel_lobby_friendship_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/lizard_hotel_lobby_friendship_pirate_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/lizard_hotel_lobby_friendship_pirate_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BOLD_INIT = 5.0
GENTLE_TRAITS = {"gentle", "kind", "patient", "caring"}


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
        female = {"girl", "woman", "mother", "clerk_f"}
        male = {"boy", "man", "father", "clerk_m", "bellhop"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Spot:
    id: str
    label: str
    the: str
    place_text: str
    level: str
    skittish: int
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class HelperMethod:
    id: str
    label: str
    phrase: str
    level_support: set[str]
    sense: int
    power: int
    setup_text: str
    success_text: str
    fail_text: str
    qa_text: str
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
class AdultRole:
    id: str
    type: str
    label: str
    entrance: str
    gift: str
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return clone

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "friend"}]
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


def _r_scared_lizard(world: World) -> list[str]:
    out: list[str] = []
    lizard = world.get("lizard")
    if lizard.meters["fear"] < THRESHOLD:
        return out
    sig = ("scared", "lizard")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("lobby").meters["flutter"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__scared__")
    return out


def _r_safe_release(world: World) -> list[str]:
    out: list[str] = []
    lizard = world.get("lizard")
    if lizard.meters["sheltered"] < THRESHOLD:
        return out
    sig = ("safe_release", "lizard")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lizard.meters["safe"] += 1
    lizard.meters["fear"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["friendship"] += 1
    out.append("__safe__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="scared_lizard", tag="emotion", apply=_r_scared_lizard),
    Rule(name="safe_release", tag="emotion", apply=_r_safe_release),
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


def works_for_spot(method: HelperMethod, spot: Spot) -> bool:
    return spot.level in method.level_support


def sensible_helpers() -> list[HelperMethod]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for spot_id, spot in SPOTS.items():
        for helper_id, helper in HELPERS.items():
            if helper.sense >= SENSE_MIN and works_for_spot(helper, spot):
                combos.append((spot_id, helper_id))
    return combos


def fear_severity(spot: Spot, delay: int) -> int:
    return spot.skittish + delay


def is_contained(method: HelperMethod, spot: Spot, delay: int) -> bool:
    return method.power >= fear_severity(spot, delay)


def initial_gentleness(trait: str) -> float:
    return 5.0 if trait in GENTLE_TRAITS else 3.0


def would_avert(relation: str, captain_age: int, friend_age: int, trait: str, trust: int) -> bool:
    older_friend = relation == "friends" and friend_age > captain_age
    authority = initial_gentleness(trait) + (2.0 if older_friend else 0.0) + (1.0 if trust >= 7 else 0.0)
    return authority > BOLD_INIT


def predict_lizard(world: World, spot_id: str) -> dict:
    sim = world.copy()
    _do_lunge(sim, narrate=False)
    lizard = sim.get("lizard")
    return {
        "fear": lizard.meters["fear"],
        "escape_risk": fear_severity(SPOTS[spot_id], int(sim.facts["delay"])),
    }


def _do_lunge(world: World, narrate: bool = True) -> None:
    lizard = world.get("lizard")
    lizard.meters["fear"] += 1
    lizard.meters["darting"] += 1
    propagate(world, narrate=narrate)


def pirate_setup(world: World, captain: Entity, friend: Entity) -> None:
    captain.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {captain.id} and {friend.id} turned the hotel lobby into a pirate harbor. "
        f"A brass luggage cart became their ship, the striped rug became a rolling sea, and a stack of suitcases became treasure."
    )
    world.say(
        f'"Captain {captain.id} and First Mate {friend.id}!" {captain.id} cried. "All hands on deck!"'
    )


def spot_lizard(world: World, captain: Entity, friend: Entity, spot: Spot) -> None:
    lizard = world.get("lizard")
    lizard.meters["noticed"] += 1
    world.say(
        f"Then {friend.id} saw a tiny green lizard at {spot.place_text}. It held very still, except for one quick blink."
    )
    world.say(
        f'"Look," {friend.id} whispered. "A real lobby lizard."'
    )


def tempt(world: World, captain: Entity) -> None:
    captain.memes["boldness"] += 1
    world.say(
        f'{captain.id} grinned. "A pirate ship needs a mascot. I can catch it and let it sail with us."'
    )


def warn(world: World, captain: Entity, friend: Entity, spot: Spot) -> None:
    pred = predict_lizard(world, spot.id)
    friend.memes["gentleness"] += 1
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_escape_risk"] = pred["escape_risk"]
    extra = " It looked small enough to frighten with just one fast hand."
    world.say(
        f'{friend.id} shook {friend.pronoun("possessive")} head. "If you grab it, it will think we are scary, not friendly. '
        f'Friends do not snatch each other.{extra}"'
    )


def back_down(world: World, captain: Entity, friend: Entity) -> None:
    captain.memes["boldness"] = 0.0
    captain.memes["respect"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'{captain.id} stopped with {captain.pronoun("possessive")} hand in the air, looked at the little lizard again, and let out a slow breath.'
    )
    world.say(
        f'"You\'re right," {captain.pronoun()} said. "A pirate friend should help, not grab."'
    )


def ask_adult(world: World, adult: Entity, adult_cfg: AdultRole, helper: HelperMethod) -> None:
    world.say(
        f"Just then {adult_cfg.entrance}. {adult.pronoun().capitalize()} listened carefully and did not laugh at their game."
    )
    world.say(
        f'"Let\'s help our small guest the gentle way," {adult.pronoun()} said, bringing {helper.phrase}.'
    )


def lunge(world: World, captain: Entity, spot: Spot) -> None:
    captain.memes["defiance"] += 1
    world.say(
        f'But the idea of a pirate mascot felt too exciting. {captain.id} reached toward {spot.the} with quick fingers.'
    )
    _do_lunge(world, narrate=False)
    world.say(
        f"{spot.The} rustled at once, and the little lizard skittered deeper in with its tail twitching like a green thread."
    )


def alarm(world: World, friend: Entity, captain: Entity) -> None:
    world.say(
        f'"{captain.id}, stop!" {friend.id} cried. "You scared it."'
    )


def rescue(world: World, adult: Entity, adult_cfg: AdultRole, helper: HelperMethod, spot: Spot) -> None:
    lizard = world.get("lizard")
    lizard.meters["sheltered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{adult_cfg.label.capitalize()} {helper.setup_text.format(spot=spot.the)}"
    )
    world.say(
        helper.success_text.format(spot=spot.the)
    )
    world.say(
        "No one squeezed or chased it. The little creature only needed a quiet path and patient hands nearby."
    )


def rescue_fail(world: World, adult_cfg: AdultRole, helper: HelperMethod, spot: Spot) -> None:
    lizard = world.get("lizard")
    lizard.meters["escaped"] += 1
    world.say(
        f"{adult_cfg.label.capitalize()} {helper.fail_text.format(spot=spot.the)}"
    )
    world.say(
        "The lizard slipped through the bright front doorway and vanished into the hedge by the steps before anyone could make another move."
    )


def release_outside(world: World, captain: Entity, friend: Entity, adult: Entity, adult_cfg: AdultRole, outcome: str) -> None:
    if outcome == "contained":
        world.say(
            f"Outside in the sunny courtyard, the lizard stepped onto a warm stone, lifted its tiny head, and blinked at them as if saying thank you."
        )
    else:
        world.say(
            "Outside, the children stood by the hedge and waited quietly. They could not see the lizard anymore, but the leaves trembled once, and that was enough to know it had found a safer place."
        )
    captain.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f'{captain.id} slipped {captain.pronoun("possessive")} hand into {friend.id}\'s. "Next time," {captain.pronoun()} said, "we do the friendly thing first."'
    )
    world.say(
        f"{adult_cfg.label.capitalize()} smiled and handed them {adult_cfg.gift}. Soon the two pirates were marching back through the hotel lobby side by side, brave, gentle, and better friends than before."
    )


def lesson(world: World, captain: Entity, friend: Entity, adult: Entity, adult_cfg: AdultRole) -> None:
    captain.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f'{adult_cfg.label.capitalize()} knelt beside them. "Small animals need calm voices and space," {adult.pronoun()} said softly. "The kindest way to be a friend is to help them feel safe."'
    )


def tell(
    spot: Spot,
    helper: HelperMethod,
    adult_cfg: AdultRole,
    captain_name: str = "Tom",
    captain_type: str = "boy",
    friend_name: str = "Lily",
    friend_type: str = "girl",
    friend_trait: str = "gentle",
    relation: str = "friends",
    trust: int = 7,
    captain_age: int = 5,
    friend_age: int = 6,
    delay: int = 0,
) -> World:
    world = World()
    captain = world.add(Entity(
        id=captain_name,
        kind="character",
        type=captain_type,
        role="captain",
        age=captain_age,
        attrs={"relation": relation},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_type,
        role="friend",
        age=friend_age,
        traits=[friend_trait],
        attrs={"relation": relation},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_cfg.type,
        role="adult",
        label=adult_cfg.label,
    ))
    lobby = world.add(Entity(id="lobby", type="place", label="the hotel lobby"))
    lizard = world.add(Entity(id="lizard", type="animal", label="the lizard"))

    captain.memes["boldness"] = BOLD_INIT
    friend.memes["gentleness"] = initial_gentleness(friend_trait)
    friend.memes["trust"] = float(trust)
    lizard.meters["fear"] = 0.0
    lizard.meters["sheltered"] = 0.0
    lizard.meters["escaped"] = 0.0
    lobby.meters["flutter"] = 0.0
    world.facts["delay"] = delay

    pirate_setup(world, captain, friend)
    spot_lizard(world, captain, friend, spot)

    world.para()
    tempt(world, captain)
    warn(world, captain, friend, spot)

    averted = would_avert(relation, captain_age, friend_age, friend_trait, trust)

    world.para()
    ask_adult(world, adult, adult_cfg, helper)

    if averted:
        back_down(world, captain, friend)
        rescue(world, adult, adult_cfg, helper, spot)
        lesson(world, captain, friend, adult, adult_cfg)
        world.para()
        release_outside(world, captain, friend, adult, adult_cfg, "contained")
        outcome = "averted"
        contained = True
    else:
        lunge(world, captain, spot)
        alarm(world, friend, captain)
        contained = is_contained(helper, spot, delay)
        world.para()
        if contained:
            rescue(world, adult, adult_cfg, helper, spot)
            lesson(world, captain, friend, adult, adult_cfg)
            world.para()
            release_outside(world, captain, friend, adult, adult_cfg, "contained")
            outcome = "contained"
        else:
            rescue_fail(world, adult_cfg, helper, spot)
            lesson(world, captain, friend, adult, adult_cfg)
            world.para()
            release_outside(world, captain, friend, adult, adult_cfg, "escaped")
            outcome = "escaped"

    world.facts.update(
        spot=spot,
        helper=helper,
        adult_cfg=adult_cfg,
        captain=captain,
        friend=friend,
        adult=adult,
        lizard=lizard,
        relation=relation,
        trust=trust,
        outcome=outcome,
        contained=contained,
        averted=averted,
        severity=fear_severity(spot, delay),
        delay=delay,
    )
    return world


SPOTS = {
    "fern": Spot(
        id="fern",
        label="fern alcove",
        the="the tall fern by the window",
        place_text="the roots of the tall fern by the window",
        level="floor",
        skittish=2,
        tags={"lizard", "fern"},
    ),
    "umbrella_stand": Spot(
        id="umbrella_stand",
        label="umbrella stand",
        the="the umbrella stand by the door",
        place_text="the umbrella stand by the door",
        level="floor",
        skittish=1,
        tags={"lizard", "umbrella"},
    ),
    "brochure_rack": Spot(
        id="brochure_rack",
        label="brochure rack",
        the="the brochure rack beside the front desk",
        place_text="a low shelf of the brochure rack beside the front desk",
        level="shelf",
        skittish=2,
        tags={"lizard", "brochure"},
    ),
}

HELPERS = {
    "towel_tunnel": HelperMethod(
        id="towel_tunnel",
        label="rolled towel tunnel",
        phrase="a rolled hotel towel like a soft tunnel",
        level_support={"floor"},
        sense=3,
        power=2,
        setup_text="laid the towel on the marble floor so one end touched {spot}, then waited without rushing.",
        success_text="After a moment, the lizard darted into the little tunnel by itself, and the grown-up lifted it gently from below.",
        fail_text="laid down the towel and waited, but the opening felt too wide and exposed for the frightened lizard.",
        qa_text="used a rolled towel to make a soft tunnel the lizard could choose",
        tags={"towel", "gentle_rescue"},
    ),
    "shoebox_shelter": HelperMethod(
        id="shoebox_shelter",
        label="shoebox shelter",
        phrase="a shoebox with air holes and a folded napkin inside",
        level_support={"floor", "shelf"},
        sense=3,
        power=3,
        setup_text="set the box near {spot}, tipped it sideways, and made a dim little shelter.",
        success_text="The lizard slipped into the quiet box on its own, and the lid went on loosely, with plenty of air.",
        fail_text="set the box near {spot}, but before it could settle, the lizard flashed past the opening.",
        qa_text="used a shoebox shelter so the lizard could hide somewhere dark and calm",
        tags={"box", "gentle_rescue"},
    ),
    "laundry_basket": HelperMethod(
        id="laundry_basket",
        label="laundry basket",
        phrase="a light laundry basket turned on its side",
        level_support={"floor"},
        sense=2,
        power=1,
        setup_text="turned the basket on its side near {spot} and tried to make a bigger shelter.",
        success_text="The lizard paused in the shade of the basket long enough to be guided into safety.",
        fail_text="turned the basket on its side near {spot}, but it was too big and clumsy to help a tiny lizard feel safe.",
        qa_text="tried a laundry basket as a shelter",
        tags={"basket", "gentle_rescue"},
    ),
    "bare_hands": HelperMethod(
        id="bare_hands",
        label="bare hands",
        phrase="bare hands",
        level_support={"floor", "shelf"},
        sense=1,
        power=0,
        setup_text="",
        success_text="",
        fail_text="reached in with bare hands",
        qa_text="tried to grab the lizard with bare hands",
        tags={"grab"},
    ),
}

ADULTS = {
    "concierge": AdultRole(
        id="concierge",
        type="clerk_f",
        label="the concierge",
        entrance="the concierge came from behind the front desk",
        gift="two paper pirate hats from the activity table",
        tags={"adult_help"},
    ),
    "bellhop": AdultRole(
        id="bellhop",
        type="bellhop",
        label="the bellhop",
        entrance="the bellhop rolled over with a shiny luggage cart",
        gift="a pair of little gold star stickers",
        tags={"adult_help"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Eli"]
TRAITS = ["gentle", "kind", "patient", "caring", "thoughtful", "careful"]


@dataclass
class StoryParams:
    spot: str
    helper: str
    adult: str
    captain: str
    captain_gender: str
    friend: str
    friend_gender: str
    friend_trait: str
    relation: str = "friends"
    trust: int = 7
    captain_age: int = 5
    friend_age: int = 6
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


KNOWLEDGE = {
    "lizard": [(
        "What is a lizard?",
        "A lizard is a small reptile with dry skin, tiny claws, and a long tail. Many lizards get scared easily and try to hide when something big comes near."
    )],
    "fern": [(
        "Why might a lizard hide by a fern?",
        "A fern has lots of leaves and shade, so it can feel like a safe hiding place. Small animals often look for cover when they are nervous."
    )],
    "umbrella": [(
        "Why would an umbrella stand seem safe to a tiny animal?",
        "It has narrow spaces and dark shadows. A tiny animal may feel less exposed there."
    )],
    "brochure": [(
        "Why might a lizard hide in a brochure rack?",
        "A rack has shelves and paper edges that make little hiding spaces. Small creatures like places where they can tuck themselves away."
    )],
    "gentle_rescue": [(
        "What is a gentle way to help a scared animal?",
        "Move slowly, keep voices soft, and give it a safe place to go on its own. Gentle help works better than grabbing because the animal feels less threatened."
    )],
    "towel": [(
        "How can a rolled towel help a tiny animal?",
        "A rolled towel can make a soft tunnel. That gives the animal a dark path to move through without being chased."
    )],
    "box": [(
        "Why can a box calm a scared animal?",
        "A small box can feel dark and sheltered. When an animal feels hidden, it often becomes less frightened."
    )],
    "basket": [(
        "Why might a big basket be hard for a tiny lizard?",
        "A basket can be too open and too large. If the shelter does not feel snug, the lizard may not trust it."
    )],
    "adult_help": [(
        "Why should children ask a grown-up for help with a wild animal?",
        "A grown-up can keep everyone calm and choose a safer way to help. Wild animals are not toys, so careful help matters."
    )],
}
KNOWLEDGE_ORDER = ["lizard", "fern", "umbrella", "brochure", "gentle_rescue", "towel", "box", "basket", "adult_help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    friend = f["friend"]
    spot = f["spot"]
    outcome = f["outcome"]
    helper = f["helper"]
    if outcome == "averted":
        return [
            'Write a pirate-flavored friendship story for a 3-to-5-year-old set in a hotel lobby and include the word "lizard".',
            f"Tell a gentle story where {captain.id} wants to catch a lizard in {spot.the}, but {friend.id} explains that friendship means helping instead of grabbing.",
            f"Write a story where two children playing pirates ask for calm grown-up help and end by walking side by side as better friends.",
        ]
    if outcome == "escaped":
        return [
            'Write a pirate-flavored friendship story for a 3-to-5-year-old set in a hotel lobby and include the word "lizard".',
            f"Tell a story where {captain.id} scares a lizard by moving too fast, and the children learn to be gentler even though the little animal slips away to safety.",
            f"Write a child-facing story where a hotel helper tries {helper.phrase}, but the real lesson is that friendship starts with patience.",
        ]
    return [
        'Write a pirate-flavored friendship story for a 3-to-5-year-old set in a hotel lobby and include the word "lizard".',
        f"Tell a story where two children playing pirates help a frightened lizard in {spot.the} instead of treating it like a toy.",
        f"Write a simple friendship story that ends with a lizard safe outside and the children learning that kind hands wait.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    friend = f["friend"]
    adult = f["adult"]
    adult_cfg = f["adult_cfg"]
    spot = f["spot"]
    helper = f["helper"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two children, {captain.id} and {friend.id}, who were playing pirates in a hotel lobby. It is also about a tiny lizard they found hiding there."
        ),
        (
            "Where did they find the lizard?",
            f"They found it at {spot.place_text}. That hiding place mattered because it made the lizard seem small, quiet, and easy to scare."
        ),
        (
            f"Why did {friend.id} tell {captain.id} not to grab the lizard?",
            f"{friend.id} said that grabbing would make the lizard feel scared instead of safe. {friend.pronoun().capitalize()} wanted to be a real friend to the little animal, not a pirate who took whatever {captain.pronoun()} wanted."
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"What changed {captain.id}'s mind?",
            f"{captain.id} looked at the lizard again and understood that a friend should help instead of snatch. The calm advice from {friend.id} and the grown-up's gentle plan gave {captain.pronoun('object')} a better way to act."
        ))
        qa.append((
            f"How did {adult_cfg.label} help?",
            f"{adult_cfg.label.capitalize()} {helper.qa_text}. That let the lizard choose a safe place to go instead of being chased."
        ))
    elif outcome == "contained":
        qa.append((
            f"How did {adult_cfg.label} help the lizard?",
            f"{adult_cfg.label.capitalize()} {helper.qa_text}. The method worked because it gave the lizard a quiet shelter and no one squeezed it."
        ))
        qa.append((
            "How did the story show friendship at the end?",
            f"At the end, the children let the lizard be safe outside and walked back together as better friends. The ending proves they had learned kindness was more important than winning the game."
        ))
    else:
        qa.append((
            "Did they catch the lizard?",
            f"No. The lizard slipped away outside before anyone could settle it into safety. That happened because it had already been frightened and the helper was not strong enough to calm the situation."
        ))
        qa.append((
            "What did the children learn anyway?",
            f"They learned that moving too fast can make a small animal run in panic. Even without holding the lizard, they still learned that friendship starts with patience and gentle choices."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["spot"].tags) | set(f["helper"].tags) | set(f["adult_cfg"].tags)
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        spot="fern",
        helper="shoebox_shelter",
        adult="concierge",
        captain="Tom",
        captain_gender="boy",
        friend="Lily",
        friend_gender="girl",
        friend_trait="gentle",
        relation="friends",
        trust=8,
        captain_age=5,
        friend_age=6,
        delay=0,
    ),
    StoryParams(
        spot="umbrella_stand",
        helper="towel_tunnel",
        adult="bellhop",
        captain="Max",
        captain_gender="boy",
        friend="Ava",
        friend_gender="girl",
        friend_trait="kind",
        relation="friends",
        trust=5,
        captain_age=6,
        friend_age=5,
        delay=0,
    ),
    StoryParams(
        spot="brochure_rack",
        helper="shoebox_shelter",
        adult="concierge",
        captain="Leo",
        captain_gender="boy",
        friend="Nora",
        friend_gender="girl",
        friend_trait="patient",
        relation="friends",
        trust=6,
        captain_age=6,
        friend_age=5,
        delay=1,
    ),
    StoryParams(
        spot="fern",
        helper="laundry_basket",
        adult="bellhop",
        captain="Sam",
        captain_gender="boy",
        friend="Mia",
        friend_gender="girl",
        friend_trait="careful",
        relation="friends",
        trust=4,
        captain_age=6,
        friend_age=5,
        delay=1,
    ),
]


def explain_rejection(spot: Spot, helper: HelperMethod) -> str:
    if helper.sense < SENSE_MIN:
        return (
            f"(No story: {helper.label} is too rough or thoughtless for helping a little lizard. "
            f"Pick a gentler method like {', '.join(sorted(h.id for h in sensible_helpers()))}.)"
        )
    return (
        f"(No story: {helper.label} does not really fit {spot.the}. "
        f"The helper must actually reach a {spot.level}-level hiding place.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.captain_age, params.friend_age, params.friend_trait, params.trust):
        return "averted"
    helper = HELPERS[params.helper]
    spot = SPOTS[params.spot]
    return "contained" if is_contained(helper, spot, params.delay) else "escaped"


ASP_RULES = r"""
sensible(H) :- helper(H), sense(H,S), sense_min(M), S >= M.
works(H,Sp) :- helper(H), spot(Sp), supports(H,L), level(Sp,L).
valid(Sp,H) :- spot(Sp), helper(H), sensible(H), works(H,Sp).

gentle_now(T) :- trait(T), is_gentle(T).
init_gentleness(5) :- trait(T), gentle_now(T).
init_gentleness(3) :- trait(T), not gentle_now(T).

older_friend :- relation(friends), captain_age(CA), friend_age(FA), FA > CA.
older_bonus(2) :- older_friend.
older_bonus(0) :- not older_friend.
trust_bonus(1) :- trust(T), T >= 7.
trust_bonus(0) :- trust(T), T < 7.

authority(G + O + TB) :- init_gentleness(G), older_bonus(O), trust_bonus(TB).
averted :- authority(A), bold_init(B), A > B.

severity(SK + D) :- chosen_spot(SP), skittish(SP,SK), delay(D).
contained :- chosen_helper(H), power(H,P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(escaped) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        lines.append(asp.fact("level", spot_id, spot.level))
        lines.append(asp.fact("skittish", spot_id, spot.skittish))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("sense", helper_id, helper.sense))
        lines.append(asp.fact("power", helper_id, helper.power))
        for level in sorted(helper.level_support):
            lines.append(asp.fact("supports", helper_id, level))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bold_init", int(BOLD_INIT)))
    for trait in sorted(GENTLE_TRAITS):
        lines.append(asp.fact("is_gentle", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_spot", params.spot),
        asp.fact("chosen_helper", params.helper),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("captain_age", params.captain_age),
        asp.fact("friend_age", params.friend_age),
        asp.fact("trait", params.friend_trait),
        asp.fact("trust", params.trust),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: pirates in a hotel lobby learn gentle friendship from a tiny lizard."
    )
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--adult", choices=ADULTS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how much extra time the scared lizard gets to bolt")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (spot, helper) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spot and args.helper:
        spot = SPOTS[args.spot]
        helper = HELPERS[args.helper]
        if not (helper.sense >= SENSE_MIN and works_for_spot(helper, spot)):
            raise StoryError(explain_rejection(spot, helper))
    if args.helper and HELPERS[args.helper].sense < SENSE_MIN:
        helper = HELPERS[args.helper]
        spot = SPOTS[args.spot] if args.spot else next(iter(SPOTS.values()))
        raise StoryError(explain_rejection(spot, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.spot is None or combo[0] == args.spot)
        and (args.helper is None or combo[1] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    spot_id, helper_id = rng.choice(sorted(combos))
    captain, captain_gender = _pick_name(rng)
    friend, friend_gender = _pick_name(rng, avoid=captain)
    adult = args.adult or rng.choice(sorted(ADULTS))
    friend_trait = rng.choice(TRAITS)
    relation = "friends"
    trust = rng.randint(3, 9)
    captain_age, friend_age = rng.sample([4, 5, 6, 7], 2)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        spot=spot_id,
        helper=helper_id,
        adult=adult,
        captain=captain,
        captain_gender=captain_gender,
        friend=friend,
        friend_gender=friend_gender,
        friend_trait=friend_trait,
        relation=relation,
        trust=trust,
        captain_age=captain_age,
        friend_age=friend_age,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.adult not in ADULTS:
        raise StoryError(f"(Unknown adult: {params.adult})")

    spot = SPOTS[params.spot]
    helper = HELPERS[params.helper]
    if helper.sense < SENSE_MIN or not works_for_spot(helper, spot):
        raise StoryError(explain_rejection(spot, helper))

    world = tell(
        spot=spot,
        helper=helper,
        adult_cfg=ADULTS[params.adult],
        captain_name=params.captain,
        captain_type=params.captain_gender,
        friend_name=params.friend,
        friend_type=params.friend_gender,
        friend_trait=params.friend_trait,
        relation=params.relation,
        trust=params.trust,
        captain_age=params.captain_age,
        friend_age=params.friend_age,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (spot, helper) combos:\n")
        for spot, helper in combos:
            print(f"  {spot:15} {helper}")
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
            header = f"### {p.captain} & {p.friend}: {p.spot}, {p.helper}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
