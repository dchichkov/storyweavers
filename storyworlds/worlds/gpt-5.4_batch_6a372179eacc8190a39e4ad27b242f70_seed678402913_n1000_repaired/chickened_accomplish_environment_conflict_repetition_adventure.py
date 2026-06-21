#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/chickened_accomplish_environment_conflict_repetition_adventure.py

A standalone storyworld about a small outdoor adventure: two children want to
accomplish a ranger-style mission that helps the environment, but one child
nearly chickens out at a scary obstacle. The turn is driven by repeated, safe
practice steps, and the ending image proves both the child and the place have
changed.

Run it
------
python storyworlds/worlds/gpt-5.4/chickened_accomplish_environment_conflict_repetition_adventure.py
python storyworlds/worlds/gpt-5.4/chickened_accomplish_environment_conflict_repetition_adventure.py --environment forest --obstacle bridge --gear rope
python storyworlds/worlds/gpt-5.4/chickened_accomplish_environment_conflict_repetition_adventure.py --environment beach --obstacle bridge
python storyworlds/worlds/gpt-5.4/chickened_accomplish_environment_conflict_repetition_adventure.py --all
python storyworlds/worlds/gpt-5.4/chickened_accomplish_environment_conflict_repetition_adventure.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/chickened_accomplish_environment_conflict_repetition_adventure.py --json
python storyworlds/worlds/gpt-5.4/chickened_accomplish_environment_conflict_repetition_adventure.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
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
        female = {"girl", "mother", "woman", "female_ranger"}
        male = {"boy", "father", "man", "male_ranger"}
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
            "female_ranger": "ranger",
            "male_ranger": "ranger",
        }.get(self.type, self.label or self.type)


@dataclass
class EnvironmentCfg:
    id: str
    label: str
    start_scene: str
    mission_place: str
    mission_image: str
    litter: str
    obstacle_ids: tuple[str, ...]
    tags: set[str] = field(default_factory=set)


@dataclass
class ObstacleCfg:
    id: str
    label: str
    phrase: str
    method: str
    fear: int
    gear_ids: tuple[str, ...]
    scene: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GearCfg:
    id: str
    label: str
    phrase: str
    helps_with: tuple[str, ...]
    steady_bonus: int
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendStyle:
    id: str
    adjective: str
    comfort_line: str
    support_bonus: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    environment: str
    obstacle: str
    gear: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    friend_style: str
    ranger_type: str
    repetitions: int
    seed: Optional[int] = None


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


