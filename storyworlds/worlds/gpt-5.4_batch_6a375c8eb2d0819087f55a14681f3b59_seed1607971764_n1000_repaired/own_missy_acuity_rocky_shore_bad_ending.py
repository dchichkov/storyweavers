#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/own_missy_acuity_rocky_shore_bad_ending.py
=====================================================================

A small folk-tale-like story world about two friends on a rocky shore, a bright
thing wanted "for my own", repeated warnings, and endings that can turn sad when
the sea is ignored.

The domain models:
- typed entities with physical meters and emotional memes
- a short causal engine (slipping causes loss, hurt, and fear)
- a reasonableness gate for plausible treasure/spot/method choices
- an inline ASP twin for the gate and the ending model
- three QA sets grounded in the simulated world state

Run it
------
    python storyworlds/worlds/gpt-5.4/own_missy_acuity_rocky_shore_bad_ending.py
    python storyworlds/worlds/gpt-5.4/own_missy_acuity_rocky_shore_bad_ending.py --spot outer_rock --method rope_loop
    python storyworlds/worlds/gpt-5.4/own_missy_acuity_rocky_shore_bad_ending.py --spot far_ledge --method hand
    python storyworlds/worlds/gpt-5.4/own_missy_acuity_rocky_shore_bad_ending.py --all
    python storyworlds/worlds/gpt-5.4/own_missy_acuity_rocky_shore_bad_ending.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/own_missy_acuity_rocky_shore_bad_ending.py --verify
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
SENSE_MIN = 1
BASE_ACUITY = 5.0
WISE_TRAITS = {"watchful", "careful", "steady", "patient"}


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
    portable: bool = False
    # two dimensions
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
class Treasure:
    id: str
    label: str
    phrase: str
    glint: str
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
class Spot:
    id: str
    label: str
    path: str
    distance: int
    slick: int
    wave: int
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
class Method:
    id: str
    label: str
    reach: int
    safety: int
    sense: int
    text: str
    fail: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_slip_consequences(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.get("seeker")
    friend = world.get("friend")
    if seeker.meters["slipped"] >= THRESHOLD:
        sig = ("slip", seeker.id)
        if sig not in world.fired:
            world.fired.add(sig)
            seeker.meters["hurt"] += 1
            seeker.meters["soaked"] += 1
            seeker.meters["empty_handed"] += 1
            seeker.memes["fear"] += 1
            friend.memes["fear"] += 1
            friend.memes["sorrow"] += 1
            world.get("treasure").meters["lost_to_sea"] += 1
            out.append("__slip__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="slip_consequences", tag="physical", apply=_r_slip_consequences),
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


def wise_acuity(trait: str) -> float:
    return BASE_ACUITY + (2.0 if trait in WISE_TRAITS else 0.0)


def can_reach(method: Method, spot: Spot) -> bool:
    return method.reach >= spot.distance


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for tid in TREASURES:
        for sid, spot in SPOTS.items():
            for mid, method in METHODS.items():
                if can_reach(method, spot) and method.sense >= SENSE_MIN:
                    combos.append((tid, sid, mid))
    return combos


def would_turn_back(relation: str, seeker_age: int, friend_age: int, trait: str) -> bool:
    older_friend = relation == "friends" and friend_age > seeker_age
    return older_friend and wise_acuity(trait) > 6.0


def danger_value(spot: Spot, tide_delay: int) -> int:
    return spot.slick + spot.wave + tide_delay


def safe_attempt(method: Method, spot: Spot, tide_delay: int, helper_loyalty: int) -> bool:
    help_bonus = 1 if helper_loyalty >= 6 and method.id != "hand" else 0
    return method.safety + help_bonus >= danger_value(spot, tide_delay)


def predict_trouble(world: World, spot_id: str, method_id: str) -> dict:
    sim = world.copy()
    spot = SPOTS[spot_id]
    method = METHODS[method_id]
    seeker = sim.get("seeker")
    if not safe_attempt(method, spot, sim.facts["tide_delay"], sim.facts["helper_loyalty"]):
        seeker.meters["slipped"] += 1
        propagate(sim, narrate=False)
    return {
        "danger": danger_value(spot, sim.facts["tide_delay"]),
        "slip": seeker.meters["slipped"] >= THRESHOLD,
    }


def shore_opening(world: World, seeker: Entity, friend: Entity, treasure: Treasure) -> None:
    seeker.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In the old days, when gulls cried like little bells above the rocky shore, "
        f"{seeker.id} and {friend.id} went down at dawn with a wicker basket to gather "
        f"{treasure.label} and shell bits the sea had left behind."
    )
    world.say(
        f"They were fast friends, and they had a custom: whatever the tide gave, they "
        f"would share, so neither child went home with a light basket."
    )


def glimpse_treasure(world: World, seeker: Entity, friend: Entity, treasure: Treasure, spot: Spot) -> None:
    world.say(
        f"Among the weed-dark stones, {treasure.phrase} flashed {treasure.glint} from "
        f"{spot.path}. The sight of it brightened both their faces."
    )
    world.say(
        f'"Look there," said {friend.id}. "The sea has set a pretty prize upon {spot.label}."'
    )


def desire_own(world: World, seeker: Entity, treasure: Treasure, spot: Spot) -> None:
    seeker.memes["greed"] += 1
    world.say(
        f"But {seeker.id} stared until wanting grew larger than wisdom. "
        f'"I will fetch it for my own," {seeker.pronoun()} said. '
        f'"No other thing in the basket shall shine like that {treasure.label}."'
    )


def acuity_warning(world: World, friend: Entity, seeker: Entity, spot: Spot, method: Method) -> None:
    pred = predict_trouble(world, spot.id, method.id)
    friend.memes["care"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_slip"] = pred["slip"]
    acuity = wise_acuity(friend.attrs.get("trait", ""))
    word = "acuity" if acuity >= 6 else "good sense"
    world.say(
        f"{friend.id} had sharp {word} for the sea and its moods. "
        f'"The tide is climbing, and {spot.label} is slick," {friend.pronoun()} said.'
    )
    world.say(
        f'"Come back from the thought of it, {seeker.id}. Come back from the thought of it. '
        f'Come back from the thought of it."'
    )


def turn_back(world: World, seeker: Entity, friend: Entity, treasure: Treasure) -> None:
    seeker.memes["relief"] += 1
    friend.memes["relief"] += 1
    seeker.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"The words were said three times, and the third time they reached {seeker.id}'s heart. "
        f"{seeker.pronoun().capitalize()} looked from the prize to {friend.id}'s face and let the wanting go."
    )
    world.say(
        f'"Better a whole ankle than a bright stone," {seeker.pronoun()} said. '
        f'Then the two friends filled their basket with humbler finds and carried it home together.'
    )
    world.say(
        f"That evening the basket was not rich, yet it was honestly won, and their friendship "
        f"shone brighter than the thing left glittering by the sea."
    )


def choose_method(world: World, seeker: Entity, friend: Entity, method: Method) -> None:
    seeker.meters["trying"] += 1
    world.say(
        f"Still {seeker.id} would not listen. {seeker.pronoun().capitalize()} {method.text}, "
        f"while {friend.id} stayed close with empty hands and a worried mouth."
    )


def succeed(world: World, seeker: Entity, friend: Entity, treasure: Treasure, spot: Spot, method: Method) -> None:
    tr = world.get("treasure")
    tr.meters["taken"] += 1
    seeker.memes["joy"] += 1
    friend.memes["relief"] += 1
    seeker.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"The sea hissed around the stones, but this time the careful plan was enough. "
        f"{seeker.id} won the {treasure.label} from {spot.label} by {method.qa_text}."
    )
    world.say(
        f"{seeker.pronoun().capitalize()} looked at it, then placed it in the middle of the basket instead of hiding it away. "
        f'"Let us keep our old custom," {seeker.pronoun()} said. "A shared treasure sits warmer than a secret one."'
    )
    world.say(
        f"So the friends walked home along the windy shore, and the bright prize nodded in the basket between them."
    )


