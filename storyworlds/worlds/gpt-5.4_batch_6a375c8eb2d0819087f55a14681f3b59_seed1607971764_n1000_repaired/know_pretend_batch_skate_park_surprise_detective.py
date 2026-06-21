#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/know_pretend_batch_skate_park_surprise_detective.py
==============================================================================

A standalone storyworld for a tiny detective-style mystery at a skate park.

Premise
-------
Two children like to pretend they are detectives at the skate park. Right before
an important moment, one child's helmet goes missing. A real clue has been left
behind, the children investigate, and the mystery turns into a warm surprise.

This world models:
- a missing physical object (the helmet),
- clue-driven investigation,
- emotional state changes (worry, curiosity, relief, pride),
- a careful-vs-hasty detective style that changes the middle turn,
- a reasonableness gate for which surprise plans, helpers, places, and clues fit.

Run it
------
python storyworlds/worlds/gpt-5.4/know_pretend_batch_skate_park_surprise_detective.py
python storyworlds/worlds/gpt-5.4/know_pretend_batch_skate_park_surprise_detective.py --all
python storyworlds/worlds/gpt-5.4/know_pretend_batch_skate_park_surprise_detective.py --qa --seed 7
python storyworlds/worlds/gpt-5.4/know_pretend_batch_skate_park_surprise_detective.py --verify
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
RASH_TRAITS = {"hasty", "jumpy"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt", "coach_woman"}
        male = {"boy", "father", "dad", "man", "uncle", "coach_man"}
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
            "aunt": "aunt",
            "uncle": "uncle",
            "coach_woman": "coach",
            "coach_man": "coach",
        }
        return mapping.get(self.type, self.label or self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class SurprisePlan:
    id: str
    reason: str
    reveal_line: str
    token: str
    token_phrase: str
    snack_batch: str
    clue: str
    place_tags: set[str] = field(default_factory=set)
    helper_tags: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    phrase: str
    inference: str
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
class Place:
    id: str
    label: str
    phrase: str
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
class HelperCfg:
    id: str
    type: str
    label: str
    phrase: str
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


def _r_missing_worry(world: World) -> list[str]:
    helmet = world.get("helmet")
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    if helmet.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    sidekick.memes["alert"] += 1
    return []


def _r_clue_curiosity(world: World) -> list[str]:
    clue = world.get("clue")
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    if clue.meters["seen"] < THRESHOLD:
        return []
    sig = ("clue_curiosity",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["curiosity"] += 1
    sidekick.memes["confidence"] += 1
    return []


def _r_accusation_sting(world: World) -> list[str]:
    helper = world.get("helper")
    if helper.memes["accused"] < THRESHOLD:
        return []
    sig = ("accusation_sting",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["stung"] += 1
    return []


def _r_reveal_relief(world: World) -> list[str]:
    helmet = world.get("helmet")
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    helper = world.get("helper")
    if helmet.meters["found"] < THRESHOLD:
        return []
    sig = ("reveal_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    sidekick.memes["joy"] += 1
    helper.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="clue_curiosity", tag="emotional", apply=_r_clue_curiosity),
    Rule(name="accusation_sting", tag="social", apply=_r_accusation_sting),
    Rule(name="reveal_relief", tag="emotional", apply=_r_reveal_relief),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def combo_valid(plan: SurprisePlan, helper: HelperCfg, place: Place, clue: Clue) -> bool:
    return (
        plan.clue == clue.id
        and bool(plan.helper_tags & helper.tags)
        and bool(plan.place_tags & place.tags)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for plan_id, plan in PLANS.items():
        for helper_id, helper in HELPERS.items():
            for place_id, place in PLACES.items():
                for clue_id, clue in CLUES.items():
                    if combo_valid(plan, helper, place, clue):
                        out.append((plan_id, helper_id, place_id, clue_id))
    return out


def outcome_of_trait(trait: str) -> str:
    return "apology_reveal" if trait in RASH_TRAITS else "gentle_reveal"


def explain_combo(plan: SurprisePlan, helper: HelperCfg, place: Place, clue: Clue) -> str:
    if plan.clue != clue.id:
        return (
            f"(No story: {clue.phrase} does not honestly point to the '{plan.id}' "
            f"surprise. Pick the clue that belongs with that plan.)"
        )
    if not (plan.helper_tags & helper.tags):
        return (
            f"(No story: {helper.phrase} is not a natural helper for the '{plan.id}' "
            f"surprise at this skate park.)"
        )
    if not (plan.place_tags & place.tags):
        return (
            f"(No story: {place.phrase} is not a sensible place to set up the "
            f"'{plan.id}' surprise.)"
        )
    return "(No story: that combination does not fit this world.)"


def predict_reveal(world: World, plan_id: str, place_id: str) -> dict:
    sim = world.copy()
    sim.facts["predicted_place"] = place_id
    sim.facts["predicted_plan"] = plan_id
    sim.get("helmet").meters["found"] += 1
    propagate(sim, narrate=False)
    return {
        "relief": sim.get("hero").memes["relief"],
        "joy": sim.get("hero").memes["joy"],
    }


def opening(world: World, hero: Entity, sidekick: Entity) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"After school, {hero.id} and {sidekick.id} hurried to the skate park, "
        f"where the ramps shone silver and the wheels on the concrete made a soft humming sound."
    )
    world.say(
        f"They loved to pretend they were detectives between turns on the little ramp. "
        f"{sidekick.id} called it The Skate Park Mystery Club, and {hero.id} always agreed."
    )


def stakes(world: World, hero: Entity, plan: SurprisePlan) -> None:
    world.say(
        f"That afternoon mattered especially to {hero.id}, because {plan.reason}. "
        f"{hero.pronoun('possessive').capitalize()} red helmet was the one thing "
        f"{hero.pronoun()} wanted ready first."
    )


def missing_helmet(world: World, hero: Entity) -> None:
    helmet = world.get("helmet")
    helmet.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {hero.id} reached the bench, the helmet was gone. "
        f"The bench held only a bent elbow pad and an empty patch of wood."
    )
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s stomach gave a tiny flip. {hero.pronoun().capitalize()} "
            f"did not know where it had gone, and the whole skate park suddenly felt much bigger."
        )


def inspect_clue(world: World, hero: Entity, sidekick: Entity, clue: Clue) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {sidekick.id} pointed down. Near the bench lay {clue.phrase}."
    )
    world.say(
        f'"I know a clue when I see one," {sidekick.id} whispered. '
        f'"This means somebody was heading toward {clue.inference}."'
    )


