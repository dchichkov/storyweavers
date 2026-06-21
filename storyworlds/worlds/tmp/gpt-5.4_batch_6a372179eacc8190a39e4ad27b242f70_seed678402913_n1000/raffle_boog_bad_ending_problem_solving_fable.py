#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/raffle_boog_bad_ending_problem_solving_fable.py
===========================================================================

A standalone story world for a small fable-like domain built from the seed
words "raffle" and "boog".

Premise
-------
At a woodland fair, a little goat named Boog becomes too eager about a raffle.
He handles the raffle container badly, the tickets scatter, and the fair pauses.
A wiser grown-up and a steady friend try to solve the problem. Some fixes are
sensible and fair; some are refused by the reasonableness gate; and if help
comes too late, the raffle is lost and the ending turns sad.

This world aims for:
- a clear beginning at the fair,
- a state-driven middle turn when the tickets spill,
- and either a fair repaired ending or a bad ending proving what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/raffle_boog_bad_ending_problem_solving_fable.py
    python storyworlds/worlds/gpt-5.4/raffle_boog_bad_ending_problem_solving_fable.py --all
    python storyworlds/worlds/gpt-5.4/raffle_boog_bad_ending_problem_solving_fable.py --place riverbank
    python storyworlds/worlds/gpt-5.4/raffle_boog_bad_ending_problem_solving_fable.py --container jar
    python storyworlds/worlds/gpt-5.4/raffle_boog_bad_ending_problem_solving_fable.py --fix chase_alone
    python storyworlds/worlds/gpt-5.4/raffle_boog_bad_ending_problem_solving_fable.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen", "duck", "mother", "aunt", "sheep"}
        male = {"boy", "goat", "fox", "father", "uncle", "badger"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    detail: str
    wind: int
    open_air: bool = True
    water_nearby: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Container:
    id: str
    label: str
    phrase: str
    spillable: bool
    wobble: str
    fail_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    tickets = world.get("tickets")
    if tickets.meters["loose"] < THRESHOLD:
        return out
    sig = ("scatter", "tickets")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    place = world.facts["place_cfg"]
    tickets.meters["at_risk"] += float(place.wind)
    world.get("fair").meters["stopped"] += 1
    hero = world.get("boog")
    friend = world.get("friend")
    elder = world.get("elder")
    hero.memes["fear"] += 1
    friend.memes["concern"] += 1
    elder.memes["concern"] += 1
    if place.water_nearby:
        tickets.meters["water_risk"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="scatter", tag="physical", apply=_r_scatter),
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


def spill_possible(container: Container) -> bool:
    return container.spillable


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def severity(place: Place, delay: int) -> int:
    return place.wind + delay + (1 if place.water_nearby else 0)


def is_saved(place: Place, fix: Fix, delay: int) -> bool:
    return fix.power >= severity(place, delay)


def predict_spill(world: World) -> dict:
    sim = world.copy()
    sim.get("tickets").meters["loose"] += 1
    propagate(sim, narrate=False)
    return {
        "at_risk": sim.get("tickets").meters["at_risk"],
        "water_risk": sim.get("tickets").meters["water_risk"],
        "fair_stopped": sim.get("fair").meters["stopped"],
    }


def fair_opening(world: World, hero: Entity, friend: Entity, elder: Entity,
                 place: Place, prize: Prize, container: Container) -> None:
    hero.memes["hope"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In the green wood, the animals gathered at {place.phrase} for a spring fair. "
        f"{place.detail}"
    )
    world.say(
        f"On a little table stood {container.phrase}, and beside it hung {prize.phrase} "
        f"with {prize.glow}."
    )
    world.say(
        f'Boog, a young goat with quick feet and quicker wishes, bought one raffle ticket. '
        f'"If luck smiles, that {prize.label} might come home with me," he said.'
    )
    world.say(
        f"{friend.id}, {hero.pronoun('possessive')} steady friend, smiled and reminded "
        f"{hero.pronoun('object')} that a raffle works only when every ticket is treated fairly."
    )
    world.say(
        f"{elder.id}, who watched the table for the whole fair, nodded once. "
        f'"Slow hooves make straight work," {elder.pronoun()} said.'
    )


def temptation(world: World, hero: Entity, container: Container, prize: Prize) -> None:
    hero.memes["eagerness"] += 1
    world.say(
        f"But Boog kept glancing at the {prize.label}. Its shine tugged at his thoughts "
        f"until patience felt much too small."
    )
    world.say(
        f'At last he put both hooves on {container.label} and said, '
        f'"Maybe I can just give it one good turn."'
    )


def warning(world: World, friend: Entity, elder: Entity, container: Container) -> None:
    pred = predict_spill(world)
    world.facts["predicted_risk"] = pred["at_risk"]
    world.facts["predicted_water_risk"] = pred["water_risk"]
    extra = ""
    if pred["water_risk"] >= THRESHOLD:
        extra = " Worse still, the stream nearby could carry the tickets away."
    world.say(
        f'{friend.id} reached out. "Boog, don\'t yank {container.label}. '
        f'If the tickets come loose, the raffle must stop."'
    )
    world.say(
        f'{elder.id} added, "A fair game is easy to start and hard to mend once scattered."'
        f"{extra}"
    )


def accident(world: World, hero: Entity, container: Container) -> None:
    hero.memes["shame"] += 1
    tickets = world.get("tickets")
    tickets.meters["loose"] += 1
    tickets.meters["mixed"] += 1
    propagate(world, narrate=False)
    place = world.facts["place_cfg"]
    near = "toward the stream" if place.water_nearby else "across the grass"
    world.say(
        f"But eagerness had already pushed harder than wisdom. Boog gave {container.label} "
        f"{container.wobble}, {container.fail_text}, and the little paper slips skipped {near}."
    )
    if place.wind >= 2:
        world.say("The wind caught their corners and made them dance faster than hooves could chase.")
    else:
        world.say("The slips did not go far, but they spread into a messy ring all around the table.")
    world.say('At once the music near the raffle table went quiet.')


def crowd_pause(world: World, elder: Entity) -> None:
    elder.memes["authority"] += 1
    world.say(
        f'"No drawing yet," said {elder.id}. "Until the tickets are gathered and counted again, '
        f'no one can know whose chance is whose."'
    )


def attempt_fix(world: World, hero: Entity, friend: Entity, elder: Entity,
                fix: Fix, place: Place, delay: int) -> None:
    hero.memes["resolve"] += 1
    friend.memes["resolve"] += 1
    elder.memes["resolve"] += 1
    if fix.id == "freeze_and_recount":
        world.say(
            f"{friend.id} hopped onto a crate and called, "
            f'"Everyone hold still! Put a leaf on any ticket you see, and we will count together."'
        )
        world.say(f"{elder.id} lifted a wing and quickly set the whole fair to orderly work.")
    elif fix.id == "blanket_sort":
        world.say(
            f'{friend.id} spread a broad blanket on the ground. "Lay every ticket here," '
            f'{friend.pronoun()} said. "Then the wind cannot nibble them while we sort."'
        )
        world.say(f"Boog flattened the corners with careful hooves while {elder.id} checked the numbers.")
    elif fix.id == "rake_back":
        world.say(
            f"{elder.id} fetched a little garden rake and drew the tickets gently from the edges "
            f"back toward the table while everyone waited in a ring."
        )
        world.say(f"Boog and {friend.id} followed behind, lifting each slip before the breeze could turn it.")
    else:
        world.say(fix.text)

    if delay > 0:
        world.say("But the first frightened moment had already cost them precious time.")


def happy_repair(world: World, hero: Entity, friend: Entity, elder: Entity,
                 place: Place, prize: Prize, fix: Fix) -> None:
    tickets = world.get("tickets")
    tickets.meters["lost"] = 0.0
    tickets.meters["safe"] += 1
    world.get("fair").meters["stopped"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    friend.memes["relief"] += 1
    elder.memes["relief"] += 1
    world.say(
        f"Soon every ticket lay in one neat pile. {elder.id} counted twice, then once more, "
        f"and the number matched the morning list."
    )
    world.say(
        f'"The raffle is fair again," {elder.pronoun()} declared. The animals clapped, and Boog '
        f'let out the breath he had been holding.'
    )
    world.say(
        f'Boog lowered his head. "I wanted luck to come faster than it should," he said. '
        f'"Instead I nearly sent everyone\'s chance flying away."'
    )
    world.say(
        f'{elder.id} touched his shoulder kindly. "Quick wanting makes crooked trouble. '
        f'Patient helping straightens it."'
    )
    world.say(
        f"When the drawing was finally held, Boog did not win the {prize.label}. "
        f"Still, he smiled as another small animal carried it home, because the game had been honest."
    )
    world.say(
        f"After that, whenever Boog passed a raffle table at {place.label}, he kept his eager hooves "
        f"to himself and used them for helping instead."
    )


def sad_loss(world: World, hero: Entity, friend: Entity, elder: Entity,
             place: Place, prize: Prize, fix: Fix) -> None:
    tickets = world.get("tickets")
    tickets.meters["lost"] += 1
    hero.memes["fear"] += 1
    hero.memes["grief"] += 1
    hero.memes["lesson"] += 1
    friend.memes["sadness"] += 1
    elder.memes["sadness"] += 1
    fail_text = fix.fail
    world.say(fail_text)
    if place.water_nearby:
        world.say(
            "A few slips touched the stream, darkened at once, and folded into useless paper petals."
        )
    else:
        world.say(
            "More and more slips tumbled under boots and stalls until no one could tell one number from another."
        )
    world.say(
        f'{elder.id} looked at the ruined pile and shook {elder.pronoun("possessive")} head. '
        f'"We must stop the raffle," {elder.pronoun()} said. "A prize cannot be drawn from confusion."'
    )
    world.say(
        f"The bright {prize.label} was taken down from its hook and packed away. No one cheered. "
        f"The fair went on, but a quiet patch stayed around the empty table."
    )
    world.say(
        f'Boog whispered, "I broke a game that belonged to everyone." He helped pick up the last scraps, '
        f"yet no fixing could give the lost chances back."
    )
    world.say(
        f"From that day on, Boog learned a hard fable-truth: when greed and hurry pull together, "
        f"they can tear a good thing past mending."
    )


def tell(place: Place, prize: Prize, container: Container, fix: Fix,
         friend_name: str = "Mira", friend_type: str = "hen",
         elder_name: str = "Old Tawny", elder_type: str = "owl",
         delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id="Boog", kind="character", type="goat", role="hero", label="Boog"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type,
                              role="friend", label=friend_name))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type,
                             role="elder", label=elder_name))
    world.add(Entity(id="fair", kind="thing", type="fair", label="raffle fair"))
    world.add(Entity(id="tickets", kind="thing", type="tickets", label="raffle tickets"))
    world.add(Entity(id="container", kind="thing", type="container", label=container.label))
    world.add(Entity(id="prize", kind="thing", type="prize", label=prize.label))
    world.facts["place_cfg"] = place

    fair_opening(world, hero, friend, elder, place, prize, container)
    world.para()
    temptation(world, hero, container, prize)
    warning(world, friend, elder, container)
    accident(world, hero, container)
    crowd_pause(world, elder)
    world.para()
    attempt_fix(world, hero, friend, elder, fix, place, delay)

    saved = is_saved(place, fix, delay)
    if saved:
        happy_repair(world, hero, friend, elder, place, prize, fix)
    else:
        sad_loss(world, hero, friend, elder, place, prize, fix)

    outcome = "saved" if saved else "lost"
    world.facts.update(
        hero=hero,
        friend=friend,
        elder=elder,
        place=place,
        prize_cfg=prize,
        container_cfg=container,
        fix=fix,
        delay=delay,
        outcome=outcome,
        saved=saved,
        severity=severity(place, delay),
        spill_happened=True,
    )
    return world


