#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/calcium_curiosity_inner_monologue_moral_value_slice.py
=================================================================================

A standalone story world about a child's curiosity over the word "calcium."

This world rebuilds a tiny slice-of-life pattern:

* a child hears that a food has calcium
* the child becomes curious and forms an unsafe mistaken idea about some
  calcium-related non-food object nearby
* the child has an inner monologue about whether to try it alone
* the child chooses the moral action -- asking a grown-up first
* the grown-up explains the difference between "contains calcium" and "is food"
* the story ends with a safe food choice and a small everyday activity that
  proves what the child learned

The world model enforces a reasonableness gate:
only some objects create a plausible confusion about calcium, and only some
foods are suitable, ordinary answers. The story refuses invalid combinations
with a clear explanation.

Run it
------
    python storyworlds/worlds/gpt-5.4/calcium_curiosity_inner_monologue_moral_value_slice.py
    python storyworlds/worlds/gpt-5.4/calcium_curiosity_inner_monologue_moral_value_slice.py --food yogurt --mistake chalk
    python storyworlds/worlds/gpt-5.4/calcium_curiosity_inner_monologue_moral_value_slice.py --mistake spoon
    python storyworlds/worlds/gpt-5.4/calcium_curiosity_inner_monologue_moral_value_slice.py --all
    python storyworlds/worlds/gpt-5.4/calcium_curiosity_inner_monologue_moral_value_slice.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/calcium_curiosity_inner_monologue_moral_value_slice.py --qa --json
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    edible: bool = False
    safe_food: bool = False
    calcium_source: bool = False
    calcium_confusing: bool = False
    owned_by: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    place: str
    room_phrase: str
    end_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    bowl_phrase: str
    texture: str
    calcium_line: str
    tags: set[str] = field(default_factory=set)
    calcium_source: bool = True
    safe_food: bool = True


@dataclass
class Mistake:
    id: str
    label: str
    phrase: str
    location: str
    clue: str
    warning: str
    explanation: str
    related: bool = True
    edible: bool = False
    calcium_confusing: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    opening: str
    end_proof: str
    body_part: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World + causal rules
# ---------------------------------------------------------------------------
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