def decide_direction(world: World, hero: Entity, sidekick: Entity, place: Place) -> None:
    world.say(
        f"So the two detectives followed the idea across the skate park, past the low rail and the painted quarter-pipe, until they were close to {place.phrase}."
    )
    pred = predict_reveal(world, world.facts["plan"].id, place.id)
    world.facts["predicted_relief"] = pred["relief"]
    world.facts["predicted_joy"] = pred["joy"]


def hasty_turn(world: World, hero: Entity, helper: Entity) -> None:
    helper.memes["accused"] += 1
    propagate(world, narrate=False)
    hero.memes["suspicion"] += 1
    world.say(
        f"When {hero.id} spotted {helper.label_word} {helper.id} there, "
        f"{hero.pronoun()} blurted, "
        f'"Did you take my helmet?"'
    )
    if helper.memes["stung"] >= THRESHOLD:
        world.say(
            f"{helper.id} blinked in surprise. {helper.pronoun().capitalize()} was not angry, "
            f"but the question landed with a little thud."
        )


def careful_turn(world: World, sidekick: Entity, helper: Entity) -> None:
    sidekick.memes["poise"] += 1
    world.say(
        f"{sidekick.id} kept a detective voice and asked, "
        f'"Excuse me, {helper.label_word} {helper.id}. Are you working on a surprise?"'
    )


def reveal(world: World, hero: Entity, sidekick: Entity, helper: Entity,
           plan: SurprisePlan, clue: Clue, place: Place) -> None:
    helmet = world.get("helmet")
    helmet.meters["missing"] = 0.0
    helmet.meters["found"] += 1
    helmet.meters["decorated"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} smiled then, and stepped aside. There was the red helmet at {place.phrase}, "
        f"with {plan.token_phrase} clipped to the strap."
    )
    world.say(
        f'Beside it sat {plan.snack_batch}. Suddenly {clue.phrase} made perfect sense.'
    )
    world.say(
        f'"I borrowed it for one minute," {helper.id} said. "{plan.reveal_line}"'
    )
    if world.get("hero").memes["relief"] >= THRESHOLD:
        world.say(
            f"{hero.id} let out a long breath, and {sidekick.id} grinned so hard {sidekick.pronoun('possessive')} cheeks puffed out."
        )