def fail_slip(world: World, seeker: Entity, friend: Entity, treasure: Treasure, spot: Spot, method: Method) -> None:
    seeker.meters["slipped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But the sea is older than wanting. {method.fail} on {spot.label}, and a cold wave struck the stones."
    )
    world.say(
        f"{seeker.id} slipped, fell hard upon one knee, and the {treasure.label} spun away in white water before "
        f"either child could catch it."
    )


def bad_ending(world: World, seeker: Entity, friend: Entity) -> None:
    seeker.memes["shame"] += 1
    friend.memes["friendship"] -= 1
    seeker.memes["friendship"] -= 1
    world.say(
        f"{friend.id} pulled {seeker.id} back from the edge and half-carried {seeker.pronoun('object')} to the dry stones. "
        f'"I called you back three times," {friend.pronoun()} whispered, and there were tears in {friend.pronoun('possessive')} eyes.'
    )
    world.say(
        f"{seeker.id} said nothing, for the knee throbbed, the basket was nearly empty, and the wish to have one shining thing "
        f"for {seeker.pronoun('possessive')} own had cost more than the thing was worth."
    )
    world.say(
        f"They went home before noon, slowly and in silence. Long after that day, whenever the tide spoke against the rocks, "
        f"both children remembered how greed can bruise the body and bend a friendship sad."
    )