PLACES = {
    "meadow": Place(
        id="meadow",
        label="the meadow fair",
        phrase="the meadow fair",
        detail="Bunting fluttered from willow poles, and the air moved in easy little gusts.",
        wind=1,
        open_air=True,
        water_nearby=False,
        tags={"fair", "wind"},
    ),
    "market": Place(
        id="market",
        label="the market square",
        phrase="the market square",
        detail="Colorful stalls stood shoulder to shoulder, and the raffle table sat under a striped awning.",
        wind=1,
        open_air=True,
        water_nearby=False,
        tags={"fair", "market"},
    ),
    "hill": Place(
        id="hill",
        label="the hill fair",
        phrase="the hill fair",
        detail="The path lay high and open, where the breeze was always a little bolder than anyone expected.",
        wind=2,
        open_air=True,
        water_nearby=False,
        tags={"fair", "wind"},
    ),
    "riverbank": Place(
        id="riverbank",
        label="the riverbank fair",
        phrase="the riverbank fair",
        detail="The stalls stood near a bright stream, and the grass leaned whenever the wind ran past.",
        wind=2,
        open_air=True,
        water_nearby=True,
        tags={"fair", "stream", "wind"},
    ),
}

PRIZES = {
    "kite": Prize(
        id="kite",
        label="red kite",
        phrase="a red kite",
        glow="a tail of yellow ribbons",
        tags={"kite"},
    ),
    "bell": Prize(
        id="bell",
        label="brass bell",
        phrase="a brass bell",
        glow="a warm golden shine",
        tags={"bell"},
    ),
    "cake": Prize(
        id="cake",
        label="honey cake",
        phrase="a honey cake",
        glow="a crust glazed like amber",
        tags={"cake"},
    ),
}

