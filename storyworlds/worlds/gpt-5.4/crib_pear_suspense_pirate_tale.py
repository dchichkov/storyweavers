#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crib_pear_suspense_pirate_tale.py
============================================================

A standalone storyworld for a suspenseful pirate-style nursery tale: while two
children are playing pirates, a pear rolls under a baby's crib and the dark
space feels like a treasure cave. One child is tempted to fetch it the wrong
way; a wiser warning, a safe grown-up method, and the baby's sleep determine
how the story turns out.

The world is intentionally small and classical:

* typed entities with physical meters and emotional memes
* a tiny forward-chaining rule engine
* a Python reasonableness gate plus an inline ASP twin
* prose driven from simulated state rather than slot-swapped text
* three Q&A sets grounded in world state

Run it
------
    python storyworlds/worlds/gpt-5.4/crib_pear_suspense_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/crib_pear_suspense_pirate_tale.py --spot deep --rescue grabber
    python storyworlds/worlds/gpt-5.4/crib_pear_suspense_pirate_tale.py --rescue hand
    python storyworlds/worlds/gpt-5.4/crib_pear_suspense_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/crib_pear_suspense_pirate_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/crib_pear_suspense_pirate_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/crib_pear_suspense_pirate_tale.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or anywhere else. This file lives one directory deeper than
