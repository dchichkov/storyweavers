#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sneaker_sight_happy_ending_magic_adventure.py
========================================================================

A standalone storyworld for a small magical adventure about a child who finds a
magic sneaker and uses it to see a hidden path. The world models a simple
problem/fix shape: an exciting goal lies beyond an obstacle, the obstacle is
reasonable only when the chosen magic can really solve it, and the ending image
proves the adventure changed the world.

Run it
------
    python storyworlds/worlds/gpt-5.4/sneaker_sight_happy_ending_magic_adventure.py
    python storyworlds/worlds/gpt-5.4/sneaker_sight_happy_ending_magic_adventure.py --place woods --obstacle mist --goal tower
    python storyworlds/worlds/gpt-5.4/sneaker_sight_happy_ending_magic_adventure.py --magic leap
    python storyworlds/worlds/gpt-5.4/sneaker_sight_happy_ending_magic_adventure.py --all
    python storyworlds/worlds/gpt-5.4/sneaker_sight_happy_ending_magic_adventure.py --verify
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
    phrase: str
    path_word: str
    wonder: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    blocks: str
    danger: str
    solve_with: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    treasure: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicMode:
    id: str
    label: str
    verb: str
    power_text: str
    solve: set[str] = field(default_factory=set)
    lesson: str = ""
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