TREASURES = {
    "moon_shell": Treasure(
        id="moon_shell",
        label="moon-shell",
        phrase="a pale moon-shell",
        glint="like milk with a lamp inside",
        tags={"shell", "sharing"},
    ),
    "blue_glass": Treasure(
        id="blue_glass",
        label="blue sea-glass",
        phrase="a round piece of blue sea-glass",
        glint="like a bit of sky caught in water",
        tags={"sea_glass", "sharing"},
    ),
    "sun_stone": Treasure(
        id="sun_stone",
        label="sun-stone",
        phrase="a smooth amber stone",
        glint="as if sunset had slept inside it",
        tags={"stone", "sharing"},
    ),
}

SPOTS = {
    "near_pool": Spot(
        id="near_pool",
        label="the near tide pool",
        path="a shallow tide pool beside the first line of rocks",
        distance=1,
        slick=1,
        wave=1,
        tags={"tide_pool"},
    ),
    "outer_rock": Spot(
        id="outer_rock",
        label="the outer rock",
        path="a black rock beyond the first wash of foam",
        distance=2,
        slick=2,
        wave=2,
        tags={"rock", "tide"},
    ),
    "far_ledge": Spot(
        id="far_ledge",
        label="the far ledge",
        path="a narrow ledge where the waves turned back snarling",
        distance=3,
        slick=2,
        wave=3,
        tags={"ledge", "tide"},
    ),
}

METHODS = {
    "hand": Method(
        id="hand",
        label="bare hands",
        reach=1,
        safety=1,
        sense=1,
        text="stepped out with bare hands, meaning to snatch the prize in a single quick grab",
        fail="reached with bare hands",
        qa_text="reaching only as far as the close stones allowed",
        tags={"slippery_rocks"},
    ),
    "drift_hook": Method(
        id="drift_hook",
        label="a driftwood hook",
        reach=2,
        safety=2,
        sense=2,
        text="found a crooked driftwood hook and edged forward to draw the prize nearer",
        fail="worked the driftwood hook as carefully as fear allowed",
        qa_text="using a driftwood hook from a steadier rock",
        tags={"tool", "slippery_rocks"},
    ),
    "rope_loop": Method(
        id="rope_loop",
        label="a rope loop",
        reach=3,
        safety=3,
        sense=3,
        text="made a rope loop from the basket cord and cast it toward the gleam",
        fail="cast the rope loop again and again",
        qa_text="looping it safely from farther back",
        tags={"rope", "tool"},
    ),
}