def _r_urge(world: World) -> list[str]:
    child = world.get("child")
    obj = world.get("mistake")
    if child.memes["curiosity"] < THRESHOLD or obj.meters["near"] < THRESHOLD:
        return []
    sig = ("urge", obj.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["temptation"] += 1
    return ["__temptation__"]


def _r_pride(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["asked_help"] < THRESHOLD:
        return []
    sig = ("pride", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="urge", tag="emotional", apply=_r_urge),
    Rule(name="pride", tag="social", apply=_r_pride),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def plausible_confusion(food: Food, mistake: Mistake) -> bool:
    return food.calcium_source and mistake.related and mistake.calcium_confusing and not mistake.edible


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for food_id, food in FOODS.items():
            for mistake_id, mistake in MISTAKES.items():
                for activity_id in ACTIVITIES:
                    if plausible_confusion(food, mistake):
                        combos.append((setting_id, food_id, mistake_id, activity_id))
    return combos


def explain_rejection(food: Food, mistake: Mistake) -> str:
    if mistake.edible:
        return (
            f"(No story: {mistake.phrase} is already something a child could eat, "
            f"so it does not create the needed mistake about what counts as safe calcium. "
            f"Pick a nearby non-food object like chalk or a shell.)"
        )
    if not mistake.related:
        return (
            f"(No story: {mistake.label} has no ordinary link to calcium, so the child's "
            f"question would feel random instead of grounded. Pick an object that might "
            f"make a child wonder about calcium.)"
        )
    if not food.calcium_source:
        return (
            f"(No story: {food.label} is not treated as the calcium food in this world, "
            f"so there is no honest starting point for the conversation.)"
        )
    return "(No story: this combination does not support a plausible calcium misunderstanding.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_if_trying(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    obj = sim.get("mistake")
    child.meters["unsafe_try"] += 1
    child.memes["worry"] += 1
    obj.meters["handled"] += 1
    return {
        "unsafe": child.meters["unsafe_try"] >= THRESHOLD,
        "worry": child.memes["worry"],
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def scene_open(world: World, child: Entity, adult: Entity, setting: Setting,
               food: Food, activity: Activity) -> None:
    child.memes["calm"] += 1
    world.say(
        f"After school, {child.id} sat with {child.pronoun('possessive')} "
        f"{adult.label_word} in {setting.room_phrase}. {activity.opening}"
    )
    world.say(
        f"On the table waited {food.bowl_phrase}, and the whole room felt slow and ordinary in a good way."
    )


def hear_calcium(world: World, child: Entity, adult: Entity, food: Food, activity: Activity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'{adult.label_word.capitalize()} slid {food.phrase} closer and said, '
        f'"This has calcium, which helps your {activity.body_part} grow strong."'
    )
    world.say(
        f"{child.id} looked down at the {food.label}. The word calcium stayed in "
        f"{child.pronoun('possessive')} head like a tiny bell."
    )


def notice_object(world: World, child: Entity, mistake: Mistake) -> None:
    obj = world.get("mistake")
    obj.meters["near"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {child.pronoun()} noticed {mistake.phrase} {mistake.location}. "
        f"{mistake.clue}"
    )


def inner_monologue(world: World, child: Entity, mistake: Mistake) -> None:
    pred = predict_if_trying(world)
    world.facts["predicted_unsafe"] = pred["unsafe"]
    child.memes["reflection"] += 1
    line = (
        f'{child.id} thought, "If calcium is in good food, then what about {mistake.label}? '
        f"Maybe it has calcium too... but {mistake.warning}."'
    )
    if pred["unsafe"]:
        line += f" {child.pronoun().capitalize()} felt a small worried flutter in {child.pronoun('possessive')} chest."
    world.say(line)


def moral_pause(world: World, child: Entity, adult: Entity) -> None:
    child.memes["self_control"] += 1
    world.say(
        f"{child.pronoun().capitalize()} reached out, then stopped. "
        f'"I should ask first," {child.pronoun()} told {child.pronoun("object")}self.'
    )
    world.say(
        f"That tiny pause felt important. {child.id} wanted an answer more than a secret try."
    )


def ask(world: World, child: Entity, adult: Entity, mistake: Mistake) -> None:
    child.memes["asked_help"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"{adult.label_word.capitalize()}, does {mistake.label} count as calcium food too?" '
        f"{child.id} asked."
    )


def explain(world: World, child: Entity, adult: Entity, food: Food, mistake: Mistake,
            response: Response) -> None:
    child.memes["understanding"] += 1
    adult.memes["care"] += 1
    world.say(
        f'{adult.label_word.capitalize()} smiled and shook {adult.pronoun("possessive")} head. '
        f'"{mistake.explanation} {response.text} {food.calcium_line}"'
    )
    world.say(
        f"{child.id} listened closely. The mixed-up idea in {child.pronoun('possessive')} head began to straighten out."
    )


def choose_food(world: World, child: Entity, food: Food) -> None:
    plate = world.get("food")
    plate.meters["eaten"] += 1
    child.meters["fed"] += 1
    child.memes["confidence"] += 1
    world.say(
        f"Then {child.id} took a careful bite of the {food.label}. It was {food.texture}, and now it made sense too."
    )


def ending(world: World, child: Entity, adult: Entity, setting: Setting, activity: Activity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"A little later, {activity.end_proof}"
    )
    world.say(
        f"{setting.end_image} {child.id} felt proud that {child.pronoun()} had chosen to ask instead of guess."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, food: Food, mistake: Mistake, activity: Activity,
         response: Response, *, child_name: str = "Mina", child_gender: str = "girl",
         adult_type: str = "grandmother") -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="child",
        attrs={"name": child_name},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=adult_type,
        label=adult_type,
        phrase=adult_type,
        role="adult",
    ))
    world.add(Entity(
        id="food",
        kind="thing",
        type="food",
        label=food.label,
        phrase=food.phrase,
        edible=True,
        safe_food=True,
        calcium_source=True,
        tags=set(food.tags),
    ))
    world.add(Entity(
        id="mistake",
        kind="thing",
        type="object",
        label=mistake.label,
        phrase=mistake.phrase,
        edible=mistake.edible,
        calcium_confusing=mistake.calcium_confusing,
        tags=set(mistake.tags),
    ))

    # Act 1
    scene_open(world, child, adult, setting, food, activity)
    hear_calcium(world, child, adult, food, activity)
    notice_object(world, child, mistake)

    # Act 2
    world.para()
    inner_monologue(world, child, mistake)
    moral_pause(world, child, adult)
    ask(world, child, adult, mistake)

    # Act 3
    world.para()
    explain(world, child, adult, food, mistake, response)
    choose_food(world, child, food)
    ending(world, child, adult, setting, activity)

    world.facts.update(
        child=child,
        adult=adult,
        setting=setting,
        food_cfg=food,
        mistake_cfg=mistake,
        activity=activity,
        response=response,
        asked_first=child.memes["asked_help"] >= THRESHOLD,
        ate_food=world.get("food").meters["eaten"] >= THRESHOLD,
        predicted_unsafe=world.facts.get("predicted_unsafe", False),
    )
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen",
        room_phrase="the small kitchen while sunlight lay across the floor",
        end_image="A spoon clinked softly against the bowl, and the window over the sink shone pale gold.",
        tags={"home"},
    ),
    "balcony": Setting(
        id="balcony",
        place="the balcony table",
        room_phrase="the little balcony table outside the apartment door",
        end_image="Pigeons bobbed on the railing, and the evening air smelled like wet leaves.",
        tags={"home"},
    ),
    "porch": Setting(
        id="porch",
        place="the front porch",
        room_phrase="the front porch where shoes rested by the mat",
        end_image="Somewhere down the street a bicycle bell rang, and the porch boards held the last warm light.",
        tags={"home"},
    ),
}

