#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/medal_digestion_conflict_surprise_rhyming_story.py
==============================================================================

A standalone storyworld for a tiny rhyming tale about a child, a hoped-for
medal, a tummy busy with digestion, a moment of conflict, and a surprising end.

Premise
-------
A child at a school field day wants to dash into a game and win a medal.
But the child has just eaten a snack. A friend or grown-up warns that
digestion takes time, and a conflict appears: rush now for the prize, or pause
and choose the wiser way?

This world models that tension with state, not templates alone:
- physical meters: full_tummy, digestion_ready, cramp, thirst, tired, medal
- emotional memes: hope, impatience, worry, relief, pride, gratitude

The ending is always complete and rhyming, with a surprise:
sometimes the child still reaches the game after waiting;
sometimes the child cannot race yet, but earns a kindness medal for helping.

Run it
------
    python storyworlds/worlds/gpt-5.4/medal_digestion_conflict_surprise_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/medal_digestion_conflict_surprise_rhyming_story.py --game race --snack cake --choice rush
    python storyworlds/worlds/gpt-5.4/medal_digestion_conflict_surprise_rhyming_story.py --snack stew --choice rush   # rejected
    python storyworlds/worlds/gpt-5.4/medal_digestion_conflict_surprise_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/medal_digestion_conflict_surprise_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/medal_digestion_conflict_surprise_rhyming_story.py --verify
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
        female = {"girl", "mother", "woman", "coach_woman"}
        male = {"boy", "father", "man", "coach_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "coach_woman": "coach",
            "coach_man": "coach",
        }
        return mapping.get(self.type, self.type)
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
class Game:
    id: str
    label: str
    action: str
    lane: str
    rhyme_goal: str
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
class Snack:
    id: str
    label: str
    phrase: str
    weight: int
    quick: bool
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
class Choice:
    id: str
    label: str
    wait_beats: int
    risk_drop: int
    text: str
    sense: int
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
class Surprise:
    id: str
    medal_kind: str
    line: str
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


