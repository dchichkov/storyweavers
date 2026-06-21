#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/squirrel_consecutive_cliff_lookout_sound_effects_foreshadowing.py
================================================================================================

A standalone story world for a heartwarming cliff-lookout quest about a squirrel,
warning sounds, and the choice between hurrying and listening.

Premise
-------
A young squirrel must carry something kind to a cliff lookout before sunset.
On the way, the path itself makes warning sounds -- clack-clack, creak-creak,
or shhh-hiss -- that foreshadow trouble. A friend offers a sensible aid. The
story turns on whether the squirrel slows down and listens.

This world models:
- typed entities with physical meters and emotional memes
- a small reasonableness gate for route/cargo/aid compatibility
- a forward-simulated warning beat
- a Python outcome model with an inline ASP twin
- grounded prompts, story QA, and world-knowledge QA

Run it
------
python storyworlds/worlds/gpt-5.4/squirrel_consecutive_cliff_lookout_sound_effects_foreshadowing.py
python storyworlds/worlds/gpt-5.4/squirrel_consecutive_cliff_lookout_sound_effects_foreshadowing.py --all
python storyworlds/worlds/gpt-5.4/squirrel_consecutive_cliff_lookout_sound_effects_foreshadowing.py --qa --seed 7
python storyworlds/worlds/gpt-5.4/squirrel_consecutive_cliff_lookout_sound_effects_foreshadowing.py --verify
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
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    # physical / emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "she"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "he"}:
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
class Quest:
    id: str
    item_label: str
    item_phrase: str
    purpose: str
    finish_line: str
    cargo: str
    fragile: bool
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
class Route:
    id: str
    label: str
    path_phrase: str
    warning_sound: str
    foreshadow: str
    risk: int
    needs: set[str] = field(default_factory=set)
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
    sense: int
    power: int
    works_on: set[str] = field(default_factory=set)
    carries: set[str] = field(default_factory=set)
    success: str = ""
    rescue: str = ""
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
class Helper:
    id: str
    kind: str
    label: str
    action: str
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    item = world.get("item")
    if hero.meters["hurrying"] < THRESHOLD:
        return out
    if hero.attrs.get("route_risk", 0) <= 0:
        return out
    sig = ("wobble", hero.id, world.facts.get("route_id", ""))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["balance_loss"] += 1
    hero.memes["fear"] += 1
    item.meters["at_risk"] += 1
    out.append("__wobble__")
    return out


