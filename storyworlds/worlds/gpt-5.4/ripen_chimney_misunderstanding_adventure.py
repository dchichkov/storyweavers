#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ripen_chimney_misunderstanding_adventure.py
======================================================================

A standalone story world for a small adventure built around a misunderstanding:
two children see smoke curling from a cottage chimney, mistake it for trouble,
and hurry off like explorers. At the cottage they learn the smoke came from an
ordinary hearth task, not danger at all. The ending then branches from world
state: sometimes fruit has already begun to ripen and they help with a real
harvest, and sometimes the fruit is still green and they leave with a promise to
come back.

The domain is deliberately narrow and constraint-checked:

* A smoke sign must be plausible for the hearth task that caused it.
* A fruit-cooking task (pie or jam) only works when the chosen fruit is one that
  can be used for that task and is ripe now.
* The children's response must fit what the smoke looked like from where they
  stood; wildly dramatic responses are refused when the sign looks mild.
* The outcome model is explicit in Python and mirrored by an inline ASP twin.

Run it
------
    python storyworlds/worlds/gpt-5.4/ripen_chimney_misunderstanding_adventure.py
    python storyworlds/worlds/gpt-5.4/ripen_chimney_misunderstanding_adventure.py --task jam --fruit pears
    python storyworlds/worlds/gpt-5.4/ripen_chimney_misunderstanding_adventure.py --approach village_bell --smoke white_ribbon
    python storyworlds/worlds/gpt-5.4/ripen_chimney_misunderstanding_adventure.py --all
    python storyworlds/worlds/gpt-5.4/ripen_chimney_misunderstanding_adventure.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/ripen_chimney_misunderstanding_adventure.py --qa --json
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    vista: str
    path: str
    adventure_line: str
    distance: int
    allows_bell: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SmokeSign:
    id: str
    label: str
    look: str
    guess: str
    urgency: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    label: str
    smoke_ids: set[str]
    needs_fruit: bool
    ripe_required: bool
    fruit_ids: set[str]
    reveal_text: str
    ripen_line: str
    harvest_text: str
    waiting_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fruit:
    id: str
    label: str
    tree: str
    ripe_now: bool
    task_ids: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Approach:
    id: str
    label: str
    carry: str
    hurry_text: str
    sense_when_urgent: int
    sense_when_mild: int
    reveal_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "friend"}]

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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    smoke = world.get("chimney")
    if smoke.meters["visibility"] < THRESHOLD:
        return out
    for kid in world.kids():
        sig = ("alarm", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["worry"] += 1
        out.append("__alarm__")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.kids():
        if kid.memes["worry"] < THRESHOLD or kid.memes["adventure"] < THRESHOLD:
            continue
        sig = ("bravery", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["courage"] += 1
        out.append("__bravery__")
    return out


def _r_harvest(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("help_harvest"):
        return out
    fruit = world.get("fruit")
    basket = world.get("basket")
    if fruit.meters["ripe"] < THRESHOLD:
        return out
    sig = ("harvest", fruit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    basket.meters["filled"] += 1
    for kid in world.kids():
        kid.memes["pride"] += 1
        kid.memes["joy"] += 1
    out.append("__harvest__")
    return out


CAUSAL_RULES = [
    Rule("alarm", "social", _r_alarm),
    Rule("bravery", "social", _r_bravery),
    Rule("harvest", "physical", _r_harvest),
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


PLACES = {
    "orchard_edge": Place(
        "orchard_edge",
        "the edge of the old orchard",
        "a little stone cottage beyond the apple trees",
        "a narrow path between rows of fruit trees",
        "Every stump looked like a lookout post, and every branch looked like part of a map.",
        1,
        allows_bell=False,
        tags={"orchard", "adventure"},
    ),
    "hill_path": Place(
        "hill_path",
        "the windy hill path above the valley",
        "the cottage roof below, with its chimney clear against the sky",
        "a steep goat path that bent around the hill",
        "From up there, the whole valley felt like an unexplored kingdom.",
        2,
        allows_bell=True,
        tags={"hill", "adventure"},
    ),
    "farm_lane": Place(
        "farm_lane",
        "the farm lane near the hedges",
        "the cottage at the far bend, half hidden by plum trees",
        "a bumpy lane with weeds growing through the middle",
        "The lane felt so quiet that even a wren hopping ahead looked like a scout.",
        1,
        allows_bell=True,
        tags={"farm", "adventure"},
    ),
}

SMOKES = {
    "dark_puff": SmokeSign(
        "dark_puff",
        "a dark puff",
        "a dark puff leap from the chimney and spread like a torn flag",
        "that something hot had gone wrong inside",
        3,
        tags={"chimney", "smoke", "mistake"},
    ),
    "white_ribbon": SmokeSign(
        "white_ribbon",
        "a white ribbon",
        "a white ribbon of smoke curl from the chimney and drift softly sideways",
        "that someone inside might still need checking on",
        1,
        tags={"chimney", "smoke", "mistake"},
    ),
    "busy_stream": SmokeSign(
        "busy_stream",
        "a busy stream",
        "a busy stream of gray smoke climb from the chimney and keep coming",
        "that the fire inside must be roaring harder than it should",
        2,
        tags={"chimney", "smoke", "mistake"},
    ),
}

TASKS = {
    "jam": Task(
        "jam",
        "boiling plum jam",
        {"dark_puff", "busy_stream"},
        needs_fruit=True,
        ripe_required=True,
        fruit_ids={"plums"},
        reveal_text="a copper pot of plum jam bubbling on the stove",
        ripen_line="The plums had finally begun to ripen, so the cottage smelled sweet and dark at the same time.",
        harvest_text="Soon purple plums thumped gently into the basket, and brave feet that had come expecting danger ended up helping with supper.",
        waiting_text="",
        tags={"jam", "fruit", "cooking"},
    ),
    "pie": Task(
        "pie",
        "baking an apple pie",
        {"white_ribbon", "busy_stream"},
        needs_fruit=True,
        ripe_required=True,
        fruit_ids={"apples"},
        reveal_text="an apple pie browning in the oven",
        ripen_line="The apples were ripe enough at last, and that was why the kitchen smelled warm and buttery.",
        harvest_text="They carried shiny apples to the table while the pie baked, and the cottage no longer looked like a place of danger at all.",
        waiting_text="",
        tags={"pie", "fruit", "cooking"},
    ),
    "kettle": Task(
        "kettle",
        "heating cider on the stove",
        {"white_ribbon", "busy_stream"},
        needs_fruit=False,
        ripe_required=False,
        fruit_ids={"apples", "pears", "plums"},
        reveal_text="a kettle humming on the stove",
        ripen_line="The fruit outside still needed a little more sun to ripen, so today's smoke came only from the little fire under the kettle.",
        harvest_text="",
        waiting_text="The caretaker tied a red ribbon to a low branch and promised to wave the children back when the fruit was ready.",
        tags={"kettle", "chimney", "waiting"},
    ),
}

FRUITS = {
    "apples": Fruit(
        "apples",
        "apples",
        "apple tree",
        True,
        {"pie", "kettle"},
        tags={"apple", "fruit", "ripen"},
    ),
    "plums": Fruit(
        "plums",
        "plums",
        "plum tree",
        True,
        {"jam", "kettle"},
        tags={"plum", "fruit", "ripen"},
    ),
    "pears": Fruit(
        "pears",
        "pears",
        "pear tree",
        False,
        {"kettle"},
        tags={"pear", "fruit", "ripen"},
    ),
}

APPROACHES = {
    "knock_first": Approach(
        "knock_first",
        "knock first",
        "",
        "They hurried along the path, trying to look like brave scouts instead of two children with a half-understood worry.",
        3,
        3,
        "At the door, they stopped long enough to knock and listen before saying why they had come.",
        tags={"ask", "adventure"},
    ),
    "water_pail": Approach(
        "water_pail",
        "carry a water pail",
        "a sloshing water pail",
        "They grabbed a little pail from the pump and marched off, careful not to spill too much as they hurried.",
        3,
        1,
        "The caretaker blinked at the pail first, then at their serious faces.",
        tags={"water", "adventure"},
    ),
    "village_bell": Approach(
        "village_bell",
        "run for the lane bell",
        "",
        "They ran to the old lane bell and rang it once before racing on, just in case other grown-ups should hear.",
        2,
        1,
        "The caretaker had already heard the bell and opened the door looking more puzzled than frightened.",
        tags={"bell", "adventure"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]
TRAITS = ["bold", "curious", "careful", "eager", "thoughtful", "quick-footed"]


def smoke_matches_task(smoke: SmokeSign, task: Task) -> bool:
    return smoke.id in task.smoke_ids


def fruit_matches_task(task: Task, fruit: Fruit) -> bool:
    if not task.needs_fruit:
        return fruit.id in task.fruit_ids
    return fruit.id in task.fruit_ids and task.id in fruit.task_ids and fruit.ripe_now == task.ripe_required


def approach_sense(place: Place, smoke: SmokeSign, approach: Approach) -> int:
    if approach.id == "village_bell" and not place.allows_bell:
        return 0
    if smoke.urgency >= 2:
        return approach.sense_when_urgent
    return approach.sense_when_mild


def sensible_approaches(place: Place, smoke: SmokeSign) -> list[Approach]:
    return [a for a in APPROACHES.values() if approach_sense(place, smoke, a) >= SENSE_MIN]


def valid_combo(place: Place, smoke: SmokeSign, task: Task, fruit: Fruit, approach: Approach) -> bool:
    return (
        smoke_matches_task(smoke, task)
        and fruit_matches_task(task, fruit)
        and approach_sense(place, smoke, approach) >= SENSE_MIN
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out = []
    for pl in PLACES:
        for sm in SMOKES:
            for tk in TASKS:
                for fr in FRUITS:
                    for ap in APPROACHES:
                        if valid_combo(PLACES[pl], SMOKES[sm], TASKS[tk], FRUITS[fr], APPROACHES[ap]):
                            out.append((pl, sm, tk, fr, ap))
    return out


def outcome_of(params: "StoryParams") -> str:
    task = TASKS[params.task]
    fruit = FRUITS[params.fruit]
    return "harvest" if task.needs_fruit and fruit.ripe_now else "return"


def predict_trouble(world: World, smoke: SmokeSign) -> dict:
    sim = world.copy()
    sim.get("chimney").meters["visibility"] += 1
    sim.facts["smoke"] = smoke
    for kid in sim.kids():
        kid.memes["adventure"] += 1
    propagate(sim, narrate=False)
    return {
        "worried_kids": sum(1 for kid in sim.kids() if kid.memes["worry"] >= THRESHOLD),
        "courageous_kids": sum(1 for kid in sim.kids() if kid.memes["courage"] >= THRESHOLD),
    }


def introduce(world: World, lead: Entity, friend: Entity, place: Place) -> None:
    for kid in (lead, friend):
        kid.memes["adventure"] += 1
        kid.memes["wonder"] += 1
    world.say(
        f"{lead.id} and {friend.id} were exploring {place.label} as if it were the edge of a hidden country. "
        f"{place.adventure_line}"
    )
    world.say(
        f"They called themselves trail captains for the afternoon and followed every bend of {place.path} as if treasure might be waiting around it."
    )


def notice(world: World, lead: Entity, friend: Entity, place: Place, smoke: SmokeSign) -> None:
    world.get("chimney").meters["visibility"] += 1
    pred = predict_trouble(world, smoke)
    world.facts["predicted_worried"] = pred["worried_kids"]
    world.facts["predicted_courage"] = pred["courageous_kids"]
    propagate(world, narrate=False)
    world.say(
        f"Then {lead.id} stopped and pointed toward {place.vista}. They saw {smoke.look}."
    )
    world.say(
        f'"That looks like a sign," {friend.id} whispered. From so far away, they guessed {smoke.guess}.'
    )


def misunderstand(world: World, lead: Entity, friend: Entity, smoke: SmokeSign) -> None:
    for kid in (lead, friend):
        kid.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The chimney was only doing what chimneys do, but from the path it seemed mysterious enough to turn a little worry into a full adventure."
    )
    if lead.memes["courage"] >= THRESHOLD or friend.memes["courage"] >= THRESHOLD:
        world.say(
            f'"We should go," said {lead.id}. The idea made their knees feel shaky, but it also made them feel brave.'
        )


def choose_approach(world: World, lead: Entity, friend: Entity, approach: Approach) -> None:
    if approach.carry:
        world.facts["carried"] = approach.carry
    world.say(approach.hurry_text)
    if approach.id == "water_pail":
        world.say(
            f'{friend.id} held the handle with both hands while {lead.id} watched the path ahead like a lookout.'
        )
    elif approach.id == "village_bell":
        world.say(
            f'The bell gave one clear clang, and then they raced on with their hearts knocking almost as loudly.'
        )


def reveal(world: World, caretaker: Entity, task: Task, fruit: Fruit, approach: Approach) -> None:
    world.say(approach.reveal_text)
    world.say(
        f"When the door opened, there was no crackling disaster inside at all. There was only {caretaker.id}, a warm kitchen, and {task.reveal_text}."
    )
    world.say(
        f'"Oh!" said {caretaker.id}, and then {caretaker.pronoun()} smiled. "So that is what you thought the smoke meant."'
    )
    world.say(task.ripen_line)
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["worry"] = 0.0
    world.facts["misunderstanding_cleared"] = True


def invite_harvest(world: World, caretaker: Entity, fruit: Fruit, task: Task) -> None:
    world.facts["help_harvest"] = True
    world.say(
        f'{caretaker.id} took them outside to the {fruit.tree}. "{fruit.label.capitalize()} do not turn ready all at once," {caretaker.pronoun()} said. "You have to watch for the ones that truly ripen."'
    )
    propagate(world, narrate=False)
    world.say(task.harvest_text)
    world.say(
        "By the time they went home, their misunderstanding had changed into a real piece of useful bravery."
    )


def wait_for_ripen(world: World, caretaker: Entity, fruit: Fruit, task: Task) -> None:
    for kid in world.kids():
        kid.memes["patience"] += 1
        kid.memes["joy"] += 1
    world.say(
        f'{caretaker.id} led them to the {fruit.tree}, where the fruit was still hard and green. "{fruit.label.capitalize()} need a little longer to ripen," {caretaker.pronoun()} said.'
    )
    world.say(task.waiting_text)
    world.say(
        "So the adventure ended not with a rescue, but with a promise and a place to return to when the branches were ready."
    )


def closing_image(world: World, lead: Entity, friend: Entity, outcome: str, fruit: Fruit) -> None:
    if outcome == "harvest":
        world.say(
            f"As the sun lowered, {lead.id} and {friend.id} walked back with sticky fingers and proud steps, already planning how they would tell the story of the brave chimney mistake."
        )
    else:
        world.say(
            f"As they walked home, they kept looking back at the ribbon on the {fruit.tree}, as if the next chapter of the adventure were already waiting there."
        )


def tell(
    place: Place,
    smoke: SmokeSign,
    task: Task,
    fruit: Fruit,
    approach: Approach,
    leader_name: str = "Lily",
    leader_type: str = "girl",
    friend_name: str = "Tom",
    friend_type: str = "boy",
    caretaker_type: str = "mother",
    lead_trait: str = "curious",
    friend_trait: str = "bold",
) -> World:
    world = World()
    lead = world.add(Entity(id=leader_name, kind="character", type=leader_type, role="leader", traits=[lead_trait]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend", traits=[friend_trait]))
    caretaker = world.add(Entity(id="Mara", kind="character", type=caretaker_type, role="caretaker", label="the caretaker"))
    chimney = world.add(Entity(id="chimney", type="chimney", label="chimney"))
    fruit_ent = world.add(Entity(id="fruit", type="fruit", label=fruit.label))
    basket = world.add(Entity(id="basket", type="basket", label="basket"))
    if fruit.ripe_now:
        fruit_ent.meters["ripe"] = 1.0

    introduce(world, lead, friend, place)
    world.para()
    notice(world, lead, friend, place, smoke)
    misunderstand(world, lead, friend, smoke)
    choose_approach(world, lead, friend, approach)
    world.para()
    reveal(world, caretaker, task, fruit, approach)
    if outcome_of(StoryParams(place.id, smoke.id, task.id, fruit.id, approach.id,
                              leader_name, leader_type, friend_name, friend_type,
                              caretaker_type, lead_trait, friend_trait, None)) == "harvest":
        invite_harvest(world, caretaker, fruit, task)
    else:
        wait_for_ripen(world, caretaker, fruit, task)
    world.para()
    closing_image(world, lead, friend, outcome_of(StoryParams(place.id, smoke.id, task.id, fruit.id, approach.id,
                                                              leader_name, leader_type, friend_name, friend_type,
                                                              caretaker_type, lead_trait, friend_trait, None)), fruit)

    world.facts.update(
        place=place,
        smoke=smoke,
        task=task,
        fruit_cfg=fruit,
        approach=approach,
        leader=lead,
        friend=friend,
        caretaker=caretaker,
        outcome=outcome_of(StoryParams(place.id, smoke.id, task.id, fruit.id, approach.id,
                                       leader_name, leader_type, friend_name, friend_type,
                                       caretaker_type, lead_trait, friend_trait, None)),
        carried=world.facts.get("carried", ""),
        misunderstanding=True,
        help_harvest=world.facts.get("help_harvest", False),
        basket_filled=basket.meters["filled"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    smoke: str
    task: str
    fruit: str
    approach: str
    leader_name: str
    leader_type: str
    friend_name: str
    friend_type: str
    caretaker_type: str
    lead_trait: str
    friend_trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "chimney": [(
        "What is a chimney?",
        "A chimney is a tall passage that lets smoke from a fire travel safely up and out of a house."
    )],
    "smoke": [(
        "Why can smoke be confusing from far away?",
        "From far away, you can see smoke without seeing the stove or fireplace that made it. That means ordinary cooking smoke can look mysterious if you do not know the cause."
    )],
    "mistake": [(
        "What is a misunderstanding?",
        "A misunderstanding happens when someone thinks something means one thing, but it really means something else."
    )],
    "ripen": [(
        "What does ripen mean?",
        "Ripen means fruit is becoming ready to eat. As fruit ripens, it usually gets softer, sweeter, and more colorful."
    )],
    "apple": [(
        "What can people make with apples?",
        "People can eat apples fresh or bake them into pies and other treats."
    )],
    "plum": [(
        "What is jam?",
        "Jam is fruit cooked with sugar until it turns thick and sweet enough to spread."
    )],
    "pear": [(
        "Why might pears need more time?",
        "Pears can look big before they are ready. Sometimes they still need more days to ripen and turn sweet."
    )],
    "water": [(
        "Why would someone carry water to a fire?",
        "Water can help put some small fires out. But first you must know whether there is really a fire."
    )],
    "bell": [(
        "Why would people ring a bell in an emergency?",
        "A bell can call other people to come quickly when help might be needed."
    )],
    "ask": [(
        "Why is it smart to ask questions before panicking?",
        "Asking questions can help you find out what is really happening. That stops a misunderstanding from growing bigger."
    )],
}
KNOWLEDGE_ORDER = ["chimney", "smoke", "mistake", "ripen", "apple", "plum", "pear", "water", "bell", "ask"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    friend = f["friend"]
    smoke = f["smoke"]
    task = f["task"]
    fruit = f["fruit_cfg"]
    outcome = f["outcome"]
    end = "ends with them helping harvest ripe fruit" if outcome == "harvest" else "ends with a promise to come back when the fruit ripens"
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the words "ripen" and "chimney" and uses a misunderstanding as the main turn.',
        f"Tell an adventure about {leader.id} and {friend.id}, who see {smoke.label} from a chimney, mistake it for trouble, and discover {task.label} instead.",
        f"Write a gentle misunderstanding story set near fruit trees where smoke from a chimney seems dangerous at first, but the truth is ordinary and kind, and the ending {end}.",
        f"Include fruit that must ripen, a cottage chimney, and a child-sized adventure with no real villain."
    ]


def pair_kind(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    friend = f["friend"]
    caretaker = f["caretaker"]
    smoke = f["smoke"]
    task = f["task"]
    fruit = f["fruit_cfg"]
    approach = f["approach"]
    pair = pair_kind(leader, friend)
    qa = [
        (
            "Who is the story about?",
            f"It is about {pair}, {leader.id} and {friend.id}, who went on a small adventure together. It also includes {caretaker.id}, the caretaker at the cottage."
        ),
        (
            "What started the adventure?",
            f"The adventure started when they saw {smoke.label} from the chimney and guessed it meant trouble. They could not see the real cause from where they stood, so the misunderstanding grew."
        ),
        (
            "Why was it a misunderstanding?",
            f"It was a misunderstanding because the children thought the chimney smoke meant danger, but it really came from {task.label}. They were reading a distant sign without enough information."
        ),
        (
            f"How did {leader.id} and {friend.id} respond?",
            f"They chose to {approach.label} and hurried to the cottage. Their response fit the adventure in their heads, even though the danger turned out not to be real."
        ),
    ]
    if f["outcome"] == "harvest":
        qa.append((
            "What changed after they reached the cottage?",
            f"The worry changed into relief when they saw there was no disaster inside. Then the adventure changed again, because they were invited to help with ripe {fruit.label} instead of rescuing anyone."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the children helping gather fruit after it had begun to ripen. The ending image shows that the frightening chimney mistake became a useful, happy visit."
        ))
    else:
        qa.append((
            "What did they learn about the fruit?",
            f"They learned that the {fruit.label} were not ready yet and still needed time to ripen. That gave the story a calm ending built on waiting instead of rushing."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a promise to come back later, not with a rescue. The ribbon on the branch proved that the misunderstanding was over and a future adventure was waiting."
        ))
    if f.get("carried"):
        qa.append((
            "What did they bring with them?",
            f"They brought {f['carried']} because they thought it might help. That detail shows how real the misunderstanding felt to them before they knew the truth."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["smoke"].tags) | set(f["fruit_cfg"].tags) | set(f["approach"].tags)
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("orchard_edge", "busy_stream", "pie", "apples", "knock_first",
                "Lily", "girl", "Tom", "boy", "mother", "curious", "bold"),
    StoryParams("farm_lane", "dark_puff", "jam", "plums", "water_pail",
                "Max", "boy", "Mia", "girl", "father", "eager", "careful"),
    StoryParams("hill_path", "white_ribbon", "kettle", "pears", "knock_first",
                "Nora", "girl", "Finn", "boy", "mother", "thoughtful", "quick-footed"),
    StoryParams("hill_path", "busy_stream", "kettle", "pears", "village_bell",
                "Sam", "boy", "Ella", "girl", "father", "bold", "curious"),
    StoryParams("farm_lane", "white_ribbon", "pie", "apples", "knock_first",
                "Ava", "girl", "Theo", "boy", "mother", "careful", "eager"),
]


def explain_smoke_task(smoke: SmokeSign, task: Task) -> str:
    return (
        f"(No story: {smoke.label} is not a reasonable sign for {task.label}. "
        f"Pick a smoke sign the task could really make.)"
    )


def explain_fruit_task(task: Task, fruit: Fruit) -> str:
    if task.needs_fruit and fruit.id not in task.fruit_ids:
        return (
            f"(No story: {task.label} does not use {fruit.label}. "
            f"Choose fruit that matches the cooking task.)"
        )
    if task.needs_fruit and not fruit.ripe_now:
        return (
            f"(No story: {fruit.label.capitalize()} have not begun to ripen enough for {task.label}. "
            f"Choose fruit that is ripe now, or choose a waiting task like kettle.)"
        )
    return (
        f"(No story: {fruit.label.capitalize()} do not fit this task.)"
    )


def explain_approach(place: Place, smoke: SmokeSign, approach: Approach) -> str:
    if approach.id == "village_bell" and not place.allows_bell:
        return (
            f"(No story: there is no lane bell at {place.label}, so that response does not fit the place.)"
        )
    return (
        f"(No story: {approach.label} is too dramatic for {smoke.label} from {place.label}. "
        f"Try a calmer response such as knock_first.)"
    )


ASP_RULES = r"""
smoke_matches(S, T) :- task_smoke(T, S).

fruit_matches(T, F) :- task(T), fruit(F), not needs_fruit(T), task_fruit(T, F).
fruit_matches(T, F) :- needs_fruit(T), task_fruit(T, F), ripe_now(F).

approach_sense(P, S, A, V) :- place(P), smoke(S), allows_bell(P), urgent(S), sense_urgent(A, V), approach(A), A = village_bell.
approach_sense(P, S, A, V) :- place(P), smoke(S), not urgent(S), allows_bell(P), sense_mild(A, V), approach(A), A = village_bell.
approach_sense(P, S, A, V) :- place(P), smoke(S), approach(A), A != village_bell, urgent(S), sense_urgent(A, V).
approach_sense(P, S, A, V) :- place(P), smoke(S), approach(A), A != village_bell, not urgent(S), sense_mild(A, V).

sensible(P, S, A) :- approach_sense(P, S, A, V), sense_min(M), V >= M.

valid(P, S, T, F, A) :- place(P), smoke(S), task(T), fruit(F), approach(A),
                        smoke_matches(S, T), fruit_matches(T, F), sensible(P, S, A).

outcome(harvest) :- chosen_task(T), needs_fruit(T), chosen_fruit(F), ripe_now(F).
outcome(return)  :- chosen_task(T), not needs_fruit(T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.allows_bell:
            lines.append(asp.fact("allows_bell", pid))
    for sid, s in SMOKES.items():
        lines.append(asp.fact("smoke", sid))
        if s.urgency >= 2:
            lines.append(asp.fact("urgent", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        if t.needs_fruit:
            lines.append(asp.fact("needs_fruit", tid))
        for sid in sorted(t.smoke_ids):
            lines.append(asp.fact("task_smoke", tid, sid))
        for fid in sorted(t.fruit_ids):
            lines.append(asp.fact("task_fruit", tid, fid))
    for fid, f in FRUITS.items():
        lines.append(asp.fact("fruit", fid))
        if f.ripe_now:
            lines.append(asp.fact("ripe_now", fid))
    for aid, a in APPROACHES.items():
        lines.append(asp.fact("approach", aid))
        lines.append(asp.fact("sense_urgent", aid, a.sense_when_urgent))
        lines.append(asp.fact("sense_mild", aid, a.sense_when_mild))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_task", params.task),
        asp.fact("chosen_fruit", params.fruit),
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
    for s in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
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
            raise StoryError("generated empty story")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a chimney misunderstanding becomes a little adventure."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--smoke", choices=SMOKES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--fruit", choices=FRUITS)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--caretaker", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.smoke and args.task:
        if not smoke_matches_task(SMOKES[args.smoke], TASKS[args.task]):
            raise StoryError(explain_smoke_task(SMOKES[args.smoke], TASKS[args.task]))
    if args.task and args.fruit:
        if not fruit_matches_task(TASKS[args.task], FRUITS[args.fruit]):
            raise StoryError(explain_fruit_task(TASKS[args.task], FRUITS[args.fruit]))
    if args.place and args.smoke and args.approach:
        if approach_sense(PLACES[args.place], SMOKES[args.smoke], APPROACHES[args.approach]) < SENSE_MIN:
            raise StoryError(explain_approach(PLACES[args.place], SMOKES[args.smoke], APPROACHES[args.approach]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.smoke is None or c[1] == args.smoke)
        and (args.task is None or c[2] == args.task)
        and (args.fruit is None or c[3] == args.fruit)
        and (args.approach is None or c[4] == args.approach)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, smoke, task, fruit, approach = rng.choice(sorted(combos))
    leader_name, leader_type = _pick_name(rng)
    friend_name, friend_type = _pick_name(rng, avoid=leader_name)
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    lead_trait = rng.choice(TRAITS)
    friend_trait = rng.choice([t for t in TRAITS if t != lead_trait] or TRAITS)
    return StoryParams(
        place, smoke, task, fruit, approach,
        leader_name, leader_type, friend_name, friend_type,
        caretaker, lead_trait, friend_trait
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        SMOKES[params.smoke],
        TASKS[params.task],
        FRUITS[params.fruit],
        APPROACHES[params.approach],
        params.leader_name,
        params.leader_type,
        params.friend_name,
        params.friend_type,
        params.caretaker_type,
        params.lead_trait,
        params.friend_trait,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, smoke, task, fruit, approach) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:12}" for part in combo))
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
            header = f"### {p.leader_name} & {p.friend_name}: {p.smoke} at {p.place} ({p.task}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