def apology(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["sorry"] += 1
    world.say(
        f'"I am sorry I jumped to the wrong idea," {hero.id} said. '
        f'"A real detective should ask before deciding."'
    )


def ending(world: World, hero: Entity, sidekick: Entity, helper: Entity, plan: SurprisePlan) -> None:
    world.say(
        f"{helper.id} settled the helmet gently onto {hero.id}'s head. "
        f"The strap clicked, the little {plan.token} brushed {hero.pronoun('possessive')} chin, and the mystery felt warm instead of scary."
    )
    world.say(
        f"Soon {hero.id} rolled down the ramp while {sidekick.id} ran beside the rail shouting clues to the wind, "
        f"and the whole skate park looked as if it were smiling back."
    )


def tell(plan: SurprisePlan, helper_cfg: HelperCfg, place: Place, clue: Clue,
         hero_name: str = "Nora", hero_gender: str = "girl",
         sidekick_name: str = "Max", sidekick_gender: str = "boy",
         trait: str = "patient") -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        attrs={"name": hero_name, "trait": trait},
    ))
    sidekick = world.add(Entity(
        id="sidekick",
        kind="character",
        type=sidekick_gender,
        label=sidekick_name,
        role="sidekick",
        attrs={"name": sidekick_name},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        role="helper",
        attrs={"name": helper_cfg.label},
        tags=set(helper_cfg.tags),
    ))
    world.add(Entity(
        id="helmet",
        type="helmet",
        label="helmet",
        role="missing_item",
        attrs={"owner": hero_name},
    ))
    world.add(Entity(
        id="clue",
        type="clue",
        label=clue.label,
        role="clue",
        tags=set(clue.tags),
    ))
    world.add(Entity(
        id="place",
        type="place",
        label=place.label,
        role="place",
        tags=set(place.tags),
    ))

    world.facts.update(
        plan=plan,
        helper_cfg=helper_cfg,
        place_cfg=place,
        clue_cfg=clue,
        trait=trait,
        outcome=outcome_of_trait(trait),
        hero_name=hero_name,
        sidekick_name=sidekick_name,
    )

    opening(world, hero, sidekick)
    stakes(world, hero, plan)

    world.para()
    missing_helmet(world, hero)
    inspect_clue(world, hero, sidekick, clue)
    decide_direction(world, hero, sidekick, place)

    world.para()
    if outcome_of_trait(trait) == "apology_reveal":
        hasty_turn(world, hero, helper)
    else:
        careful_turn(world, sidekick, helper)
    reveal(world, hero, sidekick, helper, plan, clue, place)
    if outcome_of_trait(trait) == "apology_reveal":
        apology(world, hero, helper)

    world.para()
    ending(world, hero, sidekick, helper, plan)

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        helper=helper,
        helmet=world.get("helmet"),
        clue=world.get("clue"),
        found=world.get("helmet").meters["found"] >= THRESHOLD,
        apologised=hero.memes["sorry"] >= THRESHOLD,
        surprised=world.get("helmet").meters["decorated"] >= THRESHOLD,
    )
    return world


PLANS = {
    "first_drop": SurprisePlan(
        id="first_drop",
        reason="today was the first day to try the tall starter ramp",
        reveal_line="You are ready for your first drop-in, and this brave-star charm is for that moment.",
        token="brave-star charm",
        token_phrase="a tiny brave-star charm",
        snack_batch="a warm batch of cinnamon cookies wrapped in a towel",
        clue="star_sticker",
        place_tags={"snack"},
        helper_tags={"coach", "family"},
        tags={"helmet", "surprise", "cookies"},
    ),
    "birthday_roll": SurprisePlan(
        id="birthday_roll",
        reason="it was birthday skate day, though the secret had been kept all week",
        reveal_line="Happy birthday skate day. The ribbon and the treats were all for you.",
        token="blue birthday ribbon",
        token_phrase="a neat blue birthday ribbon",
        snack_batch="a sweet batch of mini cupcakes in a paper box",
        clue="blue_ribbon",
        place_tags={"party"},
        helper_tags={"family"},
        tags={"birthday", "surprise", "cupcakes"},
    ),
    "cleanup_cheer": SurprisePlan(
        id="cleanup_cheer",
        reason="the morning clean-up team had worked hard and everyone wanted to cheer the smallest helper",
        reveal_line="This thank-you patch is because you helped the whole park shine.",
        token="thank-you patch",
        token_phrase="a little thank-you patch",
        snack_batch="a cool batch of lemon bars on a tray",
        clue="lemon_crumb",
        place_tags={"table"},
        helper_tags={"coach"},
        tags={"cleanup", "surprise", "snack"},
    ),
}

