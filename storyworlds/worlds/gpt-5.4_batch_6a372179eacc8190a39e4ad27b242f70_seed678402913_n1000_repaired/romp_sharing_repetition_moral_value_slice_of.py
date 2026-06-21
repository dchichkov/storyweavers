#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/romp_sharing_repetition_moral_value_slice_of.py
===========================================================================

A tiny slice-of-life storyworld about two children, one plaything, and the
difference between keeping fun to yourself and sharing it. The stories revolve
around a romp: one child starts a lively game with a toy that only one child can
use at a time, the other child wants a turn, and a simple turn-taking pattern
changes the whole afternoon.

The world model tracks a few physical meters (laps, waiting, sharing) and a few
emotional memes (joy, envy, patience, fairness, kindness). The prose is driven
from the simulated state: if a child keeps the toy too long, the other child's
sadness grows; if turns are set up, both children relax and the romp becomes a
shared game.

Run it
------
    python storyworlds/worlds/gpt-5.4/romp_sharing_repetition_moral_value_slice_of.py
    python storyworlds/worlds/gpt-5.4/romp_sharing_repetition_moral_value_slice_of.py --place courtyard --toy scooter
    python storyworlds/worlds/gpt-5.4/romp_sharing_repetition_moral_value_slice_of.py --toy scooter --place garden
    python storyworlds/worlds/gpt-5.4/romp_sharing_repetition_moral_value_slice_of.py --all
    python storyworlds/worlds/gpt-5.4/romp_sharing_repetition_moral_value_slice_of.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/romp_sharing_repetition_moral_value_slice_of.py --json
    python storyworlds/worlds/gpt-5.4/romp_sharing_repetition_moral_value_slice_of.py --verify
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

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PACKAGE_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
GENEROUS_TRAITS = {"gentle", "kind", "generous"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    single_user: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    surface: str
    indoor: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    motion: str
    turn_unit: str
    requires: set[str] = field(default_factory=set)
    chant: str = ""
    single_user: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    label: str
    sense: int
    shared: bool
    cue: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        return [e for e in self.entities.values() if e.role in {"holder", "waiter"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
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


def _r_waiting_hurts(world: World) -> list[str]:
    out: list[str] = []
    holder = world.entities.get("holder")
    waiter = world.entities.get("waiter")
    toy = world.entities.get("toy")
    if not holder or not waiter or not toy:
        return out
    if toy.meters["busy"] < THRESHOLD or toy.meters["shared"] >= THRESHOLD:
        return out
    if waiter.meters["waiting"] < THRESHOLD:
        return out
    sig = ("waiting_hurts", int(waiter.meters["waiting"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    waiter.memes["sad"] += 1
    waiter.memes["envy"] += 1
    holder.memes["proud"] += 0.5
    out.append("__waiting__")
    return out


def _r_sharing_soothes(world: World) -> list[str]:
    out: list[str] = []
    holder = world.entities.get("holder")
    waiter = world.entities.get("waiter")
    toy = world.entities.get("toy")
    if not holder or not waiter or not toy:
        return out
    if toy.meters["shared"] < THRESHOLD:
        return out
    sig = ("sharing_soothes", int(toy.meters["shared"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    holder.memes["kindness"] += 1
    holder.memes["fairness"] += 1
    waiter.memes["relief"] += 1
    waiter.memes["joy"] += 1
    waiter.memes["sad"] = 0.0
    out.append("__shared__")
    return out


def _r_repetition_builds_romp(world: World) -> list[str]:
    out: list[str] = []
    toy = world.entities.get("toy")
    if not toy:
        return out
    if toy.meters["turns"] < 3:
        return out
    sig = ("repetition_builds_romp",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["togetherness"] += 1
    toy.meters["romp"] += 1
    out.append("__romp__")
    return out


CAUSAL_RULES = [
    Rule(name="waiting_hurts", tag="social", apply=_r_waiting_hurts),
    Rule(name="sharing_soothes", tag="social", apply=_r_sharing_soothes),
    Rule(name="repetition_builds_romp", tag="social", apply=_r_repetition_builds_romp),
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
            if sent.startswith("__"):
                continue
            world.say(sent)
    return produced


PLACES = {
    "courtyard": Place(
        id="courtyard",
        label="the courtyard",
        scene="The little courtyard behind the building was warm with late afternoon light.",
        surface="smooth",
        indoor=False,
        tags={"outside"},
    ),
    "park_path": Place(
        id="park_path",
        label="the park path",
        scene="At the park, a flat path curved past the swings and the flower beds.",
        surface="smooth",
        indoor=False,
        tags={"outside"},
    ),
    "hallway": Place(
        id="hallway",
        label="the hallway",
        scene="The apartment hallway was long, clean, and shiny enough for wheels to whisper over it.",
        surface="smooth",
        indoor=True,
        tags={"inside"},
    ),
    "garden": Place(
        id="garden",
        label="the garden path",
        scene="The garden path was bumpy with little stones and roots poking through the dirt.",
        surface="bumpy",
        indoor=False,
        tags={"outside"},
    ),
}

TOYS = {
    "scooter": Toy(
        id="scooter",
        label="scooter",
        phrase="a bright red scooter",
        motion="zipped in a fast little curve",
        turn_unit="lap",
        requires={"smooth"},
        chant="One lap for you, one lap for me.",
        single_user=True,
        tags={"scooter", "wheels"},
    ),
    "ride_car": Toy(
        id="ride_car",
        label="ride-on car",
        phrase="a small yellow ride-on car",
        motion="rolled along with cheerful squeaks",
        turn_unit="ride",
        requires={"smooth"},
        chant="One ride for you, one ride for me.",
        single_user=True,
        tags={"car", "wheels"},
    ),
    "hopping_horse": Toy(
        id="hopping_horse",
        label="bouncy horse",
        phrase="a blue bouncy horse",
        motion="bounced boing-boing across the floor",
        turn_unit="bounce",
        requires={"smooth"},
        chant="Three bounces for you, three bounces for me.",
        single_user=True,
        tags={"bouncy", "inside_play"},
    ),
}

PLANS = {
    "take_turns": Plan(
        id="take_turns",
        label="take turns",
        sense=3,
        shared=True,
        cue="Let's make a pattern and keep switching.",
        qa_text="They took turns, so each child got a fair chance to play.",
        tags={"sharing", "turns"},
    ),
    "counting_turns": Plan(
        id="counting_turns",
        label="counting turns",
        sense=3,
        shared=True,
        cue="We can count out loud and switch every time we finish.",
        qa_text="They counted each turn and switched at the end, which kept the sharing fair.",
        tags={"sharing", "counting"},
    ),
    "keep_it": Plan(
        id="keep_it",
        label="keep it all afternoon",
        sense=1,
        shared=False,
        cue="One child simply keeps the toy.",
        qa_text="One child kept the toy and the other child was left out.",
        tags={"selfish"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["gentle", "kind", "generous", "hasty", "proud", "stubborn"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]


def works_in(place: Place, toy: Toy) -> bool:
    return place.surface in toy.requires


def sensible_plans() -> list[Plan]:
    return [p for p in PLANS.values() if p.sense >= SENSE_MIN and p.shared]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for toy_id, toy in TOYS.items():
            if works_in(place, toy) and sensible_plans():
                combos.append((place_id, toy_id))
    return combos


def shares_early(trait: str) -> bool:
    return trait in GENEROUS_TRAITS


def explain_rejection(place: Place, toy: Toy) -> str:
    return (
        f"(No story: {toy.phrase} needs a smooth place for safe zooming and turn-taking, "
        f"but {place.label} is {place.surface}. Pick a smoother place like the courtyard, "
        f"the park path, or the hallway.)"
    )


def explain_plan(plan_id: str) -> str:
    plan = PLANS[plan_id]
    better = " / ".join(sorted(p.id for p in sensible_plans()))
    return (
        f"(Refusing plan '{plan_id}': it is not a sharing plan "
        f"(sense={plan.sense} < {SENSE_MIN} or shared={plan.shared}). "
        f"Try {better}.)"
    )


@dataclass
class StoryParams:
    place: str
    toy: str
    plan: str
    holder_name: str
    holder_gender: str
    waiter_name: str
    waiter_gender: str
    helper: str
    holder_trait: str
    rounds: int = 3
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="courtyard",
        toy="scooter",
        plan="take_turns",
        holder_name="Tom",
        holder_gender="boy",
        waiter_name="Lily",
        waiter_gender="girl",
        helper="mother",
        holder_trait="proud",
        rounds=3,
    ),
    StoryParams(
        place="park_path",
        toy="ride_car",
        plan="counting_turns",
        holder_name="Mia",
        holder_gender="girl",
        waiter_name="Ben",
        waiter_gender="boy",
        helper="grandfather",
        holder_trait="gentle",
        rounds=4,
    ),
    StoryParams(
        place="hallway",
        toy="hopping_horse",
        plan="take_turns",
        holder_name="Noah",
        holder_gender="boy",
        waiter_name="Eli",
        waiter_gender="boy",
        helper="father",
        holder_trait="stubborn",
        rounds=3,
    ),
    StoryParams(
        place="courtyard",
        toy="ride_car",
        plan="counting_turns",
        holder_name="Rose",
        holder_gender="girl",
        waiter_name="Maya",
        waiter_gender="girl",
        helper="grandmother",
        holder_trait="kind",
        rounds=3,
    ),
]


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def predict_waiting(world: World) -> dict:
    sim = world.copy()
    holder = sim.get("holder")
    waiter = sim.get("waiter")
    toy = sim.get("toy")
    toy.meters["busy"] += 1
    waiter.meters["waiting"] += 1
    propagate(sim, narrate=False)
    return {
        "sad": waiter.memes["sad"] >= THRESHOLD,
        "envy": waiter.memes["envy"] >= THRESHOLD,
    }


def introduce(world: World, holder: Entity, waiter: Entity, toy_cfg: Toy) -> None:
    world.say(world.place.scene)
    world.say(
        f"{holder.id} and {waiter.id} came out ready to romp, with loose shoes, quick feet, "
        f"and the feeling that the day still had room for one more game."
    )
    world.say(
        f"Near the step waited {toy_cfg.phrase}, and both children looked at it at the same time."
    )


def first_turn(world: World, holder: Entity, waiter: Entity, toy_cfg: Toy) -> None:
    toy = world.get("toy")
    toy.meters["busy"] += 1
    toy.meters["turns"] += 1
    holder.memes["joy"] += 1
    holder.meters["rides"] += 1
    world.say(
        f'"Mine first!" {holder.id} said, hopping on. Soon {holder.pronoun()} {toy_cfg.motion} '
        f"from one end of {world.place.label} to the other."
    )
    world.say(
        f"{waiter.id} clapped at first, because the start of a romp always looked exciting."
    )


def ask_for_turn(world: World, waiter: Entity, toy_cfg: Toy) -> None:
    waiter.meters["waiting"] += 1
    waiter.memes["desire"] += 1
    world.say(
        f'After one {toy_cfg.turn_unit}, {waiter.id} held out {waiter.pronoun("possessive")} hand. '
        f'"Can I have a turn now?" {waiter.pronoun()} asked.'
    )


def keep_going(world: World, holder: Entity, waiter: Entity, toy_cfg: Toy) -> None:
    toy = world.get("toy")
    toy.meters["busy"] += 1
    holder.meters["rides"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {holder.id} gripped the handles a little tighter and went again. "
        f"{holder.pronoun().capitalize()} {toy_cfg.motion} once more, and this time "
        f"{waiter.id} did not clap."
    )
    if waiter.memes["sad"] >= THRESHOLD:
        world.say(
            f"{waiter.id}'s face grew small and quiet. Standing still while someone else kept going "
            f"did not feel like much fun at all."
        )


def gentle_offer(world: World, holder: Entity, waiter: Entity, helper: Entity, toy_cfg: Toy) -> None:
    world.say(
        f"{helper.label_word.capitalize()} had been watching from nearby. {helper.pronoun().capitalize()} came over "
        f"and crouched between them."
    )
    world.say(
        f'"A romp is bigger when two children can laugh in it," {helper.pronoun()} said. '
        f'"{PLANS[world.facts["plan"].id].cue}"'
    )
    world.say(
        f'{helper.pronoun("possessive").capitalize()} voice was calm, not cross, and it gave the afternoon a place to settle.'
    )


def early_share(world: World, holder: Entity, waiter: Entity, helper: Entity, toy_cfg: Toy) -> None:
    toy = world.get("toy")
    toy.meters["shared"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{holder.id} glanced at {waiter.id}, then at the toy, and the proud little feeling in "
        f"{holder.pronoun('possessive')} chest softened."
    )
    world.say(
        f'"Okay. One {toy_cfg.turn_unit} for me, then one for you," {holder.pronoun()} said before '
        f"{helper.label_word} even had to ask twice."
    )


def guided_share(world: World, holder: Entity, waiter: Entity, toy_cfg: Toy) -> None:
    toy = world.get("toy")
    toy.meters["shared"] += 1
    holder.memes["lesson"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{holder.id} looked at {waiter.id}'s waiting face and finally stepped off."
    )
    world.say(
        f'"You can go next," {holder.pronoun()} said, a little slowly. It was not easy to give up '
        f"something fun in the middle of it, but {holder.pronoun()} did it anyway."
    )


def turn_loop(world: World, holder: Entity, waiter: Entity, toy_cfg: Toy, rounds: int) -> None:
    toy = world.get("toy")
    chant = toy_cfg.chant
    turns_left = max(2, rounds)
    current = waiter
    other = holder
    for i in range(turns_left):
        toy.meters["turns"] += 1
        current.meters["rides"] += 1
        current.memes["joy"] += 1
        current.memes["fairness"] += 0.5
        other.memes["patience"] += 0.5
        if i < turns_left - 1:
            world.say(
                f"{current.id} took {('that' if i == 0 else 'the next')} {toy_cfg.turn_unit}, and both children "
                f"said together, \"{chant}\""
            )
        else:
            world.say(
                f"Then {current.id} took one more {toy_cfg.turn_unit}, and by then the words "
                f"\"{chant}\" had become part of the game itself."
            )
        current, other = other, current
    propagate(world, narrate=False)


def ending(world: World, holder: Entity, waiter: Entity, helper: Entity, toy_cfg: Toy) -> None:
    toy = world.get("toy")
    if toy.meters["romp"] >= THRESHOLD:
        world.say(
            f"Soon the whole place sounded different: wheels, feet, little laughs, and the same small chant "
            f"coming back again and again."
        )
    world.say(
        f"When the light thinned and it was time to go in, neither child felt left out."
    )
    world.say(
        f"{holder.id} and {waiter.id} walked back beside {helper.label_word}, carrying {toy_cfg.label} between them."
    )
    world.say(
        f"They had learned something plain and true: fun grows when it is shared, and a good romp lasts longer "
        f"when everyone gets a turn."
    )


def tell(
    place: Place,
    toy_cfg: Toy,
    plan: Plan,
    holder_name: str,
    holder_gender: str,
    waiter_name: str,
    waiter_gender: str,
    helper_type: str,
    holder_trait: str,
    rounds: int,
) -> World:
    world = World(place)
    holder = world.add(
        Entity(
            id=holder_name,
            kind="character",
            type=holder_gender,
            role="holder",
            traits=[holder_trait],
            label=holder_name,
        )
    )
    waiter = world.add(
        Entity(
            id=waiter_name,
            kind="character",
            type=waiter_gender,
            role="waiter",
            traits=["hopeful"],
            label=waiter_name,
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
        )
    )
    toy = world.add(
        Entity(
            id="toy",
            kind="thing",
            type="toy",
            label=toy_cfg.label,
            phrase=toy_cfg.phrase,
            single_user=toy_cfg.single_user,
            tags=set(toy_cfg.tags),
        )
    )

    holder.memes["ownership"] += 1
    world.facts["plan"] = plan

    introduce(world, holder, waiter, toy_cfg)
    world.para()
    first_turn(world, holder, waiter, toy_cfg)
    ask_for_turn(world, waiter, toy_cfg)

    pred = predict_waiting(world)
    world.facts["predicted_sad"] = pred["sad"]

    world.para()
    if shares_early(holder_trait):
        early_share(world, holder, waiter, helper, toy_cfg)
        world.facts["outcome"] = "self_shared"
    else:
        keep_going(world, holder, waiter, toy_cfg)
        gentle_offer(world, holder, waiter, helper, toy_cfg)
        guided_share(world, holder, waiter, toy_cfg)
        world.facts["outcome"] = "guided_share"

    world.para()
    turn_loop(world, holder, waiter, toy_cfg, rounds)
    ending(world, holder, waiter, helper, toy_cfg)

    world.facts.update(
        holder=holder,
        waiter=waiter,
        helper=helper,
        toy_cfg=toy_cfg,
        place=place,
        toy=toy,
        shared=toy.meters["shared"] >= THRESHOLD,
        rounds=rounds,
        chant=toy_cfg.chant,
        moral="fun grows when it is shared",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    holder = f["holder"]
    waiter = f["waiter"]
    toy_cfg = f["toy_cfg"]
    place = f["place"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the word "romp" and shows two children learning to share {toy_cfg.label}.',
        f"Tell a gentle everyday story set at {place.label} where {holder.id} and {waiter.id} both want the same {toy_cfg.label}, and repetition helps them learn fairness.",
        f'Write a short moral story about taking turns, using a repeated line during play, and ending with the idea that shared fun grows bigger.',
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    holder = f["holder"]
    waiter = f["waiter"]
    helper = f["helper"]
    toy_cfg = f["toy_cfg"]
    place = f["place"]
    rounds = f["rounds"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(holder, waiter)}, {holder.id} and {waiter.id}, playing at {place.label}. "
            f"{helper.label_word.capitalize()} also helps them when the play starts to feel unfair.",
        ),
        (
            f"What did the children want to play with?",
            f"They both wanted the same {toy_cfg.label}. It was fun to ride and lively enough to turn the whole afternoon into a romp.",
        ),
        (
            f"Why did {waiter.id} feel sad in the middle of the story?",
            f"{waiter.id} had to stand and wait while {holder.id} kept the {toy_cfg.label} for another turn. "
            f"Being left out made the game feel small instead of shared.",
        ),
    ]
    if f["outcome"] == "self_shared":
        qa.append(
            (
                f"Did {holder.id} share right away?",
                f"Almost. {holder.id} noticed that {waiter.id} was waiting and chose to soften before the problem grew bigger. "
                f"That early choice kept the afternoon gentle.",
            )
        )
    else:
        qa.append(
            (
                f"How did {helper.label_word} help?",
                f"{helper.label_word.capitalize()} did not scold. {helper.pronoun().capitalize()} calmly suggested a turn-taking pattern, which gave both children a fair way to keep playing.",
            )
        )
    qa.append(
        (
            "What was repeated during the game?",
            f'The children kept saying, "{f["chant"]}" while they switched. '
            f"The repeated line helped them remember whose turn came next.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"They had shared the {toy_cfg.label} for {rounds} playful rounds, and neither child felt left out at the end. "
            f"The final image of them carrying it together shows that the toy had become something shared instead of fought over.",
        )
    )
    qa.append(
        (
            "What is the lesson of the story?",
            f'The lesson is that {f["moral"]}. The children learned that a fair game lasts longer and feels better for everyone.',
        )
    )
    return qa


KNOWLEDGE = {
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting someone else use or enjoy something too. It helps everyone feel included.",
        )
    ],
    "turns": [
        (
            "What does taking turns mean?",
            "Taking turns means one person goes, then another person goes. It is a fair way to share when only one child can use something at a time.",
        )
    ],
    "counting": [
        (
            "Why can counting help children share?",
            "Counting makes the pattern clear, so everyone knows when a turn starts and ends. That helps the sharing feel fair.",
        )
    ],
    "scooter": [
        (
            "What is a scooter?",
            "A scooter is a small ride-on toy with wheels and handlebars. A child can push with one foot and glide along.",
        )
    ],
    "car": [
        (
            "What is a ride-on car?",
            "A ride-on car is a small toy car that a child can sit on and roll along. It is fun, but usually only one child can use it at once.",
        )
    ],
    "bouncy": [
        (
            "Why is a bouncy toy fun?",
            "A bouncy toy feels springy and silly, so it makes children laugh as they move. It turns ordinary movement into playful motion.",
        )
    ],
    "wheels": [
        (
            "Why do wheels move best on smooth ground?",
            "Wheels roll more easily on smooth ground because there are fewer bumps to catch them. That makes the ride safer and steadier.",
        )
    ],
    "inside_play": [
        (
            "Why do some toys stay inside?",
            "Some toys are best indoors because they work on smooth floors and can get dirty or wobbly outside. A calm indoor place helps them move safely.",
        )
    ],
}
KNOWLEDGE_ORDER = ["sharing", "turns", "counting", "scooter", "car", "bouncy", "wheels", "inside_play"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"sharing"}
    tags |= set(world.facts["plan"].tags)
    tags |= set(world.facts["toy_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.single_user:
            bits.append("single_user=True")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
valid(Place, Toy) :- place(Place), toy(Toy), requires(Toy, Surface), surface(Place, Surface).
sensible(Plan)    :- plan(Plan), sense(Plan, S), sense_min(M), S >= M, shared_plan(Plan).

% --- outcome model ---------------------------------------------------------
self_shared  :- trait(T), generous_trait(T).
guided_share :- trait(T), not generous_trait(T).

outcome(self_shared)  :- self_shared.
outcome(guided_share) :- guided_share.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("surface", place_id, place.surface))
    for toy_id, toy in TOYS.items():
        lines.append(asp.fact("toy", toy_id))
        for req in sorted(toy.requires):
            lines.append(asp.fact("requires", toy_id, req))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("sense", plan_id, plan.sense))
        if plan.shared:
            lines.append(asp.fact("shared_plan", plan_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for trait in sorted(GENEROUS_TRAITS):
        lines.append(asp.fact("generous_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_plans() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(plan for (plan,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("trait", params.holder_trait)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "self_shared" if shares_early(params.holder_trait) else "guided_share"


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

    c_plans = set(asp_sensible_plans())
    p_plans = {p.id for p in sensible_plans()}
    if c_plans == p_plans:
        print(f"OK: sensible plans match ({sorted(c_plans)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible plans: clingo={sorted(c_plans)} python={sorted(p_plans)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test story came out empty.")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: one toy, two children, repeated turns, and a sharing lesson."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--rounds", type=int, choices=[3, 4], help="how many playful rounds the turn-taking loop gets")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.toy:
        place = PLACES[args.place]
        toy = TOYS[args.toy]
        if not works_in(place, toy):
            raise StoryError(explain_rejection(place, toy))
    if args.plan and args.plan in PLANS and (PLANS[args.plan].sense < SENSE_MIN or not PLANS[args.plan].shared):
        raise StoryError(explain_plan(args.plan))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.toy is None or c[1] == args.toy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, toy_id = rng.choice(sorted(combos))
    plan_id = args.plan or rng.choice(sorted(p.id for p in sensible_plans()))
    holder_gender = rng.choice(["girl", "boy"])
    waiter_gender = rng.choice(["girl", "boy"])
    holder_name = _pick_name(rng, holder_gender)
    waiter_name = _pick_name(rng, waiter_gender, avoid=holder_name)
    helper = args.helper or rng.choice(HELPERS)
    holder_trait = rng.choice(TRAITS)
    rounds = args.rounds if args.rounds is not None else rng.choice([3, 4])
    return StoryParams(
        place=place_id,
        toy=toy_id,
        plan=plan_id,
        holder_name=holder_name,
        holder_gender=holder_gender,
        waiter_name=waiter_name,
        waiter_gender=waiter_gender,
        helper=helper,
        holder_trait=holder_trait,
        rounds=rounds,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.toy not in TOYS:
        raise StoryError(f"(Unknown toy: {params.toy})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    place = PLACES[params.place]
    toy_cfg = TOYS[params.toy]
    plan = PLANS[params.plan]

    if not works_in(place, toy_cfg):
        raise StoryError(explain_rejection(place, toy_cfg))
    if plan.sense < SENSE_MIN or not plan.shared:
        raise StoryError(explain_plan(plan.id))

    world = tell(
        place=place,
        toy_cfg=toy_cfg,
        plan=plan,
        holder_name=params.holder_name,
        holder_gender=params.holder_gender,
        waiter_name=params.waiter_name,
        waiter_gender=params.waiter_gender,
        helper_type=params.helper,
        holder_trait=params.holder_trait,
        rounds=params.rounds,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible plans: {', '.join(asp_sensible_plans())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, toy) combos:\n")
        for place, toy in combos:
            print(f"  {place:10} {toy}")
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
            header = f"### {p.holder_name} and {p.waiter_name}: {p.toy} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