# most worlds, so we go up three levels to the storyworlds/ package directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "cautious", "gentle", "thoughtful", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "baby_girl"}
        male = {"boy", "father", "dad", "man", "baby_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    titles: tuple[str, str]
    goal: str
    cave_word: str
    send_off: str


@dataclass
class Spot:
    id: str
    label: str
    depth: int
    gloom: str
    mouth: str
    under_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RiskyMove:
    id: str
    label: str
    sense: int
    reach: int
    noise: int
    crib_force: int
    pear_bruise: int
    line: str
    fail_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rescue:
    id: str
    label: str
    sense: int
    reach: int
    quiet: int
    text: str
    qa_text: str
    gift: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_rattle(world: World) -> list[str]:
    out: list[str] = []
    crib = world.get("crib")
    baby = world.get("baby")
    if crib.meters["rattled"] >= THRESHOLD:
        sig = ("rattle", "crib")
        if sig not in world.fired:
            world.fired.add(sig)
            baby.meters["startled"] += 1
            for kid in world.kids():
                kid.memes["fear"] += 1
            out.append("__rattle__")
    return out


def _r_wake(world: World) -> list[str]:
    out: list[str] = []
    baby = world.get("baby")
    sleeper = int(world.facts["sleeper"])
    if baby.meters["startled"] >= sleeper and baby.meters["awake"] < THRESHOLD:
        sig = ("wake", "baby")
        if sig not in world.fired:
            world.fired.add(sig)
            baby.meters["awake"] += 1
            baby.memes["cry"] += 1
            for kid in world.kids():
                kid.memes["guilt"] += 1
                kid.memes["fear"] += 1
            out.append("__wake__")
    return out


def _r_bruise(world: World) -> list[str]:
    out: list[str] = []
    pear = world.get("pear")
    if pear.meters["bumped"] >= THRESHOLD and pear.meters["bruised"] < THRESHOLD:
        sig = ("bruise", "pear")
        if sig not in world.fired:
            world.fired.add(sig)
            pear.meters["bruised"] += 1
            out.append("__bruise__")
    return out


CAUSAL_RULES = [
    Rule("rattle", "physical", _r_rattle),
    Rule("wake", "social", _r_wake),
    Rule("bruise", "physical", _r_bruise),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def sensible_rescues() -> list[Rescue]:
    return [r for r in RESCUES.values() if r.sense >= SENSE_MIN]


def move_can_reach(move: RiskyMove, spot: Spot) -> bool:
    return move.reach >= spot.depth


def rescue_can_reach(rescue: Rescue, spot: Spot) -> bool:
    return rescue.reach >= spot.depth


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme in THEMES:
        for spot_id, spot in SPOTS.items():
            for move_id, move in RISKY_MOVES.items():
                if not move_can_reach(move, spot):
                    continue
                for rescue_id, rescue in RESCUES.items():
                    if rescue.sense >= SENSE_MIN and rescue_can_reach(rescue, spot):
                        combos.append((theme, spot_id, move_id, rescue_id))
    return combos


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (3.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def outcome_of(params: "StoryParams") -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        quiet = RESCUES[params.rescue].quiet
        return "averted_asleep" if quiet >= params.sleeper else "averted_woke"
    move = RISKY_MOVES[params.risky]
    rescue = RESCUES[params.rescue]
    noise = move.noise
    if rescue.quiet < params.sleeper:
        noise += 1
    return "woke" if noise >= params.sleeper else "slept"


def explain_reach(kind: str, label: str, spot: Spot) -> str:
    return (
        f"(No story: {label} cannot reach {spot.label}. The pear is {spot.under_text}, "
        f"so choose a {kind} that can actually reach that far.)"
    )


def explain_rescue(rescue_id: str) -> str:
    r = RESCUES[rescue_id]
    better = ", ".join(sorted(x.id for x in sensible_rescues()))
    return (
        f"(Refusing rescue '{rescue_id}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a calmer, safer rescue such as {better}.)"
    )


def predict_trouble(world: World, spot: Spot, move: RiskyMove) -> dict:
    sim = world.copy()
    _do_risky(sim, spot, move, narrate=False)
    baby = sim.get("baby")
    pear = sim.get("pear")
    return {
        "awake": baby.meters["awake"] >= THRESHOLD,
        "startled": baby.meters["startled"],
        "bruised": pear.meters["bruised"] >= THRESHOLD,
    }


def _do_risky(world: World, spot: Spot, move: RiskyMove, narrate: bool = True) -> None:
    crib = world.get("crib")
    pear = world.get("pear")
    crib.meters["rattled"] += move.crib_force
    pear.meters["bumped"] += move.pear_bruise
    world.facts["attempted_risky"] = True
    propagate(world, narrate=narrate)


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    first_title, second_title = theme.titles
    world.say(
        f"On a soft afternoon, {a.id} and {b.id} turned the hallway outside the nursery into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{first_title} {a.id} and {second_title} {b.id}!" {a.id} whispered. '
        f'"Let\'s find {theme.goal}."'
    )


def snack_rolls(world: World, a: Entity, b: Entity, baby: Entity, spot: Spot) -> None:
    pear = world.get("pear")
    pear.meters["hidden"] = 1
    world.say(
        f"Inside the nursery, {baby.id} was asleep in the crib, one fist tucked under {baby.pronoun('possessive')} cheek."
    )
    world.say(
        f"On the dresser sat a small fruit bowl for later. Then one round green pear wobbled, rolled off, "
        f"and slipped {spot.under_text}."
    )
    world.say(
        f"The floor went quiet again. Under the crib, the pear looked like a lost bit of treasure."
    )
    a.memes["desire"] += 1
    b.memes["wonder"] += 1


def dark_need(world: World, b: Entity, theme: Theme, spot: Spot) -> None:
    world.say(
        f"But the {theme.cave_word} under the crib was {spot.gloom}. You could only see {spot.mouth} before the shadows swallowed the rest."
    )
    world.say(
        f'{b.id} leaned closer. "It\'s in there all right," {b.pronoun()} whispered.'
    )


def tempt(world: World, a: Entity, move: RiskyMove) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id}\'s eyes shone. "Treasure should not be left in a cave," {a.pronoun()} said. '
        f'"I can get it with {move.label}."'
    )


def warn(world: World, b: Entity, a: Entity, move: RiskyMove, spot: Spot, parent: Entity) -> None:
    pred = predict_trouble(world, spot, move)
    b.memes["caution"] += 1
    world.facts["predicted_awake"] = pred["awake"]
    world.facts["predicted_bruised"] = pred["bruised"]
    extra = "and make the crib creak"
    if pred["awake"]:
        extra += f", and then {world.get('baby').id} could wake up crying"
    world.say(
        f'{b.id} caught {a.id}\'s sleeve. "No, {a.id}. If you do that, you could {extra}," {b.pronoun()} said. '
        f'"{parent.label_word.capitalize()} should help with this one."'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} opened {a.pronoun("possessive")} mouth to argue, then looked at the sleeping crib and let out a small breath. '
        f'"All right," {a.pronoun()} whispered. "We\'ll ask {parent.label_word}."'
    )