def _r_blocked(world: World) -> list[str]:
    hero = world.get("hero")
    obstacle = world.get("obstacle")
    if hero.meters["at_obstacle"] < THRESHOLD or obstacle.meters["open"] >= THRESHOLD:
        return []
    sig = ("blocked",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    world.get("trail").meters["risk"] += 1
    return ["__blocked__"]


def _r_open_path(world: World) -> list[str]:
    sneaker = world.get("sneaker")
    obstacle = world.get("obstacle")
    if sneaker.meters["casting"] < THRESHOLD or obstacle.meters["solvable"] < THRESHOLD:
        return []
    sig = ("open",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["open"] += 1
    hero = world.get("hero")
    hero.memes["hope"] += 1
    world.get("trail").meters["clear"] += 1
    return ["__open__"]


CAUSAL_RULES = [
    Rule(name="blocked", tag="physical", apply=_r_blocked),
    Rule(name="open_path", tag="physical", apply=_r_open_path),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for item in produced:
            world.say(item)
    return produced


PLACES = {
    "woods": Place(
        id="woods",
        label="whispering woods",
        phrase="the whispering woods behind the village",
        path_word="fern path",
        wonder="silver leaves clicked softly above the trail",
        tags={"woods", "adventure"},
    ),
    "cliffs": Place(
        id="cliffs",
        label="sunny cliffs",
        phrase="the sunny cliffs above the sea",
        path_word="stone path",
        wonder="small gulls wheeled through bright blue air",
        tags={"cliffs", "adventure"},
    ),
    "meadow": Place(
        id="meadow",
        label="star meadow",
        phrase="the star meadow at the edge of town",
        path_word="flower path",
        wonder="bells of blue flowers nodded in the breeze",
        tags={"meadow", "adventure"},
    ),
}

OBSTACLES = {
    "mist": Obstacle(
        id="mist",
        label="mist",
        phrase="a wall of moon-pale mist",
        blocks="sight",
        danger="The child could not see where the path went.",
        solve_with={"sight", "wind"},
        tags={"mist", "sight"},
    ),
    "ravine": Obstacle(
        id="ravine",
        label="ravine",
        phrase="a narrow ravine with a broken stepping path",
        blocks="reach",
        danger="The child could see the way ahead, but could not cross safely.",
        solve_with={"leap", "bridge"},
        tags={"ravine"},
    ),
    "thorn_gate": Obstacle(
        id="thorn_gate",
        label="thorn gate",
        phrase="a ring of enchanted thorns",
        blocks="passage",
        danger="The child could not squeeze through without getting scratched.",
        solve_with={"song", "sight"},
        tags={"thorns"},
    ),
}

GOALS = {
    "tower": Goal(
        id="tower",
        label="star tower",
        phrase="the little star tower on the hill",
        treasure="a bell that could ring rainbow light",
        ending_image="The tower window shone gold across the valley.",
        tags={"tower", "magic"},
    ),
    "pond": Goal(
        id="pond",
        label="silver pond",
        phrase="the silver pond hidden under willow branches",
        treasure="a cup of sparkling water for the village garden",
        ending_image="The pond flashed like a coin under the evening sky.",
        tags={"pond", "magic"},
    ),
    "nest": Goal(
        id="nest",
        label="cloud nest",
        phrase="the cloud nest where a baby moonbird waited",
        treasure="a lost ribbon-star to return to the nest",
        ending_image="The moonbird tucked its head under one bright wing and slept.",
        tags={"bird", "magic"},
    ),
}

MAGIC = {
    "sight": MagicMode(
        id="sight",
        label="far sight",
        verb="show hidden steps",
        power_text="the blue stripe on the sneaker glowed, and bright footprints appeared where no ordinary eyes could see",
        solve={"sight", "passage"},
        lesson="Some paths only appear when you look carefully and kindly.",
        tags={"sight", "sneaker", "magic"},
    ),
    "leap": MagicMode(
        id="leap",
        label="spring leap",
        verb="take a giant jump",
        power_text="the magic sneaker grew warm, and one brave step carried the child farther than any ordinary hop",
        solve={"reach"},
        lesson="Courage works best when it lands on something real.",
        tags={"jump", "sneaker", "magic"},
    ),
    "song": MagicMode(
        id="song",
        label="humming charm",
        verb="hum open the way",
        power_text="the sole of the sneaker thrummed like a tiny drum, and the nearest thorns curled aside to listen",
        solve={"passage"},
        lesson="A gentle sound can untangle a hard knot.",
        tags={"song", "sneaker", "magic"},
    ),
    "wind": MagicMode(
        id="wind",
        label="wind whisper",
        verb="blow the path clear",
        power_text="the laces fluttered by themselves, and a sweet little wind brushed the air until the hidden trail came clear",
        solve={"sight"},
        lesson="Sometimes help comes as softly as a breeze.",
        tags={"wind", "sneaker", "magic"},
    ),
    "bridge": MagicMode(
        id="bridge",
        label="ribbon bridge",
        verb="lay a shining bridge",
        power_text="a silver ribbon poured from the sneaker tongue and stretched itself neatly across the gap",
        solve={"reach"},
        lesson="Good magic makes a safe way for others too.",
        tags={"bridge", "sneaker", "magic"},
    ),
}

GIRL_NAMES = ["Lila", "Mira", "Nora", "Ava", "Tessa", "Ruby", "Ella", "Mina"]
BOY_NAMES = ["Finn", "Leo", "Theo", "Milo", "Ben", "Sam", "Owen", "Eli"]
TRAITS = ["curious", "brave", "careful", "hopeful", "quick", "kind"]


def valid_combo(place_id: str, obstacle_id: str, magic_id: str) -> bool:
    obstacle = OBSTACLES[obstacle_id]
    magic = MAGIC[magic_id]
    return obstacle.blocks in magic.solve or bool(obstacle.solve_with & magic.solve)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for obstacle_id in OBSTACLES:
            for goal_id in GOALS:
                for magic_id in MAGIC:
                    if valid_combo(place_id, obstacle_id, magic_id):
                        combos.append((place_id, obstacle_id, goal_id, magic_id))
    return combos


@dataclass
class StoryParams:
    place: str
    obstacle: str
    goal: str
    magic: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="woods",
        obstacle="mist",
        goal="tower",
        magic="sight",
        name="Lila",
        gender="girl",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        place="cliffs",
        obstacle="ravine",
        goal="nest",
        magic="bridge",
        name="Finn",
        gender="boy",
        parent="father",
        trait="brave",
    ),
    StoryParams(
        place="meadow",
        obstacle="thorn_gate",
        goal="pond",
        magic="song",
        name="Mina",
        gender="girl",
        parent="mother",
        trait="kind",
    ),
    StoryParams(
        place="woods",
        obstacle="thorn_gate",
        goal="tower",
        magic="sight",
        name="Theo",
        gender="boy",
        parent="father",
        trait="careful",
    ),
    StoryParams(
        place="cliffs",
        obstacle="mist",
        goal="pond",
        magic="wind",
        name="Ruby",
        gender="girl",
        parent="mother",
        trait="hopeful",
    ),
]


def explain_rejection(obstacle_id: str, magic_id: str) -> str:
    obstacle = OBSTACLES[obstacle_id]
    magic = MAGIC[magic_id]
    return (
        f"(No story: {magic.label} cannot honestly solve {obstacle.phrase}. "
        f"The obstacle blocks {obstacle.blocks}, so pick magic that really opens the way.)"
    )


def introduce(world: World, hero: Entity, parent: Entity, place: Place) -> None:
    world.say(
        f"One bright morning, {hero.id} set out for {place.phrase} with {hero.pronoun('possessive')} "
        f"{parent.label_word}. {place.wonder}"
    )
    world.say(
        f"{hero.pronoun().capitalize()} had one ordinary shoe and one strange old sneaker with a blue stripe, "
        f"because that was the only magic sneaker the attic chest had given {hero.pronoun('object')}."
    )


def hear_call(world: World, hero: Entity, goal: Goal) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"From far away came a tiny calling sound from {goal.phrase}. It seemed to promise {goal.treasure}."
    )
    world.say(
        f'{hero.id} stopped and whispered, "I think an adventure is asking for me."'
    )


