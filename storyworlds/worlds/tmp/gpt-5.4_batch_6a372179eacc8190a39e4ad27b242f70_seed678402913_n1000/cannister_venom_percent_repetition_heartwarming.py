#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cannister_venom_percent_repetition_heartwarming.py
==============================================================================

A standalone storyworld about a child carrying a water cannister for a kind
outdoor chore, spotting a snake in the way, learning a calm safety refrain, and
finishing the chore with help. The required seed words appear naturally:

- cannister
- venom
- percent

The world's repeated line is: "Back up, breathe, call for help."

Run it
------
    python storyworlds/worlds/gpt-5.4/cannister_venom_percent_repetition_heartwarming.py
    python storyworlds/worlds/gpt-5.4/cannister_venom_percent_repetition_heartwarming.py --setting garden --chore birdbath
    python storyworlds/worlds/gpt-5.4/cannister_venom_percent_repetition_heartwarming.py --snake copperhead --response tap_tail
    python storyworlds/worlds/gpt-5.4/cannister_venom_percent_repetition_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/cannister_venom_percent_repetition_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4/cannister_venom_percent_repetition_heartwarming.py --verify
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
SAFE_MIN = 2
REFRAIN = "Back up, breathe, call for help."


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
        female = {"girl", "woman", "mother", "mom", "aunt", "grandmother", "ranger_woman"}
        male = {"boy", "man", "father", "dad", "uncle", "grandfather", "ranger_man"}
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
            "aunt": "aunt",
            "uncle": "uncle",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    nature: str
    opening: str
    sign_percent: int
    snake_kinds: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Chore:
    id: str
    target: str
    need: str
    finish: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SnakeKind:
    id: str
    label: str
    colors: str
    temperament: str
    habitat: set[str] = field(default_factory=set)
    venomous: bool = False
    danger: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    safe: int
    ranger_needed: bool
    text: str
    qa_text: str
    fail_text: str
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
        out = World()
        out.entities = copy.deepcopy(self.entities)
        out.fired = set(self.fired)
        out.paragraphs = [[]]
        out.facts = copy.deepcopy(self.facts)
        return out


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_near_snake(world: World) -> list[str]:
    child = world.get("child")
    snake = world.get("snake")
    if child.meters["reaching"] < THRESHOLD or snake.meters["blocking"] < THRESHOLD:
        return []
    sig = ("danger",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    world.get("adult").memes["protective"] += 1
    world.get("path").meters["danger"] += 1
    return ["__danger__"]


def _r_safe_distance(world: World) -> list[str]:
    child = world.get("child")
    snake = world.get("snake")
    if child.meters["distance"] < THRESHOLD or snake.meters["blocking"] < THRESHOLD:
        return []
    sig = ("calmer",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["calm"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    return []


def _r_help_clears_risk(world: World) -> list[str]:
    if world.get("snake").meters["blocking"] < THRESHOLD:
        return []
    if world.get("helper").meters["guided"] < THRESHOLD:
        return []
    sig = ("clear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("snake").meters["blocking"] = 0.0
    world.get("path").meters["danger"] = 0.0
    world.get("child").memes["relief"] += 1
    world.get("adult").memes["relief"] += 1
    return []


def _r_finish_chore(world: World) -> list[str]:
    if world.get("chore_target").meters["watered"] < THRESHOLD:
        return []
    sig = ("birds_return",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("child").memes["joy"] += 1
    world.get("adult").memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="near_snake", tag="risk", apply=_r_near_snake),
    Rule(name="safe_distance", tag="emotion", apply=_r_safe_distance),
    Rule(name="help_clears_risk", tag="resolution", apply=_r_help_clears_risk),
    Rule(name="finish_chore", tag="resolution", apply=_r_finish_chore),
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


def habitat_ok(setting: Setting, snake: SnakeKind) -> bool:
    return setting.id in snake.habitat and snake.id in setting.snake_kinds


def safe_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.safe >= SAFE_MIN]


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    safer = ", ".join(sorted(r.id for r in safe_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on safety "
        f"(safe={response.safe} < {SAFE_MIN}). This world only tells calm, sensible "
        f"snake-safety stories. Try: {safer}.)"
    )


def predict_risk(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["reaching"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("path").meters["danger"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, adult: Entity, setting: Setting, chore: Chore) -> None:
    child.memes["kindness"] += 1
    world.say(
        f"{child.id} loved small caring jobs. That morning, {adult.label_word} and "
        f"{child.pronoun('subject')} walked to {setting.place} with a blue water "
        f"cannister because {chore.need}."
    )
    world.say(setting.opening)
    world.say(
        f"{child.id} swung the cannister carefully and smiled. Helping felt important."
    )


def notice_task(world: World, child: Entity, chore: Chore) -> None:
    world.say(
        f'"I can do it," {child.id} said, looking at {chore.target}. '
        f'{chore.need.capitalize()}.'
    )
    child.memes["eager"] += 1


def spot_snake(world: World, child: Entity, snake: Entity, snake_cfg: SnakeKind) -> None:
    snake.meters["blocking"] += 1
    world.say(
        f"But halfway there, {child.id} stopped. A {snake_cfg.colors} snake was "
        f"curled across the path, warm and still like a little rope that could move."
    )
    world.say(
        f"{child.id} hugged the cannister closer and stared at the snake."
    )


def warn(world: World, child: Entity, adult: Entity, setting: Setting, snake_cfg: SnakeKind) -> None:
    pred = predict_risk(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{adult.label_word.capitalize()} knelt beside {child.id}. "{REFRAIN}" '
        f'{adult.pronoun()} whispered once.'
    )
    world.say(
        f'Then {adult.pronoun()} said, "The sign by the gate says only '
        f'{setting.sign_percent} percent of the snakes around here have venom that '
        f'can make people very sick. But we never guess which snake is which. '
        f'We give every snake space."'
    )
    if snake_cfg.venomous:
        world.say(
            f"The snake might have venom, so standing back was the safest choice."
        )
    else:
        world.say(
            f"Even though many snakes here are harmless, guessing from far away is not safe."
        )


def reach_then_stop(world: World, child: Entity) -> None:
    child.meters["reaching"] += 1
    propagate(world, narrate=False)
    world.say(
        f"For one quick second, {child.id} almost stepped forward with the cannister."
    )
    if child.memes["fear"] >= THRESHOLD:
        world.say(
            f"Then the quiet warning inside {child.pronoun('possessive')} chest felt real, and "
            f"{child.pronoun('subject')} froze."
        )


def step_back(world: World, child: Entity, adult: Entity) -> None:
    child.meters["distance"] += 1
    child.memes["trust"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"{REFRAIN}" {child.id} repeated.'
    )
    world.say(
        f"{child.pronoun().capitalize()} took three slow steps back until {adult.label_word} "
        f"rested a steady hand on {child.pronoun('possessive')} shoulder."
    )


def call_helper(world: World, adult: Entity, helper: Entity, response: Response) -> None:
    adult.memes["care"] += 1
    helper.meters["coming"] += 1
    if response.ranger_needed:
        world.say(
            f'{adult.label_word.capitalize()} used the phone and called the park ranger. '
            f'"A child found a snake near the path," {adult.pronoun()} said.'
        )
    else:
        world.say(
            f'{adult.label_word.capitalize()} waited with {child_name(world)} and watched the snake '
            f'from far away.'
        )


def child_name(world: World) -> str:
    return world.get("child").id


def resolve_snake(world: World, helper: Entity, snake: Entity, response: Response, snake_cfg: SnakeKind) -> None:
    helper.meters["guided"] += 1
    propagate(world, narrate=False)
    if response.id == "ranger_tub":
        world.say(
            f"Soon the ranger arrived with a tall clear tub and a long hook. "
            f"{helper.pronoun().capitalize()} moved slowly, slowly, slowly."
        )
        world.say(response.text.format(snake=snake_cfg.label))
    elif response.id == "wait_path":
        world.say(
            f"For a minute nobody hurried. They just watched from far away."
        )
        world.say(response.text.format(snake=snake_cfg.label))
    else:
        world.say(response.text.format(snake=snake_cfg.label))


def finish_chore(world: World, child: Entity, adult: Entity, chore: Chore) -> None:
    world.get("chore_target").meters["watered"] += 1
    world.get("cannister").meters["emptied"] += 1
    propagate(world, narrate=False)
    world.say(
        f"After the path was clear, {child.id} carried the cannister the rest of the way."
    )
    world.say(
        f"{chore.finish} {chore.ending_image}"
    )


def close_story(world: World, child: Entity, adult: Entity) -> None:
    child.memes["lesson"] += 1
    world.say(
        f'{adult.label_word.capitalize()} smiled and squeezed {child.id}\'s hand. '
        f'"You remembered the safe words," {adult.pronoun()} said.'
    )
    world.say(
        f'"{REFRAIN}" {child.id} answered again, and this time the words sounded warm instead of scared.'
    )


def tell(
    setting: Setting,
    chore: Chore,
    snake_cfg: SnakeKind,
    response: Response,
    *,
    child_name_value: str = "Mira",
    child_type: str = "girl",
    adult_type: str = "grandfather",
    helper_type: str = "ranger_woman",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name_value, role="child"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label="the grown-up", role="adult"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label="the ranger", role="helper"))
    snake = world.add(Entity(id="snake", type="snake", label=snake_cfg.label, tags=set(snake_cfg.tags)))
    path = world.add(Entity(id="path", type="path", label="the path"))
    cannister = world.add(Entity(id="cannister", type="tool", label="water cannister"))
    chore_target = world.add(Entity(id="chore_target", type="target", label=chore.target))

    child.attrs["name"] = child_name_value
    adult.attrs["setting"] = setting.id
    world.facts["refrain"] = REFRAIN

    introduce(world, child, adult, setting, chore)
    notice_task(world, child, chore)

    world.para()
    spot_snake(world, child, snake, snake_cfg)
    warn(world, child, adult, setting, snake_cfg)
    reach_then_stop(world, child)
    step_back(world, child, adult)

    world.para()
    call_helper(world, adult, helper, response)
    resolve_snake(world, helper, snake, response, snake_cfg)
    finish_chore(world, child, adult, chore)

    world.para()
    close_story(world, child, adult)

    outcome = "ranger_help" if response.ranger_needed else "waited_safely"
    world.facts.update(
        child=child,
        adult=adult,
        helper=helper,
        snake=snake,
        setting=setting,
        chore=chore,
        snake_cfg=snake_cfg,
        response=response,
        outcome=outcome,
        target_watered=world.get("chore_target").meters["watered"] >= THRESHOLD,
        used_refrain=3,
        sign_percent=setting.sign_percent,
        venomous=snake_cfg.venomous,
    )
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the garden behind the library",
        nature="flowers and stones",
        opening="Bees hummed over the marigolds, and the little path smelled like mint.",
        sign_percent=10,
        snake_kinds={"garter", "copperhead"},
        tags={"garden"},
    ),
    "pond": Setting(
        id="pond",
        place="the duck pond path",
        nature="reeds and water",
        opening="The reeds shivered in the breeze, and small rings kept opening on the pond.",
        sign_percent=15,
        snake_kinds={"garter", "watersnake"},
        tags={"pond"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the school orchard",
        nature="young trees",
        opening="The apple leaves flickered silver-green, and the dirt path was warm in the sun.",
        sign_percent=8,
        snake_kinds={"garter", "copperhead"},
        tags={"orchard"},
    ),
}

CHORES = {
    "birdbath": Chore(
        id="birdbath",
        target="the stone birdbath",
        need="the birdbath was nearly dry",
        finish="Water rang against the birdbath in bright little plinks.",
        ending_image="In another moment, two sparrows fluttered down to drink.",
        tags={"birds", "water"},
    ),
    "sunflowers": Chore(
        id="sunflowers",
        target="the drooping sunflowers",
        need="the tallest sunflowers were thirsty",
        finish="The thirsty roots drank quietly while the sunflowers lifted their heads.",
        ending_image="A goldfinch landed on one stem as if it had been waiting.",
        tags={"flowers", "water"},
    ),
    "sapling": Chore(
        id="sapling",
        target="the new apple sapling",
        need="the young tree needed one more careful drink",
        finish="The dark soil drank the water around the sapling's small roots.",
        ending_image="Its leaves looked brighter, and a tiny ladybug climbed the stem.",
        tags={"tree", "water"},
    ),
}

SNAKES = {
    "garter": SnakeKind(
        id="garter",
        label="garter snake",
        colors="striped brown-and-gold",
        temperament="shy",
        habitat={"garden", "pond", "orchard"},
        venomous=False,
        danger=1,
        tags={"snake"},
    ),
    "watersnake": SnakeKind(
        id="watersnake",
        label="water snake",
        colors="dark banded brown",
        temperament="nervous",
        habitat={"pond"},
        venomous=False,
        danger=1,
        tags={"snake", "pond"},
    ),
    "copperhead": SnakeKind(
        id="copperhead",
        label="copperhead",
        colors="copper-and-chestnut",
        temperament="still",
        habitat={"garden", "orchard"},
        venomous=True,
        danger=3,
        tags={"snake", "venom"},
    ),
}

RESPONSES = {
    "ranger_tub": Response(
        id="ranger_tub",
        safe=3,
        ranger_needed=True,
        text="The ranger guided the {snake} gently into the tub and carried it to a quiet patch of woods far from the path.",
        qa_text="A ranger came with a tall tub and moved the snake safely away from the path.",
        fail_text="Someone tried to handle the snake without training.",
        tags={"ranger", "snake"},
    ),
    "wait_path": Response(
        id="wait_path",
        safe=2,
        ranger_needed=False,
        text="At last the {snake} lifted its head, slid into the grass, and left the path all by itself.",
        qa_text="They waited from far away until the snake slid off the path on its own.",
        fail_text="Someone crowded the snake and made it feel trapped.",
        tags={"wait", "snake"},
    ),
    "tap_tail": Response(
        id="tap_tail",
        safe=1,
        ranger_needed=False,
        text="Someone tapped at the snake's tail with a stick.",
        qa_text="Someone poked at the snake.",
        fail_text="Poking a snake can make it feel trapped or scared.",
        tags={"unsafe"},
    ),
}


GIRL_NAMES = ["Mira", "Lila", "Nora", "Ava", "Zoe", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Owen", "Leo", "Ben", "Finn", "Noah", "Eli", "Sam", "Theo"]
ADULT_TYPES = ["mother", "father", "aunt", "uncle", "grandmother", "grandfather"]
HELPER_TYPES = ["ranger_woman", "ranger_man"]


@dataclass
class StoryParams:
    setting: str
    chore: str
    snake: str
    response: str
    child_name: str
    child_type: str
    adult_type: str
    helper_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "snake": [
        (
            "What should you do if you see a snake on a path?",
            "Stop, step back, and tell a grown-up right away. Giving a snake space keeps both you and the snake safer."
        )
    ],
    "venom": [
        (
            "What is venom?",
            "Venom is a special poison some animals make to protect themselves or catch food. That is why children should never touch unknown snakes."
        )
    ],
    "ranger": [
        (
            "What does a park ranger do?",
            "A park ranger helps care for outdoor places, plants, and animals. Rangers also help people stay safe around wildlife."
        )
    ],
    "wait": [
        (
            "Why is waiting sometimes the safest choice around wildlife?",
            "Wild animals often move away on their own when people stay calm and give them space. Waiting can solve the problem without scaring the animal."
        )
    ],
    "water": [
        (
            "Why do birds and plants need water?",
            "Birds need water to drink, and plants need water to stay healthy and grow. A small caring chore can help many living things."
        )
    ],
}
KNOWLEDGE_ORDER = ["snake", "venom", "ranger", "wait", "water"]


CURATED = [
    StoryParams(
        setting="garden",
        chore="birdbath",
        snake="garter",
        response="wait_path",
        child_name="Mira",
        child_type="girl",
        adult_type="grandfather",
        helper_type="ranger_woman",
        seed=1,
    ),
    StoryParams(
        setting="pond",
        chore="sunflowers",
        snake="watersnake",
        response="ranger_tub",
        child_name="Owen",
        child_type="boy",
        adult_type="aunt",
        helper_type="ranger_man",
        seed=2,
    ),
    StoryParams(
        setting="orchard",
        chore="sapling",
        snake="copperhead",
        response="ranger_tub",
        child_name="Lila",
        child_type="girl",
        adult_type="mother",
        helper_type="ranger_woman",
        seed=3,
    ),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for chore_id in CHORES:
            for snake_id, snake in SNAKES.items():
                if not habitat_ok(setting, snake):
                    continue
                for response_id, response in RESPONSES.items():
                    if response.safe < SAFE_MIN:
                        continue
                    if snake.venomous and not response.ranger_needed:
                        continue
                    combos.append((setting_id, chore_id, snake_id, response_id))
    return combos


def explain_rejection(setting: Setting, snake: SnakeKind) -> str:
    return (
        f"(No story: a {snake.label} does not fit naturally at {setting.place}. "
        f"Pick a snake that belongs in that setting.)"
    )


def explain_combo_response(snake: SnakeKind, response: Response) -> str:
    if snake.venomous and not response.ranger_needed:
        return (
            f"(No story: a {snake.label} should not be handled with a simple wait-only ending "
            f"in this world. Venom risk means the story requires trained help.)"
        )
    return "(No story: this combination is not part of the calm safety model.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    chore = f["chore"]
    snake = f["snake_cfg"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words "cannister", "venom", and "percent".',
        f"Tell a gentle outdoor story where {child.attrs['name']} carries a water cannister to help at {setting.place}, sees a {snake.label}, and learns a calm refrain.",
        f'Write a story with repetition using the line "{REFRAIN}" and end with {chore.target} being helped safely.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    setting = f["setting"]
    chore = f["chore"]
    snake_cfg = f["snake_cfg"]
    response = f["response"]
    child_name_value = child.attrs["name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name_value}, a child carrying a water cannister with {adult.label_word}. They were trying to help {chore.target} at {setting.place}."
        ),
        (
            "What problem did the child find on the path?",
            f"{child_name_value} found a {snake_cfg.label} curled across the path. That made it unsafe to walk closer with the cannister."
        ),
        (
            "What words did the grown-up teach the child to repeat?",
            f'The grown-up taught {child_name_value} to say, "{REFRAIN}" The repeated words helped {child.pronoun("object")} slow down and make a safe choice.'
        ),
        (
            "Why did the story mention percent and venom?",
            f"The grown-up explained that only {f['sign_percent']} percent of the local snakes were known for venom that could make people very sick. But they also said people should never guess from far away, so every snake deserved space."
        ),
    ]
    if response.id == "ranger_tub":
        qa.append(
            (
                "How was the snake problem solved?",
                f"{response.qa_text} That kept the child far back while the path became safe again."
            )
        )
    else:
        qa.append(
            (
                "How was the snake problem solved?",
                f"{response.qa_text} They stayed patient and did not scare the snake by crowding it."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"After the path was clear, {child_name_value} finished the chore and helped {chore.target}. The ending feels warm because the child learned a safe habit and still got to be kind."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"snake", "water"}
    if f["venomous"]:
        tags.add("venom")
    if f["response"].ranger_needed:
        tags.add("ranger")
    else:
        tags.add("wait")
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


ASP_RULES = r"""
safe_response(R) :- response(R), safe(R,S), safe_min(M), S >= M.
habitat_ok(St, Sn) :- setting(St), snake(Sn), lives_in(Sn, St), found_in(St, Sn).
needs_ranger(Sn) :- venomous(Sn).
valid(St, Ch, Sn, R) :- setting(St), chore(Ch), snake(Sn), response(R),
                        habitat_ok(St, Sn), safe_response(R),
                        not bad_pair(Sn, R).
bad_pair(Sn, R) :- needs_ranger(Sn), not ranger_needed(R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        lines.append(asp.fact("percent", setting_id, setting.sign_percent))
        for snake_id in sorted(setting.snake_kinds):
            lines.append(asp.fact("found_in", setting_id, snake_id))
    for chore_id in CHORES:
        lines.append(asp.fact("chore", chore_id))
    for snake_id, snake in SNAKES.items():
        lines.append(asp.fact("snake", snake_id))
        for habitat in sorted(snake.habitat):
            lines.append(asp.fact("lives_in", snake_id, habitat))
        if snake.venomous:
            lines.append(asp.fact("venomous", snake_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("safe", response_id, response.safe))
        if response.ranger_needed:
            lines.append(asp.fact("ranger_needed", response_id))
    lines.append(asp.fact("safe_min", SAFE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        smoke = generate(CURATED[0])
        if not smoke.story or "cannister" not in smoke.story or "percent" not in smoke.story:
            raise StoryError("(Smoke test failed: generated story missed required seed words.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:12} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child, a snake, a water cannister, and a calm repeated safety refrain."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--chore", choices=CHORES)
    ap.add_argument("--snake", choices=SNAKES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--adult-type", choices=ADULT_TYPES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].safe < SAFE_MIN:
        raise StoryError(explain_response(args.response))

    if args.setting and args.snake:
        setting = SETTINGS[args.setting]
        snake = SNAKES[args.snake]
        if not habitat_ok(setting, snake):
            raise StoryError(explain_rejection(setting, snake))

    if args.snake and args.response:
        snake = SNAKES[args.snake]
        response = RESPONSES[args.response]
        if snake.venomous and not response.ranger_needed:
            raise StoryError(explain_combo_response(snake, response))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.chore is None or combo[1] == args.chore)
        and (args.snake is None or combo[2] == args.snake)
        and (args.response is None or combo[3] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, chore_id, snake_id, response_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name_value = args.name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    adult_type = args.adult_type or rng.choice(ADULT_TYPES)
    helper_type = rng.choice(HELPER_TYPES)

    return StoryParams(
        setting=setting_id,
        chore=chore_id,
        snake=snake_id,
        response=response_id,
        child_name=child_name_value,
        child_type=child_type,
        adult_type=adult_type,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.chore not in CHORES:
        raise StoryError(f"(Unknown chore: {params.chore})")
    if params.snake not in SNAKES:
        raise StoryError(f"(Unknown snake: {params.snake})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    setting = SETTINGS[params.setting]
    chore = CHORES[params.chore]
    snake = SNAKES[params.snake]
    response = RESPONSES[params.response]

    if not habitat_ok(setting, snake):
        raise StoryError(explain_rejection(setting, snake))
    if response.safe < SAFE_MIN:
        raise StoryError(explain_response(params.response))
    if snake.venomous and not response.ranger_needed:
        raise StoryError(explain_combo_response(snake, response))

    world = tell(
        setting=setting,
        chore=chore,
        snake_cfg=snake,
        response=response,
        child_name_value=params.child_name,
        child_type=params.child_type,
        adult_type=params.adult_type,
        helper_type=params.helper_type,
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
        print(f"{len(combos)} compatible (setting, chore, snake, response) combos:\n")
        for setting_id, chore_id, snake_id, response_id in combos:
            print(f"  {setting_id:8} {chore_id:10} {snake_id:10} {response_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.chore} at {p.setting} with {p.snake} ({p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
