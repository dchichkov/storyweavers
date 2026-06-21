#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/teeny_friendship_suspense_mystery.py
===============================================================

A standalone story world for a tiny child-facing mystery with friendship and a
small, suspenseful search. Two friends notice that a treasured little object is
missing. They follow a teeny clue trail, grow nervous near a shadowy hiding
spot, and solve the mystery together.

The world is intentionally small and constraint-checked:

* A culprit can only leave clue kinds it could really leave.
* A culprit can only hide an object in places it could plausibly reach.
* A friend can only recover the object with a method that fits the hiding spot.
* Some pairs lead to a "false scare" before the gentle reveal, while others are
  straightforward finds.

Run it
------
    python storyworlds/worlds/gpt-5.4/teeny_friendship_suspense_mystery.py
    python storyworlds/worlds/gpt-5.4/teeny_friendship_suspense_mystery.py --culprit kitten --clue yarn --spot under_sofa
    python storyworlds/worlds/gpt-5.4/teeny_friendship_suspense_mystery.py --clue feather
    python storyworlds/worlds/gpt-5.4/teeny_friendship_suspense_mystery.py --all
    python storyworlds/worlds/gpt-5.4/teeny_friendship_suspense_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/teeny_friendship_suspense_mystery.py --trace
    python storyworlds/worlds/gpt-5.4/teeny_friendship_suspense_mystery.py --verify
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
BRAVE_ENOUGH = 5


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    intro: str
    hush: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    phrase: str
    clues: set[str] = field(default_factory=set)
    spots: set[str] = field(default_factory=set)
    rustle: str = ""
    reveal: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    trail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    creepy: str
    reach: set[str] = field(default_factory=set)
    false_scare: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    phrase: str
    spots: set[str] = field(default_factory=set)
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


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
        return [e for e in self.entities.values() if e.role in {"owner", "friend"}]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    owner = world.get("owner")
    token = world.get("token")
    if token.attrs.get("missing") and ("worry", owner.id) not in world.fired:
        world.fired.add(("worry", owner.id))
        owner.memes["sad"] += 1
        owner.memes["worry"] += 1
    return []


def _r_comfort(world: World) -> list[str]:
    owner = world.get("owner")
    friend = world.get("friend")
    if owner.memes["worry"] >= THRESHOLD and ("comfort", friend.id) not in world.fired:
        world.fired.add(("comfort", friend.id))
        friend.memes["care"] += 1
        owner.memes["hope"] += 1
    return []


def _r_suspense(world: World) -> list[str]:
    room = world.get("room")
    if room.meters["shadow"] >= THRESHOLD and ("shadow_fear", "kids") not in world.fired:
        world.fired.add(("shadow_fear", "kids"))
        for kid in world.kids():
            kid.memes["fear"] += 1
    return []


def _r_find_relief(world: World) -> list[str]:
    token = world.get("token")
    if token.attrs.get("found") and ("relief", "kids") not in world.fired:
        world.fired.add(("relief", "kids"))
        for kid in world.kids():
            kid.memes["relief"] += 1
            kid.memes["joy"] += 1
            kid.memes["fear"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="worry", tag="emotion", apply=_r_worry),
    Rule(name="comfort", tag="friendship", apply=_r_comfort),
    Rule(name="suspense", tag="emotion", apply=_r_suspense),
    Rule(name="relief", tag="emotion", apply=_r_find_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "living_room": Place(
        id="living_room",
        label="living room",
        intro="The afternoon light made the living room look warm, except for one dim corner by the sofa.",
        hush="The room went so quiet that even tiny sounds seemed important.",
        tags={"room"},
    ),
    "sunroom": Place(
        id="sunroom",
        label="sunroom",
        intro="The sunroom was bright by the windows, but the basket shelf underneath stayed full of little shadows.",
        hush="The glass walls held in every rustle until it sounded like a secret.",
        tags={"room"},
    ),
    "porch": Place(
        id="porch",
        label="porch",
        intro="The porch boards were bright in the sun, though the steps underneath were dark and cool.",
        hush="For a moment the porch seemed to be holding its breath.",
        tags={"outside"},
    ),
}