def part_kindly(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["love"] += 1
    world.say(
        f'{hero.id}\'s {parent.label_word} squeezed {hero.pronoun("possessive")} shoulder. '
        f'"Stay on the path, use your kind head, and come tell me what you find," '
        f'{parent.pronoun()} said.'
    )


def approach(world: World, hero: Entity, place: Place, obstacle: Obstacle, goal: Goal) -> None:
    hero.meters["at_obstacle"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {hero.id} followed the {place.path_word} until {hero.pronoun()} nearly reached {goal.phrase}."
    )
    world.say(
        f"But across the way stood {obstacle.phrase}. {obstacle.danger}"
    )


def predict_clear(world: World) -> bool:
    sim = world.copy()
    sim.get("sneaker").meters["casting"] += 1
    propagate(sim, narrate=False)
    return sim.get("obstacle").meters["open"] >= THRESHOLD


def doubt(world: World, hero: Entity, magic: MagicMode) -> None:
    world.say(
        f"{hero.id} looked down at the old sneaker. It felt silly to trust one shoe, even a magic one."
    )
    if magic.id == "sight":
        world.say(
            f"Still, {hero.pronoun()} remembered the attic note that promised true sight to brave walkers."
        )
    else:
        world.say(
            f"Still, the laces gave a tiny twitch, as if the sneaker already knew a way forward."
        )


def cast_magic(world: World, hero: Entity, magic: MagicMode) -> None:
    sneaker = world.get("sneaker")
    sneaker.meters["casting"] += 1
    hero.memes["courage"] += 1
    world.say(
        f"{hero.id} stamped once, twice, and asked the sneaker to {magic.verb}. At once, {magic.power_text}."
    )
    propagate(world, narrate=False)


def cross(world: World, hero: Entity, obstacle: Obstacle) -> None:
    world.get("trail").meters["crossed"] += 1
    hero.meters["past_obstacle"] += 1
    hero.memes["joy"] += 1
    if obstacle.id == "mist":
        world.say(
            f"With new sight, {hero.id} stepped from bright footprint to bright footprint until the mist was behind {hero.pronoun('object')}."
        )
    elif obstacle.id == "ravine":
        world.say(
            f"{hero.id} crossed the gap with a pounding heart, then laughed when both feet landed safe on the far side."
        )
    else:
        world.say(
            f"{hero.id} slipped through the opened way without a single scratch on {hero.pronoun('possessive')} knees."
        )


def reach_goal(world: World, hero: Entity, goal: Goal) -> None:
    hero.meters["at_goal"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"Beyond the obstacle waited {goal.phrase}, just as magical as the story had promised."
    )
    if goal.id == "tower":
        world.say(
            f"Inside, {hero.id} rang {goal.treasure}, and soft bands of rainbow light slid over the roofs below."
        )
    elif goal.id == "pond":
        world.say(
            f"There {hero.pronoun()} filled a little cup with {goal.treasure}, and the water sparkled without spilling."
        )
    else:
        world.say(
            f"There {hero.pronoun()} set down {goal.treasure}, and the baby moonbird chirped with sleepy happiness."
        )


def return_home(world: World, hero: Entity, parent: Entity, goal: Goal, magic: MagicMode) -> None:
    hero.memes["pride"] += 1
    hero.memes["love"] += 1
    world.say(
        f"When {hero.id} came back, {hero.pronoun('possessive')} {parent.label_word} was waiting at the gate."
    )
    if goal.id == "pond":
        world.say(
            f"Together they poured the sparkling water onto the village garden, and every drooping stem lifted its head."
        )
    elif goal.id == "tower":
        world.say(
            f"Together they watched the rainbow light from the tower dance across every window in the lane."
        )
    else:
        world.say(
            f"Together they listened as the moonbird settled safely in its nest and the evening sky turned calm and pearly."
        )
    world.say(
        f'{hero.id} held up the sneaker and grinned. "{magic.lesson}"'
    )
    world.say(goal.ending_image)


def tell(
    place: Place,
    obstacle: Obstacle,
    goal: Goal,
    magic: MagicMode,
    *,
    name: str,
    gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            label=name,
            phrase=name,
            role="hero",
            traits=[trait],
            tags={"hero"},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label="the parent",
            phrase="the parent",
            role="parent",
            tags={"adult"},
        )
    )
    sneaker = world.add(
        Entity(
            id="sneaker",
            type="sneaker",
            label="sneaker",
            phrase="the magic sneaker",
            role="artifact",
            tags={"sneaker", "magic"},
        )
    )
    trail = world.add(
        Entity(
            id="trail",
            type="trail",
            label=place.path_word,
            phrase=place.path_word,
            role="path",
        )
    )
    obstacle_ent = world.add(
        Entity(
            id="obstacle",
            type="obstacle",
            label=obstacle.label,
            phrase=obstacle.phrase,
            role="obstacle",
            attrs={"blocks": obstacle.blocks},
            tags=set(obstacle.tags),
        )
    )
    if valid_combo(place.id, obstacle.id, magic.id):
        obstacle_ent.meters["solvable"] += 1

    introduce(world, hero, parent, place)
    hear_call(world, hero, goal)
    part_kindly(world, hero, parent)

    world.para()
    approach(world, hero, place, obstacle, goal)
    doubt(world, hero, magic)

    world.para()
    if not predict_clear(world):
        raise StoryError(explain_rejection(obstacle.id, magic.id))
    cast_magic(world, hero, magic)
    cross(world, hero, obstacle)
    reach_goal(world, hero, goal)

    world.para()
    return_home(world, hero, parent, goal, magic)

    world.facts.update(
        hero=hero,
        parent=parent,
        sneaker=sneaker,
        trail=trail,
        place=place,
        obstacle_cfg=obstacle,
        goal_cfg=goal,
        magic_cfg=magic,
        obstacle_open=world.get("obstacle").meters["open"] >= THRESHOLD,
        reached_goal=hero.meters["at_goal"] >= THRESHOLD,
        happy_ending=hero.memes["pride"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "sneaker": [
        (
            "What is a sneaker?",
            "A sneaker is a soft shoe made for walking, running, and playing. It bends more easily than a stiff dress shoe."
        )
    ],
    "sight": [
        (
            "What does sight mean?",
            "Sight is your ability to see with your eyes. Good sight helps you notice where things are and how to move safely."
        )
    ],
    "mist": [
        (
            "Why is mist hard to walk through?",
            "Mist is made of tiny drops of water floating in the air. It can hide the path and make it harder to see where to step."
        )
    ],
    "ravine": [
        (
            "What is a ravine?",
            "A ravine is a deep crack or steep little valley in the ground. You should cross one only where there is a safe path or bridge."
        )
    ],
    "thorns": [
        (
            "Why do thorns hurt?",
            "Thorns are sharp points on some plants. They protect the plant, but they can scratch skin and catch on clothes."
        )
    ],
    "bridge": [
        (
            "What does a bridge do?",
            "A bridge makes a safe way over a gap or water. It lets people cross from one side to the other."
        )
    ],
    "magic": [
        (
            "What is magic in a story?",
            "Magic in a story is a special power that can do surprising things. In a good adventure, the magic still needs to solve the right problem."
        )
    ],
    "adventure": [
        (
            "What makes something an adventure?",
            "An adventure is a journey with something new, risky, or exciting in it. The traveler has to keep going and make good choices."
        )
    ],
}

KNOWLEDGE_ORDER = ["sneaker", "sight", "mist", "ravine", "thorns", "bridge", "magic", "adventure"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    obstacle = f["obstacle_cfg"]
    goal = f["goal_cfg"]
    magic = f["magic_cfg"]
    return [
        'Write a magical adventure story for a 3-to-5-year-old that includes the words "sneaker" and "sight" and ends happily.',
        f"Tell a gentle adventure where {hero.id} finds a magic sneaker, travels through {place.phrase}, and uses {magic.label} to get past {obstacle.phrase}.",
        f"Write a short story about a child reaching {goal.phrase} by solving a real problem with the right kind of magic, not just random spells.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    place = f["place"]
    obstacle = f["obstacle_cfg"]
    goal = f["goal_cfg"]
    magic = f["magic_cfg"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child who went on a magical adventure with one special sneaker. {hero.id}'s {pw} starts the story by sending {hero.pronoun('object')} off kindly."
        ),
        (
            "Where did the adventure happen?",
            f"The adventure happened in {place.phrase}. The path there led toward {goal.phrase}."
        ),
        (
            "What problem stopped the child?",
            f"The problem was {obstacle.phrase}. {obstacle.danger}"
        ),
        (
            "How did the sneaker help?",
            f"The sneaker used {magic.label}. It worked because that kind of magic could really solve a problem that blocked {obstacle.blocks}."
        ),
    ]
    if f["obstacle_open"]:
        qa.append(
            (
                "Why was sight important in this story?",
                f"Sight mattered because the path could not be trusted until the child could truly see the way. The magic changed confusion into a clear next step."
            )
        )
    if f["reached_goal"]:
        qa.append(
            (
                f"What happened when {hero.id} reached the goal?",
                f"{hero.id} reached {goal.phrase} and found {goal.treasure}. That success showed the adventure had been worth the fear and effort."
            )
        )
    if f["happy_ending"]:
        qa.append(
            (
                "Why is this a happy ending?",
                f"It is a happy ending because the child gets home safe, shares the good result, and keeps the magic lesson. The last image shows the world brighter and calmer than it was at the start."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sneaker", "magic", "adventure"}
    obstacle = f["obstacle_cfg"]
    magic = f["magic_cfg"]
    if obstacle.id == "mist":
        tags.add("mist")
        tags.add("sight")
    elif obstacle.id == "ravine":
        tags.add("ravine")
    else:
        tags.add("thorns")
    if magic.id == "bridge":
        tags.add("bridge")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:9} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
compatible_magic(M, O) :- magic(M), obstacle(O), solves(M, B), blocks(O, B).
compatible_magic(M, O) :- magic(M), obstacle(O), solves(M, B), obstacle_allows(O, B).
valid(P, O, G, M) :- place(P), obstacle(O), goal(G), magic(M), compatible_magic(M, O).
clears(O, M) :- compatible_magic(M, O).
reachable(O, M) :- clears(O, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("blocks", obstacle_id, obstacle.blocks))
        for item in sorted(obstacle.solve_with):
            lines.append(asp.fact("obstacle_allows", obstacle_id, item))
    for goal_id in GOALS:
        lines.append(asp.fact("goal", goal_id))
    for magic_id, magic in MAGIC.items():
        lines.append(asp.fact("magic", magic_id))
        for item in sorted(magic.solve):
            lines.append(asp.fact("solves", magic_id, item))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_reachable(obstacle_id: str, magic_id: str) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", obstacle_id),
            asp.fact("chosen_magic", magic_id),
            "ok :- chosen_obstacle(O), chosen_magic(M), reachable(O, M).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show ok/0."))
    return bool(asp.atoms(model, "ok"))


def outcome_ok(params: StoryParams) -> bool:
    return valid_combo(params.place, params.obstacle, params.magic)


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

    for params in CURATED:
        if asp_reachable(params.obstacle, params.magic) != outcome_ok(params):
            rc = 1
            print(f"MISMATCH on curated case: {params}")
            break
    else:
        print(f"OK: reachability matches Python on {len(CURATED)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Magic adventure storyworld: a child, a sneaker, and a hidden path."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible scenarios from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.magic and not valid_combo(args.place or next(iter(PLACES)), args.obstacle, args.magic):
        raise StoryError(explain_rejection(args.obstacle, args.magic))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.goal is None or combo[2] == args.goal)
        and (args.magic is None or combo[3] == args.magic)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, goal_id, magic_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        obstacle=obstacle_id,
        goal=goal_id,
        magic=magic_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"Unknown obstacle: {params.obstacle}")
    if params.goal not in GOALS:
        raise StoryError(f"Unknown goal: {params.goal}")
    if params.magic not in MAGIC:
        raise StoryError(f"Unknown magic: {params.magic}")
    if not valid_combo(params.place, params.obstacle, params.magic):
        raise StoryError(explain_rejection(params.obstacle, params.magic))

    world = tell(
        PLACES[params.place],
        OBSTACLES[params.obstacle],
        GOALS[params.goal],
        MAGIC[params.magic],
        name=params.name,
        gender=params.gender,
        parent_type=params.parent,
        trait=params.trait,
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, obstacle, goal, magic) combos:\n")
        for place_id, obstacle_id, goal_id, magic_id in combos:
            print(f"  {place_id:8} {obstacle_id:11} {goal_id:8} {magic_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.magic} at {p.place} past {p.obstacle} toward {p.goal}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