def _r_cleanup(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.role != "place":
            continue
        if ent.meters["litter_removed"] < THRESHOLD:
            continue
        sig = ("cleanup", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["health"] += 1
        for actor in [e for e in world.entities.values() if e.role in ("hero", "friend")]:
            actor.memes["pride"] += 1
        out.append("__cleaner__")
    return out


def _r_crossing_relief(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.role != "hero":
            continue
        if ent.meters["crossed"] < THRESHOLD:
            continue
        sig = ("relief", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["fear"] = 0.0
        ent.memes["relief"] += 1
        ent.memes["confidence"] += 1
        out.append("__crossed__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="cleanup", tag="physical", apply=_r_cleanup),
    Rule(name="crossing_relief", tag="emotional", apply=_r_crossing_relief),
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


ENVIRONMENTS = {
    "forest": EnvironmentCfg(
        id="forest",
        label="forest trail",
        start_scene="The piney trail smelled cool and green after the night rain.",
        mission_place="the lookout stump",
        mission_image="the little brass bell hanging beside the lookout stump",
        litter="a crumpled snack wrapper",
        obstacle_ids=("bridge", "hill"),
        tags={"environment", "forest"},
    ),
    "river": EnvironmentCfg(
        id="river",
        label="river path",
        start_scene="The river path glittered beside the water, and reeds nodded in the breeze.",
        mission_place="the stone marker",
        mission_image="the painted stone marker beside the shining river",
        litter="a plastic bottle caught in the reeds",
        obstacle_ids=("bridge", "rocks"),
        tags={"environment", "river"},
    ),
    "beach": EnvironmentCfg(
        id="beach",
        label="dune path",
        start_scene="The dune path curled between tall grasses while the sea hissed nearby.",
        mission_place="the shell flag",
        mission_image="the bright shell flag at the top of the dunes",
        litter="a tangled piece of string near the grass",
        obstacle_ids=("hill", "rocks"),
        tags={"environment", "beach"},
    ),
}

OBSTACLES = {
    "bridge": ObstacleCfg(
        id="bridge",
        label="bridge",
        phrase="a narrow plank bridge over a muddy stream",
        method="hold the side rope and take slow heel-to-toe steps",
        fear=4,
        gear_ids=("rope", "boots"),
        scene="The boards made a tiny clack under each breeze.",
        tags={"bridge", "crossing"},
    ),
    "hill": ObstacleCfg(
        id="hill",
        label="hill",
        phrase="a steep dirt hill with roots like little steps",
        method="plant each foot by a root and use steady pulls",
        fear=3,
        gear_ids=("boots", "rope"),
        scene="Pebbles slipped down whenever someone touched the slope.",
        tags={"hill", "climb"},
    ),
    "rocks": ObstacleCfg(
        id="rocks",
        label="rocks",
        phrase="a string of wet rocks leading across a shallow stream",
        method="aim for the dry tops and move one foot at a time",
        fear=4,
        gear_ids=("boots",),
        scene="The water kept slipping around the stones with a shiny whisper.",
        tags={"rocks", "crossing"},
    ),
}

GEAR = {
    "boots": GearCfg(
        id="boots",
        label="boots",
        phrase="mud-grip boots",
        helps_with=("bridge", "hill", "rocks"),
        steady_bonus=1,
        tags={"boots", "gear"},
    ),
    "rope": GearCfg(
        id="rope",
        label="rope",
        phrase="a guide rope with big knots",
        helps_with=("bridge", "hill"),
        steady_bonus=2,
        tags={"rope", "gear"},
    ),
}

FRIEND_STYLES = {
    "calm": FriendStyle(
        id="calm",
        adjective="calm",
        comfort_line="We do not have to rush. Small brave steps still count.",
        support_bonus=2,
        tags={"calm"},
    ),
    "cheery": FriendStyle(
        id="cheery",
        adjective="cheery",
        comfort_line="One step, then another. Adventures are built that way.",
        support_bonus=1,
        tags={"cheery"},
    ),
    "steady": FriendStyle(
        id="steady",
        adjective="steady",
        comfort_line="Try it the safe way with me right beside you.",
        support_bonus=2,
        tags={"steady"},
    ),
}

GIRL_NAMES = ["Lina", "Mia", "Nora", "Ava", "Zoe", "Tara", "Ruby", "June"]
BOY_NAMES = ["Owen", "Max", "Leo", "Finn", "Ben", "Eli", "Theo", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for env_id, env in ENVIRONMENTS.items():
        for obstacle_id in env.obstacle_ids:
            obstacle = OBSTACLES[obstacle_id]
            for gear_id, gear in GEAR.items():
                if obstacle.id in gear.helps_with and gear.id in obstacle.gear_ids:
                    combos.append((env_id, obstacle_id, gear_id))
    return sorted(combos)


def explain_rejection(environment: str, obstacle: str, gear: str) -> str:
    if environment not in ENVIRONMENTS:
        return f"(Unknown environment '{environment}'.)"
    if obstacle not in OBSTACLES:
        return f"(Unknown obstacle '{obstacle}'.)"
    if gear not in GEAR:
        return f"(Unknown gear '{gear}'.)"
    env = ENVIRONMENTS[environment]
    obs = OBSTACLES[obstacle]
    if obstacle not in env.obstacle_ids:
        return (
            f"(No story: {obs.label} does not fit the {env.label}. "
            f"Pick an obstacle that belongs in that environment.)"
        )
    if obstacle not in GEAR[gear].helps_with:
        return (
            f"(No story: {GEAR[gear].label} would not honestly help with the {obs.label}. "
            f"Pick gear that matches the obstacle.)"
        )
    return "(No story: this combination is not supported.)"


def support_score(friend_style: FriendStyle, gear: GearCfg, repetitions: int) -> int:
    return friend_style.support_bonus + gear.steady_bonus + repetitions


def outcome_of(params: StoryParams) -> str:
    if params.environment not in ENVIRONMENTS or params.obstacle not in OBSTACLES or params.gear not in GEAR:
        raise StoryError("(Unknown parameter key in outcome_of().)")
    if (params.environment, params.obstacle, params.gear) not in valid_combos():
        raise StoryError(explain_rejection(params.environment, params.obstacle, params.gear))
    score = support_score(FRIEND_STYLES[params.friend_style], GEAR[params.gear], params.repetitions)
    fear = OBSTACLES[params.obstacle].fear
    return "accomplished" if score >= fear + 1 else "turn_back"


def predict_crossing(world: World, obstacle: ObstacleCfg, gear: GearCfg, friend_style: FriendStyle,
                     repetitions: int) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.memes["fear"] = float(obstacle.fear)
    sim.facts["attempts"] = repetitions
    score = support_score(friend_style, gear, repetitions)
    sim.facts["predicted_support"] = score
    sim.facts["predicted_success"] = score >= obstacle.fear + 1
    return {
        "fear": obstacle.fear,
        "support": score,
        "success": bool(sim.facts["predicted_success"]),
    }


def introduce(world: World, env: EnvironmentCfg, hero: Entity, friend: Entity, ranger: Entity) -> None:
    hero.memes["hope"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"{hero.id} and {friend.id} met the park {ranger.label_word} at the edge of the {env.label}. "
        f"{env.start_scene}"
    )
    world.say(
        f'"Today\'s badge mission," the {ranger.label_word} said, "is simple: help the environment, '
        f"reach {env.mission_place}, and ring {env.mission_image}."'
    )


def receive_gear(world: World, hero: Entity, friend: Entity, gear: GearCfg) -> None:
    world.say(
        f"The {ranger_word(world)} handed them {gear.phrase}, and both children stood a little taller."
    )
    hero.meters["equipped"] += 1
    friend.meters["equipped"] += 1


def ranger_word(world: World) -> str:
    ranger = world.get("ranger")
    return ranger.label_word


def find_litter(world: World, env: EnvironmentCfg, hero: Entity, friend: Entity) -> None:
    place = world.get("place")
    world.say(
        f"Before they had gone far, {hero.id} spotted {env.litter} beside the path. "
        f'"That should not stay here," {hero.pronoun()} said.'
    )
    place.meters["litter_removed"] += 1
    hero.meters["helped"] += 1
    friend.meters["helped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} tucked it into the trail bag, and the path already looked kinder to the animals."
    )


def face_obstacle(world: World, obstacle: ObstacleCfg, hero: Entity, friend: Entity) -> None:
    hero.memes["fear"] = float(obstacle.fear)
    world.say(
        f"Soon they reached {obstacle.phrase}. {obstacle.scene}"
    )
    world.say(
        f"{hero.id} stopped so suddenly that {friend.id} almost bumped into {hero.pronoun('object')}."
    )
    world.say(
        f'For a moment, {hero.id} almost chickened out. "{obstacle.label.capitalize()} missions look easier in maps," '
        f"{hero.pronoun()} whispered."
    )


def encourage(world: World, hero: Entity, friend: Entity, friend_style: FriendStyle,
              obstacle: ObstacleCfg, repetitions: int) -> None:
    friend.memes["care"] += 1
    hero.memes["supported"] += friend_style.support_bonus
    world.say(
        f'{friend.id}, who was always {friend_style.adjective}, touched the guide rope and said, '
        f'"{friend_style.comfort_line}"'
    )
    mantra = "Step, breathe, hold"
    world.say(
        f'"We can say {mantra.lower()} together," {friend.id} added. '
        f'Then they practiced the words: "{mantra}. {mantra}. {mantra}."'
    )
    for _ in range(repetitions):
        hero.memes["practice"] += 1
    if repetitions == 1:
        world.say(
            f"They practiced the safe method once: {obstacle.method}."
        )
    elif repetitions == 2:
        world.say(
            f"They practiced the safe method twice on flat ground first: {obstacle.method}."
        )
    else:
        world.say(
            f"They practiced the safe method three times on flat ground first: {obstacle.method}."
        )


def attempt_crossing(world: World, hero: Entity, friend: Entity, obstacle: ObstacleCfg,
                     gear: GearCfg, friend_style: FriendStyle, repetitions: int) -> str:
    place = world.get("place")
    score = support_score(friend_style, gear, repetitions)
    world.facts["support"] = score
    world.facts["fear"] = obstacle.fear
    hero.meters["attempted"] += 1
    if score >= obstacle.fear + 1:
        hero.meters["crossed"] += 1
        place.meters["progress"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{hero.id} put on the {gear.label}, took a breath, and began. "
            f"{friend.id} stayed beside {hero.pronoun('object')} and repeated, "
            f'"Step, breathe, hold."'
        )
        world.say(
            f"One careful move became another, and soon {hero.id} was across. "
            f"What had looked huge from far away now felt possible."
        )
        return "accomplished"
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} tried the first move in the {gear.label}, but {hero.pronoun('possessive')} knees still wobbled. "
        f'The words "Step, breathe, hold" helped, yet not enough this time.'
    )
    world.say(
        f'"We can turn back and still be honest adventurers," the {ranger_word(world)} said when they caught up.'
    )
    return "turn_back"


def mission_end_success(world: World, env: EnvironmentCfg, hero: Entity, friend: Entity) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["pride"] += 1
    friend.memes["pride"] += 1
    world.say(
        f"At {env.mission_place}, {hero.id} rang {env.mission_image}, and the clear little sound flew through the air."
    )
    world.say(
        f'"We did it," {hero.id} said. "We helped the environment and accomplish-ed our mission."'
    )
    world.say(
        f'The {ranger_word(world)} laughed softly. "You accomplished it," {world.get("ranger").pronoun()} said. '
        f"The cleaner trail behind them and the bright bell ahead made the whole adventure feel real."
    )


def mission_end_turn_back(world: World, env: EnvironmentCfg, hero: Entity, friend: Entity) -> None:
    hero.memes["disappointment"] += 1
    friend.memes["care"] += 1
    world.say(
        f"They did not reach {env.mission_place} that day. Still, {hero.id} carried the trail bag back with {friend.id}, "
        f"and the path was cleaner than before."
    )
    world.say(
        f'"I did not accomplish the whole badge," {hero.id} said, "but I helped the environment and I know the safe steps now."'
    )
    world.say(
        f'The {ranger_word(world)} nodded. "That is how brave adventures grow," {world.get("ranger").pronoun()} said. '
        f"Behind them, the path looked tidier and less lonely."
    )


def tell(params: StoryParams) -> World:
    if params.environment not in ENVIRONMENTS:
        raise StoryError(f"(Unknown environment '{params.environment}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle '{params.obstacle}'.)")
    if params.gear not in GEAR:
        raise StoryError(f"(Unknown gear '{params.gear}'.)")
    if params.friend_style not in FRIEND_STYLES:
        raise StoryError(f"(Unknown friend style '{params.friend_style}'.)")
    if (params.environment, params.obstacle, params.gear) not in valid_combos():
        raise StoryError(explain_rejection(params.environment, params.obstacle, params.gear))
    if params.repetitions not in (1, 2, 3):
        raise StoryError("(Repetitions must be 1, 2, or 3.)")

    env = ENVIRONMENTS[params.environment]
    obstacle = OBSTACLES[params.obstacle]
    gear = GEAR[params.gear]
    friend_style = FRIEND_STYLES[params.friend_style]

    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_gender, label=params.friend_name, role="friend"))
    ranger = world.add(Entity(id="ranger", kind="character", type=params.ranger_type, label="ranger", role="ranger"))
    place = world.add(Entity(id="place", kind="thing", type="place", label=env.label, role="place"))

    world.facts.update(
        env=env,
        obstacle=obstacle,
        gear=gear,
        friend_style=friend_style,
        repetitions=params.repetitions,
    )

    introduce(world, env, hero, friend, ranger)
    receive_gear(world, hero, friend, gear)
    world.para()
    find_litter(world, env, hero, friend)
    face_obstacle(world, obstacle, hero, friend)
    world.para()
    pred = predict_crossing(world, obstacle, gear, friend_style, params.repetitions)
    world.facts["predicted_success"] = pred["success"]
    encourage(world, hero, friend, friend_style, obstacle, params.repetitions)
    outcome = attempt_crossing(world, hero, friend, obstacle, gear, friend_style, params.repetitions)
    world.para()
    if outcome == "accomplished":
        mission_end_success(world, env, hero, friend)
    else:
        mission_end_turn_back(world, env, hero, friend)

    world.facts.update(
        hero=hero,
        friend=friend,
        ranger=ranger,
        place=place,
        outcome=outcome,
        litter_removed=place.meters["litter_removed"] >= THRESHOLD,
        place_health=place.meters["health"],
        crossed=hero.meters["crossed"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "environment": [
        (
            "What does environment mean?",
            "The environment is the world around us, like air, water, plants, animals, and the places where they live. When people keep a place clean and safe, they help the environment."
        )
    ],
    "bridge": [
        (
            "Why do people cross a narrow bridge slowly?",
            "A narrow bridge gives you less room for your feet, so slow steps help you stay balanced. Moving carefully is safer than rushing."
        )
    ],
    "hill": [
        (
            "Why can a steep hill feel hard to climb?",
            "A steep hill tilts your body backward and can make your feet slip. Small, steady steps make climbing easier."
        )
    ],
    "rocks": [
        (
            "Why are wet rocks slippery?",
            "Wet rocks can be slick because water makes it easier for shoes to slide. That is why people step carefully on them."
        )
    ],
    "rope": [
        (
            "How can a rope help on a trail?",
            "A rope can give your hands something steady to hold. That can help you balance when a path feels tricky."
        )
    ],
    "boots": [
        (
            "Why do grippy boots help outdoors?",
            "Grippy boots help your feet hold the ground better. They can make mud, roots, and wet stones safer to step on."
        )
    ],
    "litter": [
        (
            "Why should litter be picked up?",
            "Litter can hurt animals and make a place look uncared for. Picking it up helps keep the area cleaner and safer."
        )
    ],
    "practice": [
        (
            "Why does practice help when something feels scary?",
            "Practice breaks a big job into smaller parts your body can learn. When you repeat safe steps, the job often feels less frightening."
        )
    ],
}
KNOWLEDGE_ORDER = ["environment", "litter", "bridge", "hill", "rocks", "rope", "boots", "practice"]


def generation_prompts(world: World) -> list[str]:
    env = world.facts["env"]
    obstacle = world.facts["obstacle"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes the exact words "chickened", "accomplish", and "environment".',
        f"Tell a gentle adventure where {hero.label} nearly chickened out at a {obstacle.label}, but a friend uses repeated safe steps to help.",
        f"Write a story set on a {env.label} where children help the environment during a mission and end with a clear image that proves what changed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    ranger = world.facts["ranger"]
    env = world.facts["env"]
    obstacle = world.facts["obstacle"]
    gear = world.facts["gear"]
    repetitions = world.facts["repetitions"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {friend.label}, two children on a small mission with a ranger. They are trying to help the environment while having an adventure."
        ),
        (
            "What mission did they have?",
            f"They were supposed to help the environment and reach {env.mission_place}. The bell or marker at the end showed whether they finished the trail mission."
        ),
        (
            f"Why did {hero.label} almost chicken out?",
            f"{hero.label} stopped at {obstacle.phrase} because it looked scary and difficult. The obstacle felt bigger than {hero.pronoun('possessive')} courage in that moment."
        ),
        (
            f"What did {friend.label} do to help?",
            f"{friend.label} stayed calm and taught a repeated safe pattern: 'Step, breathe, hold.' They also practiced the method {repetitions} time{'s' if repetitions != 1 else ''} before the real crossing."
        ),
        (
            "How did they help the environment?",
            f"They picked up {env.litter} from the trail. That small action made the path cleaner for animals and people."
        ),
    ]
    if outcome == "accomplished":
        qa.append(
            (
                "Did they accomplish the mission?",
                f"Yes. {hero.label} used the {gear.label}, followed the safe method, and got across the obstacle. Then {hero.pronoun()} reached {env.mission_place} and rang the bell or touched the marker."
            )
        )
        qa.append(
            (
                f"How did {hero.label} feel at the end?",
                f"{hero.label} felt relieved and proud. The finished crossing and the cleaner trail showed that {hero.pronoun()} had grown braver."
            )
        )
    else:
        qa.append(
            (
                "Did they accomplish the whole mission?",
                f"No, not the whole badge mission. But they still helped the environment and learned the safe steps for next time."
            )
        )
        qa.append(
            (
                f"Was turning back a failure?",
                f"No. Turning back was the safe choice when the obstacle still felt too hard. The story shows that honesty and caution can be part of a real adventure too."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    obstacle = world.facts["obstacle"]
    gear = world.facts["gear"]
    tags: set[str] = {"environment", "litter", "practice", obstacle.id, gear.id}
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
        if ent.label:
            bits.append(f"label={ent.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        environment="forest",
        obstacle="bridge",
        gear="rope",
        hero_name="Lina",
        hero_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        friend_style="calm",
        ranger_type="female_ranger",
        repetitions=3,
    ),
    StoryParams(
        environment="river",
        obstacle="rocks",
        gear="boots",
        hero_name="Max",
        hero_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        friend_style="steady",
        ranger_type="male_ranger",
        repetitions=2,
    ),
    StoryParams(
        environment="beach",
        obstacle="hill",
        gear="boots",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        friend_style="cheery",
        ranger_type="female_ranger",
        repetitions=2,
    ),
    StoryParams(
        environment="forest",
        obstacle="hill",
        gear="boots",
        hero_name="Eli",
        hero_gender="boy",
        friend_name="June",
        friend_gender="girl",
        friend_style="cheery",
        ranger_type="male_ranger",
        repetitions=1,
    ),
]


ASP_RULES = r"""
valid(E, O, G) :- environment(E), obstacle(O), gear(G), allows(E, O), helps(G, O), needs(O, G).

support(S) :- chosen_friend_style(F), friend_bonus(F, FB),
              chosen_gear(G), gear_bonus(G, GB),
              repetitions(R), S = FB + GB + R.

accomplished :- chosen_obstacle(O), fear(O, F), support(S), S >= F + 1.
turn_back    :- chosen_obstacle(O), fear(O, F), support(S), S < F + 1.

outcome(accomplished) :- accomplished.
outcome(turn_back) :- turn_back.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for env_id, env in ENVIRONMENTS.items():
        lines.append(asp.fact("environment", env_id))
        for obstacle_id in env.obstacle_ids:
            lines.append(asp.fact("allows", env_id, obstacle_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("fear", obstacle_id, obstacle.fear))
        for gear_id in obstacle.gear_ids:
            lines.append(asp.fact("needs", obstacle_id, gear_id))
    for gear_id, gear in GEAR.items():
        lines.append(asp.fact("gear", gear_id))
        lines.append(asp.fact("gear_bonus", gear_id, gear.steady_bonus))
        for obstacle_id in gear.helps_with:
            lines.append(asp.fact("helps", gear_id, obstacle_id))
    for style_id, style in FRIEND_STYLES.items():
        lines.append(asp.fact("friend_style", style_id))
        lines.append(asp.fact("friend_bonus", style_id, style.support_bonus))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_gear", params.gear),
        asp.fact("chosen_friend_style", params.friend_style),
        asp.fact("repetitions", params.repetitions),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_generation() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "environment" not in sample.story:
        raise StoryError("(Smoke test failed: story text missing expected content.)")
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        emit(sample, trace=False, qa=True, header="### smoke")
    finally:
        sys.stdout = old
    if "### smoke" not in buf.getvalue():
        raise StoryError("(Smoke test failed: emit() did not produce output.)")


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
    parser = build_parser()
    for s in range(30):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure during verify for seed {s}.")
            break
    mismatch = 0
    for p in cases:
        try:
            py = outcome_of(p)
            asp_out = asp_outcome(p)
            if py != asp_out:
                mismatch += 1
        except StoryError as err:
            rc = 1
            print(f"Outcome check crashed: {err}")
            break
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        _smoke_generation()
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld: a child nearly chickens out during an environment-helping mission."
    )
    ap.add_argument("--environment", choices=sorted(ENVIRONMENTS))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--gear", choices=sorted(GEAR))
    ap.add_argument("--friend-style", choices=sorted(FRIEND_STYLES))
    ap.add_argument("--repetitions", type=int, choices=[1, 2, 3])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--ranger", choices=["female_ranger", "male_ranger"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.environment and args.obstacle and args.gear:
        combo = (args.environment, args.obstacle, args.gear)
        if combo not in valid_combos():
            raise StoryError(explain_rejection(args.environment, args.obstacle, args.gear))

    combos = [
        combo for combo in valid_combos()
        if (args.environment is None or combo[0] == args.environment)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.gear is None or combo[2] == args.gear)
    ]
    if not combos:
        if args.environment and args.obstacle and args.gear:
            raise StoryError(explain_rejection(args.environment, args.obstacle, args.gear))
        raise StoryError("(No valid combination matches the given options.)")

    environment, obstacle, gear = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    friend_style = args.friend_style or rng.choice(sorted(FRIEND_STYLES))
    ranger_type = args.ranger or rng.choice(["female_ranger", "male_ranger"])
    repetitions = args.repetitions if args.repetitions is not None else rng.choice([1, 2, 3])

    return StoryParams(
        environment=environment,
        obstacle=obstacle,
        gear=gear,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        friend_style=friend_style,
        ranger_type=ranger_type,
        repetitions=repetitions,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (environment, obstacle, gear) combos:\n")
        for env, obstacle, gear in combos:
            print(f"  {env:9} {obstacle:8} {gear}")
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
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = (
                f"### {p.hero_name} and {p.friend_name}: "
                f"{p.environment} / {p.obstacle} / {p.gear} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