TREASURES = {
    "bell": Treasure(
        id="bell",
        label="bell",
        phrase="a teeny silver bell from their friendship bracelet set",
        sound="gave a soft, bright jingle when it moved",
        tags={"bell", "friendship"},
    ),
    "key": Treasure(
        id="key",
        label="tiny key",
        phrase="a teeny pretend key from their clubhouse box",
        sound="clicked like a secret when it tapped the floor",
        tags={"key", "friendship"},
    ),
    "star": Treasure(
        id="star",
        label="star charm",
        phrase="a teeny gold star charm they liked to trade back and forth for luck",
        sound="made the faintest tink sound",
        tags={"charm", "friendship"},
    ),
}

CLUES = {
    "yarn": Clue(
        id="yarn",
        label="yarn",
        phrase="a teeny piece of blue yarn",
        trail="A teeny piece of blue yarn lay by the chair leg, and another bit waited farther on like a little arrow.",
        tags={"yarn"},
    ),
    "crumb": Clue(
        id="crumb",
        label="cracker crumb",
        phrase="a teeny cracker crumb",
        trail="A teeny cracker crumb sat on the floor, then another, then another, making a tiny trail to follow.",
        tags={"crumb"},
    ),
    "feather": Clue(
        id="feather",
        label="feather",
        phrase="a teeny gray feather",
        trail="A teeny gray feather rested near the toy box, and one more feather showed the way ahead.",
        tags={"feather"},
    ),
    "leaf": Clue(
        id="leaf",
        label="leaf",
        phrase="a teeny curled leaf",
        trail="A teeny curled leaf had somehow blown inside, and a second one pointed toward the hiding place.",
        tags={"leaf"},
    ),
}

SPOTS = {
    "under_sofa": Spot(
        id="under_sofa",
        label="under the sofa",
        phrase="under the sofa where the dust shadows were deepest",
        creepy="Only a narrow dark strip showed under the sofa, and something tiny rustled there.",
        reach={"reach", "flashlight_hook"},
        false_scare=True,
        tags={"sofa"},
    ),
    "basket_shelf": Spot(
        id="basket_shelf",
        label="behind the basket shelf",
        phrase="behind the basket shelf in a stripe of shade",
        creepy="The baskets made stacked little caves, and one of them trembled almost too softly to see.",
        reach={"reach", "tiptoe"},
        false_scare=True,
        tags={"shelf"},
    ),
    "flowerpot": Spot(
        id="flowerpot",
        label="behind the flowerpot",
        phrase="behind the flowerpot by the porch rail",
        creepy="The leaves shook once, and then stood still again as if they had swallowed a secret.",
        reach={"reach", "tiptoe"},
        false_scare=False,
        tags={"flowerpot"},
    ),
    "step_gap": Spot(
        id="step_gap",
        label="under the porch step",
        phrase="under the porch step in a cool dark gap",
        creepy="The space under the step looked black in the middle, and the boards answered with a tiny tick.",
        reach={"flashlight_hook"},
        false_scare=True,
        tags={"step"},
    ),
}

CULPRITS = {
    "kitten": Culprit(
        id="kitten",
        label="kitten",
        phrase="the family kitten",
        clues={"yarn"},
        spots={"under_sofa", "basket_shelf"},
        rustle="A whiskery little shape twitched in the dark.",
        reveal="The family kitten blinked back at them with the missing treasure tucked by its paws.",
        tags={"kitten", "pet"},
    ),
    "mouse": Culprit(
        id="mouse",
        label="mouse",
        phrase="a small brown mouse",
        clues={"crumb", "leaf"},
        spots={"step_gap", "flowerpot"},
        rustle="Two bead-bright eyes flashed and vanished again.",
        reveal="A small brown mouse had dragged the treasure beside its nest of leaves.",
        tags={"mouse"},
    ),
    "bird": Culprit(
        id="bird",
        label="bird",
        phrase="a busy little bird",
        clues={"feather", "leaf"},
        spots={"flowerpot", "step_gap"},
        rustle="Something gave a quick flutter and then was still.",
        reveal="A busy little bird had dropped the treasure near twigs it was gathering.",
        tags={"bird"},
    ),
    "puppy": Culprit(
        id="puppy",
        label="puppy",
        phrase="the neighbor's playful puppy",
        clues={"crumb", "yarn"},
        spots={"under_sofa", "flowerpot"},
        rustle="A small nose snuffled once in the dark.",
        reveal="The neighbor's playful puppy wagged at them, proud of the treasure it had carried away.",
        tags={"puppy", "pet"},
    ),
}