def _r_heavy_rush_cramp(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["full_tummy"] < THRESHOLD:
        return []
    if hero.memes["rushing"] < THRESHOLD:
        return []
    sig = ("heavy_rush_cramp", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["cramp"] += 1
    hero.memes["worry"] += 1
    return ["__cramp__"]


def _r_wait_settles(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["waiting"] < THRESHOLD:
        return []
    sig = ("wait_settles", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    amount = hero.attrs.get("wait_beats", 0)
    if amount >= hero.attrs.get("needed_wait", 0):
        hero.meters["digestion_ready"] += 1
        hero.meters["full_tummy"] = 0.0
        hero.memes["relief"] += 1
        return ["__settled__"]
    hero.meters["full_tummy"] = max(0.0, hero.meters["full_tummy"] - 1)
    hero.memes["hope"] += 0.5
    return []


def _r_water_helps(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["water"] < THRESHOLD:
        return []
    sig = ("water_helps", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if hero.meters["cramp"] >= THRESHOLD:
        hero.meters["cramp"] = max(0.0, hero.meters["cramp"] - 1)
    hero.memes["relief"] += 1
    return []


def _r_ready_run(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["digestion_ready"] < THRESHOLD:
        return []
    if hero.meters["cramp"] >= THRESHOLD:
        return []
    if hero.memes["tries_game"] < THRESHOLD:
        return []
    sig = ("ready_run", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["finished"] += 1
    hero.memes["pride"] += 1
    return ["__finish__"]


CAUSAL_RULES = [
    Rule(name="heavy_rush_cramp", tag="physical", apply=_r_heavy_rush_cramp),
    Rule(name="wait_settles", tag="physical", apply=_r_wait_settles),
    Rule(name="water_helps", tag="physical", apply=_r_water_helps),
    Rule(name="ready_run", tag="physical", apply=_r_ready_run),
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


def needed_wait(snack: Snack) -> int:
    return 1 if snack.quick else 2


def risky_combo(snack: Snack, choice: Choice) -> bool:
    return snack.weight >= 2 and choice.id == "rush"


def sensible_choices() -> list[Choice]:
    return [c for c in CHOICES.values() if c.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for game_id in GAMES:
        for snack_id, snack in SNACKS.items():
            for choice_id, choice in CHOICES.items():
                if choice.sense < SENSE_MIN:
                    continue
                if snack.weight == 3 and choice.id == "rush":
                    continue
                combos.append((game_id, snack_id, choice_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    snack = SNACKS[params.snack]
    choice = CHOICES[params.choice]
    if choice.id == "rush" and snack.weight >= 2:
        return "kindness_medal"
    if choice.wait_beats >= needed_wait(snack):
        return "earned_medal"
    return "kindness_medal"


def predict_outcome(world: World, snack: Snack, choice: Choice) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.attrs["wait_beats"] = choice.wait_beats
    if choice.id == "rush":
        hero.memes["rushing"] += 1
    else:
        hero.memes["waiting"] += 1
        if choice.id == "sip_stretch":
            hero.meters["water"] += 1
    propagate(sim, narrate=False)
    return {
        "cramp": hero.meters["cramp"] >= THRESHOLD,
        "ready": hero.meters["digestion_ready"] >= THRESHOLD,
        "needed_wait": hero.attrs["needed_wait"],
        "wait_beats": choice.wait_beats,
    }


def opening(world: World, hero: Entity, friend: Entity, game: Game) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"On the school field, under a bright blue petal, "
        f"{hero.id} saw a table with a shining medal."
    )
    world.say(
        f'"If I {game.action} well, I may hear cheers swell," '
        f"said {hero.id}, while {friend.id} grinned as well."
    )


def snack_time(world: World, hero: Entity, snack: Snack) -> None:
    hero.meters["full_tummy"] = float(snack.weight)
    world.say(
        f"But first came a snack: {snack.phrase} for the way, "
        f"and {hero.id} ate it up before the big play."
    )
    world.say(
        f"Soon {hero.pronoun('possessive')} tummy felt busy in a soft little way, "
        f"for digestion needs moments and cannot just obey."
    )


def warning(world: World, hero: Entity, friend: Entity, coach: Entity,
            snack: Snack, choice: Choice) -> None:
    pred = predict_outcome(world, snack, choice)
    world.facts["predicted_cramp"] = pred["cramp"]
    world.facts["predicted_ready"] = pred["ready"]
    world.facts["predicted_wait"] = pred["needed_wait"]
    friend.memes["care"] += 1
    coach.memes["care"] += 1
    world.say(
        f'"Wait just a bit," said {friend.id}. "Do not tumble or sway. '
        f'Your digestion is working; let it finish its way."'
    )
    if pred["cramp"]:
        world.say(
            f'"If you rush with that tummy, a cramp may arrive," '
            f"said {coach.label_word}, 'and slow down your stride.'"
        )
    else:
        world.say(
            f'"Choose your pace with some care, and your feet may still fly," '
            f"said {coach.label_word}, with a warm, steady eye."
        )


def conflict(world: World, hero: Entity, game: Game) -> None:
    hero.memes["impatience"] += 1
    world.say(
        f"But {hero.id} wanted the medal, the clap, and the call; "
        f"{hero.pronoun().capitalize()} wriggled with hurry and wanted it all."
    )
    world.say(
        f'"The {game.label} starts now! If I wait, I may fall '
        f'behind all the others and miss it all!"'
    )


def choose_path(world: World, hero: Entity, choice: Choice) -> None:
    if choice.id == "rush":
        hero.memes["rushing"] += 1
    else:
        hero.memes["waiting"] += 1
        hero.attrs["wait_beats"] = choice.wait_beats
    world.say(choice.text)


def do_pause_support(world: World, hero: Entity, friend: Entity, choice: Choice) -> None:
    if choice.id == "sit_breath":
        world.say(
            f"So {hero.id} sat on the bench in the sun for a spell, "
            f"and breathed slow with {friend.id} till {hero.pronoun('possessive')} heartbeat felt well."
        )
    elif choice.id == "sip_stretch":
        hero.meters["water"] += 1
        world.say(
            f"So {hero.id} took little sips and stretched tall like a tree, "
            f"while {friend.id} counted softly, 'One, two, and three.'"
        )
    propagate(world, narrate=False)
    if hero.meters["digestion_ready"] >= THRESHOLD:
        world.say(
            f"The tight little flutter grew quiet and small; "
            f"digestion was done, and {hero.id} stood tall."
        )


def rush_result(world: World, hero: Entity, game: Game) -> None:
    propagate(world, narrate=False)
    if hero.meters["cramp"] >= THRESHOLD:
        world.say(
            f"But halfway to {game.lane}, {hero.pronoun('possessive')} middle said, 'No!' "
            f"A cramp made {hero.pronoun('object')} slow down and bend low."
        )
        world.say(
            f"The medal seemed farther than moments before, "
            f"and tears made two tiny dark dots on the floor."
        )
    else:
        world.say(
            f"{hero.id} hurried ahead with a bright eager grin, "
            f"and still found enough comfort to join in and begin."
        )


def attempt_game(world: World, hero: Entity, game: Game) -> None:
    hero.memes["tries_game"] += 1
    propagate(world, narrate=False)
    if hero.meters["finished"] >= THRESHOLD:
        world.say(
            f"Then {hero.id} {game.action} with quick, careful tread, "
            f"and laughter like ribbons streamed out overhead."
        )
        world.say(
            f"{hero.pronoun().capitalize()} did not come first by a mile or a dash, "
            f"but {hero.pronoun().capitalize()} finished with joy and a bright, happy flash."
        )


def surprise_kindness(world: World, hero: Entity, friend: Entity, coach: Entity,
                      surprise: Surprise) -> None:
    hero.memes["gratitude"] += 1
    hero.memes["pride"] += 1
    hero.meters["medal"] += 1
    world.say(
        f"Then came the surprise, gentle, sudden, and sweet: "
        f"{coach.label_word.capitalize()} held up a medal and stepped to {hero.pronoun('possessive')} feet."
    )
    world.say(
        f'{surprise.line} "{hero.id}," {coach.pronoun()} said, '
        f'"you listened at last, and you helped with good heart instead."'
    )
    world.say(
        f"{friend.id} clapped first, and the whole field joined in the cheer; "
        f"the medal felt warm because kindness lived near."
    )


def surprise_finish_medal(world: World, hero: Entity, friend: Entity, coach: Entity,
                          surprise: Surprise) -> None:
    hero.memes["gratitude"] += 1
    hero.meters["medal"] += 1
    world.say(
        f"Then came the surprise with a glittering gleam: "
        f"{coach.label_word.capitalize()} called {hero.id} from the edge of the team."
    )
    world.say(
        f'{surprise.line} "{hero.id}," {coach.pronoun()} said, '
        f'"you chose a wise pace, and that shone more than speed."'
    )
    world.say(
        f"{friend.id} laughed, and the medal bounced bright on {hero.pronoun('possessive')} chest; "
        f"the field felt more golden because patience was best."
    )


def tell(game: Game, snack: Snack, choice: Choice, surprise: Surprise,
         hero_name: str = "Mina", hero_gender: str = "girl",
         friend_name: str = "Toby", friend_gender: str = "boy",
         coach_type: str = "coach_woman") -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        attrs={},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        attrs={},
    ))
    coach = world.add(Entity(
        id="Coach",
        kind="character",
        type=coach_type,
        role="coach",
        label="the coach",
        attrs={},
    ))
    world.facts["helper_task"] = "stacked the beanbags and straightened the cones"
    hero.attrs["needed_wait"] = needed_wait(snack)
    hero.attrs["wait_beats"] = 0
    hero.meters["full_tummy"] = 0.0
    hero.meters["digestion_ready"] = 0.0
    hero.meters["cramp"] = 0.0
    hero.meters["water"] = 0.0
    hero.meters["finished"] = 0.0
    hero.meters["medal"] = 0.0
    hero.memes["hope"] = 0.0
    hero.memes["impatience"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["pride"] = 0.0
    hero.memes["gratitude"] = 0.0
    hero.memes["tries_game"] = 0.0
    hero.memes["rushing"] = 0.0
    hero.memes["waiting"] = 0.0

    opening(world, hero, friend, game)
    snack_time(world, hero, snack)

    world.para()
    warning(world, hero, friend, coach, snack, choice)
    conflict(world, hero, game)
    choose_path(world, hero, choice)

    world.para()
    if choice.id == "rush":
        rush_result(world, hero, game)
        world.say(
            f"Seeing {hero.pronoun('object')} pause, {friend.id} stayed near, not far; "
            f"together they {world.facts['helper_task']}."
        )
        world.facts["helper_used"] = True
        world.facts["outcome"] = "kindness_medal"
        surprise_kindness(world, hero, friend, coach, surprise)
    else:
        do_pause_support(world, hero, friend, choice)
        attempt_game(world, hero, game)
        if hero.meters["finished"] >= THRESHOLD:
            world.facts["helper_used"] = False
            world.facts["outcome"] = "earned_medal"
            surprise_finish_medal(world, hero, friend, coach, surprise)
        else:
            world.facts["helper_used"] = True
            world.say(
                f"The game had begun, yet {hero.id} did not pout or meddle; "
                f"{hero.pronoun().capitalize()} helped the smaller children one by one settle."
            )
            world.facts["outcome"] = "kindness_medal"
            surprise_kindness(world, hero, friend, coach, surprise)

    world.facts.update(
        hero=hero,
        friend=friend,
        coach=coach,
        game=game,
        snack=snack,
        choice=choice,
        surprise=surprise,
        cramp=hero.meters["cramp"] >= THRESHOLD,
        digestion_ready=hero.meters["digestion_ready"] >= THRESHOLD,
        medal=hero.meters["medal"] >= THRESHOLD,
    )
    return world


GAMES = {
    "race": Game(
        id="race",
        label="sack race",
        action="hopped through the sack race",
        lane="the starting line",
        rhyme_goal="race",
        tags={"race", "medal"},
    ),
    "relay": Game(
        id="relay",
        label="beanbag relay",
        action="ran the beanbag relay",
        lane="the chalk lane",
        rhyme_goal="relay",
        tags={"relay", "medal"},
    ),
    "hop": Game(
        id="hop",
        label="hoop hop",
        action="hopped through the hoop hop",
        lane="the hoop row",
        rhyme_goal="hop",
        tags={"hop", "medal"},
    ),
}

SNACKS = {
    "apple": Snack(
        id="apple",
        label="apple slices",
        phrase="cool apple slices",
        weight=1,
        quick=True,
        tags={"apple", "digestion", "food"},
    ),
    "yogurt": Snack(
        id="yogurt",
        label="yogurt cup",
        phrase="a creamy yogurt cup",
        weight=1,
        quick=True,
        tags={"yogurt", "digestion", "food"},
    ),
    "sandwich": Snack(
        id="sandwich",
        label="sandwich",
        phrase="a round little sandwich",
        weight=2,
        quick=False,
        tags={"sandwich", "digestion", "food"},
    ),
    "cake": Snack(
        id="cake",
        label="cake",
        phrase="a thick slice of cake",
        weight=2,
        quick=False,
        tags={"cake", "digestion", "food"},
    ),
    "stew": Snack(
        id="stew",
        label="stew bowl",
        phrase="a warm bowl of stew",
        weight=3,
        quick=False,
        tags={"stew", "digestion", "food"},
    ),
}

CHOICES = {
    "rush": Choice(
        id="rush",
        label="rush straight in",
        wait_beats=0,
        risk_drop=0,
        text="So off dashed the wish in a jingly rush, with quick little feet and a hot little hush.",
        sense=1,
        tags={"rush", "conflict"},
    ),
    "sit_breath": Choice(
        id="sit_breath",
        label="sit and breathe",
        wait_beats=2,
        risk_drop=2,
        text="So {name} chose a bench and a calmer small plan: wait, breathe, and begin when digestion began.",
        sense=3,
        tags={"wait", "breathing", "conflict"},
    ),
    "sip_stretch": Choice(
        id="sip_stretch",
        label="sip water and stretch",
        wait_beats=1,
        risk_drop=1,
        text="So {name} chose small sips and a long easy stretch, giving tummy and heartbeat a gentler new sketch.",
        sense=3,
        tags={"wait", "water", "conflict"},
    ),
}

SURPRISES = {
    "kindness": Surprise(
        id="kindness",
        medal_kind="kindness medal",
        line="It was not the fastest-feet medal at all. It was the kindness medal, bright, round, and small.",
        qa_text="the coach gave a kindness medal for listening and helping",
        tags={"kindness_medal", "surprise", "medal"},
    ),
    "steady": Surprise(
        id="steady",
        medal_kind="steady choice medal",
        line="It was a steady-choice medal, a twinkling new sight, for waiting with wisdom and joining in right.",
        qa_text="the coach gave a steady-choice medal for waiting wisely",
        tags={"steady_medal", "surprise", "medal"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Ruby", "Tess", "Ivy", "Zoe"]
BOY_NAMES = ["Toby", "Eli", "Finn", "Leo", "Milo", "Ben", "Owen", "Sam"]


@dataclass
class StoryParams:
    game: str
    snack: str
    choice: str
    surprise: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    coach_type: str
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
    "digestion": [
        (
            "What is digestion?",
            "Digestion is what your body does with food after you eat it. Your stomach and the rest of your body slowly break the food down so it can help you grow and move.",
        )
    ],
    "cramp": [
        (
            "Why can running right after a big snack make your tummy hurt?",
            "A big snack can leave your stomach feeling full while your body is still working on digestion. If you start bouncing and running right away, your middle can feel tight or crampy.",
        )
    ],
    "water": [
        (
            "Why can a sip of water and a short rest help after eating?",
            "A small rest gives your body time to settle, and a sip of water can feel refreshing. It is not magic, but slowing down can help you notice when your body feels ready again.",
        )
    ],
    "medal": [
        (
            "What is a medal?",
            "A medal is a small prize, often made of metal, that people wear on a ribbon. It can be given for winning, trying hard, helping, or showing good choices.",
        )
    ],
    "kindness": [
        (
            "Can someone earn a prize for kindness instead of being fastest?",
            "Yes. Grown-ups sometimes give prizes for helpfulness, honesty, or care, because those things matter too.",
        )
    ],
    "race": [
        (
            "What is a relay or race game?",
            "It is a game where children move from one point to another, sometimes taking turns or carrying something. People try their best, but the game is also about teamwork and fun.",
        )
    ],
}

KNOWLEDGE_ORDER = ["digestion", "cramp", "water", "medal", "kindness", "race"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    game = world.facts["game"]
    snack = world.facts["snack"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that uses the words "medal" and "digestion".',
        f"Tell a rhyming field-day story where {hero.id} wants a medal in a {game.label} after eating {snack.label}, and a conflict appears about whether to rush or wait.",
        "Write a gentle rhyming story with conflict and a surprise ending where a child listens to their body and learns that prizes can mean more than speed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, coach = f["hero"], f["friend"], f["coach"]
    game, snack, choice = f["game"], f["snack"], f["choice"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who wanted a medal at the school field day, with {friend.id} and the coach nearby. They were all at the game area when the problem began.",
        ),
        (
            f"Why was there a conflict before the {game.label}?",
            f"There was a conflict because {hero.id} wanted to begin right away, but {hero.pronoun('possessive')} body was still busy with digestion after eating {snack.label}. The wish to win pulled one way, while the tummy warning pulled the other way.",
        ),
        (
            f"What warning did {friend.id} and the coach give?",
            f"They warned that digestion takes time and that rushing too soon could make {hero.pronoun('possessive')} tummy hurt. Their warning was about {hero.pronoun('possessive')} real body, not just about following rules.",
        ),
    ]
    if choice.id == "rush":
        qa.append(
            (
                f"What happened when {hero.id} rushed?",
                f"{hero.id} got a cramp and had to slow down before the game really began. That happened because {hero.pronoun('possessive')} tummy was still too full for quick running.",
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} handle the problem?",
                f"{hero.id} paused instead of rushing and gave digestion time to settle. That calmer choice helped {hero.pronoun('object')} feel more ready and less worried.",
            )
        )
    if f["outcome"] == "earned_medal":
        qa.append(
            (
                "What was the surprise at the end?",
                f"The surprise was that the coach still gave {hero.id} a medal after the game, even though the story focused on patience as much as speed. The medal showed that wise choices mattered too.",
            )
        )
    else:
        qa.append(
            (
                "What was the surprise at the end?",
                f"The surprise was that the coach gave {hero.id} a medal for kindness instead of for finishing first. It happened after {hero.id} listened, slowed down, and helped near the game.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"digestion", "medal"}
    if world.facts["choice"].id == "sip_stretch":
        tags.add("water")
    tags.add("cramp")
    tags.add("race")
    if world.facts["outcome"] == "kindness_medal":
        tags.add("kindness")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        game="race",
        snack="cake",
        choice="sip_stretch",
        surprise="steady",
        hero_name="Mina",
        hero_gender="girl",
        friend_name="Toby",
        friend_gender="boy",
        coach_type="coach_woman",
    ),
    StoryParams(
        game="relay",
        snack="sandwich",
        choice="sit_breath",
        surprise="steady",
        hero_name="Eli",
        hero_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        coach_type="coach_man",
    ),
    StoryParams(
        game="hop",
        snack="cake",
        choice="rush",
        surprise="kindness",
        hero_name="Lila",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        coach_type="coach_woman",
    ),
    StoryParams(
        game="race",
        snack="apple",
        choice="sip_stretch",
        surprise="steady",
        hero_name="Ben",
        hero_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        coach_type="coach_man",
    ),
    StoryParams(
        game="relay",
        snack="sandwich",
        choice="rush",
        surprise="kindness",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Sam",
        friend_gender="boy",
        coach_type="coach_woman",
    ),
]


def explain_rejection(snack: Snack, choice: Choice) -> str:
    if choice.sense < SENSE_MIN:
        return (
            f"(Refusing choice '{choice.id}': it scores too low on common sense "
            f"(sense={choice.sense} < {SENSE_MIN}). Try a calmer choice like "
            f"{', '.join(sorted(c.id for c in sensible_choices()))}.)"
        )
    if snack.weight == 3 and choice.id == "rush":
        return (
            f"(No story: rushing into a game right after {snack.phrase} is too unreasonable "
            f"for this world. The tummy would still be far too busy with digestion, so pick a waiting choice.)"
        )
    return "(No story: this snack and choice do not make a reasonable scenario.)"


ASP_RULES = r"""
choice_sensible(C) :- choice(C), sense(C,S), sense_min(M), S >= M.
heavy(S) :- snack(S), weight(S,W), W >= 2.
very_heavy(S) :- snack(S), weight(S,3).

valid(G,S,C) :- game(G), snack(S), choice_sensible(C), not invalid_combo(S,C).
invalid_combo(S,rush) :- very_heavy(S).

needed_wait(S,1) :- quick(S).
needed_wait(S,2) :- snack(S), not quick(S).

outcome(kindness_medal) :- chosen_snack(S), chosen_choice(rush), heavy(S).
outcome(earned_medal) :- chosen_snack(S), chosen_choice(C), waits(C,W), needed_wait(S,N), W >= N, C != rush.
outcome(kindness_medal) :- chosen_snack(S), chosen_choice(C), C != rush, waits(C,W), needed_wait(S,N), W < N.
outcome(kindness_medal) :- chosen_snack(S), chosen_choice(rush), not heavy(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for gid in GAMES:
        lines.append(asp.fact("game", gid))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("weight", sid, snack.weight))
        if snack.quick:
            lines.append(asp.fact("quick", sid))
    for cid, choice in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("sense", cid, choice.sense))
        lines.append(asp.fact("waits", cid, choice.wait_beats))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
            asp.fact("chosen_snack", params.snack),
            asp.fact("chosen_choice", params.choice),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: a child wants a medal, digestion causes conflict, and a surprise changes the ending."
    )
    ap.add_argument("--game", choices=GAMES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--coach-type", choices=["coach_woman", "coach_man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.snack and args.choice:
        snack = SNACKS[args.snack]
        choice = CHOICES[args.choice]
        if choice.sense < SENSE_MIN or (snack.weight == 3 and choice.id == "rush"):
            raise StoryError(explain_rejection(snack, choice))

    combos = [
        c
        for c in valid_combos()
        if (args.game is None or c[0] == args.game)
        and (args.snack is None or c[1] == args.snack)
        and (args.choice is None or c[2] == args.choice)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    game, snack, choice = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    coach_type = args.coach_type or rng.choice(["coach_woman", "coach_man"])
    expected = outcome_of(
        StoryParams(
            game=game,
            snack=snack,
            choice=choice,
            surprise="steady",
            hero_name=hero_name,
            hero_gender=hero_gender,
            friend_name=friend_name,
            friend_gender=friend_gender,
            coach_type=coach_type,
        )
    )
    surprise = args.surprise or ("steady" if expected == "earned_medal" else "kindness")
    return StoryParams(
        game=game,
        snack=snack,
        choice=choice,
        surprise=surprise,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        coach_type=coach_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        game = GAMES[params.game]
        snack = SNACKS[params.snack]
        choice = CHOICES[params.choice]
        surprise = SURPRISES[params.surprise]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from err

    if (params.game, params.snack, params.choice) not in set(valid_combos()):
        raise StoryError(explain_rejection(snack, choice))

    expected = outcome_of(params)
    if expected == "earned_medal" and surprise.id != "steady":
        raise StoryError("(Invalid surprise: earned-medal stories require the steady medal surprise.)")
    if expected == "kindness_medal" and surprise.id != "kindness":
        raise StoryError("(Invalid surprise: kindness-medal stories require the kindness surprise.)")

    choice_text = choice.text.format(name=params.hero_name)
    choice = Choice(
        id=choice.id,
        label=choice.label,
        wait_beats=choice.wait_beats,
        risk_drop=choice.risk_drop,
        text=choice_text,
        sense=choice.sense,
        tags=set(choice.tags),
    )

    world = tell(
        game=game,
        snack=snack,
        choice=choice,
        surprise=surprise,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        coach_type=params.coach_type,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for s in range(40):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {s}.")
            break

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
        smoke = generate(cases[0])
        if not smoke.story or "medal" not in smoke.story or "digestion" not in smoke.story:
            raise StoryError("smoke test story missing required content")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
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
        print(f"{len(combos)} compatible (game, snack, choice) combos:\n")
        for game, snack, choice in combos:
            print(f"  {game:8} {snack:9} {choice}")
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
            header = f"### {p.hero_name}: {p.game}, {p.snack}, {p.choice} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