FOODS = {
    "milk": Food(
        id="milk",
        label="milk",
        phrase="a glass of milk",
        bowl_phrase="a glass of milk beside a plate of crackers",
        texture="cool and plain",
        calcium_line="Milk is food, and that is one safe way to get calcium.",
        tags={"milk", "calcium_food"},
    ),
    "yogurt": Food(
        id="yogurt",
        label="yogurt",
        phrase="a cup of yogurt",
        bowl_phrase="a cup of yogurt with sliced strawberries",
        texture="smooth and chilly",
        calcium_line="Yogurt is food, and that is one safe way to get calcium.",
        tags={"yogurt", "calcium_food"},
    ),
    "cheese": Food(
        id="cheese",
        label="cheese",
        phrase="a few cubes of cheese",
        bowl_phrase="a little plate of cheese cubes and apple slices",
        texture="soft and a little salty",
        calcium_line="Cheese is food, and that is one safe way to get calcium.",
        tags={"cheese", "calcium_food"},
    ),
}

MISTAKES = {
    "chalk": Mistake(
        id="chalk",
        label="chalk",
        phrase="a stub of sidewalk chalk",
        location="near the flowerpot",
        clue="It was pale and dusty, the sort of thing that looked important just because grown-ups talked about it carefully.",
        warning="chalk is for drawing, not for eating",
        explanation="No, sweetheart. Some things may have minerals in them, but that does not make them food.",
        related=True,
        edible=False,
        calcium_confusing=True,
        tags={"chalk", "ask_first"},
    ),
    "eggshell": Mistake(
        id="eggshell",
        label="an eggshell",
        phrase="a clean half eggshell from baking",
        location="on a towel by the sink",
        clue="It looked fragile and white, almost like a little cup made of the same word she had just heard.",
        warning="an eggshell from baking is not a snack",
        explanation="No, sweetheart. Eggshells are not a snack, even if people talk about calcium when they talk about them.",
        related=True,
        edible=False,
        calcium_confusing=True,
        tags={"eggshell", "ask_first"},
    ),
    "shell": Mistake(
        id="shell",
        label="the shell",
        phrase="a tiny shell from the keepsake dish",
        location="beside the window",
        clue="It was white at the edge and curled like a small secret from the beach.",
        warning="the shell belongs in the dish, not in a mouth",
        explanation="No, sweetheart. A shell is something to keep and look at, not something to chew.",
        related=True,
        edible=False,
        calcium_confusing=True,
        tags={"shell", "ask_first"},
    ),
    "spoon": Mistake(
        id="spoon",
        label="the spoon",
        phrase="a metal spoon",
        location="by the napkin",
        clue="It shone brightly, but it had nothing to do with the question at hand.",
        warning="the spoon is only for scooping",
        explanation="No, sweetheart. A spoon helps you eat food, but it is not food itself.",
        related=False,
        edible=False,
        calcium_confusing=False,
        tags={"spoon"},
    ),
}