CLUES = {
    "star_sticker": Clue(
        id="star_sticker",
        label="star sticker",
        phrase="a shiny gold star sticker backing",
        inference="the snack table near the fence",
        tags={"sticker"},
    ),
    "blue_ribbon": Clue(
        id="blue_ribbon",
        label="blue ribbon",
        phrase="a curled piece of blue ribbon",
        inference="the party bench under the shade sail",
        tags={"ribbon"},
    ),
    "lemon_crumb": Clue(
        id="lemon_crumb",
        label="lemon crumb",
        phrase="a yellow lemon-bar crumb dusted with sugar",
        inference="the folding table by the mural wall",
        tags={"food"},
    ),
}

PLACES = {
    "snack_table": Place(
        id="snack_table",
        label="snack table",
        phrase="the snack table near the fence",
        tags={"snack", "table"},
    ),
    "party_bench": Place(
        id="party_bench",
        label="party bench",
        phrase="the party bench under the shade sail",
        tags={"party"},
    ),
    "mural_table": Place(
        id="mural_table",
        label="mural table",
        phrase="the folding table by the mural wall",
        tags={"table", "coach"},
    ),
}

HELPERS = {
    "coach_mina": HelperCfg(
        id="coach_mina",
        type="coach_woman",
        label="Mina",
        phrase="Coach Mina",
        tags={"coach"},
    ),
    "dad_omar": HelperCfg(
        id="dad_omar",
        type="father",
        label="Omar",
        phrase="Dad Omar",
        tags={"family"},
    ),
    "aunt_lina": HelperCfg(
        id="aunt_lina",
        type="aunt",
        label="Lina",
        phrase="Aunt Lina",
        tags={"family"},
    ),
}

TRAITS = ["patient", "careful", "hasty", "jumpy"]
GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Ella", "Ruby", "June"]
BOY_NAMES = ["Max", "Leo", "Finn", "Theo", "Sam", "Eli", "Noah", "Jack"]


@dataclass
class StoryParams:
    plan: str
    helper: str
    place: str
    clue: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
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


KNOWLEDGE = {
    "helmet": [
        (
            "Why do skaters wear helmets?",
            "Helmets protect your head if you fall. A good helmet helps make skating safer."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks closely, notices clues, and asks careful questions. Good detectives do not guess too fast."
        )
    ],
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something hidden for a little while so it can feel special when it is revealed. A kind surprise should make someone feel happy and safe."
        )
    ],
    "ribbon": [
        (
            "What is a ribbon used for at a party?",
            "A ribbon can decorate a gift or mark something special. Its bright color can also work like a clue in a story."
        )
    ],
    "sticker": [
        (
            "What is a sticker?",
            "A sticker is a small piece of paper or plastic with glue on one side. People use stickers to decorate things."
        )
    ],
    "snack": [
        (
            "What does the word batch mean in cooking?",
            "A batch is a group of cookies, bars, or other food made together at one time. One batch can be shared with many people."
        )
    ],
    "skate_park": [
        (
            "What is a skate park?",
            "A skate park is a place with ramps, rails, and smooth ground for skating. People practice skills there and take turns using the space."
        )
    ],
}
KNOWLEDGE_ORDER = ["skate_park", "helmet", "detective", "surprise", "ribbon", "sticker", "snack"]