METHODS = {
    "reach": Method(
        id="reach",
        phrase="knelt down and reached in carefully",
        qa_text="They knelt down and reached in carefully.",
        tags={"reach"},
    ),
    "flashlight_hook": Method(
        id="flashlight_hook",
        phrase="used a flashlight and a bent toy hook to pull it out gently",
        qa_text="They used a flashlight and a bent toy hook to pull it out gently.",
        tags={"flashlight"},
    ),
    "tiptoe": Method(
        id="tiptoe",
        phrase="stood on tiptoe and lifted the basket just enough to peek behind it",
        qa_text="They stood on tiptoe and lifted the basket just enough to peek behind it.",
        tags={"tiptoe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Eli", "Theo", "Finn", "Noah"]
TRAITS = ["careful", "kind", "curious", "steady", "gentle", "brave"]


def clue_fits(culprit: Culprit, clue: Clue) -> bool:
    return clue.id in culprit.clues


def spot_fits(culprit: Culprit, spot: Spot) -> bool:
    return spot.id in culprit.spots


def method_for(spot: Spot) -> Optional[Method]:
    for method in METHODS.values():
        if method.id in spot.reach:
            return method
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for culprit_id, culprit in CULPRITS.items():
            for clue_id, clue in CLUES.items():
                for spot_id, spot in SPOTS.items():
                    if clue_fits(culprit, clue) and spot_fits(culprit, spot) and method_for(spot):
                        combos.append((place_id, culprit_id, clue_id, spot_id))
    return combos


def is_false_scare(spot: Spot) -> bool:
    return spot.false_scare


def courage_score(trait: str, helper_trait: str) -> int:
    score = 4
    if trait in {"brave", "steady"}:
        score += 1
    if helper_trait in {"kind", "gentle", "steady", "brave"}:
        score += 1
    return score


def brave_enough(trait: str, helper_trait: str) -> bool:
    return courage_score(trait, helper_trait) >= BRAVE_ENOUGH


def outcome_of(params: "StoryParams") -> str:
    spot = SPOTS[params.spot]
    if is_false_scare(spot) and not brave_enough(params.owner_trait, params.friend_trait):
        return "call_grownup"
    return "solve"


def explain_rejection(culprit: Culprit, clue: Clue, spot: Spot) -> str:
    if not clue_fits(culprit, clue):
        return (f"(No story: {culprit.phrase} would not leave {clue.phrase} behind, "
                f"so the clue trail would not make sense.)")
    if not spot_fits(culprit, spot):
        return (f"(No story: {culprit.phrase} would not plausibly hide the treasure "
                f"{spot.label}, so the mystery's answer would feel fake.)")
    if not method_for(spot):
        return (f"(No story: there is no gentle way in this world to recover something "
                f"from {spot.label}.)")
    return "(No story: this combination does not make a reasonable mystery.)"


def explain_method(spot: Spot) -> str:
    return (f"(No story: {spot.label} needs a fitting recovery method, but none was "
            f"found in the method catalog.)")


def introduce(world: World, owner: Entity, friend: Entity, place: Place, treasure: Treasure) -> None:
    owner.memes["love"] += 1
    friend.memes["love"] += 1
    token = world.get("token")
    world.say(
        f"{owner.id} and {friend.id} were best friends, and that afternoon they sat in the {place.label} making up secret clues for each other."
    )
    world.say(
        f"Between them lay {treasure.phrase}. It {treasure.sound}, and they liked to say it belonged to both of them."
    )
    token.attrs["shared"] = True


def missing(world: World, owner: Entity, friend: Entity, place: Place) -> None:
    token = world.get("token")
    token.attrs["missing"] = True
    token.meters["moved"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {owner.id} looked down and blinked. The little treasure was gone."
    )
    world.say(
        f'{place.hush} "{friend.id}," {owner.id} whispered, "it was right here a moment ago."'
    )


def comfort(world: World, owner: Entity, friend: Entity) -> None:
    propagate(world, narrate=False)
    world.say(
        f"{friend.id} moved closer instead of laughing. "
        f'"We will solve it together," {friend.pronoun()} said, taking {owner.pronoun("possessive")} hand for one quick squeeze.'
    )


def find_clue(world: World, clue: Clue) -> None:
    room = world.get("room")
    room.meters["mystery"] += 1
    world.say(clue.trail)
    world.say("That was enough to turn a missing thing into a real mystery.")


def follow_trail(world: World, owner: Entity, friend: Entity, spot: Spot) -> None:
    owner.memes["attention"] += 1
    friend.memes["attention"] += 1
    world.say(
        f"Side by side, they followed the tiny trail until it ended {spot.phrase}."
    )


def suspense(world: World, culprit: Culprit, spot: Spot, owner: Entity, friend: Entity) -> None:
    room = world.get("room")
    room.meters["shadow"] += 1
    propagate(world, narrate=False)
    world.say(spot.creepy)
    world.say(culprit.rustle)
    if owner.memes["fear"] >= THRESHOLD or friend.memes["fear"] >= THRESHOLD:
        world.say(
            f"{owner.id} held still. {friend.id} held still too. For one second, both friends wondered if the dark was hiding something much bigger."
        )


def solve(world: World, culprit: Culprit, spot: Spot, method: Method, owner: Entity, friend: Entity) -> None:
    token = world.get("token")
    world.say(
        f"But {friend.id} whispered, " + '"Let us be careful, not scared."' if False else ""
    )


def solve_mystery(world: World, culprit: Culprit, spot: Spot, method: Method,
                  owner: Entity, friend: Entity, treasure: Treasure) -> None:
    token = world.get("token")
    world.say(
        f'"Let us be careful, not scared," {friend.id} whispered.'
    )
    world.say(
        f"Together they {method.phrase}."
    )
    token.attrs["found"] = True
    token.attrs["missing"] = False
    token.attrs["holder"] = owner.id
    token.meters["safe"] += 1
    propagate(world, narrate=False)
    world.say(culprit.reveal)
    world.say(
        f"{owner.id} laughed a shaky little laugh as {owner.pronoun()} picked up the {treasure.label}. "
        f"It had not been lost forever after all."
    )


def grownup_help(world: World, owner: Entity, friend: Entity, spot: Spot,
                 culprit: Culprit, treasure: Treasure) -> None:
    helper = world.get("grownup")
    token = world.get("token")
    owner.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'"Maybe the mystery is a little too spooky from here," {friend.id} said, still staying beside {owner.id}.'
    )
    world.say(
        f"So they called for {helper.label_word}, who came with a flashlight and a warm voice."
    )
    token.attrs["found"] = True
    token.attrs["missing"] = False
    token.attrs["holder"] = owner.id
    token.meters["safe"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} shone the light {spot.label} and smiled."
    )
    world.say(
        f"{culprit.reveal} A moment later, the {treasure.label} was back in {owner.id}'s hand."
    )