GIRL_NAMES = ["Missy", "Lina", "Mara", "Tessa", "Nell", "Bryn"]
BOY_NAMES = ["Rowan", "Jory", "Finn", "Tarin", "Eli", "Corin"]
TRAITS = ["watchful", "careful", "steady", "patient", "bold", "restless"]


@dataclass
class StoryParams:
    treasure: str
    spot: str
    method: str
    seeker: str
    seeker_gender: str
    friend: str
    friend_gender: str
    friend_trait: str
    relation: str = "friends"
    seeker_age: int = 6
    friend_age: int = 7
    helper_loyalty: int = 7
    tide_delay: int = 1
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
    "tide_pool": [(
        "What is a tide pool?",
        "A tide pool is a little pool of seawater left between rocks when the tide goes out. Small sea creatures and shells can stay there until the water returns.",
    )],
    "tide": [(
        "What is the tide?",
        "The tide is the sea moving in and out. When the tide comes in, waves reach farther up the shore and can make rocks more dangerous.",
    )],
    "slippery_rocks": [(
        "Why are wet rocks slippery?",
        "Wet rocks can be smooth and covered with seaweed, so shoes and feet slide on them easily. That is why people must step slowly and carefully near the sea.",
    )],
    "rope": [(
        "What can a rope help you do?",
        "A rope can help you reach or pull something from a safer place. It lets you stay farther back instead of stepping too close to danger.",
    )],
    "sharing": [(
        "Why is sharing good for friends?",
        "Sharing helps friends feel included and trusted. It keeps one person's wanting from growing bigger than the friendship.",
    )],
    "sea_glass": [(
        "What is sea-glass?",
        "Sea-glass is old glass the sea has worn smooth over a long time. The waves rub it until its sharp edges are gone.",
    )],
    "shell": [(
        "What is a shell?",
        "A shell is the hard outside home of a sea creature like a snail or clam. After the creature is gone, the shell can wash onto the shore.",
    )],
    "stone": [(
        "Why do stones by the sea look smooth?",
        "Waves roll them and knock them against one another over and over. That rubbing wears away the rough corners and makes them smooth.",
    )],
}
KNOWLEDGE_ORDER = ["tide_pool", "tide", "slippery_rocks", "rope", "sharing", "sea_glass", "shell", "stone"]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two friends"
    if a.type == "boy" and b.type == "boy":
        return "two friends"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    friend = f["friend"]
    treasure = f["treasure_cfg"]
    spot = f["spot_cfg"]
    outcome = f["outcome"]
    if outcome == "bad":
        return [
            f'Write a folk-tale style story for a 3-to-5-year-old set on a rocky shore, using the words "own", "Missy", and "acuity". Include friendship, repetition, and a bad ending.',
            f"Tell a cautionary tale where {seeker.id} wants a shining {treasure.label} for {seeker.pronoun('possessive')} own, ignores {friend.id}'s repeated warning, and is hurt on {spot.label}.",
            f"Write a simple sea-side folktale where a friend speaks the same warning three times, but greed wins and the ending turns sad.",
        ]
    if outcome == "averted":
        return [
            f'Write a folk-tale style story set on a rocky shore with the words "own", "Missy", and "acuity". Make repetition and friendship important.',
            f"Tell a tale where {friend.id}'s acuity helps {seeker.id} turn back from danger after hearing the same warning three times.",
            f"Write a gentle story where a child gives up keeping a treasure for {seeker.pronoun('possessive')} own and goes home with friendship kept safe.",
        ]
    return [
        f'Write a folk-tale style story set on a rocky shore with the words "own", "Missy", and "acuity". Include repetition and friendship.',
        f"Tell a story where two friends spot a shining {treasure.label}, and a careful tool helps them reach it without losing their promise to share.",
        f"Write a short seaside tale in which repeated warnings matter and the ending image shows friendship made stronger.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    friend = f["friend"]
    treasure = f["treasure_cfg"]
    spot = f["spot_cfg"]
    method = f["method_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(seeker, friend)}, {seeker.id} and {friend.id}, on a rocky shore. They began as close friends who usually shared what the sea gave them.",
        ),
        (
            "What did they find on the rocky shore?",
            f"They found {treasure.phrase} shining from {spot.path}. Its bright look is what tempted {seeker.id} to go farther than was wise.",
        ),
        (
            f"Why did {friend.id} warn {seeker.id}?",
            f"{friend.id} could see that {spot.label} was slick and that the tide was climbing. Because of that sharp acuity, {friend.pronoun()} understood that one careless step could lead to a slip.",
        ),
        (
            "What was repeated in the story?",
            f"The warning was repeated three times: {friend.id} told {seeker.id} to come back from the thought of going after the prize. The repetition made the warning sound like an old folktale lesson.",
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"What changed {seeker.id}'s mind?",
            f"{seeker.id} finally listened on the third warning and let go of the wish to keep the treasure for {seeker.pronoun('possessive')} own. Seeing {friend.id}'s worried face mattered more than the shining thing.",
        ))
        qa.append((
            "How did the story end?",
            f"It ended quietly and safely. The children carried home a plain basket, but their friendship stayed whole and became the brightest part of the day.",
        ))
    elif outcome == "safe":
        qa.append((
            f"How did they get the treasure safely?",
            f"{seeker.id} used {method.label} to reach from farther back instead of trusting bare feet on the worst rocks. The safer method let the friends keep their old sharing custom.",
        ))
        qa.append((
            "What proves the friendship changed for the better?",
            f"{seeker.id} did not hide the prize away as a private thing. Instead, {seeker.pronoun()} put it in the middle of the basket so both friends could share the joy.",
        ))
    else:
        qa.append((
            f"What happened when {seeker.id} ignored the warning?",
            f"{seeker.id} slipped on the rocks, hurt a knee, and lost the shining treasure to the sea. The bad ending came from choosing wanting over caution while the tide was rising.",
        ))
        qa.append((
            "Why is the ending sad?",
            f"The children went home early, hurt and silent, with almost nothing in their basket. The loss was not only the treasure, but also the happy feeling their friendship had at the start.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["spot_cfg"].tags) | set(f["method_cfg"].tags) | set(f["treasure_cfg"].tags)
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def tell(
    treasure: Treasure,
    spot: Spot,
    method: Method,
    seeker_name: str = "Missy",
    seeker_gender: str = "girl",
    friend_name: str = "Rowan",
    friend_gender: str = "boy",
    friend_trait: str = "watchful",
    relation: str = "friends",
    seeker_age: int = 6,
    friend_age: int = 7,
    helper_loyalty: int = 7,
    tide_delay: int = 1,
) -> World:
    world = World()
    seeker = world.add(Entity(
        id=seeker_name,
        kind="character",
        type=seeker_gender,
        role="seeker",
        age=seeker_age,
        attrs={"relation": relation},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        age=friend_age,
        attrs={"relation": relation, "trait": friend_trait},
    ))
    world.add(Entity(id="treasure", type="treasure", label=treasure.label, portable=True))
    world.add(Entity(id="shore", type="place", label="rocky shore"))

    seeker.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0
    friend.memes["acuity"] = wise_acuity(friend_trait)
    world.facts["tide_delay"] = tide_delay
    world.facts["helper_loyalty"] = helper_loyalty

    shore_opening(world, seeker, friend, treasure)
    glimpse_treasure(world, seeker, friend, treasure, spot)

    world.para()
    desire_own(world, seeker, treasure, spot)
    acuity_warning(world, friend, seeker, spot, method)

    if would_turn_back(relation, seeker_age, friend_age, friend_trait):
        world.para()
        turn_back(world, seeker, friend, treasure)
        outcome = "averted"
    else:
        world.para()
        choose_method(world, seeker, friend, method)
        if safe_attempt(method, spot, tide_delay, helper_loyalty):
            succeed(world, seeker, friend, treasure, spot, method)
            outcome = "safe"
        else:
            fail_slip(world, seeker, friend, treasure, spot, method)
            world.para()
            bad_ending(world, seeker, friend)
            outcome = "bad"

    world.facts.update(
        seeker=seeker,
        friend=friend,
        treasure_cfg=treasure,
        spot_cfg=spot,
        method_cfg=method,
        outcome=outcome,
        relation=relation,
        hurt=seeker.meters["hurt"] >= THRESHOLD,
        lost=world.get("treasure").meters["lost_to_sea"] >= THRESHOLD,
        shared=world.get("treasure").meters["taken"] >= THRESHOLD and outcome == "safe",
    )
    return world


def explain_combo(treasure: Treasure, spot: Spot, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return f"(No story: {method.label} is below the world's common-sense threshold.)"
    if not can_reach(method, spot):
        return (
            f"(No story: {method.label} cannot honestly reach {spot.label}. "
            f"The world refuses a story where the chosen method cannot touch the treasure.)"
        )
    return "(No story: this combination is not plausible here.)"


def outcome_of(params: StoryParams) -> str:
    if would_turn_back(params.relation, params.seeker_age, params.friend_age, params.friend_trait):
        return "averted"
    if safe_attempt(METHODS[params.method], SPOTS[params.spot], params.tide_delay, params.helper_loyalty):
        return "safe"
    return "bad"


ASP_RULES = r"""
valid(T,S,M) :- treasure(T), spot(S), method(M), reach(M,R), distance(S,D), R >= D, sense(M,Se), sense_min(Min), Se >= Min.

older_friend :- relation(friends), seeker_age(SA), friend_age(FA), FA > SA.
wise_trait(T) :- trait(T), careful_trait(T).
acuity(7) :- wise_trait(_).
acuity(5) :- trait(T), not careful_trait(T).
averted :- older_friend, acuity(A), A > 6.

danger(V) :- chosen_spot(S), slick(S,Sk), wave(S,W), tide_delay(D), V = Sk + W + D.
help_bonus(1) :- helper_loyalty(L), L >= 6, chosen_method(M), M != hand.
help_bonus(0) :- not help_bonus(1).
safe_attempt :- chosen_method(M), safety(M,Sf), danger(Dg), help_bonus(B), Sf + B >= Dg.

outcome(averted) :- averted.
outcome(safe) :- not averted, safe_attempt.
outcome(bad) :- not averted, not safe_attempt.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        lines.append(asp.fact("distance", sid, spot.distance))
        lines.append(asp.fact("slick", sid, spot.slick))
        lines.append(asp.fact("wave", sid, spot.wave))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("reach", mid, method.reach))
        lines.append(asp.fact("safety", mid, method.safety))
        lines.append(asp.fact("sense", mid, method.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for tr in sorted(WISE_TRAITS):
        lines.append(asp.fact("careful_trait", tr))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_spot", params.spot),
        asp.fact("chosen_method", params.method),
        asp.fact("relation", params.relation),
        asp.fact("seeker_age", params.seeker_age),
        asp.fact("friend_age", params.friend_age),
        asp.fact("trait", params.friend_trait),
        asp.fact("helper_loyalty", params.helper_loyalty),
        asp.fact("tide_delay", params.tide_delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


CURATED = [
    StoryParams(
        treasure="moon_shell",
        spot="near_pool",
        method="hand",
        seeker="Missy",
        seeker_gender="girl",
        friend="Rowan",
        friend_gender="boy",
        friend_trait="steady",
        relation="friends",
        seeker_age=5,
        friend_age=7,
        helper_loyalty=8,
        tide_delay=0,
    ),
    StoryParams(
        treasure="blue_glass",
        spot="outer_rock",
        method="drift_hook",
        seeker="Missy",
        seeker_gender="girl",
        friend="Jory",
        friend_gender="boy",
        friend_trait="watchful",
        relation="friends",
        seeker_age=7,
        friend_age=7,
        helper_loyalty=7,
        tide_delay=1,
    ),
    StoryParams(
        treasure="sun_stone",
        spot="far_ledge",
        method="rope_loop",
        seeker="Missy",
        seeker_gender="girl",
        friend="Finn",
        friend_gender="boy",
        friend_trait="careful",
        relation="friends",
        seeker_age=7,
        friend_age=6,
        helper_loyalty=8,
        tide_delay=1,
    ),
    StoryParams(
        treasure="moon_shell",
        spot="outer_rock",
        method="drift_hook",
        seeker="Lina",
        seeker_gender="girl",
        friend="Missy",
        friend_gender="girl",
        friend_trait="patient",
        relation="friends",
        seeker_age=7,
        friend_age=8,
        helper_loyalty=7,
        tide_delay=1,
    ),
    StoryParams(
        treasure="blue_glass",
        spot="outer_rock",
        method="hand",
        seeker="Missy",
        seeker_gender="girl",
        friend="Corin",
        friend_gender="boy",
        friend_trait="watchful",
        relation="friends",
        seeker_age=7,
        friend_age=6,
        helper_loyalty=4,
        tide_delay=2,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a rocky-shore folktale about friendship, repetition, and a bright thing wanted for one's own."
    )
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--seeker")
    ap.add_argument("--friend")
    ap.add_argument("--seeker-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--tide-delay", type=int, choices=[0, 1, 2], help="how much extra time the tide has had to rise")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spot and args.method:
        spot = SPOTS[args.spot]
        method = METHODS[args.method]
        if not can_reach(method, spot) or method.sense < SENSE_MIN:
            treasure = TREASURES[args.treasure] if args.treasure else next(iter(TREASURES.values()))
            raise StoryError(explain_combo(treasure, spot, method))

    combos = [
        c for c in valid_combos()
        if (args.treasure is None or c[0] == args.treasure)
        and (args.spot is None or c[1] == args.spot)
        and (args.method is None or c[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    treasure, spot, method = rng.choice(sorted(combos))
    seeker_gender = args.seeker_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    seeker = args.seeker or _pick_name(rng, seeker_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=seeker)
    friend_trait = args.trait or rng.choice(TRAITS)
    tide_delay = args.tide_delay if args.tide_delay is not None else rng.randint(0, 2)
    seeker_age, friend_age = rng.sample([5, 6, 7, 8], 2)
    helper_loyalty = rng.randint(4, 9)

    return StoryParams(
        treasure=treasure,
        spot=spot,
        method=method,
        seeker=seeker,
        seeker_gender=seeker_gender,
        friend=friend,
        friend_gender=friend_gender,
        friend_trait=friend_trait,
        relation="friends",
        seeker_age=seeker_age,
        friend_age=friend_age,
        helper_loyalty=helper_loyalty,
        tide_delay=tide_delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.method not in METHODS or params.spot not in SPOTS:
        raise StoryError("(Invalid parameters.)")
    if not any(c == (params.treasure, params.spot, params.method) for c in valid_combos()):
        raise StoryError(explain_combo(TREASURES[params.treasure], SPOTS[params.spot], METHODS[params.method]))

    world = tell(
        treasure=TREASURES[params.treasure],
        spot=SPOTS[params.spot],
        method=METHODS[params.method],
        seeker_name=params.seeker,
        seeker_gender=params.seeker_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        friend_trait=params.friend_trait,
        relation=params.relation,
        seeker_age=params.seeker_age,
        friend_age=params.friend_age,
        helper_loyalty=params.helper_loyalty,
        tide_delay=params.tide_delay,
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
    parser = build_parser()
    for s in range(40):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {s}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (treasure, spot, method) combos:\n")
        for treasure, spot, method in combos:
            print(f"  {treasure:10} {spot:10} {method}")
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
            header = f"### {p.seeker} and {p.friend}: {p.treasure} at {p.spot} by {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