ACTIVITIES = {
    "hop": Activity(
        id="hop",
        opening="Soon, she hoped, they would go downstairs to draw hopscotch squares.",
        end_proof="when they finally went outside, the chalk stayed on the ground where it belonged, and the hopping game felt easy and light on her feet.",
        body_part="bones",
        tags={"bones", "play"},
    ),
    "water_plants": Activity(
        id="water_plants",
        opening="After snack, she wanted to help carry the small watering can to the plants.",
        end_proof="after snack, she carried the little watering can to the herbs and set it down carefully by the basil.",
        body_part="bones",
        tags={"bones", "helping"},
    ),
    "tooth": Activity(
        id="tooth",
        opening="She had been wiggling a loose baby tooth all afternoon and thinking about growing up.",
        end_proof="later she grinned into the hallway mirror, wiggled her loose tooth once more, and laughed.",
        body_part="teeth and bones",
        tags={"teeth", "growing"},
    ),
}

RESPONSES = {
    "explain_and_offer": Response(
        id="explain_and_offer",
        sense=3,
        text="Food is what we eat, and when you wonder about something strange, the safe thing is to ask a grown-up and choose a real food instead.",
        qa_text="The grown-up explained the difference between a real food and a non-food object, then pointed the child back to the safe snack.",
        tags={"ask_first", "safe_food"},
    ),
    "just_say_no": Response(
        id="just_say_no",
        sense=1,
        text="Just do not touch that.",
        qa_text="The grown-up only said no without explaining.",
        tags={"ask_first"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Ruby", "Ella", "Tara", "Zoe"]
BOY_NAMES = ["Owen", "Ben", "Milo", "Theo", "Eli", "Sam", "Noah", "Leo"]


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    food: str
    mistake: str
    activity: str
    response: str
    child_name: str
    child_gender: str
    adult_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "calcium_food": [
        (
            "What is calcium?",
            "Calcium is a mineral your body uses to help build strong bones and teeth. You get it from food, not by tasting random objects.",
        )
    ],
    "milk": [
        (
            "Does milk have calcium?",
            "Yes. Milk is a food that can give your body calcium, which helps bones and teeth grow strong.",
        )
    ],
    "yogurt": [
        (
            "Does yogurt have calcium?",
            "Yes. Yogurt is a food that can give your body calcium, and it is meant to be eaten.",
        )
    ],
    "cheese": [
        (
            "Does cheese have calcium?",
            "Yes. Cheese is a food with calcium, so it is one ordinary safe snack for growing bodies.",
        )
    ],
    "chalk": [
        (
            "Why should you not eat chalk?",
            "Chalk is for drawing, not for eating. Even if something makes you curious, you should ask a grown-up before putting it in your mouth.",
        )
    ],
    "eggshell": [
        (
            "Should a child eat an eggshell from the counter?",
            "No. An eggshell on the counter is not a snack, so a child should ask a grown-up and choose real food instead.",
        )
    ],
    "shell": [
        (
            "Can you eat a shell from a keepsake dish?",
            "No. A shell is for looking at or keeping, not for chewing or swallowing.",
        )
    ],
    "ask_first": [
        (
            "What should you do if you wonder whether something is safe to eat?",
            "Ask a grown-up first. Asking is wiser than guessing, because not everything near food is food.",
        )
    ],
    "bones": [
        (
            "What do bones do?",
            "Bones help hold your body up and help you move. They work with your muscles so you can run, hop, and carry things.",
        )
    ],
    "teeth": [
        (
            "Why do teeth matter?",
            "Teeth help you bite and chew food, and they also help your smile look bright. Children need to take care of them as they grow.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "calcium_food",
    "milk",
    "yogurt",
    "cheese",
    "chalk",
    "eggshell",
    "shell",
    "ask_first",
    "bones",
    "teeth",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    food = f["food_cfg"]
    mistake = f["mistake_cfg"]
    activity = f["activity"]
    return [
        (
            f'Write a gentle slice-of-life story for a 3-to-5-year-old that includes the word "calcium", '
            f"features a curious child, and ends with the child asking a grown-up before doing something uncertain."
        ),
        (
            f"Tell a homey story where {child.attrs['name']} hears that {food.label} has calcium, "
            f"wonders about {mistake.label}, has an inner monologue, and learns that real curiosity should be guided by honesty and asking first."
        ),
        (
            f"Write a simple everyday story about a child, a snack, and a small misunderstanding about calcium, "
            f"ending with {activity.end_proof}"
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    food = f["food_cfg"]
    mistake = f["mistake_cfg"]
    activity = f["activity"]
    name = child.attrs["name"]
    pw = adult.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name} and {name}'s {pw}. They are sharing a quiet snack and a small question at home.",
        ),
        (
            f"Why did {name} start thinking about calcium?",
            f"{pw.capitalize()} said that the {food.label} had calcium to help {activity.body_part} grow strong. That new word stayed in {name}'s mind and made {child.pronoun('object')} curious.",
        ),
        (
            f"What mistake did {name} almost make?",
            f"{name} almost treated {mistake.label} as if it might be food. The mistake came from hearing about calcium and then noticing a nearby object that seemed connected in {child.pronoun('possessive')} imagination.",
        ),
        (
            f"What happened inside {name}'s head before {child.pronoun()} spoke?",
            f"{name} wondered whether {mistake.label} might count as calcium too. Then {child.pronoun().capitalize()} felt unsure and stopped to think, which is what turned the story toward a safer choice.",
        ),
        (
            f"What was the wise thing {name} did?",
            f"{name} asked {pw} before trying anything. That was wise because asking for help is better than secretly guessing about what is safe to eat.",
        ),
        (
            f"What did {name}'s {pw} explain?",
            f"{pw.capitalize()} explained that not everything connected to calcium is food. {child.pronoun().capitalize()} helped {name} see the difference between a real snack and a non-food object.",
        ),
        (
            f"How did the story end?",
            f"{name} chose the {food.label} instead, and later {activity.end_proof} The ending shows that {child.pronoun()} learned something and carried that lesson into ordinary life.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"calcium_food"} | set(f["food_cfg"].tags) | set(f["mistake_cfg"].tags) | set(f["activity"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if e.edible:
            flags.append("edible")
        if e.safe_food:
            flags.append("safe_food")
        if e.calcium_source:
            flags.append("calcium_source")
        if e.calcium_confusing:
            flags.append("calcium_confusing")
        if flags:
            bits.append(f"flags={flags}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% plausible confusion about calcium:
valid_confusion(F, M) :- food(F), calcium_food(F), mistake(M), related(M), confusing(M), not edible_mistake(M).

valid(S, F, M, A) :- setting(S), valid_confusion(F, M), activity(A).

sensible(R) :- response(R), sense(R, V), sense_min(Min), V >= Min.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid, food in FOODS.items():
        lines.append(asp.fact("food", fid))
        if food.calcium_source:
            lines.append(asp.fact("calcium_food", fid))
    for mid, mistake in MISTAKES.items():
        lines.append(asp.fact("mistake", mid))
        if mistake.related:
            lines.append(asp.fact("related", mid))
        if mistake.calcium_confusing:
            lines.append(asp.fact("confusing", mid))
        if mistake.edible:
            lines.append(asp.fact("edible_mistake", mid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    py_sensible = {r.id for r in sensible_responses()}
    cl_sensible = set(asp_sensible())
    if py_sensible == cl_sensible:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(cl_sensible)} python={sorted(py_sensible)}")

    # smoke test ordinary generation
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# CLI contract
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="kitchen",
        food="yogurt",
        mistake="chalk",
        activity="hop",
        response="explain_and_offer",
        child_name="Mina",
        child_gender="girl",
        adult_type="grandmother",
    ),
    StoryParams(
        setting="balcony",
        food="milk",
        mistake="shell",
        activity="water_plants",
        response="explain_and_offer",
        child_name="Owen",
        child_gender="boy",
        adult_type="mother",
    ),
    StoryParams(
        setting="porch",
        food="cheese",
        mistake="eggshell",
        activity="tooth",
        response="explain_and_offer",
        child_name="Lila",
        child_gender="girl",
        adult_type="father",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child's curiosity about calcium, an inner monologue, and the moral value of asking first."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--mistake", choices=MISTAKES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.food and args.mistake:
        if not plausible_confusion(FOODS[args.food], MISTAKES[args.mistake]):
            raise StoryError(explain_rejection(FOODS[args.food], MISTAKES[args.mistake]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.food is None or c[1] == args.food)
        and (args.mistake is None or c[2] == args.mistake)
        and (args.activity is None or c[3] == args.activity)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, food_id, mistake_id, activity_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult_type = args.adult or rng.choice(["mother", "father", "grandmother"])
    return StoryParams(
        setting=setting_id,
        food=food_id,
        mistake=mistake_id,
        activity=activity_id,
        response=response_id,
        child_name=name,
        child_gender=gender,
        adult_type=adult_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.food not in FOODS:
        raise StoryError(f"(Invalid food: {params.food})")
    if params.mistake not in MISTAKES:
        raise StoryError(f"(Invalid mistake: {params.mistake})")
    if params.activity not in ACTIVITIES:
        raise StoryError(f"(Invalid activity: {params.activity})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Invalid response: {params.response})")
    food = FOODS[params.food]
    mistake = MISTAKES[params.mistake]
    if not plausible_confusion(food, mistake):
        raise StoryError(explain_rejection(food, mistake))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        SETTINGS[params.setting],
        food,
        mistake,
        ACTIVITIES[params.activity],
        RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_type=params.adult_type,
    )

    story = world.render().replace("child", params.child_name)
    story = story.replace("adult", world.get("adult").label_word)
    story = story.replace("  ", " ")
    story = story.replace("..", ".")

    # restore visible names in the story body
    story = story.replace("child", params.child_name)
    return StorySample(
        params=params,
        story=story.replace("Mina", params.child_name) if params.child_name != "Mina" and "Mina" in story and world.get("child").attrs["name"] == params.child_name else story,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, food, mistake, activity) combos:\n")
        for setting_id, food_id, mistake_id, activity_id in combos:
            print(f"  {setting_id:8} {food_id:7} {mistake_id:8} {activity_id}")
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
            header = f"### {p.child_name}: {p.food} / {p.mistake} / {p.activity}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