def ending(world: World, owner: Entity, friend: Entity, treasure: Treasure, place: Place, outcome: str) -> None:
    owner.memes["gratitude"] += 1
    friend.memes["gratitude"] += 1
    if outcome == "solve":
        world.say(
            f'{owner.id} fastened the {treasure.label} between them again. "It felt less scary because you stayed with me," {owner.pronoun()} said.'
        )
    else:
        world.say(
            f'{owner.id} tucked the {treasure.label} safely into a pocket. "I am glad we asked for help together," {owner.pronoun()} said.'
        )
    world.say(
        f"{friend.id} smiled, and soon the {place.label} did not feel shadowy at all. The mystery was over, but their friendship felt bigger than before."
    )


def tell(place: Place, treasure: Treasure, culprit: Culprit, clue: Clue, spot: Spot,
         owner_name: str = "Lily", owner_gender: str = "girl",
         friend_name: str = "Ben", friend_gender: str = "boy",
         owner_trait: str = "careful", friend_trait: str = "kind",
         grownup_type: str = "mother") -> World:
    world = World()
    owner = world.add(Entity(
        id="owner",
        kind="character",
        type=owner_gender,
        label=owner_name,
        phrase=owner_name,
        role="owner",
        attrs={"trait": owner_trait},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        phrase=friend_name,
        role="friend",
        attrs={"trait": friend_trait},
    ))
    grownup = world.add(Entity(
        id="grownup",
        kind="character",
        type=grownup_type,
        label="the grown-up",
        phrase="the grown-up",
        role="grownup",
    ))
    token = world.add(Entity(
        id="token",
        kind="thing",
        type="treasure",
        label=treasure.label,
        phrase=treasure.phrase,
        attrs={"missing": False, "found": False},
        tags=set(treasure.tags),
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="place",
        label=place.label,
        phrase=place.label,
        tags=set(place.tags),
    ))

    world.facts["display_owner_name"] = owner_name
    world.facts["display_friend_name"] = friend_name

    world.say(place.intro)
    introduce(world, owner, friend, place, treasure)
    world.para()
    missing(world, owner, friend, place)
    comfort(world, owner, friend)
    find_clue(world, clue)
    follow_trail(world, owner, friend, spot)
    world.para()
    suspense(world, culprit, spot, owner, friend)

    method = method_for(spot)
    if method is None:
        raise StoryError(explain_method(spot))

    outcome = "solve"
    if is_false_scare(spot) and not brave_enough(owner_trait, friend_trait):
        outcome = "call_grownup"

    world.para()
    if outcome == "solve":
        solve_mystery(world, culprit, spot, method, owner, friend, treasure)
    else:
        grownup_help(world, owner, friend, spot, culprit, treasure)

    world.para()
    ending(world, owner, friend, treasure, place, outcome)

    world.facts.update(
        place=place,
        treasure=treasure,
        culprit=culprit,
        clue=clue,
        spot=spot,
        method=method,
        owner=owner,
        friend=friend,
        grownup=grownup,
        outcome=outcome,
        false_scare=is_false_scare(spot),
        owner_trait=owner_trait,
        friend_trait=friend_trait,
        brave=brave_enough(owner_trait, friend_trait),
        courage=courage_score(owner_trait, friend_trait),
    )
    return world