def _r_drop(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    item = world.get("item")
    if hero.meters["balance_loss"] < THRESHOLD:
        return out
    risk = hero.attrs.get("route_risk", 0) + world.facts.get("delay", 0)
    aid_power = world.facts.get("aid_power", 0)
    sig = ("drop", item.id, risk, aid_power)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if aid_power < risk:
        item.meters["damaged"] += 1
        hero.memes["sadness"] += 1
        out.append("__damaged__")
    else:
        hero.memes["relief"] += 1
        out.append("__saved__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="drop", tag="physical", apply=_r_drop),
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


def aid_fits(route: Route, quest: Quest, aid: Aid) -> bool:
    return route.id in aid.works_on and quest.cargo in aid.carries


def sensible_aids() -> list[Aid]:
    return [a for a in AIDS.values() if a.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for qid, quest in QUESTS.items():
        for rid, route in ROUTES.items():
            for aid_id, aid in AIDS.items():
                if aid_fits(route, quest, aid) and aid.sense >= SENSE_MIN:
                    combos.append((qid, rid, aid_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_heed(route: Route, trait: str, consecutive_count: int) -> bool:
    authority = initial_caution(trait) + consecutive_count
    return authority > BRAVERY_INIT + max(0, route.risk - 2)


def outcome_of(params: "StoryParams") -> str:
    if params.quest not in QUESTS or params.route not in ROUTES or params.aid not in AIDS:
        raise StoryError("(Invalid params: unknown quest, route, or aid.)")
    route = ROUTES[params.route]
    quest = QUESTS[params.quest]
    aid = AIDS[params.aid]
    if not aid_fits(route, quest, aid):
        raise StoryError(explain_rejection(route, quest, aid))
    if aid.sense < SENSE_MIN:
        raise StoryError(explain_aid(params.aid))
    if would_heed(route, params.trait, params.consecutive_count):
        return "careful"
    risk = route.risk + params.delay
    if aid.power >= risk:
        return "saved"
    return "shared"


def predict_crossing(world: World, route: Route, delay: int) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    item = sim.get("item")
    hero.attrs["route_risk"] = route.risk
    sim.facts["delay"] = delay
    hero.meters["hurrying"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": hero.meters["balance_loss"] >= THRESHOLD,
        "damaged": item.meters["damaged"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"On a golden evening at the cliff lookout, {hero.id} the squirrel had a kind little quest. "
        f"{hero.pronoun().capitalize()} wanted to carry {quest.item_phrase} up to the high railing "
        f"so it could help with {quest.purpose}."
    )
    world.say(
        f"{helper.id} was there too, ready to {helper.attrs['helper_action']}. "
        f"From the cliff, the sea below flashed silver and the pines leaned toward the wind."
    )


def setup_item(world: World, hero: Entity, quest: Quest) -> None:
    item = world.get("item")
    hero.memes["care"] += 1
    world.say(
        f"{hero.id} held {item.label} close. {quest.finish_line} felt so near that "
        f"{hero.pronoun()} could almost picture everyone smiling already."
    )


def foreshadow(world: World, hero: Entity, route: Route, consecutive_count: int) -> None:
    world.say(
        f"But the way up was {route.path_phrase}. As soon as {hero.id} stepped closer, "
        f"the path answered with {route.warning_sound}! {route.warning_sound}! "
        f"{route.foreshadow}"
    )
    if consecutive_count >= 2:
        world.say(
            f"Those were {consecutive_count} consecutive warning sounds, close together, "
            f"and they made the whole hill seem to whisper, slow down."
        )


def tempt(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["urgency"] += 1
    world.say(
        f'"If I hurry, I can still be first," {hero.id} said, twitching {hero.pronoun("possessive")} tail. '
        f'The quest felt important, and important things can make even a sweet squirrel want to rush.'
    )


def warn(world: World, hero: Entity, helper: Entity, route: Route, aid: Aid, delay: int) -> None:
    pred = predict_crossing(world, route, delay)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_damaged"] = pred["damaged"]
    hero.memes["caution"] += 1
    end = "You will wobble, and your bundle may not make it." if pred["damaged"] else "You will wobble if you dash like that."
    world.say(
        f'{helper.id} listened to the sounds and shook {helper.pronoun("possessive")} head. '
        f'"Hear that? {route.warning_sound}! That path is telling us something. Use {aid.phrase} and go gently. '
        f'{end}"'
    )


def heed(world: World, hero: Entity, helper: Entity, route: Route, aid: Aid) -> None:
    hero.memes["trust"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"{hero.id} stopped, took one deep breath, and listened. Then {hero.pronoun()} nodded, "
        f"let {helper.id} help with {aid.phrase}, and crossed {route.label} one careful paw-step at a time."
    )
    world.say(aid.success)
    world.get("item").meters["delivered"] += 1


def hurry(world: World, hero: Entity, route: Route, delay: int) -> None:
    hero.meters["hurrying"] += 1
    hero.attrs["route_risk"] = route.risk
    world.facts["delay"] = delay
    propagate(world, narrate=False)
    world.say(
        f"But the sunset colors looked brighter by the second, and {hero.id} dashed onto {route.label}. "
        f"{route.warning_sound}! went the path again."
    )
    if hero.meters["balance_loss"] >= THRESHOLD:
        world.say(
            f"One stone skipped, one board tipped, or one patch of needles slid under {hero.pronoun('possessive')} feet. "
            f"{hero.id} wobbled and clutched the bundle tight."
        )


def rescue(world: World, hero: Entity, helper: Entity, aid: Aid) -> None:
    hero.memes["gratitude"] += 1
    hero.memes["relief"] += 1
    world.get("item").meters["delivered"] += 1
    world.say(aid.rescue.format(helper=helper.id, hero=hero.id))
    world.say(
        f"{hero.id}'s heart thumped hard for a moment, and then slowed again when {hero.pronoun()} felt the bundle safe in {hero.pronoun('possessive')} paws."
    )


def share_resolution(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    item = world.get("item")
    item.meters["shared_fix"] += 1
    hero.memes["love"] += 1
    hero.memes["gratitude"] += 1
    world.say(
        f"The bundle bumped the ground, and {quest.item_label} was no longer perfect. {hero.id}'s ears drooped."
    )
    world.say(
        f'But {helper.id} came close and smiled. "A kind quest does not end just because a bundle gets messy," '
        f'{helper.pronoun()} said. Together they gathered what they could, and the friends at the lookout added their own little bits until the gift was enough.'
    )
    world.say(
        f"By the time the sky turned peach and lavender, the cliff lookout was glowing with shared kindness instead of worry."
    )


def arrival(world: World, hero: Entity, helper: Entity, quest: Quest, outcome: str) -> None:
    hero.memes["joy"] += 1
    if outcome == "careful":
        closing = "Everyone could see that listening had carried the kindness all the way to the top."
    elif outcome == "saved":
        closing = f"{hero.id} smiled at {helper.id}, knowing help can be just as brave as speed."
    else:
        closing = "What reached the top was not a perfect bundle, but a bigger feeling: everyone sharing."
    world.say(
        f"At last they reached the railing of the cliff lookout and finished {quest.purpose}. "
        f"{quest.finish_line} {closing}"
    )


def tell(
    quest: Quest,
    route: Route,
    aid: Aid,
    helper_cfg: Helper,
    *,
    hero_name: str = "Pip",
    hero_trait: str = "careful",
    helper_name: str = "Tavi",
    consecutive_count: int = 2,
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type="animal",
            label="the squirrel",
            traits=[hero_trait],
            role="hero",
            attrs={},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type="animal",
            label=helper_cfg.label,
            role="helper",
            attrs={"helper_action": helper_cfg.action},
        )
    )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="bundle",
            label=quest.item_label,
            portable=True,
            attrs={"cargo": quest.cargo, "fragile": quest.fragile},
        )
    )

    hero.memes["bravery"] = BRAVERY_INIT
    hero.memes["caution"] = initial_caution(hero_trait)
    hero.attrs["route_risk"] = route.risk
    world.facts["route_id"] = route.id
    world.facts["aid_power"] = aid.power
    world.facts["delay"] = delay
    world.facts["consecutive_count"] = consecutive_count

    introduce(world, hero, helper, quest)
    setup_item(world, hero, quest)

    world.para()
    foreshadow(world, hero, route, consecutive_count)
    tempt(world, hero, quest)
    warn(world, hero, helper, route, aid, delay)

    outcome = "careful"
    if would_heed(route, hero_trait, consecutive_count):
        world.para()
        heed(world, hero, helper, route, aid)
    else:
        world.para()
        hurry(world, hero, route, delay)
        if aid.power >= route.risk + delay:
            outcome = "saved"
            rescue(world, hero, helper, aid)
        else:
            outcome = "shared"
            world.get("item").meters["damaged"] += 1
            share_resolution(world, hero, helper, quest)

    world.para()
    arrival(world, hero, helper, quest, outcome)

    world.facts.update(
        hero=hero,
        helper=helper,
        quest=quest,
        route=route,
        aid=aid,
        helper_cfg=helper_cfg,
        item=item,
        outcome=outcome,
        delivered=item.meters["delivered"] >= THRESHOLD or item.meters["shared_fix"] >= THRESHOLD,
        damaged=item.meters["damaged"] >= THRESHOLD,
    )
    return world


QUESTS = {
    "lantern": Quest(
        id="lantern",
        item_label="the lantern jar",
        item_phrase="a little lantern jar with two glow-seeds inside",
        purpose="the evening welcome light",
        finish_line="Soon the jar shone like a tiny warm moon beside the railing.",
        cargo="glowy",
        fragile=True,
        tags={"lantern", "quest", "light"},
    ),
    "muffins": Quest(
        id="muffins",
        item_label="the muffin basket",
        item_phrase="a basket of berry muffins wrapped in a blue cloth",
        purpose="the lookout sharing snack",
        finish_line="Soon the sweet berry smell curled through the evening air.",
        cargo="crumbly",
        fragile=True,
        tags={"muffin", "quest", "sharing"},
    ),
    "banner": Quest(
        id="banner",
        item_label="the welcome banner",
        item_phrase="a rolled welcome banner stitched from soft leaves",
        purpose="the hilltop welcome sign",
        finish_line="Soon the banner fluttered kindly in the breeze above the path.",
        cargo="fluttery",
        fragile=False,
        tags={"banner", "quest", "welcome"},
    ),
}

ROUTES = {
    "pebble_steps": Route(
        id="pebble_steps",
        label="the pebble steps",
        path_phrase="a row of tiny cliff steps edged with loose stones",
        warning_sound="clack-clack",
        foreshadow="Little pebbles tapped one another and rattled down toward the sea.",
        risk=3,
        needs={"strap", "sled"},
        tags={"pebbles", "sound", "cliff"},
    ),
    "old_bridge": Route(
        id="old_bridge",
        label="the old bridge",
        path_phrase="an old plank bridge stretched between two rocks",
        warning_sound="creak-creak",
        foreshadow="The ropes swayed and the boards complained before anyone was halfway across.",
        risk=2,
        needs={"rope"},
        tags={"bridge", "sound", "cliff"},
    ),
    "pine_ramp": Route(
        id="pine_ramp",
        label="the pine-needle ramp",
        path_phrase="a sloping ramp dusted with dry pine needles",
        warning_sound="shhh-hiss",
        foreshadow="The needles whispered over the wood like slippers on a polished floor.",
        risk=2,
        needs={"strap", "rope"},
        tags={"pine", "sound", "cliff"},
    ),
}

AIDS = {
    "chest_strap": Aid(
        id="chest_strap",
        label="a chest strap",
        phrase="the chest strap",
        sense=3,
        power=2,
        works_on={"pebble_steps", "pine_ramp"},
        carries={"glowy", "crumbly", "fluttery"},
        success="The bundle stayed snug against the squirrel's chest instead of swinging about.",
        rescue="{helper} sprang alongside {hero}, tightened the chest strap, and steadied the bundle before it could tumble away.",
        tags={"strap", "safety"},
    ),
    "guide_rope": Aid(
        id="guide_rope",
        label="a guide rope",
        phrase="the guide rope",
        sense=3,
        power=3,
        works_on={"old_bridge", "pine_ramp"},
        carries={"glowy", "crumbly", "fluttery"},
        success="With the guide rope under one paw, even the wind seemed easier to answer.",
        rescue="{helper} flicked the guide rope toward {hero}, and together they leaned back until paws and bundle were steady again.",
        tags={"rope", "safety"},
    ),
    "moss_sled": Aid(
        id="moss_sled",
        label="a moss sled",
        phrase="the moss sled",
        sense=2,
        power=3,
        works_on={"pebble_steps"},
        carries={"glowy", "fluttery"},
        success="The sled slid between the stones so softly that not one pebble jumped at all.",
        rescue="{helper} caught the front of the moss sled and held it straight while {hero} found a safe foothold.",
        tags={"sled", "safety"},
    ),
    "leaf_tray": Aid(
        id="leaf_tray",
        label="a leaf tray",
        phrase="the leaf tray",
        sense=1,
        power=1,
        works_on={"old_bridge"},
        carries={"crumbly"},
        success="The tray looked neat, but it trembled at every little sway.",
        rescue="{helper} tried to pinch the wobbling tray flat, but it was never the best tool for a swaying bridge.",
        tags={"tray"},
    ),
}

HELPERS = {
    "robin": Helper(
        id="robin",
        kind="bird",
        label="the robin",
        action="hover nearby and watch the windy path",
        tags={"bird", "helper"},
    ),
    "goat": Helper(
        id="goat",
        kind="animal",
        label="the mountain goat",
        action="plant careful hooves and brace the steeper places",
        tags={"goat", "helper"},
    ),
    "mole": Helper(
        id="mole",
        kind="animal",
        label="the mole",
        action="listen to the ground and notice the first little shifts",
        tags={"mole", "helper"},
    ),
}

NAMES = ["Pip", "Nettle", "Moss", "Junie", "Acorn", "Tumble", "Clover", "Bramble"]
HELPER_NAMES = ["Tavi", "Luma", "Fern", "Rill", "Skip", "Miri"]
TRAITS = ["careful", "steady", "thoughtful", "eager", "bouncy", "bold"]


@dataclass
class StoryParams:
    quest: str
    route: str
    aid: str
    helper: str
    hero_name: str
    helper_name: str
    trait: str
    consecutive_count: int = 2
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
    "squirrel": [
        (
            "What is a squirrel?",
            "A squirrel is a small animal with a fluffy tail. Squirrels are good climbers and often carry nuts or other little things in their paws.",
        )
    ],
    "cliff": [
        (
            "What is a cliff lookout?",
            "A cliff lookout is a high place near the edge of a cliff where you can stop and see far away. Because it is high and windy, you need to walk carefully there.",
        )
    ],
    "foreshadow": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when a story gives a small hint before something important happens later. A warning sound or a worried glance can help you feel that a problem may be coming.",
        )
    ],
    "sound": [
        (
            "Why do stories use sound effects like clack-clack or creak-creak?",
            "Sound effects help you imagine what the place feels like. They can also warn you that something is loose, shaky, or changing.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a special job or journey with a purpose. In stories, a quest often matters because someone is trying to help, find, or deliver something important.",
        )
    ],
    "rope": [
        (
            "What does a guide rope do?",
            "A guide rope gives you something steady to hold while you cross a tricky place. It helps you keep your balance and move more slowly.",
        )
    ],
    "strap": [
        (
            "Why would a chest strap help carry something?",
            "A chest strap keeps a bundle close to your body instead of letting it swing. When a bundle swings less, it is easier to balance.",
        )
    ],
    "sharing": [
        (
            "Why can sharing fix a problem?",
            "Sharing helps because one friend's loss does not have to stay a loss when others help. A group can turn a small accident into a warm ending.",
        )
    ],
    "bridge": [
        (
            "Why does an old bridge creak?",
            "An old bridge can creak when wood and rope shift under weight and wind. Those sounds can be a sign to slow down and cross carefully.",
        )
    ],
    "pebbles": [
        (
            "Why do loose pebbles make clacking sounds?",
            "Loose pebbles tap one another when they shift or roll. That sound can mean the ground is not as steady as it looks.",
        )
    ],
    "pine": [
        (
            "Why are pine needles slippery?",
            "Dry pine needles can slide over smooth wood or hard ground. That makes it easier for feet to slip if someone hurries.",
        )
    ],
}
KNOWLEDGE_ORDER = ["squirrel", "cliff", "foreshadow", "sound", "quest", "rope", "strap", "sharing", "bridge", "pebbles", "pine"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    quest = f["quest"]
    route = f["route"]
    aid = f["aid"]
    hero = f["hero"]
    outcome = f["outcome"]
    if outcome == "careful":
        return [
            f'Write a heartwarming story for a 3-to-5-year-old about a squirrel on a quest at a cliff lookout. Include the word "consecutive" and the sound "{route.warning_sound}".',
            f"Tell a gentle story where {hero.id} hears consecutive warning sounds on {route.label}, slows down, and uses {aid.label} to finish a kind quest safely.",
            f"Write a story with foreshadowing where the path warns a squirrel before the trouble happens, and the squirrel listens in time.",
        ]
    if outcome == "saved":
        return [
            f'Write a heartwarming story about a squirrel carrying {quest.item_label} to a cliff lookout. Include sound effects, a wobble, and a helpful rescue.',
            f"Tell a quest story where {hero.id} hurries after hearing {route.warning_sound}, but a friend uses {aid.label} to help before the gift is lost.",
            f"Write a story with foreshadowing and a warm ending where help arrives fast after the warning signs come true.",
        ]
    return [
        f'Write a heartwarming story about a squirrel quest at a cliff lookout where sound effects foreshadow a small accident, but friends share to make things right.',
        f"Tell a story where {hero.id} rushes after hearing {route.warning_sound}, the bundle gets messy, and the lookout friends still make the evening special together.",
        f"Write a gentle story showing that a kind quest can still succeed through sharing, even after a mistake.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    quest = f["quest"]
    route = f["route"]
    aid = f["aid"]
    outcome = f["outcome"]
    consecutive_count = f["consecutive_count"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a squirrel with a kind quest, and {helper.id}, the friend who helped on the path. They were trying to reach the cliff lookout before evening.",
        ),
        (
            "What was the squirrel trying to do?",
            f"{hero.id} was carrying {quest.item_phrase} to help with {quest.purpose}. The whole trip mattered because the gift was meant to brighten the cliff lookout.",
        ),
        (
            "How did the story use sound to warn about trouble?",
            f"The path made the sound {route.warning_sound}, and it happened as {consecutive_count} consecutive warning sounds. That noise foreshadowed that the route was loose or shaky before the real wobble came.",
        ),
        (
            f"Why did {helper.id} tell {hero.id} to use {aid.label}?",
            f"{helper.id} heard the warning sounds and understood that {route.label} was risky. {aid.label.capitalize()} was the sensible way to keep both the squirrel and the bundle steadier on that route.",
        ),
    ]
    if outcome == "careful":
        qa.append(
            (
                f"Why did {hero.id} get to the top safely?",
                f"{hero.id} listened instead of rushing. Because the squirrel slowed down and used {aid.label}, the warning sounds became useful advice instead of the start of an accident.",
            )
        )
    elif outcome == "saved":
        qa.append(
            (
                f"What happened when {hero.id} hurried?",
                f"{hero.id} wobbled on the path when the warning sounds came true. Then {helper.id} used {aid.label} to steady the crossing, so the quest bundle was saved.",
            )
        )
        qa.append(
            (
                "How did the ending prove something changed?",
                f"The ending shows that {hero.id} reached the lookout with help instead of speed alone. The squirrel finishes the quest while understanding that brave hearts can still accept a steady paw.",
            )
        )
    else:
        qa.append(
            (
                f"Did the quest fail when the bundle was damaged?",
                f"No. The bundle was no longer perfect, but the friends at the lookout shared what they had. The ending becomes heartwarming because kindness grows larger after the small accident.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the cliff lookout glowing with shared kindness. Even after the wobble, the friends worked together until the evening still felt welcoming and warm.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"squirrel", "cliff", "foreshadow", "sound", "quest"}
    route = f["route"]
    aid = f["aid"]
    outcome = f["outcome"]
    if "bridge" in route.tags:
        tags.add("bridge")
    if "pebbles" in route.tags:
        tags.add("pebbles")
    if "pine" in route.tags:
        tags.add("pine")
    if "rope" in aid.tags:
        tags.add("rope")
    if "strap" in aid.tags or "sled" in aid.tags:
        tags.add("strap")
    if outcome == "shared":
        tags.add("sharing")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(route: Route, quest: Quest, aid: Aid) -> str:
    if route.id not in aid.works_on:
        return (
            f"(No story: {aid.label} does not make sense on {route.label}. "
            f"Pick an aid that works on that route.)"
        )
    if quest.cargo not in aid.carries:
        return (
            f"(No story: {aid.label} is not a good way to carry {quest.item_label}. "
            f"Pick an aid that suits that kind of bundle.)"
        )
    return "(No story: this route, quest, and aid do not fit together.)"


def explain_aid(aid_id: str) -> str:
    aid = AIDS[aid_id]
    return (
        f"(Refusing aid '{aid_id}': it scores too low on common sense "
        f"(sense={aid.sense} < {SENSE_MIN}). Try a steadier aid instead.)"
    )


ASP_RULES = r"""
% reasonableness gate
valid(Q, R, A) :- quest(Q), route(R), aid(A), works_on(A, R), carries(A, C), cargo(Q, C),
                  sense(A, S), sense_min(M), S >= M.

% outcome model
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

heed_threshold(Risk, BR + Risk - 2) :- route_risk(Risk), bravery_init(BR), Risk >= 2.
heed_threshold(Risk, BR) :- route_risk(Risk), bravery_init(BR), Risk < 2.
authority(C + N) :- init_caution(C), consecutive_count(N).
heeds :- authority(A), heed_threshold(_, T), A > T.

cross_risk(V) :- route_risk(R), delay(D), V = R + D.
saved_by_aid :- chosen_aid(A), power(A, P), cross_risk(V), P >= V.

outcome(careful) :- heeds.
outcome(saved) :- not heeds, saved_by_aid.
outcome(shared) :- not heeds, not saved_by_aid.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("cargo", qid, q.cargo))
    for rid, r in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("route_risk_of", rid, r.risk))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("sense", aid_id, aid.sense))
        lines.append(asp.fact("power", aid_id, aid.power))
        for rid in sorted(aid.works_on):
            lines.append(asp.fact("works_on", aid_id, rid))
        for cargo in sorted(aid.carries):
            lines.append(asp.fact("carries", aid_id, cargo))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    route = ROUTES[params.route]
    scenario = "\n".join(
        [
            asp.fact("trait", params.trait),
            asp.fact("consecutive_count", params.consecutive_count),
            asp.fact("delay", params.delay),
            asp.fact("chosen_aid", params.aid),
            asp.fact("route_risk", route.risk),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        quest="lantern",
        route="old_bridge",
        aid="guide_rope",
        helper="robin",
        hero_name="Pip",
        helper_name="Tavi",
        trait="careful",
        consecutive_count=2,
        delay=0,
    ),
    StoryParams(
        quest="muffins",
        route="pine_ramp",
        aid="guide_rope",
        helper="goat",
        hero_name="Junie",
        helper_name="Fern",
        trait="eager",
        consecutive_count=2,
        delay=0,
    ),
    StoryParams(
        quest="banner",
        route="pebble_steps",
        aid="moss_sled",
        helper="mole",
        hero_name="Moss",
        helper_name="Rill",
        trait="bold",
        consecutive_count=2,
        delay=1,
    ),
    StoryParams(
        quest="muffins",
        route="pebble_steps",
        aid="chest_strap",
        helper="goat",
        hero_name="Clover",
        helper_name="Luma",
        trait="steady",
        consecutive_count=3,
        delay=0,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a squirrel hears warning sounds on a cliff-lookout quest."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--consecutive-count", type=int, choices=[1, 2, 3], dest="consecutive_count")
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra difficulty from waiting too long")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python / ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.aid and AIDS[args.aid].sense < SENSE_MIN:
        raise StoryError(explain_aid(args.aid))
    if args.quest and args.route and args.aid:
        route = ROUTES[args.route]
        quest = QUESTS[args.quest]
        aid = AIDS[args.aid]
        if not aid_fits(route, quest, aid):
            raise StoryError(explain_rejection(route, quest, aid))

    combos = [
        combo
        for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.route is None or combo[1] == args.route)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest, route, aid = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    trait = args.trait or rng.choice(TRAITS)
    consecutive_count = args.consecutive_count if args.consecutive_count is not None else rng.choice([2, 3])
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    hero_name = rng.choice(NAMES)
    helper_name = rng.choice([n for n in HELPER_NAMES if n != hero_name])
    return StoryParams(
        quest=quest,
        route=route,
        aid=aid,
        helper=helper,
        hero_name=hero_name,
        helper_name=helper_name,
        trait=trait,
        consecutive_count=consecutive_count,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"(Invalid quest: {params.quest})")
    if params.route not in ROUTES:
        raise StoryError(f"(Invalid route: {params.route})")
    if params.aid not in AIDS:
        raise StoryError(f"(Invalid aid: {params.aid})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Invalid trait: {params.trait})")
    route = ROUTES[params.route]
    quest = QUESTS[params.quest]
    aid = AIDS[params.aid]
    if aid.sense < SENSE_MIN:
        raise StoryError(explain_aid(params.aid))
    if not aid_fits(route, quest, aid):
        raise StoryError(explain_rejection(route, quest, aid))

    world = tell(
        quest=quest,
        route=route,
        aid=aid,
        helper_cfg=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_trait=params.trait,
        helper_name=params.helper_name,
        consecutive_count=params.consecutive_count,
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


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(100):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"ERROR: resolve_params failed unexpectedly for seed {seed}.")
            break

    bad = 0
    for p in cases:
        try:
            py_out = outcome_of(p)
            asp_out = asp_outcome(p)
            if py_out != asp_out:
                bad += 1
                print(f"MISMATCH outcome for {p}: python={py_out} asp={asp_out}")
        except StoryError as err:
            bad += 1
            print(f"ERROR during outcome check for {p}: {err}")
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke-test generation/emit passed.")
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
        print(f"{len(combos)} compatible (quest, route, aid) combos:\n")
        for q, r, a in combos:
            print(f"  {q:8} {r:13} {a}")
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
            header = f"### {p.hero_name}: {p.quest} via {p.route} with {p.aid} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
