#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cooperative_hero_friendship_bad_ending_fairy_tale.py
================================================================================

A standalone storyworld for a small fairy-tale domain about friendship, haste,
and the difference between being a lone hero and a cooperative one.

Premise
-------
In a valley of cottages and moonlit hedges, a child hero and a dear friend are
trusted with a small magical relic. They must carry it across one dangerous
place and bring it to a hill shrine before moonset. The friend can foresee the
risk and urges a sensible, cooperative plan with the right protection. If the
hero breaks from the friend and rushes alone, the relic is ruined and the quest
fails. Even when they stay together, a weak aid or too much delay can still
lead to a bad ending. In the happy stories, cooperation and the right tool keep
the relic safe.

Run it
------
    python storyworlds/worlds/gpt-5.4/cooperative_hero_friendship_bad_ending_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/cooperative_hero_friendship_bad_ending_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/cooperative_hero_friendship_bad_ending_fairy_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/cooperative_hero_friendship_bad_ending_fairy_tale.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
PRIDE_INIT = 7
AID_MIN = 2
STEADY_TRAITS = {"steady", "wise", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman", "fairy"}
        male = {"boy", "father", "king", "man", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "queen": "queen",
            "wizard": "wizard",
            "mother": "mother",
            "father": "father",
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
class Quest:
    id: str
    valley: str
    need: str
    shrine: str
    result: str
    dark_image: str
    bright_image: str
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
class Relic:
    id: str
    label: str
    phrase: str
    glow: str
    ruined: str
    need_two_hands: str
    risk_type: str
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
class Obstacle:
    id: str
    label: str
    place_text: str
    threat: str
    severity: int
    risk_type: str
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
class Aid:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
    power: int = 0
    use_text: str = ""
    fail_text: str = ""
    qa_text: str = ""
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


def _r_ruin_relic(world: World) -> list[str]:
    relic = world.get("relic")
    if relic.meters["struck"] < THRESHOLD:
        return []
    sig = ("ruin_relic",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    relic.meters["ruined"] += 1
    for eid in ("hero", "friend"):
        if eid in world.entities:
            world.get(eid).memes["grief"] += 1
    if "valley" in world.entities:
        world.get("valley").meters["hope"] = 0.0
        world.get("valley").meters["gloom"] += 1
    return ["__ruined__"]


def _r_quarrel_hurts_friendship(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["defiance"] < THRESHOLD:
        return []
    sig = ("quarrel_hurts_friendship",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["friendship_hurt"] += 1
    friend.memes["friendship_hurt"] += 1
    return ["__friendship_hurt__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="ruin_relic", tag="physical", apply=_r_ruin_relic),
    Rule(name="quarrel_hurts_friendship", tag="social", apply=_r_quarrel_hurts_friendship),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def relic_at_risk(relic: Relic, obstacle: Obstacle) -> bool:
    return relic.risk_type == obstacle.risk_type


def suitable_aids() -> list[Aid]:
    return [aid for aid in AIDS.values() if aid.power >= AID_MIN]


def select_compatible_aids(obstacle: Obstacle) -> list[Aid]:
    return [aid for aid in suitable_aids() if obstacle.risk_type in aid.guards]


def crossing_severity(obstacle: Obstacle, delay: int) -> int:
    return obstacle.severity + delay


def is_protected(aid: Aid, obstacle: Obstacle, delay: int) -> bool:
    return obstacle.risk_type in aid.guards and aid.power >= crossing_severity(obstacle, delay)


def trait_bonus(trait: str) -> int:
    return 2 if trait in STEADY_TRAITS else 1


def would_split(friendship: int, friend_trait: str) -> bool:
    authority = friendship + trait_bonus(friend_trait) + 1
    return authority < PRIDE_INIT


def predict_risk(world: World, obstacle_id: str) -> dict:
    sim = world.copy()
    obstacle = OBSTACLES[obstacle_id]
    relic = sim.get("relic")
    aid = sim.get("aid")
    sim.facts["delay"] = 0
    attempt_crossing(sim, obstacle, aid, narrate=False)
    return {
        "ruined": relic.meters["ruined"] >= THRESHOLD,
        "gloom": sim.get("valley").meters["gloom"],
    }


def opening(world: World, hero: Entity, friend: Entity, quest: Quest) -> None:
    hero.memes["dream"] += 1
    friend.memes["love"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"In {quest.valley}, where hedges glittered at dusk and tiny lamps woke with the fireflies, "
        f"{hero.id} wanted to be a hero more than anything."
    )
    world.say(
        f"On most days {friend.id}, {hero.pronoun('possessive')} dearest friend, walked beside "
        f"{hero.pronoun('object')}, and the two were known as a wonderfully cooperative pair."
    )


def trouble(world: World, elder: Entity, quest: Quest) -> None:
    world.say(
        f"But one evening {quest.need}. The cottages grew hushed, and even the crickets seemed to wait."
    )
    world.say(
        f'The old {elder.label_word} came to the square and said, "Only a true-hearted child can carry '
        f'help to {quest.shrine} before moonset."'
    )


def entrust(world: World, hero: Entity, friend: Entity, relic: Relic, quest: Quest) -> None:
    world.say(
        f"{hero.id} and {friend.id} were given {relic.phrase}, which {relic.glow}."
    )
    world.say(
        f"If it reached {quest.shrine}, {quest.result}."
    )


def approach(world: World, hero: Entity, friend: Entity, obstacle: Obstacle) -> None:
    hero.memes["urgency"] += 1
    friend.memes["urgency"] += 1
    world.say(
        f"They hurried until they came to {obstacle.place_text}. Moonlight silvered the stones, "
        f"but {obstacle.threat}."
    )


def temptation(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["pride"] += 1
    world.say(
        f'"There is no time to creep," said {hero.id}. "If I run ahead, everyone will see that I am the hero."'
    )


def warning(world: World, hero: Entity, friend: Entity, elder: Entity, relic: Relic, obstacle: Obstacle, aid: Aid) -> None:
    pred = predict_risk(world, obstacle.id)
    world.facts["predicted_ruin"] = pred["ruined"]
    friend.memes["caution"] += 1
    extra = " The thought of losing both the relic and the warm feeling between them made " \
            f"{friend.id} hold {friend.pronoun('possessive')} breath."
    world.say(
        f'{friend.id} touched {hero.id}\'s sleeve. "Please do not go alone," {friend.pronoun()} said. '
        f'"{relic.need_two_hands}, and {aid.phrase} will help us through. '
        f'The {elder.label_word} trusted both of us."{extra}'
    )


def split_up(world: World, hero: Entity, friend: Entity, relic: Entity) -> None:
    hero.memes["defiance"] += 1
    hero.meters["alone"] += 1
    friend.memes["fear"] += 1
    relic.meters["unsupported"] += 1
    propagate(world, narrate=False)
    world.say(
        f'But {hero.id} pulled away. "I can do it faster by myself," {hero.pronoun()} said, '
        f'and before {friend.id} could answer, {hero.pronoun()} rushed on alone with the relic.'
    )


def stay_together(world: World, hero: Entity, friend: Entity, aid: Aid) -> None:
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    hero.memes["cooperation"] += 1
    friend.memes["cooperation"] += 1
    world.say(
        f"{hero.id} looked at {friend.id}, heard the tremble in {friend.pronoun('possessive')} voice, "
        f"and stopped. Together they took {aid.phrase} and set their hands to the same careful rhythm."
    )


def attempt_crossing(world: World, obstacle: Obstacle, aid_ent: Entity, narrate: bool = True) -> None:
    relic = world.get("relic")
    hero = world.get("hero")
    friend = world.get("friend")
    delay = int(world.facts.get("delay", 0))
    if obstacle.risk_type not in set(aid_ent.attrs.get("guards", set())):
        relic.meters["struck"] += 1
    elif aid_ent.meters["protection"] < float(crossing_severity(obstacle, delay)):
        relic.meters["struck"] += 1
    propagate(world, narrate=False)
    if not narrate:
        return
    if relic.meters["ruined"] >= THRESHOLD:
        hero.memes["fear"] += 1
        friend.memes["fear"] += 1
        world.say(
            f"{aid_ent.attrs['fail_text']} In one dreadful blink, the relic was spoiled."
        )
    else:
        world.say(
            f"{aid_ent.attrs['use_text']} Step by step, they crossed without letting the danger touch the relic."
        )


def lone_crossing(world: World, hero: Entity, friend: Entity, obstacle: Obstacle, relic: Relic) -> None:
    relic_ent = world.get("relic")
    relic_ent.meters["struck"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} had scarcely reached the middle when {obstacle.threat.lower()} "
        f"The precious {relic.label} lurched in {hero.pronoun('possessive')} hands."
    )
    world.say(
        f"{friend.id} cried out from behind, but it was too late: {relic.ruined}."
    )


def success_end(world: World, hero: Entity, friend: Entity, quest: Quest) -> None:
    valley = world.get("valley")
    valley.meters["hope"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"At last they climbed to {quest.shrine} and laid the relic in its silver place. "
        f"At once {quest.result.lower()}."
    )
    world.say(
        f"{hero.id} did not boast this time. {hero.pronoun().capitalize()} squeezed {friend.id}'s hand and laughed, "
        f"for now {hero.pronoun()} knew that the bravest hero was a cooperative one."
    )
    world.say(quest.bright_image)


def bad_end(world: World, hero: Entity, friend: Entity, quest: Quest) -> None:
    hero.memes["regret"] += 1
    friend.memes["regret"] += 1
    world.say(
        f"They reached the hill with nothing useful left to offer. Because the relic was spoiled, "
        f"{quest.dark_image.lower()}."
    )
    if hero.memes["friendship_hurt"] >= THRESHOLD:
        world.say(
            f"{hero.id} and {friend.id} stood side by side, yet not quite together. "
            f"The road home felt longer than the road out, and neither child knew how to mend the ache at once."
        )
    else:
        world.say(
            f"{hero.id} leaned against {friend.id}, and both were quiet with sorrow. "
            f"They had stayed together, but they had come too late for the valley's need."
        )


def tell(
    quest: Quest,
    relic: Relic,
    obstacle: Obstacle,
    aid: Aid,
    hero_name: str = "Rowan",
    hero_gender: str = "boy",
    friend_name: str = "Elsi",
    friend_gender: str = "girl",
    friend_trait: str = "steady",
    elder_type: str = "wizard",
    friendship: int = 4,
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend",
                              traits=[friend_trait]))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label="the elder", role="elder"))
    valley = world.add(Entity(id="valley", type="place", label=quest.valley))
    relic_ent = world.add(Entity(id="relic", type="relic", label=relic.label))
    aid_ent = world.add(Entity(
        id="aid",
        type="aid",
        label=aid.label,
        attrs={
            "guards": set(aid.guards),
            "use_text": aid.use_text,
            "fail_text": aid.fail_text,
        },
    ))
    aid_ent.meters["protection"] = float(aid.power)
    valley.meters["hope"] = 1.0
    valley.meters["gloom"] = 0.0
    hero.memes["pride"] = float(PRIDE_INIT)
    friend.memes["steadiness"] = float(trait_bonus(friend_trait))
    hero.attrs["display_name"] = hero_name
    friend.attrs["display_name"] = friend_name
    world.facts["delay"] = delay

    opening(world, hero, friend, quest)
    trouble(world, elder, quest)
    entrust(world, hero, friend, relic, quest)

    world.para()
    approach(world, hero, friend, obstacle)
    temptation(world, hero, obstacle)
    warning(world, hero, friend, elder, relic, obstacle, aid)

    split = would_split(friendship, friend_trait)
    if split:
        split_up(world, hero, friend, relic_ent)
        world.para()
        lone_crossing(world, hero, friend, obstacle, relic)
        world.para()
        bad_end(world, hero, friend, quest)
        outcome = "failed"
    else:
        stay_together(world, hero, friend, aid)
        world.para()
        attempt_crossing(world, obstacle, aid_ent, narrate=True)
        world.para()
        if relic_ent.meters["ruined"] >= THRESHOLD:
            bad_end(world, hero, friend, quest)
            outcome = "failed"
        else:
            success_end(world, hero, friend, quest)
            outcome = "saved"

    world.facts.update(
        quest=quest,
        relic_cfg=relic,
        obstacle=obstacle,
        aid_cfg=aid,
        hero=hero,
        friend=friend,
        elder=elder,
        friendship=friendship,
        split=split,
        ruined=relic_ent.meters["ruined"] >= THRESHOLD,
        outcome=outcome,
        success=(outcome == "saved"),
    )
    return world


QUESTS = {
    "moon_lilies": Quest(
        id="moon_lilies",
        valley="Willowmere",
        need="the moon-lilies in the village pond had folded shut before their time",
        shrine="the Hill of Soft Bells",
        result="the moon-lilies would open again and pour pale light over the water",
        dark_image="the moon-lilies stayed closed and the pond lay dim as pewter",
        bright_image="Soon the pond shone like a little sky, and every cottage window caught the silver gleam",
        tags={"flowers", "friendship"},
    ),
    "well_song": Quest(
        id="well_song",
        valley="Briar Hollow",
        need="the wishing well had fallen silent, and no fresh singing water rose in its bucket",
        shrine="the Round Stone Crown",
        result="the well would sing again and sweet water would rise for every home",
        dark_image="the well stayed mute, and the bucket came up heavy and dry",
        bright_image="Before dawn the well was singing again, and the first bucket sparkled as if stars had melted into it",
        tags={"well", "friendship"},
    ),
    "orchard_lanterns": Quest(
        id="orchard_lanterns",
        valley="Thistledown Vale",
        need="the lantern-fruit in the orchard had gone dark among the branches",
        shrine="the Lantern Arch",
        result="the orchard lights would wake and glow like little moons in the leaves",
        dark_image="the orchard remained dark, and the branches hung like black lace against the sky",
        bright_image="One by one, warm lights blossomed in the orchard, and the leaves looked stitched with gold",
        tags={"orchard", "friendship"},
    ),
}

RELICS = {
    "starflame": Relic(
        id="starflame",
        label="starflame lantern",
        phrase="a starflame lantern, no bigger than a teacup",
        glow="burned with a blue-gold flame that hated rough wind",
        ruined="the little flame shivered, guttered, and went out",
        need_two_hands="This lantern needs two steady hands",
        risk_type="wind",
        tags={"lantern", "wind"},
    ),
    "dew_pearl": Relic(
        id="dew_pearl",
        label="dew-pearl bowl",
        phrase="a bowl of dawn-dew cupped in moon glass",
        glow="held one trembling pearl of water that must not be jolted",
        ruined="the bowl knocked against stone, and the pearl burst into nothing",
        need_two_hands="This bowl must be carried with two calm pairs of hands",
        risk_type="jolt",
        tags={"glass", "care"},
    ),
    "silk_banner": Relic(
        id="silk_banner",
        label="silk sun-banner",
        phrase="a folded silk sun-banner sewn with tiny gold thread",
        glow="shimmered faintly, but rain would blot its magic away",
        ruined="cold drops soaked the silk until the magic bled out in pale streaks",
        need_two_hands="This banner must be kept high and dry together",
        risk_type="rain",
        tags={"silk", "rain"},
    ),
}

OBSTACLES = {
    "wind_bridge": Obstacle(
        id="wind_bridge",
        label="the Wind-Bridge",
        place_text="the Wind-Bridge above the ravine",
        threat="gusts came whistling through the planks hard enough to snatch a hat or twist a flame",
        severity=3,
        risk_type="wind",
        tags={"bridge", "wind"},
    ),
    "rain_pass": Obstacle(
        id="rain_pass",
        label="the Rain Pass",
        place_text="the Rain Pass between two dripping cliffs",
        threat="rain ran there in silver sheets and spattered every uncovered thing",
        severity=2,
        risk_type="rain",
        tags={"rain", "pass"},
    ),
    "stone_stairs": Obstacle(
        id="stone_stairs",
        label="the Stone Stairs",
        place_text="the Stone Stairs curling up the hill",
        threat="the narrow steps were chipped and uneven, so one hard stumble could dash a treasure to pieces",
        severity=2,
        risk_type="jolt",
        tags={"stairs", "stone"},
    ),
}

AIDS = {
    "wind_shield": Aid(
        id="wind_shield",
        label="wind-shield hood",
        phrase="the wind-shield hood",
        guards={"wind"},
        power=3,
        use_text="They raised the hood over the lantern, leaned shoulder to shoulder, and let each gust pass around them",
        fail_text="They tried to hide behind the hood, but the night wind tore around its edge and struck straight through",
        qa_text="They used the wind-shield hood together so the gusts could not bite the flame",
        tags={"wind", "hood"},
    ),
    "wax_cloak": Aid(
        id="wax_cloak",
        label="waxed leaf-cloak",
        phrase="the waxed leaf-cloak",
        guards={"rain"},
        power=2,
        use_text="They spread the waxed cloak above the relic like a green roof and moved in small matching steps",
        fail_text="They held up the cloak, but the rain found every gap and drummed through onto the relic",
        qa_text="They held the waxed leaf-cloak over the relic together to keep the rain off",
        tags={"rain", "cloak"},
    ),
    "moss_cradle": Aid(
        id="moss_cradle",
        label="moss cradle",
        phrase="the moss cradle",
        guards={"jolt"},
        power=2,
        use_text="They nested the bowl in the moss cradle and carried it between them so softly that even the pebbles seemed to hush",
        fail_text="They set the relic in the moss cradle, but the climb was too rough and the cradle lurched in their hands",
        qa_text="They used the moss cradle together so the climb would not shake the relic",
        tags={"moss", "care"},
    ),
    "ribbon_loop": Aid(
        id="ribbon_loop",
        label="moon-ribbon loop",
        phrase="the moon-ribbon loop",
        guards={"wind"},
        power=1,
        use_text="They tied the ribbon neatly around the relic and hoped it would be enough",
        fail_text="They trusted the ribbon, but it was too flimsy for the danger before them",
        qa_text="They tried to use the moon-ribbon loop together",
        tags={"ribbon"},
    ),
}

GIRL_NAMES = ["Elsi", "Mira", "Nella", "Tansy", "Ivy", "Lina", "Poppy", "Faye"]
BOY_NAMES = ["Rowan", "Alder", "Finn", "Milo", "Bram", "Nico", "Tobin", "Perrin"]
TRAITS = ["steady", "wise", "gentle", "bright", "earnest", "patient"]


@dataclass
class StoryParams:
    quest: str
    relic: str
    obstacle: str
    aid: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    friend_trait: str
    elder: str
    friendship: int = 4
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for quest_id in QUESTS:
        for relic_id, relic in RELICS.items():
            for obstacle_id, obstacle in OBSTACLES.items():
                if not relic_at_risk(relic, obstacle):
                    continue
                for aid_id, aid in AIDS.items():
                    if obstacle.risk_type in aid.guards and aid.power >= AID_MIN:
                        combos.append((quest_id, relic_id, obstacle_id, aid_id))
    return combos


KNOWLEDGE = {
    "friendship": [
        (
            "What does friendship mean?",
            "Friendship means caring about someone, listening to them, and staying kind even when things feel hard. Good friends help one another make wiser choices.",
        )
    ],
    "hero": [
        (
            "Does a hero always work alone?",
            "No. A hero can be brave alone, but many of the best heroes listen, share the work, and protect others. In many fairy tales, courage and cooperation belong together.",
        )
    ],
    "wind": [
        (
            "Why can wind be dangerous to a small flame?",
            "Wind pushes air hard against a flame and can make it flicker out. A tiny magical flame still needs shelter if the gusts are strong.",
        )
    ],
    "rain": [
        (
            "Why can rain ruin something delicate?",
            "Rain can soak cloth, blur colors, or wash away small bits of magic. That is why delicate things must be kept dry.",
        )
    ],
    "glass": [
        (
            "Why do you carry glass carefully?",
            "Glass can crack or break if it is knocked against something hard. Careful hands and slow steps help keep it safe.",
        )
    ],
    "bridge": [
        (
            "Why do people walk carefully on a bridge?",
            "A bridge can be narrow or windy, especially high above the ground. Careful walking helps keep people and precious things steady.",
        )
    ],
    "cloak": [
        (
            "What does a cloak do in a fairy tale?",
            "A cloak covers something and keeps it safer from cold, rain, or watchful eyes. In fairy tales, a cloak often helps travelers protect what they carry.",
        )
    ],
    "moss": [
        (
            "Why is soft moss good for protecting fragile things?",
            "Moss is springy and soft, so it can cushion little bumps. That makes it useful for carrying something that must not be shaken.",
        )
    ],
    "hood": [
        (
            "What is a hood or shield for around a lantern?",
            "It blocks the strongest gusts so the flame does not blow out. A cover makes a lantern much safer to carry in wind.",
        )
    ],
}

KNOWLEDGE_ORDER = ["friendship", "hero", "wind", "rain", "glass", "bridge", "cloak", "moss", "hood"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    quest = f["quest"]
    obstacle = f["obstacle"]
    relic = f["relic_cfg"]
    if f["outcome"] == "failed":
        return [
            'Write a fairy tale for a 3-to-5-year-old that includes the words "cooperative" and "hero" and ends sadly.',
            f"Tell a fairy tale where two friends must carry a magical relic through {obstacle.label}, but the child who wants to be the hero forgets to work cooperatively and the quest fails.",
            f"Write a gentle but unhappy story about friendship where {relic.label} is spoiled on the way to {quest.shrine}, leaving the valley unchanged.",
        ]
    return [
        'Write a fairy tale for a 3-to-5-year-old that includes the words "cooperative" and "hero" and ends happily.',
        f"Tell a fairy tale where two friends carry a magical relic through {obstacle.label} by working cooperatively, and the child who wanted to be the hero learns to share the task.",
        f"Write a simple story about friendship and courage where careful teamwork saves a valley before moonset.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    quest = f["quest"]
    relic = f["relic_cfg"]
    obstacle = f["obstacle"]
    aid = f["aid_cfg"]
    hero_name = hero.attrs.get("display_name", hero.id)
    friend_name = friend.attrs.get("display_name", friend.id)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, who longed to be a hero, and {friend_name}, {hero.pronoun('possessive')} dear friend. The two children were trusted with a magical errand for their valley.",
        ),
        (
            "What were they trying to do?",
            f"They were trying to bring the {relic.label} to {quest.shrine}. If they could get it there in time, {quest.result.lower()}.",
        ),
        (
            f"Why was {obstacle.label} dangerous?",
            f"{obstacle.label} was dangerous because {obstacle.threat.lower()}. That danger matched the weakness of the {relic.label}.",
        ),
        (
            f"What warning did {friend_name} give {hero_name}?",
            f"{friend_name} warned {hero_name} not to rush ahead alone. {friend.pronoun().capitalize()} knew the relic needed careful hands and the right help to cross safely.",
        ),
    ]
    if f["split"]:
        qa.append(
            (
                f"Why did the quest fail?",
                f"The quest failed because {hero_name} broke away from {friend_name} and tried to carry the relic alone. That hurt their teamwork, and the danger spoiled the relic before it reached the shrine.",
            )
        )
        qa.append(
            (
                f"How did the ending show a problem in their friendship?",
                f"They were still standing near each other, but they did not feel fully together anymore. The failed errand and {hero_name}'s choice to rush alone left a sore feeling between them.",
            )
        )
    elif f["ruined"]:
        qa.append(
            (
                "Why did the ending turn sad even though they stayed together?",
                f"They stayed together and used {aid.label}, but they were too late for such a hard crossing. Because the danger was stronger than their protection, the relic was spoiled anyway.",
            )
        )
    else:
        qa.append(
            (
                f"How did they get through {obstacle.label} safely?",
                f"They used {aid.qa_text}. Their teamwork mattered because the relic was delicate, and careful shared steps kept the danger from reaching it.",
            )
        )
        qa.append(
            (
                f"What did {hero_name} learn?",
                f"{hero_name} learned that being a hero did not mean shining alone. {hero.pronoun().capitalize()} learned that a cooperative heart and a faithful friend could save the valley together.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"friendship", "hero"}
    tags |= set(f["relic_cfg"].tags)
    tags |= set(f["obstacle"].tags)
    if f["success"]:
        tags |= set(f["aid_cfg"].tags)
    else:
        tags |= set(f["aid_cfg"].tags)
    out: list[tuple[str, str]] = []
    mapping = {
        "friendship": "friendship",
        "hero": "hero",
        "wind": "wind",
        "rain": "rain",
        "glass": "glass",
        "bridge": "bridge",
        "cloak": "cloak",
        "moss": "moss",
        "hood": "hood",
        "care": "moss",
        "pass": "rain",
    }
    for raw in tags:
        _ = raw
    seen: set[str] = set()
    for raw_tag in tags:
        k = mapping.get(raw_tag)
        if k and k not in seen:
            seen.add(k)
    ordered = [k for k in KNOWLEDGE_ORDER if k in seen]
    for key in ordered:
        out.extend(KNOWLEDGE[key])
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {}
            for k, v in ent.attrs.items():
                if isinstance(v, set):
                    shown[k] = sorted(v)
                elif v:
                    shown[k] = v
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest="moon_lilies",
        relic="starflame",
        obstacle="wind_bridge",
        aid="wind_shield",
        hero_name="Rowan",
        hero_gender="boy",
        friend_name="Elsi",
        friend_gender="girl",
        friend_trait="steady",
        elder="wizard",
        friendship=5,
        delay=0,
    ),
    StoryParams(
        quest="well_song",
        relic="silk_banner",
        obstacle="rain_pass",
        aid="wax_cloak",
        hero_name="Mira",
        hero_gender="girl",
        friend_name="Tobin",
        friend_gender="boy",
        friend_trait="wise",
        elder="queen",
        friendship=4,
        delay=0,
    ),
    StoryParams(
        quest="orchard_lanterns",
        relic="dew_pearl",
        obstacle="stone_stairs",
        aid="moss_cradle",
        hero_name="Alder",
        hero_gender="boy",
        friend_name="Faye",
        friend_gender="girl",
        friend_trait="gentle",
        elder="wizard",
        friendship=2,
        delay=0,
    ),
    StoryParams(
        quest="moon_lilies",
        relic="starflame",
        obstacle="wind_bridge",
        aid="wind_shield",
        hero_name="Poppy",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        friend_trait="earnest",
        elder="queen",
        friendship=4,
        delay=1,
    ),
    StoryParams(
        quest="well_song",
        relic="dew_pearl",
        obstacle="stone_stairs",
        aid="moss_cradle",
        hero_name="Nico",
        hero_gender="boy",
        friend_name="Lina",
        friend_gender="girl",
        friend_trait="patient",
        elder="wizard",
        friendship=5,
        delay=2,
    ),
]


def explain_rejection(relic: Relic, obstacle: Obstacle) -> str:
    return (
        f"(No story: {obstacle.label} threatens {obstacle.risk_type}, but {relic.label} is only at risk from "
        f"{relic.risk_type}. That would not create an honest fairy-tale danger.)"
    )


def explain_aid(aid: Aid, obstacle: Obstacle) -> str:
    good = ", ".join(sorted(a.id for a in select_compatible_aids(obstacle)))
    return (
        f"(No story: {aid.label} does not sensibly protect against {obstacle.risk_type}, or it is too weak "
        f"for this world. Try one of: {good}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_split(params.friendship, params.friend_trait):
        return "failed"
    return "saved" if is_protected(AIDS[params.aid], OBSTACLES[params.obstacle], params.delay) else "failed"


ASP_RULES = r"""
% --- gate ---------------------------------------------------------------
risk_match(R, O) :- relic_risk(R, K), obstacle_risk(O, K).
strong_aid(A)    :- aid(A), power(A, P), aid_min(M), P >= M.
compatible_aid(A, O) :- strong_aid(A), obstacle_risk(O, K), guards(A, K).
valid(Q, R, O, A) :- quest(Q), relic(R), obstacle(O), risk_match(R, O), compatible_aid(A, O).

% --- outcome ------------------------------------------------------------
trait_bonus(T, 2) :- steady_trait(T).
trait_bonus(T, 1) :- trait(T), not steady_trait(T).
authority(F + B + 1) :- friendship(F), chosen_trait(T), trait_bonus(T, B).
split :- authority(A), pride_init(P), A < P.

severity(S + D) :- chosen_obstacle(O), base_severity(O, S), delay(D).
protected :- chosen_aid(A), chosen_obstacle(O), compatible_aid(A, O), power(A, P), severity(V), P >= V.

outcome(failed) :- split.
outcome(saved)  :- not split, protected.
outcome(failed) :- not split, not protected.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("relic_risk", rid, relic.risk_type))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("obstacle_risk", oid, obstacle.risk_type))
        lines.append(asp.fact("base_severity", oid, obstacle.severity))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("power", aid_id, aid.power))
        for g in sorted(aid.guards):
            lines.append(asp.fact("guards", aid_id, g))
    for tr in TRAITS:
        lines.append(asp.fact("trait", tr))
    for tr in sorted(STEADY_TRAITS):
        lines.append(asp.fact("steady_trait", tr))
    lines.append(asp.fact("aid_min", AID_MIN))
    lines.append(asp.fact("pride_init", PRIDE_INIT))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_aid", params.aid),
            asp.fact("chosen_trait", params.friend_trait),
            asp.fact("friendship", params.friendship),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=False, qa=True, header="smoke")
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a would-be hero, a friend, a magical relic, and the cost of failing to cooperate."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--elder", choices=["queen", "wizard"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("--friendship", type=int, choices=[0, 1, 2, 3, 4, 5])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.relic and args.obstacle:
        relic = RELICS[args.relic]
        obstacle = OBSTACLES[args.obstacle]
        if not relic_at_risk(relic, obstacle):
            raise StoryError(explain_rejection(relic, obstacle))
    if args.aid and args.obstacle:
        aid = AIDS[args.aid]
        obstacle = OBSTACLES[args.obstacle]
        if obstacle.risk_type not in aid.guards or aid.power < AID_MIN:
            raise StoryError(explain_aid(aid, obstacle))

    combos = [
        combo
        for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.relic is None or combo[1] == args.relic)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.aid is None or combo[3] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest, relic, obstacle, aid = rng.choice(sorted(combos))
    hero_name, hero_gender = _pick_child(rng)
    friend_name, friend_gender = _pick_child(rng, avoid=hero_name)
    elder = args.elder or rng.choice(["queen", "wizard"])
    friend_trait = rng.choice(TRAITS)
    friendship = args.friendship if args.friendship is not None else rng.randint(0, 5)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        quest=quest,
        relic=relic,
        obstacle=obstacle,
        aid=aid,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        friend_trait=friend_trait,
        elder=elder,
        friendship=friendship,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest: {params.quest})")
    if params.relic not in RELICS:
        raise StoryError(f"(Unknown relic: {params.relic})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")

    quest = QUESTS[params.quest]
    relic = RELICS[params.relic]
    obstacle = OBSTACLES[params.obstacle]
    aid = AIDS[params.aid]

    if not relic_at_risk(relic, obstacle):
        raise StoryError(explain_rejection(relic, obstacle))
    if obstacle.risk_type not in aid.guards or aid.power < AID_MIN:
        raise StoryError(explain_aid(aid, obstacle))

    world = tell(
        quest=quest,
        relic=relic,
        obstacle=obstacle,
        aid=aid,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        friend_trait=params.friend_trait,
        elder_type=params.elder,
        friendship=params.friendship,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, relic, obstacle, aid) combos:\n")
        for quest, relic, obstacle, aid in combos:
            print(f"  {quest:16} {relic:12} {obstacle:12} {aid}")
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.relic} through {p.obstacle} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