def defy(world: World, a: Entity, b: Entity, move: RiskyMove) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"Just one quick try," {a.id} whispered. {move.line}'
    )
    if b.memes["caution"] >= 6:
        world.say(
            f"{b.id} pressed both hands over {b.pronoun('possessive')} mouth, already afraid of the sound."
        )


def risky_attempt(world: World, a: Entity, b: Entity, baby: Entity, spot: Spot, move: RiskyMove) -> None:
    _do_risky(world, spot, move)
    crib = world.get("crib")
    pear = world.get("pear")
    world.say(
        f"For one heartbeat, nothing happened. Then the crib gave a tiny wooden creak."
    )
    if crib.meters["rattled"] >= THRESHOLD:
        world.say(
            f"The room felt suddenly much smaller. {a.id} and {b.id} stood still as sailors in a storm listening for the next sound."
        )
    if pear.meters["bruised"] >= THRESHOLD:
        world.say(
            "Under the crib, the pear bumped against a leg and came away with a soft brown bruise."
        )
    if baby.meters["awake"] >= THRESHOLD:
        world.say(
            f"{baby.id}'s eyes flew open, and a cry rose sharp and surprised in the dark."
        )
    else:
        world.say(
            f"{baby.id} stirred, sighed once, and kept sleeping."
        )


def rescue(world: World, parent: Entity, baby: Entity, rescue_cfg: Rescue, spot: Spot) -> None:
    pear = world.get("pear")
    pear.meters["hidden"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came in at once, understood the whole room with one glance, and {rescue_cfg.text}"
    )
    world.say(
        f"In another breath, the pear was back in the light and the crib stood still again."
    )
    if baby.meters["awake"] >= THRESHOLD:
        baby.memes["comfort"] += 1
        world.say(
            f"{parent.label_word.capitalize()} laid one gentle hand on the crib rail until {baby.id}'s crying slowed to little hiccups."
        )
    else:
        world.say(
            f"{baby.id} slept on, warm and quiet in the crib."
        )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, baby: Entity, move: RiskyMove) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    line = "Cribs are for babies to sleep in, not for climbing or shaking"
    if baby.meters["awake"] >= THRESHOLD:
        world.say(
            f'{parent.label_word.capitalize()} knelt beside them and kept {parent.pronoun("possessive")} voice soft. '
            f'"I am glad you stayed here and let me help," {parent.pronoun()} said. '
            f'"But remember: {line}. Dark places can wait for a calm grown-up hand."'
        )
    else:
        world.say(
            f'{parent.label_word.capitalize()} smiled a little, still whispering. '
            f'"Thank you for stopping before the room turned louder," {parent.pronoun()} said. '
            f'"Remember: {line}. If treasure rolls under a crib, call me."'
        )
    world.say(
        f"{a.id} nodded first. Then {b.id} nodded too, both of them looking at the quiet crib as if it were a real captain's rule."
    )
    world.facts["lesson_line"] = line
    world.facts["risky_label"] = move.label


def safe_gift(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme, rescue_cfg: Rescue) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next day, {parent.label_word} had a surprise: {rescue_cfg.gift}."
    )
    world.say(
        f'"For treasure hunts away from the crib," {parent.pronoun()} said with a smile.'
    )
    world.say(
        f"{a.id} took the tool, {b.id} held the little light, and together they {theme.send_off}."
    )


THEMES = {
    "pirates": Theme(
        "pirates",
        "a hush-hush pirate harbor",
        "A blanket over two chairs was their cabin, a cardboard tube was their spyglass, "
        "and a blue scarf on the floor was the sea.",
        ("Captain", "Scout"),
        "the lost fruit treasure",
        "cave",
        "sailed down the hall toward a new safe adventure",
    ),
    "corsairs": Theme(
        "corsairs",
        "a moonlit pirate deck",
        "A laundry basket was their ship, a wooden spoon was their mast, "
        "and a striped towel was the rolling sea.",
        ("Captain", "Lookout"),
        "the hidden green treasure",
        "cavern",
        "set off to hunt pretend treasure where no baby was sleeping",
    ),
}