def pair_word(owner: Entity, friend: Entity) -> str:
    if owner.type == "girl" and friend.type == "girl":
        return "two best friends"
    if owner.type == "boy" and friend.type == "boy":
        return "two best friends"
    return "two best friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    owner = f["owner"]
    friend = f["friend"]
    treasure = f["treasure"]
    culprit = f["culprit"]
    spot = f["spot"]
    outcome = f["outcome"]
    if outcome == "call_grownup":
        return [
            'Write a gentle mystery story for a 3-to-5-year-old that includes the word "teeny", a missing tiny object, and two friends who ask for help when the search feels too spooky.',
            f"Tell a suspenseful but kind story where {world.facts['display_owner_name']} and {world.facts['display_friend_name']} follow a tiny clue trail to {spot.label}, then solve the mystery with a grown-up's help.",
            f'Write a friendship mystery where a teeny treasure disappears, the friends stay together, and the ending shows that asking for help can be brave.',
        ]
    return [
        'Write a gentle mystery story for a 3-to-5-year-old that includes the word "teeny", friendship, and suspense around a missing tiny object.',
        f"Tell a small mystery where {world.facts['display_owner_name']} and {world.facts['display_friend_name']} follow clues and discover that {culprit.phrase} took their {treasure.label}.",
        f'Write a child-facing suspense story with a warm ending: two friends feel nervous in the dark, stay together, and solve the mystery themselves.',
    ]