def generation_prompts(world: World) -> list[str]:
    plan = world.facts["plan"]
    helper = world.facts["helper_cfg"]
    place = world.facts["place_cfg"]
    clue = world.facts["clue_cfg"]
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    outcome = world.facts["outcome"]
    prompts = [
        'Write a short detective-style story for a 3-to-5-year-old set at a skate park. Include the words "know", "pretend", and "batch".',
        f"Tell a gentle mystery where {hero.label} and {sidekick.label} pretend to be detectives after a helmet goes missing at the skate park, and a clue leads them to {place.phrase}.",
    ]
    if outcome == "apology_reveal":
        prompts.append(
            f"Write a surprise story where {hero.label} rushes to the wrong idea, then learns to ask careful questions when {helper.phrase} reveals a kind secret."
        )
    else:
        prompts.append(
            f"Write a cozy detective story where a clue near a bench leads to {helper.phrase}, who has been preparing a surprise connected to {plan.reason}."
        )
    prompts.append(
        f"End with the mystery solved, the surprise revealed, and {plan.snack_batch} waiting nearby."
    )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    helper = world.facts["helper"]
    plan = world.facts["plan"]
    clue = world.facts["clue_cfg"]
    place = world.facts["place_cfg"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {sidekick.label}, two children at the skate park who like to pretend they are detectives. It is also about {helper.label_word} {helper.label}, who was secretly preparing a kind surprise."
        ),
        (
            "What was the mystery at the beginning?",
            f"{hero.label}'s helmet was missing from the bench. That made the skate park feel suddenly huge, because {hero.label} wanted the helmet before the special moment in the story."
        ),
        (
            "What clue did the children find?",
            f"They found {clue.phrase} near the bench. The clue mattered because it pointed them toward {place.phrase}, where the surprise was being prepared."
        ),
        (
            "Why did the clue help solve the case?",
            f"The clue matched the hidden surprise plan. Once the children followed it, the mystery changed from a missing-helmet problem into a clear trail leading to the reveal."
        ),
        (
            "What was the surprise?",
            f"The helper had borrowed the helmet for a moment and clipped on {plan.token_phrase}. There was also {plan.snack_batch}, which made the reveal feel festive and warm."
        ),
    ]
    if outcome == "apology_reveal":
        qa.append(
            (
                f"Why did {hero.label} say sorry?",
                f"{hero.label} asked the accusing question before checking all the facts. After the helmet was found and the surprise was explained, {hero.pronoun('subject').capitalize()} understood that a careful detective should ask first and guess later."
            )
        )
    else:
        qa.append(
            (
                "How did the children act like good detectives?",
                f"They looked closely, noticed the clue, and asked a calm question instead of jumping to blame. That careful method helped the truth come out without hurting anyone's feelings."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the helmet back on {hero.label}'s head and the mystery solved. The final picture is bright and happy, because the skate park that felt worrying at first now feels full of cheering and play."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"helmet", "detective", "surprise", "skate_park", "snack"}
    clue = world.facts["clue_cfg"]
    if "ribbon" in clue.tags:
        tags.add("ribbon")
    if "sticker" in clue.tags:
        tags.add("sticker")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        plan="first_drop",
        helper="coach_mina",
        place="snack_table",
        clue="star_sticker",
        hero_name="Nora",
        hero_gender="girl",
        sidekick_name="Max",
        sidekick_gender="boy",
        trait="patient",
    ),
    StoryParams(
        plan="birthday_roll",
        helper="aunt_lina",
        place="party_bench",
        clue="blue_ribbon",
        hero_name="Leo",
        hero_gender="boy",
        sidekick_name="Mia",
        sidekick_gender="girl",
        trait="hasty",
    ),
    StoryParams(
        plan="cleanup_cheer",
        helper="coach_mina",
        place="mural_table",
        clue="lemon_crumb",
        hero_name="Ruby",
        hero_gender="girl",
        sidekick_name="Finn",
        sidekick_gender="boy",
        trait="careful",
    ),
    StoryParams(
        plan="first_drop",
        helper="dad_omar",
        place="snack_table",
        clue="star_sticker",
        hero_name="Sam",
        hero_gender="boy",
        sidekick_name="Ella",
        sidekick_gender="girl",
        trait="jumpy",
    ),
]


def explain_gender(name: str, gender: str) -> str:
    return f"(No story: the name '{name}' does not match the chosen gender '{gender}' in this small world.)"