SPOTS = {
    "shallow": Spot(
        "shallow",
        "the front edge under the crib",
        1,
        "dim but not fully black",
        "the pear's pale curve near the front rail",
        "under the front edge of the crib",
        tags={"crib", "dark"},
    ),
    "deep": Spot(
        "deep",
        "the far shadow under the crib",
        2,
        "dark as the inside of a box",
        "only two crib legs and a stripe of floor",
        "into the far shadow under the crib",
        tags={"crib", "dark"},
    ),
}

RISKY_MOVES = {
    "hand": RiskyMove(
        "hand",
        "just one arm",
        2,
        1,
        1,
        0,
        0,
        "He dropped to his knees and reached under the crib with bare fingers.",
        "but his fingers could not reach far enough",
        tags={"reach", "crib"},
    ),
    "hook": RiskyMove(
        "hook",
        "the cardboard-tube hook from the game",
        2,
        2,
        2,
        1,
        1,
        "She lowered the cardboard tube and nudged around with pirate determination.",
        "but the tube bumped the crib and only shoved the pear farther",
        tags={"tool", "crib"},
    ),
    "shake": RiskyMove(
        "shake",
        "a hard tug on the crib rail",
        1,
        2,
        3,
        2,
        1,
        "He put both hands on the crib rail as if he could jiggle the treasure loose.",
        "but the crib rattled before the pear came free",
        tags={"unsafe", "crib"},
    ),
}

