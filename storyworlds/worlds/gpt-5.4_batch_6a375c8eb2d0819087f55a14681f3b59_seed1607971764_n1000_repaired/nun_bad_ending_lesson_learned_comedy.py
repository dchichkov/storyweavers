#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/nun_bad_ending_lesson_learned_comedy.py
==================================================================

A standalone story world about a child in a funny hurry, a kind nun, and a
surprise that goes gloriously wrong. Every generated story is a small comedy
with a bad ending that stays safe: the treat is ruined, everyone is sticky or
crumbly, and the lesson is to slow down and ask for help.

Domain summary
--------------
At a little school, a child wants to carry a surprise treat to a nun. Another
child warns that the chosen carrier over the chosen path is too wobbly. The
child dashes anyway. The world model pushes the treat from eager motion to
wobble to spill, and the ending image proves what changed: the surprise is
squashed, but the children learned to carry kindness carefully.

Run it
------
    python storyworlds/worlds/gpt-5.4/nun_bad_ending_lesson_learned_comedy.py
    python storyworlds/worlds/gpt-5.4/nun_bad_ending_lesson_learned_comedy.py --surprise jelly_tower
    python storyworlds/worlds/gpt-5.4/nun_bad_ending_lesson_learned_comedy.py --carrier basket
    python storyworlds/worlds/gpt-5.4/nun_bad_ending_lesson_learned_comedy.py --all
    python storyworlds/worlds/gpt-5.4/nun_bad_ending_lesson_learned_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/nun_bad_ending_lesson_learned_comedy.py --trace
    python storyworlds/worlds/gpt-5.4/nun_bad_ending_lesson_learned_comedy.py --asp
    python storyworlds/worlds/gpt-5.4/nun_bad_ending_lesson_learned_comedy.py --verify
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
RISK_MIN = 2


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
        female = {"girl", "woman", "nun", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    fragility: int
    motion: str
    spill_text: str
    remains_text: str
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
class Carrier:
    id: str
    label: str
    phrase: str
    stability: int
    style: str
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
class Path:
    id: str
    label: str
    phrase: str
    bump: int
    detail: str
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


def risk_score(surprise: Surprise, carrier: Carrier, path: Path) -> int:
    return surprise.fragility + path.bump - carrier.stability


def hazard(surprise: Surprise, carrier: Carrier, path: Path) -> bool:
    return risk_score(surprise, carrier, path) >= RISK_MIN


def outcome_kind(surprise: Surprise, carrier: Carrier, path: Path) -> str:
    score = risk_score(surprise, carrier, path)
    return "splat" if score >= 4 else "plop"


def _r_wobble(world: World) -> list[str]:
    treat = world.get("treat")
    if treat.meters["moving"] < THRESHOLD:
        return []
    if world.facts["risk_score"] < RISK_MIN:
        return []
    sig = ("wobble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    treat.meters["wobble"] += 1
    world.get("hero").memes["alarm"] += 1
    world.get("friend").memes["alarm"] += 1
    return ["__wobble__"]


def _r_spill(world: World) -> list[str]:
    treat = world.get("treat")
    if treat.meters["wobble"] < THRESHOLD:
        return []
    sig = ("spill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    treat.meters["spilled"] += 1
    treat.meters["whole"] = 0.0
    world.get("floor").meters["mess"] += 1
    world.get("hero").memes["embarrassment"] += 1
    world.get("friend").memes["embarrassment"] += 1
    world.get("nun").memes["surprise"] += 1
    return ["__spill__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="spill", tag="physical", apply=_r_spill),
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


def predict_spill(world: World) -> dict:
    sim = world.copy()
    sim.get("treat").meters["moving"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("treat").meters["wobble"] >= THRESHOLD,
        "spilled": sim.get("treat").meters["spilled"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, friend: Entity, nun: Entity) -> None:
    world.say(
        f"At Saint Brigid's School, {hero.id} and {friend.id} had a plan that felt "
        f"very grand and a little too secret. They wanted to carry a thank-you surprise "
        f"to {nun.id}, the kind nun who kept peppermint drops in one pocket and chalk dust in the other."
    )


def make_surprise(world: World, hero: Entity, surprise: Surprise) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"That morning they had made {surprise.phrase}. It looked wonderful, but it also "
        f"{surprise.motion}, as if it had its own silly opinions."
    )


def choose_route(world: World, carrier: Carrier, path: Path) -> None:
    world.say(
        f"To deliver it, {world.get('hero').id} set it on {carrier.phrase} and pointed toward "
        f"{path.phrase}. {path.detail}"
    )


def warn(world: World, friend: Entity, hero: Entity, nun: Entity,
         surprise: Surprise, carrier: Carrier, path: Path) -> None:
    pred = predict_spill(world)
    world.facts["predicted_spill"] = pred["spilled"]
    friend.memes["caution"] += 1
    extra = " It is going to wiggle right off." if pred["wobble"] else ""
    world.say(
        f'{friend.id} squinted at the load. "{hero.id}, if you rush {surprise.label} on '
        f'{carrier.label} over {path.label}, we will not arrive with a surprise. '
        f'We will arrive with a story for {nun.id}.{extra}"'
    )


def defy(world: World, hero: Entity, carrier: Carrier) -> None:
    hero.memes["impatience"] += 1
    world.say(
        f'{hero.id} grinned anyway. "I will be quick," {hero.pronoun()} said, which is what people say '
        f'just before they are not quick in the useful way. Then {hero.pronoun()} grabbed {carrier.label} and hurried off.'
    )


def move_surprise(world: World, hero: Entity, surprise: Surprise, carrier: Carrier, path: Path) -> None:
    treat = world.get("treat")
    treat.meters["moving"] += 1
    propagate(world, narrate=False)
    if treat.meters["wobble"] >= THRESHOLD:
        world.say(
            f"Across {path.label}, the {surprise.label} began to wobble. It leaned left, then right, "
            f"then performed the sort of little dance that never ends well on {carrier.label}."
        )
    if treat.meters["spilled"] >= THRESHOLD:
        if world.facts["outcome"] == "splat":
            world.say(
                f"Then came the great schoolyard disaster: {surprise.spill_text}. "
                f"It was not graceful. It was magnificent."
            )
        else:
            world.say(
                f"Then came a smaller but still dreadful sound -- plop! {surprise.spill_text}"
            )


def nun_arrives(world: World, nun: Entity, hero: Entity, friend: Entity) -> None:
    nun.memes["kindness"] += 1
    world.say(
        f"{nun.id} heard the commotion and came around the corner. For one tiny second, "
        f"{hero.id} froze. {friend.id} froze. Even the pigeons looked interested."
    )
    world.say(
        f"Then the nun pressed one hand to her cheek and let out a surprised laugh so warm "
        f"that nobody needed to hide behind a bush."
    )


def lesson(world: World, nun: Entity, hero: Entity, friend: Entity,
           surprise: Surprise, carrier: Carrier, path: Path) -> None:
    hero.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    hero.memes["shame"] += 1
    world.say(
        f'"Well," said {nun.id}, "the floor has certainly received {surprise.label} with great enthusiasm." '
        f'She handed them a cloth and added, "Kindness still counts when the surprise fails. '
        f'But next time, slow feet and extra hands beat hurry."'
    )
    world.say(
        f'{hero.id} looked at the mess and nodded. "{friend.id} was right," {hero.pronoun()} admitted. '
        f'"A wobbly thing on {carrier.label} over {path.label} is not a brave idea. It is just a fast one."'
    )


def ending(world: World, nun: Entity, hero: Entity, friend: Entity, surprise: Surprise) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"They cleaned up together while {nun.id} told them that even a ruined surprise can turn into a funny memory. "
        f"In the end, there was no grand treat left to present -- only {surprise.remains_text} and three people trying not to laugh too hard."
    )
    world.say(
        f"By lunchtime, {hero.id} had learned the lesson perfectly: if you want to carry kindness to a nun, "
        f"carry it slowly."
    )


def tell(surprise: Surprise, carrier: Carrier, path: Path,
         hero_name: str = "Milo", hero_gender: str = "boy",
         friend_name: str = "Tess", friend_gender: str = "girl",
         nun_name: str = "Sister Agnes") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    nun = world.add(Entity(id=nun_name, kind="character", type="nun", role="nun", label="the nun"))
    treat = world.add(Entity(id="treat", type="treat", label=surprise.label))
    floor = world.add(Entity(id="floor", type="floor", label="the floor"))

    treat.meters["whole"] = 1.0
    treat.meters["moving"] = 0.0
    treat.meters["wobble"] = 0.0
    treat.meters["spilled"] = 0.0
    floor.meters["mess"] = 0.0
    hero.memes["impatience"] = 0.0
    friend.memes["caution"] = 0.0
    world.facts["risk_score"] = risk_score(surprise, carrier, path)
    world.facts["outcome"] = outcome_kind(surprise, carrier, path)
    world.facts["surprise_cfg"] = surprise
    world.facts["carrier_cfg"] = carrier
    world.facts["path_cfg"] = path

    introduce(world, hero, friend, nun)
    make_surprise(world, hero, surprise)
    choose_route(world, carrier, path)

    world.para()
    warn(world, friend, hero, nun, surprise, carrier, path)
    defy(world, hero, carrier)

    world.para()
    move_surprise(world, hero, surprise, carrier, path)
    nun_arrives(world, nun, hero, friend)

    world.para()
    lesson(world, nun, hero, friend, surprise, carrier, path)
    ending(world, nun, hero, friend, surprise)

    world.facts.update(
        hero=hero,
        friend=friend,
        nun=nun,
        treat=treat,
        floor=floor,
        spilled=treat.meters["spilled"] >= THRESHOLD,
        lesson_learned=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


SURPRISES = {
    "jelly_tower": Surprise(
        id="jelly_tower",
        label="jelly tower",
        phrase="a bright red jelly tower with whipped cream on top",
        fragility=3,
        motion="quivered like a tiny haunted castle",
        spill_text="The jelly tower slid sideways, saluted the air, and collapsed in one shining wobble across the stones",
        remains_text="a red wobble on the ground and one heroic blob of whipped cream on a shoe",
        tags={"jelly", "spill", "patience"},
    ),
    "cream_puffs": Surprise(
        id="cream_puffs",
        label="cream puff stack",
        phrase="a tower of cream puffs dusted with sugar",
        fragility=3,
        motion="shivered whenever anyone breathed too confidently near it",
        spill_text="The cream puffs rolled in every direction at once, as if they had decided recess had started early",
        remains_text="powdered sugar on sleeves and cream puffs peeking from under a bench",
        tags={"bakery", "spill", "patience"},
    ),
    "lemonade": Surprise(
        id="lemonade",
        label="pitcher of lemonade",
        phrase="a cold pitcher of lemonade with lemon slices bobbing on top",
        fragility=2,
        motion="sloshed with every hopeful little step",
        spill_text="The lemonade lurched, leapt the rim, and ran down in a sparkling yellow river",
        remains_text="sticky shoes, lemon slices on the path, and one brave paper napkin trying its best",
        tags={"lemonade", "spill", "patience"},
    ),
}

CARRIERS = {
    "roller_skates": Carrier(
        id="roller_skates",
        label="roller skates",
        phrase="a tray balanced above a pair of roller skates",
        stability=0,
        style="wild",
        tags={"roller_skates", "balance"},
    ),
    "serving_tray": Carrier(
        id="serving_tray",
        label="a serving tray",
        phrase="a shiny serving tray held out at chest height",
        stability=1,
        style="wobbly",
        tags={"tray", "balance"},
    ),
    "wagon": Carrier(
        id="wagon",
        label="a little red wagon",
        phrase="a little red wagon with one squeaky wheel",
        stability=2,
        style="rattly",
        tags={"wagon", "balance"},
    ),
    "basket": Carrier(
        id="basket",
        label="a picnic basket",
        phrase="a picnic basket lined with a folded towel",
        stability=4,
        style="steady",
        tags={"basket", "careful"},
    ),
}

PATHS = {
    "cobblestones": Path(
        id="cobblestones",
        label="the cobblestones",
        phrase="the old cobblestones beside the chapel garden",
        bump=2,
        detail="Every stone stood up as if it wished to be noticed by wheels and feet.",
        tags={"cobblestones", "bumpy"},
    ),
    "steps": Path(
        id="steps",
        label="the chapel steps",
        phrase="the chapel steps",
        bump=2,
        detail="The steps were short, steep, and completely innocent-looking.",
        tags={"steps", "bumpy"},
    ),
    "hall": Path(
        id="hall",
        label="the polished hall",
        phrase="the polished hall outside the music room",
        bump=1,
        detail="The floor was smooth, but smooth floors can still be excellent places for foolish speed.",
        tags={"hall", "slippery"},
    ),
    "grass": Path(
        id="grass",
        label="the grass",
        phrase="the soft grass by the fig tree",
        bump=1,
        detail="The ground looked gentle, though gentle ground still likes to tilt a wagon wheel now and then.",
        tags={"grass", "outdoors"},
    ),
}

GIRL_NAMES = ["Tess", "Mina", "Ruby", "Ella", "Nora", "Pia", "Lila", "June"]
BOY_NAMES = ["Milo", "Ben", "Owen", "Theo", "Jack", "Finn", "Leo", "Eli"]
NUN_NAMES = ["Sister Agnes", "Sister Lucia", "Sister Bernadette", "Sister Clare"]


@dataclass
class StoryParams:
    surprise: str
    carrier: str
    path: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    nun: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, surprise in SURPRISES.items():
        for cid, carrier in CARRIERS.items():
            for pid, path in PATHS.items():
                if hazard(surprise, carrier, path):
                    combos.append((sid, cid, pid))
    return sorted(combos)


KNOWLEDGE = {
    "nun": [
        (
            "What is a nun?",
            "A nun is a woman in a religious community. In some schools or churches, a nun may teach, pray, and help take care of people.",
        )
    ],
    "jelly": [
        (
            "Why is jelly hard to carry?",
            "Jelly wiggles when it moves. If it wiggles too much, it can slide right off a plate or tray.",
        )
    ],
    "bakery": [
        (
            "Why do cream puffs fall apart easily?",
            "Cream puffs are light and puffy, and they can roll or squash quickly. A bumpy trip can turn a neat stack into a messy one.",
        )
    ],
    "lemonade": [
        (
            "Why does lemonade spill when you run?",
            "The drink keeps moving even after your hands move. When it sloshes against the sides, it can jump over the rim.",
        )
    ],
    "roller_skates": [
        (
            "Why are roller skates a silly way to carry food?",
            "Roller skates are made for gliding, not for balancing a treat. If the floor or ground bumps you, your hands can wobble too much.",
        )
    ],
    "tray": [
        (
            "What is a serving tray for?",
            "A serving tray helps carry plates or cups from one place to another. It works best when the person holding it walks slowly and keeps it level.",
        )
    ],
    "wagon": [
        (
            "Why can a wagon make a treat bump around?",
            "A wagon rolls over cracks, stones, and grass. Each little bump can shake whatever is inside.",
        )
    ],
    "basket": [
        (
            "Why is a basket steadier than a tray on skates?",
            "A basket holds things down inside its sides, and steady hands keep it from tipping. It is not magic, but it helps a lot.",
        )
    ],
    "cobblestones": [
        (
            "What are cobblestones?",
            "Cobblestones are rounded stones used to make a path. They look pretty, but they make a bumpy ride.",
        )
    ],
    "steps": [
        (
            "Why are steps tricky when you carry something wobbly?",
            "Each step changes your height and balance. A wobbly thing can tip when your body jerks up or down.",
        )
    ],
    "patience": [
        (
            "Why does moving slowly help with a fragile surprise?",
            "Slow steps give your hands time to stay steady. Patience can protect something delicate better than rushing can.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "nun",
    "jelly",
    "bakery",
    "lemonade",
    "roller_skates",
    "tray",
    "wagon",
    "basket",
    "cobblestones",
    "steps",
    "patience",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    nun = f["nun"]
    surprise = f["surprise_cfg"]
    carrier = f["carrier_cfg"]
    path = f["path_cfg"]
    return [
        f'Write a short comedy for a 3-to-5-year-old that includes the word "nun" and ends with a funny bad ending and a lesson learned.',
        f"Tell a gentle story where {hero.id} tries to bring {surprise.phrase} to {nun.id}, but rushing it on {carrier.label} over {path.label} turns the surprise into a mess.",
        f"Write a playful cautionary story about a child hurrying a wobbly treat to a nun and learning that careful help is better than fast pride.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    nun = f["nun"]
    surprise = f["surprise_cfg"]
    carrier = f["carrier_cfg"]
    path = f["path_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {friend.id}, and {nun.id}, a kind nun at school. {hero.id} wanted to bring her a surprise.",
        ),
        (
            "What surprise were they carrying for the nun?",
            f"They were carrying {surprise.phrase}. It looked lovely, but it was already the sort of treat that could wobble or spill if handled badly.",
        ),
        (
            f"Why did {friend.id} warn {hero.id}?",
            f"{friend.id} could see that {surprise.label} on {carrier.label} over {path.label} was a bad mix. The danger came from the bumpy trip and the shaky way of carrying it.",
        ),
        (
            "What went wrong?",
            f"The treat wobbled and spilled before it reached the nun. The ending was funny, but it was still bad because the surprise was ruined.",
        ),
        (
            f"How did {nun.id} react?",
            f"{nun.id} did not shout. She laughed kindly, helped them clean up, and turned the embarrassment into a lesson.",
        ),
    ]
    if outcome == "splat":
        qa.append(
            (
                "Was the mess small or big?",
                f"It was a big mess. The risk was high enough that the treat did not just tip a little -- it collapsed or poured out completely.",
            )
        )
    else:
        qa.append(
            (
                "Was the bad ending still serious even though it was funny?",
                f"Yes, because the surprise was still spoiled. Even a smaller plop meant they could not present the treat the way they planned.",
            )
        )
    qa.append(
        (
            f"What lesson did {hero.id} learn?",
            f"{hero.id} learned to slow down with fragile things and ask for extra hands. The story shows that being in a hurry can spoil a kind plan.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"nun"}
    tags |= set(f["surprise_cfg"].tags)
    tags |= set(f["carrier_cfg"].tags)
    tags |= set(f["path_cfg"].tags)
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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: risk_score={world.facts.get('risk_score')} outcome={world.facts.get('outcome')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(surprise: Surprise, carrier: Carrier, path: Path) -> str:
    score = risk_score(surprise, carrier, path)
    return (
        f"(No story: {surprise.label} on {carrier.label} over {path.label} is too stable here "
        f"(risk={score} < {RISK_MIN}). This world only tells comic bad-ending stories where the "
        f"surprise really does wobble and spill.)"
    )


CURATED = [
    StoryParams(
        surprise="jelly_tower",
        carrier="roller_skates",
        path="cobblestones",
        hero="Milo",
        hero_gender="boy",
        friend="Tess",
        friend_gender="girl",
        nun="Sister Agnes",
    ),
    StoryParams(
        surprise="cream_puffs",
        carrier="serving_tray",
        path="steps",
        hero="Ruby",
        hero_gender="girl",
        friend="Ben",
        friend_gender="boy",
        nun="Sister Lucia",
    ),
    StoryParams(
        surprise="lemonade",
        carrier="wagon",
        path="cobblestones",
        hero="Theo",
        hero_gender="boy",
        friend="Mina",
        friend_gender="girl",
        nun="Sister Clare",
    ),
    StoryParams(
        surprise="jelly_tower",
        carrier="serving_tray",
        path="hall",
        hero="Ella",
        hero_gender="girl",
        friend="Jack",
        friend_gender="boy",
        nun="Sister Bernadette",
    ),
    StoryParams(
        surprise="cream_puffs",
        carrier="wagon",
        path="steps",
        hero="Nora",
        hero_gender="girl",
        friend="Leo",
        friend_gender="boy",
        nun="Sister Agnes",
    ),
]


ASP_RULES = r"""
risk(S,C,P,R) :- surprise(S), carrier(C), path(P),
                 fragility(S,F), stability(C,St), bump(P,B), R = F + B - St.
hazard(S,C,P) :- risk(S,C,P,R), risk_min(M), R >= M.

outcome(S,C,P,splat) :- risk(S,C,P,R), R >= 4.
outcome(S,C,P,plop)  :- hazard(S,C,P), not outcome(S,C,P,splat).

valid(S,C,P) :- surprise(S), carrier(C), path(P), hazard(S,C,P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = [asp.fact("risk_min", RISK_MIN)]
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("fragility", sid, s.fragility))
    for cid, c in CARRIERS.items():
        lines.append(asp.fact("carrier", cid))
        lines.append(asp.fact("stability", cid, c.stability))
    for pid, p in PATHS.items():
        lines.append(asp.fact("path", pid))
        lines.append(asp.fact("bump", pid, p.bump))
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
            asp.fact("chosen_surprise", params.surprise),
            asp.fact("chosen_carrier", params.carrier),
            asp.fact("chosen_path", params.path),
            "picked(O) :- chosen_surprise(S), chosen_carrier(C), chosen_path(P), outcome(S,C,P,O).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show picked/1."))
    atoms = asp.atoms(model, "picked")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a comic bad-ending surprise for a nun. "
        "Unspecified choices are picked at random from valid spill-prone combos."
    )
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--nun", choices=NUN_NAMES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid spill-prone combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.surprise and args.carrier and args.path:
        s = SURPRISES[args.surprise]
        c = CARRIERS[args.carrier]
        p = PATHS[args.path]
        if not hazard(s, c, p):
            raise StoryError(explain_rejection(s, c, p))

    combos = [
        combo for combo in valid_combos()
        if (args.surprise is None or combo[0] == args.surprise)
        and (args.carrier is None or combo[1] == args.carrier)
        and (args.path is None or combo[2] == args.path)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    surprise_id, carrier_id, path_id = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    nun = args.nun or rng.choice(NUN_NAMES)
    return StoryParams(
        surprise=surprise_id,
        carrier=carrier_id,
        path=path_id,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        nun=nun,
    )


def generate(params: StoryParams) -> StorySample:
    if params.surprise not in SURPRISES:
        raise StoryError(f"(Unknown surprise: {params.surprise})")
    if params.carrier not in CARRIERS:
        raise StoryError(f"(Unknown carrier: {params.carrier})")
    if params.path not in PATHS:
        raise StoryError(f"(Unknown path: {params.path})")

    surprise = SURPRISES[params.surprise]
    carrier = CARRIERS[params.carrier]
    path = PATHS[params.path]
    if not hazard(surprise, carrier, path):
        raise StoryError(explain_rejection(surprise, carrier, path))

    world = tell(
        surprise=surprise,
        carrier=carrier,
        path=path,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        nun_name=params.nun,
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


def outcome_of(params: StoryParams) -> str:
    return outcome_kind(SURPRISES[params.surprise], CARRIERS[params.carrier], PATHS[params.path])


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = []
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad.append((p, asp_outcome(p), outcome_of(p)))
    if not bad:
        print(f"OK: ASP outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcome differences.")
        for p, a, py in bad[:5]:
            print(f"  {p.surprise}/{p.carrier}/{p.path}: asp={a} python={py}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke-tested ordinary story generation.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} spill-prone (surprise, carrier, path) combos:\n")
        for s, c, p in combos:
            print(f"  {s:12} {c:13} {p:12}  [{outcome_kind(SURPRISES[s], CARRIERS[c], PATHS[p])}]")
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
            header = f"### {p.hero} carries {p.surprise} on {p.carrier} over {p.path} [{outcome_of(p)}]"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