ASP_RULES = r"""
helper_ok(P,H) :- plan(P), helper(H), plan_helper_tag(P,T), helper_tag(H,T).
place_ok(P,L)  :- plan(P), place(L), plan_place_tag(P,T), place_tag(L,T).
valid(P,H,L,C) :- plan(P), helper(H), place(L), clue(C),
                  plan_clue(P,C), helper_ok(P,H), place_ok(P,L).

apology_reveal :- chosen_trait(T), rash(T).
gentle_reveal  :- chosen_trait(T), not rash(T).

outcome(apology_reveal) :- apology_reveal.
outcome(gentle_reveal)  :- gentle_reveal.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("plan_clue", pid, plan.clue))
        for tag in sorted(plan.helper_tags):
            lines.append(asp.fact("plan_helper_tag", pid, tag))
        for tag in sorted(plan.place_tags):
            lines.append(asp.fact("plan_place_tag", pid, tag))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for tag in sorted(helper.tags):
            lines.append(asp.fact("helper_tag", hid, tag))
    for lid, place in PLACES.items():
        lines.append(asp.fact("place", lid))
        for tag in sorted(place.tags):
            lines.append(asp.fact("place_tag", lid, tag))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
    for trait in sorted(RASH_TRAITS):
        lines.append(asp.fact("rash", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(trait: str) -> str:
    import asp

    model = asp.one_model(
        asp_program(f"chosen_trait({asp.term(trait)}).", "#show outcome/1.")
    )
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in combo gate:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    bad = []
    for trait in TRAITS:
        if asp_outcome(trait) != outcome_of_trait(trait):
            bad.append((trait, asp_outcome(trait), outcome_of_trait(trait)))
    if not bad:
        print("OK: trait outcome model matches Python.")
    else:
        rc = 1
        print("MISMATCH in trait outcome model:")
        for row in bad:
            print(" ", row)

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective-style surprise mystery at a skate park. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick-name")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plan and args.helper and args.place and args.clue:
        plan = PLANS[args.plan]
        helper = HELPERS[args.helper]
        place = PLACES[args.place]
        clue = CLUES[args.clue]
        if not combo_valid(plan, helper, place, clue):
            raise StoryError(explain_combo(plan, helper, place, clue))

    combos = [
        combo for combo in valid_combos()
        if (args.plan is None or combo[0] == args.plan)
        and (args.helper is None or combo[1] == args.helper)
        and (args.place is None or combo[2] == args.place)
        and (args.clue is None or combo[3] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    plan_id, helper_id, place_id, clue_id = rng.choice(sorted(combos))
    trait = args.trait or rng.choice(TRAITS)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    sidekick_gender = args.sidekick_gender or rng.choice(["girl", "boy"])
    sidekick_name = args.sidekick_name or _pick_name(rng, sidekick_gender, avoid=hero_name)

    if hero_gender == "girl" and hero_name in BOY_NAMES:
        raise StoryError(explain_gender(hero_name, hero_gender))
    if hero_gender == "boy" and hero_name in GIRL_NAMES:
        raise StoryError(explain_gender(hero_name, hero_gender))
    if sidekick_gender == "girl" and sidekick_name in BOY_NAMES:
        raise StoryError(explain_gender(sidekick_name, sidekick_gender))
    if sidekick_gender == "boy" and sidekick_name in GIRL_NAMES:
        raise StoryError(explain_gender(sidekick_name, sidekick_gender))

    return StoryParams(
        plan=plan_id,
        helper=helper_id,
        place=place_id,
        clue=clue_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    missing = []
    if params.plan not in PLANS:
        missing.append(f"plan={params.plan}")
    if params.helper not in HELPERS:
        missing.append(f"helper={params.helper}")
    if params.place not in PLACES:
        missing.append(f"place={params.place}")
    if params.clue not in CLUES:
        missing.append(f"clue={params.clue}")
    if params.trait not in TRAITS:
        missing.append(f"trait={params.trait}")
    if missing:
        raise StoryError("(Invalid story params: " + ", ".join(missing) + ")")

    plan = PLANS[params.plan]
    helper = HELPERS[params.helper]
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    if not combo_valid(plan, helper, place, clue):
        raise StoryError(explain_combo(plan, helper, place, clue))

    world = tell(
        plan=plan,
        helper_cfg=helper,
        place=place,
        clue=clue,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        sidekick_name=params.sidekick_name,
        sidekick_gender=params.sidekick_gender,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name).replace("sidekick", params.sidekick_name),
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
        print(f"{len(combos)} compatible (plan, helper, place, clue) combos:\n")
        for plan, helper, place, clue in combos:
            print(f"  {plan:13} {helper:11} {place:11} {clue}")
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
            header = f"### {p.hero_name} & {p.sidekick_name}: {p.plan} at {p.place} ({outcome_of_trait(p.trait)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