RESCUES = {
    "hand": Rescue(
        "hand",
        "a quiet grown-up hand",
        2,
        1,
        3,
        "knelt down, reached under with a calm hand, and rolled the pear gently back",
        "reached under the crib with a calm hand and rolled the pear back out",
        "a tiny pocket flashlight and a cloth treasure bag",
        tags={"help", "pear"},
    ),
    "grabber": Rescue(
        "grabber",
        "a reacher claw",
        3,
        2,
        3,
        "fetched the long grabber from the closet and pinched the pear carefully by its stem",
        "used the long grabber to pinch the pear carefully by its stem",
        "a child-safe grabber claw painted gold and a little lantern",
        tags={"grabber", "help", "pear"},
    ),
    "broom": Rescue(
        "broom",
        "a broom handle",
        1,
        2,
        1,
        "used a broom handle from the hall closet to poke at the pear",
        "poked at the pear with a broom handle",
        "nothing at all",
        tags={"tool"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
BABY_GIRL_NAMES = ["Poppy", "Mimi", "June", "Ivy", "Tess"]
BABY_BOY_NAMES = ["Owen", "Milo", "Ned", "Jude", "Otis"]
TRAITS = ["careful", "cautious", "gentle", "thoughtful", "curious", "bold", "sensible"]


@dataclass
class StoryParams:
    theme: str
    spot: str
    risky: str
    rescue: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    baby_name: str
    baby_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 5
    sleeper: int = 2
    seed: Optional[int] = None


KNOWLEDGE = {
    "crib": [(
        "What is a crib?",
        "A crib is a small bed with rails for a baby. It is made to keep a baby safe while sleeping."
    )],
    "pear": [(
        "What is a pear?",
        "A pear is a sweet fruit with soft flesh inside. It bruises easily if it gets bumped."
    )],
    "dark": [(
        "Why can dark places feel spooky?",
        "In the dark, you cannot see very much, so your brain starts wondering what might happen next. That can make a quiet room feel suspenseful."
    )],
    "grabber": [(
        "What is a reacher claw?",
        "A reacher claw is a long tool that helps you pick something up from far away. It lets a grown-up get an object without climbing or stretching dangerously."
    )],
    "help": [(
        "Why should children ask a grown-up for help around a crib?",
        "A crib must stay steady and calm for the baby inside. A grown-up can reach safely without shaking it."
    )],
    "unsafe": [(
        "Why is it a bad idea to shake a crib?",
        "Shaking a crib can scare the baby and make the crib wobble. Baby furniture should stay still and gentle."
    )],
}

KNOWLEDGE_ORDER = ["crib", "pear", "dark", "grabber", "help", "unsafe"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b = f["instigator"], f["cautioner"]
    baby = f["baby"]
    rescue_cfg = f["rescue_cfg"]
    spot = f["spot_cfg"]
    theme = f["theme"]
    outcome = f["outcome"]
    base = (
        f'Write a suspenseful pirate-style story for a 3-to-5-year-old where a pear rolls under a crib while {baby.id} is sleeping.'
    )
    if outcome.startswith("averted"):
        return [
            base,
            f"Tell a gentle near-miss story where {a.id} wants to reach into {spot.label}, but {b.id} warns {a.pronoun('object')} and they ask a grown-up instead.",
            f'Write a quiet pirate tale with suspense, a crib, and a pear, ending with {rescue_cfg.label} and a safe treasure hunt away from the crib.',
        ]
    if outcome == "woke":
        return [
            base,
            f"Tell a suspense story where {a.id} ignores a warning, the crib creaks, and {baby.id} wakes up before {a.pronoun('possessive')} {f['parent'].label_word} safely gets the pear back.",
            f'Write a child-facing pirate tale that shows why children should not shake or poke around a crib, but ends with comfort and a calm lesson.',
        ]
    return [
        base,
        f"Tell a suspense story where {a.id} tries to get the pear from under the crib, but the baby stays asleep and a grown-up safely rescues the treasure.",
        f'Write a pirate-flavored nursery story with a dark under-crib cave, a careful grown-up rescue, and an ending image that proves the children learned a safer way.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, baby, parent = f["instigator"], f["cautioner"], f["baby"], f["parent"]
    spot, move, rescue_cfg = f["spot_cfg"], f["risky_cfg"], f["rescue_cfg"]
    pair = pair_noun(a, b, f["relation"])
    out = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, playing pirates near {baby.id}'s crib. It is also about {baby.id}, who was sleeping, and their {parent.label_word}, who helped."
        ),
        (
            "What made the room feel suspenseful?",
            f"A pear rolled {spot.under_text}, and the space under the crib was dark enough to feel like a little cave. The children had to stay quiet because {baby.id} was asleep there."
        ),
        (
            f"Why did {b.id} warn {a.id}?",
            f"{b.id} knew that {move.label} could make the crib creak and startle the baby. The warning came from seeing that the pear was under a sleeping baby's crib, not just from wanting to spoil the game."
        ),
    ]
    if out.startswith("averted"):
        qa.append((
            f"What did {a.id} do after the warning?",
            f"{a.id} stopped and agreed to ask {parent.label_word} for help. Because {a.pronoun()} backed down before touching the crib, the room stayed calmer."
        ))
    else:
        qa.append((
            f"What happened when {a.id} tried to get the pear?",
            f"The crib creaked and the whole room went still while the children listened. That one risky try turned the treasure game into real suspense."
        ))
    if out in {"woke", "averted_woke"}:
        qa.append((
            f"Did {baby.id} wake up, and why?",
            f"Yes. {baby.id} woke because the room became too noisy or startling near the crib. Once the crib was disturbed, the quiet sleeping moment was broken."
        ))
    else:
        qa.append((
            f"Did {baby.id} stay asleep?",
            f"Yes. {baby.id} stayed asleep because the final help was calm enough and the crib was kept steady. The safe rescue protected the baby's rest as well as the pear."
        ))
    qa.append((
        f"How did the grown-up get the pear back?",
        f"{parent.label_word.capitalize()} {rescue_cfg.qa_text}. That worked because {rescue_cfg.label} could reach the pear without shaking the crib."
    ))
    qa.append((
        "How did the story end?",
        f"It ended with a safer kind of treasure hunt. The children learned that a crib is not part of the game, and later they had tools for adventure somewhere calmer."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"crib", "pear", "dark"} | set(world.facts["spot_cfg"].tags)
    tags |= set(world.facts["rescue_cfg"].tags)
    tags |= set(world.facts["risky_cfg"].tags)
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
        if e.age:
            bits.append(f"age={e.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def tell(
    theme: Theme,
    spot: Spot,
    risky: RiskyMove,
    rescue_cfg: Rescue,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    baby_name: str = "Poppy",
    baby_gender: str = "baby_girl",
    parent_type: str = "mother",
    trait: str = "careful",
    relation: str = "siblings",
    instigator_age: int = 6,
    cautioner_age: int = 5,
    sleeper: int = 2,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator, kind="character", type=instigator_gender,
        role="instigator", age=instigator_age, attrs={"relation": relation}
    ))
    b = world.add(Entity(
        id=cautioner, kind="character", type=cautioner_gender,
        role="cautioner", age=cautioner_age, traits=[trait], attrs={"relation": relation}
    ))
    baby = world.add(Entity(
        id=baby_name, kind="character", type=baby_gender, role="baby"
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, role="parent", label="the parent"
    ))
    crib = world.add(Entity(id="crib", type="crib", label="crib"))
    pear = world.add(Entity(id="pear", type="pear", label="pear"))
    room = world.add(Entity(id="room", type="room", label="nursery"))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    world.facts["sleeper"] = sleeper

    play_setup(world, a, b, theme)
    snack_rolls(world, a, b, baby, spot)
    dark_need(world, b, theme, spot)

    world.para()
    tempt(world, a, risky)
    warn(world, b, a, risky, spot, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    world.para()
    if averted:
        back_down(world, a, b, parent)
        if rescue_cfg.quiet < sleeper:
            baby.meters["startled"] += 1
            propagate(world, narrate=False)
        rescue(world, parent, baby, rescue_cfg, spot)
        lesson(world, parent, a, b, baby, risky)
    else:
        defy(world, a, b, risky)
        risky_attempt(world, a, b, baby, spot, risky)
        world.para()
        rescue(world, parent, baby, rescue_cfg, spot)
        lesson(world, parent, a, b, baby, risky)

    world.para()
    safe_gift(world, parent, a, b, theme, rescue_cfg)

    outcome = outcome_of(StoryParams(
        theme=theme.id,
        spot=spot.id,
        risky=risky.id,
        rescue=rescue_cfg.id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        baby_name=baby_name,
        baby_gender=baby_gender,
        parent=parent_type,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        sleeper=sleeper,
    ))

    world.facts.update(
        theme=theme,
        spot_cfg=spot,
        risky_cfg=risky,
        rescue_cfg=rescue_cfg,
        instigator=a,
        cautioner=b,
        baby=baby,
        parent=parent,
        crib=crib,
        pear=pear,
        room=room,
        relation=relation,
        outcome=outcome,
        averted=averted,
    )
    return world


CURATED = [
    StoryParams(
        "pirates", "deep", "hook", "grabber",
        "Tom", "boy", "Lily", "girl", "Poppy", "baby_girl",
        "mother", "careful", relation="siblings", instigator_age=6, cautioner_age=8, sleeper=3
    ),
    StoryParams(
        "pirates", "deep", "hook", "grabber",
        "Max", "boy", "Mia", "girl", "Otis", "baby_boy",
        "father", "curious", relation="friends", instigator_age=6, cautioner_age=6, sleeper=3
    ),
    StoryParams(
        "corsairs", "shallow", "hand", "hand",
        "Ava", "girl", "Ben", "boy", "June", "baby_girl",
        "mother", "gentle", relation="siblings", instigator_age=5, cautioner_age=7, sleeper=2
    ),
]


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
sensible_rescue(R) :- rescue(R), sense(R, S), sense_min(M), S >= M.
move_reaches(Mv, Sp) :- risky_move(Mv), spot(Sp), move_reach(Mv, R), spot_depth(Sp, D), R >= D.
rescue_reaches(R, Sp) :- rescue(R), spot(Sp), rescue_reach(R, RR), spot_depth(Sp, D), RR >= D.
valid(T, Sp, Mv, R) :- theme(T), spot(Sp), risky_move(Mv), rescue(R),
                       move_reaches(Mv, Sp), rescue_reaches(R, Sp), sensible_rescue(R).

% --- outcome inference -----------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(3) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

attempt_noise(N) :- chosen_move(Mv), move_noise(Mv, N).
rescue_penalty(1) :- chosen_rescue(R), sleeper(S), rescue_quiet(R, Q), Q < S.
rescue_penalty(0) :- chosen_rescue(R), sleeper(S), rescue_quiet(R, Q), Q >= S.
total_noise(N + P) :- attempt_noise(N), rescue_penalty(P).

outcome(averted_asleep) :- averted, chosen_rescue(R), sleeper(S), rescue_quiet(R, Q), Q >= S.
outcome(averted_woke)   :- averted, chosen_rescue(R), sleeper(S), rescue_quiet(R, Q), Q < S.
outcome(woke)           :- not averted, total_noise(N), sleeper(S), N >= S.
outcome(slept)          :- not averted, total_noise(N), sleeper(S), N < S.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for sid, s in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        lines.append(asp.fact("spot_depth", sid, s.depth))
    for mid, m in RISKY_MOVES.items():
        lines.append(asp.fact("risky_move", mid))
        lines.append(asp.fact("move_reach", mid, m.reach))
        lines.append(asp.fact("move_noise", mid, m.noise))
    for rid, r in RESCUES.items():
        lines.append(asp.fact("rescue", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("rescue_reach", rid, r.reach))
        lines.append(asp.fact("rescue_quiet", rid, r.quiet))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for tr in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", tr))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_rescues() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_rescue/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_rescue"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_move", params.risky),
        asp.fact("chosen_rescue", params.rescue),
        asp.fact("sleeper", params.sleeper),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    c_sens = set(asp_sensible_rescues())
    p_sens = {r.id for r in sensible_rescues()}
    if c_sens == p_sens:
        print(f"OK: sensible rescues match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible rescues: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke-tested ordinary story generation.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Suspenseful pirate nursery storyworld: a pear rolls under a crib, and children must choose between a risky treasure grab and calm grown-up help."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--risky", choices=RISKY_MOVES)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--sleeper", type=int, choices=[2, 3], help="how easily the baby wakes")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def _pick_baby(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["baby_girl", "baby_boy"])
    if gender == "baby_girl":
        return rng.choice(BABY_GIRL_NAMES), gender
    return rng.choice(BABY_BOY_NAMES), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.rescue and RESCUES[args.rescue].sense < SENSE_MIN:
        raise StoryError(explain_rescue(args.rescue))
    if args.spot and args.risky:
        spot = SPOTS[args.spot]
        move = RISKY_MOVES[args.risky]
        if not move_can_reach(move, spot):
            raise StoryError(explain_reach("risky move", move.label, spot))
    if args.spot and args.rescue:
        spot = SPOTS[args.spot]
        rescue_cfg = RESCUES[args.rescue]
        if not rescue_can_reach(rescue_cfg, spot):
            raise StoryError(explain_reach("rescue", rescue_cfg.label, spot))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.spot is None or c[1] == args.spot)
        and (args.risky is None or c[2] == args.risky)
        and (args.rescue is None or c[3] == args.rescue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, spot, risky, rescue = rng.choice(sorted(combos))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    baby_name, baby_gender = _pick_baby(rng)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7, 8], 2)
    sleeper = args.sleeper if args.sleeper is not None else rng.choice([2, 3])
    return StoryParams(
        theme, spot, risky, rescue,
        instigator, ig, cautioner, cg, baby_name, baby_gender,
        parent, trait, relation=relation,
        instigator_age=instigator_age, cautioner_age=cautioner_age,
        sleeper=sleeper,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        THEMES[params.theme],
        SPOTS[params.spot],
        RISKY_MOVES[params.risky],
        RESCUES[params.rescue],
        params.instigator,
        params.instigator_gender,
        params.cautioner,
        params.cautioner_gender,
        params.baby_name,
        params.baby_gender,
        params.parent,
        params.trait,
        params.relation,
        params.instigator_age,
        params.cautioner_age,
        params.sleeper,
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
        print(asp_program("", "#show valid/4.\n#show sensible_rescue/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible rescues: {', '.join(asp_sensible_rescues())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, spot, risky, rescue) combos:\n")
        for theme, spot, risky, rescue in combos:
            print(f"  {theme:8} {spot:8} {risky:8} {rescue}")
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
            header = f"### {p.instigator} & {p.cautioner}: pear under crib ({p.theme}, {p.spot}, {p.risky}->{p.rescue}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