CONTAINERS = {
    "drum": Container(
        id="drum",
        label="the raffle drum",
        phrase="a painted raffle drum",
        spillable=True,
        wobble="such an eager spin that its latch jumped",
        fail_text="the door flew open",
        tags={"drum", "raffle"},
    ),
    "basket": Container(
        id="basket",
        label="the wicker basket",
        phrase="a wicker basket for raffle slips",
        spillable=True,
        wobble="a reckless shove",
        fail_text="it tipped sideways",
        tags={"basket", "raffle"},
    ),
    "jar": Container(
        id="jar",
        label="the glass jar",
        phrase="a thick glass jar with a screw-top lid",
        spillable=False,
        wobble="a little shake",
        fail_text="nothing happened",
        tags={"jar", "raffle"},
    ),
}

FIXES = {
    "freeze_and_recount": Fix(
        id="freeze_and_recount",
        sense=3,
        power=4,
        text="",
        fail="They tried to call for order at last, but too many tickets had already escaped the circle of helpers.",
        qa_text="called everyone to hold still, mark each ticket, and recount them together",
        tags={"recount", "fairness"},
    ),
    "blanket_sort": Fix(
        id="blanket_sort",
        sense=3,
        power=3,
        text="",
        fail="The blanket gathered some slips, but the loose ones kept skittering away before the sorting could catch up.",
        qa_text="spread a blanket, gathered the tickets onto it, and sorted them there",
        tags={"blanket", "sorting"},
    ),
    "rake_back": Fix(
        id="rake_back",
        sense=2,
        power=2,
        text="",
        fail="The little rake helped near the table, but the farthest slips were already too scattered to trust.",
        qa_text="used a little rake to draw the scattered tickets back before counting them",
        tags={"rake", "sorting"},
    ),
    "chase_alone": Fix(
        id="chase_alone",
        sense=1,
        power=1,
        text="Boog dashed after the flying slips by himself, snatching at one and then another while the rest kept running from him.",
        fail="Boog chased one ticket after another alone, and each frantic grab only stirred the rest farther apart.",
        qa_text="chased the tickets alone",
        tags={"chasing"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in sorted(PLACES):
        for prize_id in sorted(PRIZES):
            for container_id, container in CONTAINERS.items():
                if spill_possible(container):
                    combos.append((place_id, prize_id, container_id))
    return combos


@dataclass
class StoryParams:
    place: str
    prize: str
    container: str
    fix: str
    friend_name: str
    friend_type: str
    elder_name: str
    elder_type: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "raffle": [(
        "What is a raffle?",
        "A raffle is a game where people get numbered tickets and one ticket is chosen for the prize. It must be fair, or no one can trust the result.",
    )],
    "fairness": [(
        "Why must raffle tickets be counted carefully?",
        "They must be counted carefully so every person keeps one fair chance and no number is lost or doubled. If the count is wrong, the drawing is not honest anymore.",
    )],
    "wind": [(
        "Why is wind a problem for paper tickets?",
        "Paper is light, so wind can push it and spin it away quickly. That makes little slips hard to gather and count.",
    )],
    "stream": [(
        "Why is a stream bad for lost paper?",
        "Water soaks paper and makes the writing blur or tear. Once that happens, the paper may not be useful anymore.",
    )],
    "kite": [(
        "What is a kite?",
        "A kite is a light toy that rises in the air when the wind pulls its string. Children often run with it on breezy days.",
    )],
    "bell": [(
        "What does a bell do?",
        "A bell rings when it is shaken or struck. People use bells to make a bright, clear sound.",
    )],
    "cake": [(
        "What is a honey cake?",
        "A honey cake is a sweet cake made with honey. It smells warm and tastes rich and soft.",
    )],
    "sorting": [(
        "Why is sorting a good way to solve a mixed-up mess?",
        "Sorting puts things back into groups so you can check them one by one. It turns a confusing pile into something your eyes and hands can manage.",
    )],
    "blanket": [(
        "How can a blanket help with small flying things?",
        "A blanket makes one big still place to lay things down. That can stop little papers from sliding or blowing farther away.",
    )],
    "recount": [(
        "What does recount mean?",
        "Recount means to count something again carefully. People do that when they need to make sure the number is correct.",
    )],
}
KNOWLEDGE_ORDER = [
    "raffle",
    "fairness",
    "wind",
    "stream",
    "kite",
    "bell",
    "cake",
    "sorting",
    "blanket",
    "recount",
]

FRIENDS = [
    ("Mira", "hen"),
    ("Pip", "duck"),
    ("Fern", "sheep"),
]
ELDERS = [
    ("Old Tawny", "owl"),
    ("Aunt Brindle", "goat"),
    ("Master Reed", "badger"),
]


CURATED = [
    StoryParams(
        place="meadow",
        prize="kite",
        container="drum",
        fix="freeze_and_recount",
        friend_name="Mira",
        friend_type="hen",
        elder_name="Old Tawny",
        elder_type="owl",
        delay=0,
    ),
    StoryParams(
        place="hill",
        prize="bell",
        container="basket",
        fix="blanket_sort",
        friend_name="Pip",
        friend_type="duck",
        elder_name="Master Reed",
        elder_type="badger",
        delay=0,
    ),
    StoryParams(
        place="riverbank",
        prize="cake",
        container="drum",
        fix="rake_back",
        friend_name="Fern",
        friend_type="sheep",
        elder_name="Old Tawny",
        elder_type="owl",
        delay=1,
    ),
    StoryParams(
        place="riverbank",
        prize="kite",
        container="basket",
        fix="freeze_and_recount",
        friend_name="Mira",
        friend_type="hen",
        elder_name="Aunt Brindle",
        elder_type="goat",
        delay=1,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    prize = f["prize_cfg"]
    fix = f["fix"]
    outcome = f["outcome"]
    base = (
        f'Write a short fable for a 3-to-5-year-old that uses the words "raffle" and "Boog". '
        f'The story takes place at {place.phrase} and a prize is {prize.phrase}.'
    )
    if outcome == "lost":
        return [
            base,
            f"Tell a woodland fable where Boog handles the raffle badly, the tickets scatter, and the problem-solving attempt with {fix.id.replace('_', ' ')} comes too late, so the ending is sad.",
            "Write a cautionary animal fable about fairness, hurry, and shared games, ending with a lost raffle and a clear moral.",
        ]
    return [
        base,
        f"Tell a fable where Boog causes trouble at a raffle but helps solve it by using {fix.id.replace('_', ' ')}, so the fair can continue honestly.",
        "Write a gentle animal fable about a problem made by impatience and repaired by careful helping and fairness.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    elder = f["elder"]
    place = f["place"]
    prize = f["prize_cfg"]
    container = f["container_cfg"]
    fix = f["fix"]
    outcome = f["outcome"]
    items: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Boog, a young goat at a woodland fair, and the animals around him. "
            f"{friend.id} tried to steady him, and {elder.id} helped guide what happened after the trouble.",
        ),
        (
            "What did Boog want?",
            f"Boog wanted the {prize.label}, so he was excited about the raffle from the start. "
            f"That eager wish is what made him handle {container.label} too roughly.",
        ),
        (
            "What was the problem in the story?",
            f"The raffle tickets spilled out and scattered, so the fair could not keep drawing honestly. "
            f"Once the slips were mixed and flying, no one could trust whose chance belonged to whom.",
        ),
        (
            "Why did the raffle have to stop?",
            f'The raffle had to stop because the tickets were no longer in safe order. '
            f'A raffle must be fair, and scattered tickets make fairness hard to prove.',
        ),
    ]
    if outcome == "saved":
        items.append(
            (
                "How did they solve the problem?",
                f"They {fix.qa_text}. That worked because it made the tickets still enough to gather and count again before too many were lost.",
            )
        )
        items.append(
            (
                "Did Boog win the prize?",
                f"No, Boog did not win the {prize.label}. Still, he accepted the result because the raffle became fair again, and that mattered more than his own wish.",
            )
        )
        items.append(
            (
                "What did Boog learn?",
                f'Boog learned that hurry and wanting can damage a shared game. '
                f'He also learned that careful helping and honest counting can mend trouble when people act in time.',
            )
        )
    else:
        items.append(
            (
                "Could they save the raffle?",
                f"No. They tried to solve the problem, but the tickets had already become too scattered to trust, so the raffle was canceled.",
            )
        )
        items.append(
            (
                "How did the story end?",
                f"The prize was packed away and no one cheered at the raffle table. "
                f"Boog had to face the sad truth that his hurry spoiled something meant for everyone.",
            )
        )
        items.append(
            (
                "What did Boog learn from the bad ending?",
                f"Boog learned that some mistakes hurt more than one person and cannot always be fixed in time. "
                f"The bad ending taught him that fairness is fragile when greed and hurry take hold.",
            )
        )
    return items


def world_knowledge_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"raffle", "fairness"}
    place = f["place"]
    prize = f["prize_cfg"]
    fix = f["fix"]
    tags |= set(place.tags)
    tags |= set(prize.tags)
    tags |= set(fix.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_container(container: Container) -> str:
    return (
        f"(No story: {container.phrase} would not spill from Boog's eager turn the way this fable needs. "
        f"Pick a container like the raffle drum or the wicker basket.)"
    )


def explain_fix(fix: Fix) -> str:
    good = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix.id}': it is too weak or frantic for this world "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {good}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "saved" if is_saved(PLACES[params.place], FIXES[params.fix], params.delay) else "lost"


ASP_RULES = r"""
spill_possible(C) :- container(C), spillable(C).

valid(P, Pr, C) :- place(P), prize(Pr), container(C), spill_possible(C).

sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.

severity(V) :- chosen_place(P), wind(P, W), delay(D), water_bonus(P, WB), V = W + D + WB.
saved :- chosen_fix(F), power(F, PW), severity(V), PW >= V.
lost :- not saved.

outcome(saved) :- saved.
outcome(lost) :- lost.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("wind", place_id, place.wind))
        lines.append(asp.fact("water_bonus", place_id, 1 if place.water_nearby else 0))
    for prize_id in PRIZES:
        lines.append(asp.fact("prize", prize_id))
    for container_id, container in CONTAINERS.items():
        lines.append(asp.fact("container", container_id))
        if container.spillable:
            lines.append(asp.fact("spillable", container_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("power", fix_id, fix.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(f for (f,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_fix", params.fix),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {fix.id for fix in sensible_fixes()}
    asp_sensible = set(asp_sensible_fixes())
    if py_sensible == asp_sensible:
        print(f"OK: sensible fixes match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(asp_sensible)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    seeds_checked = 0
    parser = build_parser()
    while seeds_checked < 40:
        args = parser.parse_args([])
        try:
            params = resolve_params(args, random.Random(seeds_checked))
        except StoryError:
            seeds_checked += 1
            continue
        cases.append(params)
        seeds_checked += 1

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story during verify smoke test")
        print("OK: generate() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: Boog, a raffle, and a problem solved well or badly."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how much time slips away before the fix begins")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.container is not None:
        container = CONTAINERS[args.container]
        if not spill_possible(container):
            raise StoryError(explain_container(container))
    if args.fix is not None and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(FIXES[args.fix]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.prize is None or combo[1] == args.prize)
        and (args.container is None or combo[2] == args.container)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, prize, container = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    friend_name, friend_type = rng.choice(FRIENDS)
    elder_name, elder_type = rng.choice(ELDERS)
    return StoryParams(
        place=place,
        prize=prize,
        container=container,
        fix=fix,
        friend_name=friend_name,
        friend_type=friend_type,
        elder_name=elder_name,
        elder_type=elder_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.container not in CONTAINERS:
        raise StoryError(f"(Unknown container: {params.container})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if not spill_possible(CONTAINERS[params.container]):
        raise StoryError(explain_container(CONTAINERS[params.container]))
    if FIXES[params.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(FIXES[params.fix]))

    world = tell(
        place=PLACES[params.place],
        prize=PRIZES[params.prize],
        container=CONTAINERS[params.container],
        fix=FIXES[params.fix],
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_items(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible_fixes())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, prize, container) combos:\n")
        for place, prize, container in combos:
            print(f"  {place:10} {prize:8} {container}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### Boog at {p.place}: {p.container} / {p.fix} / {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