KNOWLEDGE = {
    "bell": [("What is a bell?", "A bell is a small object that makes a ringing sound when it moves or is shaken.")],
    "key": [("What is a key?", "A key is a little tool that can open a lock. In pretend play, a toy key can feel like part of a secret adventure.")],
    "charm": [("What is a charm?", "A charm is a tiny decoration people can hang on a bracelet or necklace.")],
    "friendship": [("What does friendship mean?", "Friendship means caring about each other, staying kind, and helping when one friend feels worried or sad.")],
    "kitten": [("Why do kittens carry little things away?", "Kittens like to bat, chase, and carry small objects because they feel like toys to them.")],
    "puppy": [("Why do puppies pick things up?", "Puppies explore with their mouths and like to carry interesting things around while they play.")],
    "mouse": [("Why might a mouse drag a small thing to a hiding place?", "A mouse may pull little objects into a snug hiding place while it explores for food or nesting bits.")],
    "bird": [("Why do birds collect small things?", "Some birds gather twigs, leaves, and other tiny things while building or fixing a nest.")],
    "yarn": [("What is yarn?", "Yarn is a soft string used for knitting and crafts. It comes in long strands that can leave little fuzzy bits behind.")],
    "crumb": [("What is a crumb?", "A crumb is a very small piece of food that breaks off from something bigger, like a cracker.")],
    "feather": [("What is a feather?", "A feather is a light, soft part that covers a bird's body and helps it fly and stay warm.")],
    "leaf": [("What is a leaf?", "A leaf is the flat green part that grows on many plants and trees.")],
    "flashlight": [("What does a flashlight do?", "A flashlight makes light in dark places so you can see clearly and safely.")],
}
KNOWLEDGE_ORDER = ["friendship", "bell", "key", "charm", "kitten", "puppy", "mouse", "bird",
                   "yarn", "crumb", "feather", "leaf", "flashlight"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    owner = f["owner"]
    friend = f["friend"]
    treasure = f["treasure"]
    culprit = f["culprit"]
    clue = f["clue"]
    spot = f["spot"]
    method = f["method"]
    outcome = f["outcome"]
    owner_name = f["display_owner_name"]
    friend_name = f["display_friend_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_word(owner, friend)}, {owner_name} and {friend_name}. They care about the same little treasure and solve the problem together."
        ),
        (
            "What went missing?",
            f"The missing thing was {treasure.phrase}. It mattered because the two friends liked to share it and treat it as something special."
        ),
        (
            f"How did {owner_name} and {friend_name} start solving the mystery?",
            f"They looked for a clue instead of guessing wildly. When they found {clue.phrase}, it gave them a real trail to follow."
        ),
        (
            "Why did the story feel suspenseful?",
            f"It felt suspenseful because the clue trail ended in a dark hiding place and they heard a tiny rustle there. For a moment, the friends did not know what was waiting in the shadows."
        ),
    ]
    if outcome == "solve":
        qa.append((
            f"How did the friends solve the mystery?",
            f"They stayed together and {method.qa_text} Then they discovered that {culprit.phrase} had taken the treasure."
        ))
        qa.append((
            f"What changed at the end?",
            f"The treasure was back, and the dark place stopped feeling scary. {owner_name} felt braver because {friend_name} stayed close the whole time."
        ))
    else:
        qa.append((
            f"Why did the friends call a grown-up?",
            f"They had followed the clues correctly, but the hiding place felt too spooky to handle alone. Calling for help was a careful choice, not a failure."
        ))
        qa.append((
            f"What changed at the end?",
            f"The treasure was found, and the friends learned they could solve problems together even when they needed help. The mystery ended gently because they stayed kind and sensible."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["treasure"].tags)
    tags |= set(world.facts["culprit"].tags)
    tags |= set(world.facts["clue"].tags)
    tags |= {"friendship"}
    if world.facts["method"].id == "flashlight_hook":
        tags |= {"flashlight"}
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


@dataclass
class StoryParams:
    place: str
    treasure: str
    culprit: str
    clue: str
    spot: str
    owner_name: str
    owner_gender: str
    friend_name: str
    friend_gender: str
    owner_trait: str
    friend_trait: str
    grownup: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="living_room",
        treasure="bell",
        culprit="kitten",
        clue="yarn",
        spot="under_sofa",
        owner_name="Lily",
        owner_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        owner_trait="careful",
        friend_trait="brave",
        grownup="mother",
    ),
    StoryParams(
        place="porch",
        treasure="key",
        culprit="mouse",
        clue="leaf",
        spot="step_gap",
        owner_name="Mia",
        owner_gender="girl",
        friend_name="Zoe",
        friend_gender="girl",
        owner_trait="gentle",
        friend_trait="kind",
        grownup="father",
    ),
    StoryParams(
        place="sunroom",
        treasure="star",
        culprit="kitten",
        clue="yarn",
        spot="basket_shelf",
        owner_name="Leo",
        owner_gender="boy",
        friend_name="Nora",
        friend_gender="girl",
        owner_trait="steady",
        friend_trait="curious",
        grownup="mother",
    ),
    StoryParams(
        place="porch",
        treasure="star",
        culprit="bird",
        clue="feather",
        spot="flowerpot",
        owner_name="Sam",
        owner_gender="boy",
        friend_name="Ella",
        friend_gender="girl",
        owner_trait="curious",
        friend_trait="steady",
        grownup="father",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a teeny friendship mystery with suspense. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("--owner-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mystery setups derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.clue and not clue_fits(CULPRITS[args.culprit], CLUES[args.clue]):
        raise StoryError(explain_rejection(CULPRITS[args.culprit], CLUES[args.clue], next(iter(SPOTS.values()))))
    if args.culprit and args.spot and not spot_fits(CULPRITS[args.culprit], SPOTS[args.spot]):
        clue = CLUES[args.clue] if args.clue else next(iter(CLUES.values()))
        raise StoryError(explain_rejection(CULPRITS[args.culprit], clue, SPOTS[args.spot]))
    if args.spot and method_for(SPOTS[args.spot]) is None:
        raise StoryError(explain_method(SPOTS[args.spot]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.clue is None or combo[2] == args.clue)
        and (args.spot is None or combo[3] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, culprit, clue, spot = rng.choice(sorted(combos))
    treasure = args.treasure or rng.choice(sorted(TREASURES))
    owner_gender = args.owner_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    owner_name = pick_name(rng, owner_gender)
    friend_name = pick_name(rng, friend_gender, avoid=owner_name)
    owner_trait = rng.choice(TRAITS)
    friend_trait = rng.choice(TRAITS)
    grownup = args.grownup or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        treasure=treasure,
        culprit=culprit,
        clue=clue,
        spot=spot,
        owner_name=owner_name,
        owner_gender=owner_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        owner_trait=owner_trait,
        friend_trait=friend_trait,
        grownup=grownup,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        treasure = TREASURES[params.treasure]
        culprit = CULPRITS[params.culprit]
        clue = CLUES[params.clue]
        spot = SPOTS[params.spot]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter key: {exc.args[0]})") from None

    if not clue_fits(culprit, clue) or not spot_fits(culprit, spot) or method_for(spot) is None:
        raise StoryError(explain_rejection(culprit, clue, spot))

    world = tell(
        place=place,
        treasure=treasure,
        culprit=culprit,
        clue=clue,
        spot=spot,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        owner_trait=params.owner_trait,
        friend_trait=params.friend_trait,
        grownup_type=params.grownup,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        label = e.label or e.id
        lines.append(f"  {e.id:8} ({e.type:8}) label={label!r} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(P, C, Cl, S) :- place(P), culprit(C), clue(Cl), spot(S),
                      leaves(C, Cl), hides(C, S), recoverable(S).

strong_trait(brave).
strong_trait(steady).
soft_help(kind).
soft_help(gentle).
soft_help(steady).
soft_help(brave).

owner_bonus(1) :- chosen_owner_trait(T), strong_trait(T).
owner_bonus(0) :- chosen_owner_trait(T), not strong_trait(T).
friend_bonus(1) :- chosen_friend_trait(T), soft_help(T).
friend_bonus(0) :- chosen_friend_trait(T), not soft_help(T).

courage(4 + OB + FB) :- owner_bonus(OB), friend_bonus(FB).
brave_enough :- courage(C), brave_threshold(B), C >= B.

outcome(call_grownup) :- chosen_spot(S), false_scare(S), not brave_enough.
outcome(solve) :- chosen_spot(S), not false_scare(S).
outcome(solve) :- chosen_spot(S), false_scare(S), brave_enough.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        for clue_id in sorted(culprit.clues):
            lines.append(asp.fact("leaves", culprit_id, clue_id))
        for spot_id in sorted(culprit.spots):
            lines.append(asp.fact("hides", culprit_id, spot_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        if method_for(spot):
            lines.append(asp.fact("recoverable", spot_id))
        if spot.false_scare:
            lines.append(asp.fact("false_scare", spot_id))
    lines.append(asp.fact("brave_threshold", BRAVE_ENOUGH))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_spot", params.spot),
        asp.fact("chosen_owner_trait", params.owner_trait),
        asp.fact("chosen_friend_trait", params.friend_trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
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
    for s in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation/emit succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, culprit, clue, spot) combos:\n")
        for place, culprit, clue, spot in combos:
            print(f"  {place:12} {culprit:8} {clue:8} {spot}")
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
            header = f"### {p.owner_name} & {p.friend_name}: {p.culprit}, {p.clue}, {p.spot} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
