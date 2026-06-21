#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/prayer_community_garden_flashback_humor_superhero_story.py
======================================================================================

A standalone storyworld for a tiny "superhero story" set in a community garden.

The seed asks for:
- prayer
- community garden
- flashback
- humor
- superhero style

This world models children playing garden superheroes when they discover a real
garden problem: a patch of plants is in trouble. One child blurts out a silly,
comic "super fix." The other child remembers a short flashback from an earlier
garden lesson, says a small prayer for wisdom, and together they choose a
sensible response. Sometimes they arrive in time and the plants recover; if the
delay is too long, the patch is saved only partly and the children learn to act
faster next time.

The world enforces a common-sense gate:
- each crop only has certain plausible problems
- a response must match the problem's real need
- low-sense joke responses are known but refused

Run it
------
    python storyworlds/worlds/gpt-5.4/prayer_community_garden_flashback_humor_superhero_story.py
    python storyworlds/worlds/gpt-5.4/prayer_community_garden_flashback_humor_superhero_story.py --crop tomatoes --problem thirsty --response watering_can
    python storyworlds/worlds/gpt-5.4/prayer_community_garden_flashback_humor_superhero_story.py --response cape_fan
    python storyworlds/worlds/gpt-5.4/prayer_community_garden_flashback_humor_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/prayer_community_garden_flashback_humor_superhero_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/prayer_community_garden_flashback_humor_superhero_story.py --verify
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Crop:
    id: str
    label: str
    phrase: str
    patch: str
    color: str
    plural: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    need: str
    severity: int
    symptom: str
    cause: str
    danger_line: str
    flashback: str
    joke_idea: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    provides: str
    action_text: str
    fail_text: str
    qa_text: str
    gift_line: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_problem_spreads(world: World) -> list[str]:
    patch = world.entities.get("patch")
    garden = world.entities.get("garden")
    if patch is None or garden is None:
        return []
    if patch.meters["trouble"] < THRESHOLD:
        return []
    sig = ("trouble_spreads",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in [e for e in world.characters() if e.role in {"hero", "sidekick"}]:
        kid.memes["concern"] += 1
    garden.meters["worry"] += 1
    return ["__trouble__"]


def _r_recovery(world: World) -> list[str]:
    patch = world.entities.get("patch")
    if patch is None:
        return []
    if patch.meters["helped"] < THRESHOLD:
        return []
    sig = ("recovery",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    patch.meters["droop"] = max(0.0, patch.meters["droop"] - 1.0)
    patch.meters["hope"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="problem_spreads", tag="physical", apply=_r_problem_spreads),
    Rule(name="recovery", tag="physical", apply=_r_recovery),
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


CROP_PROBLEMS = {
    "tomatoes": {"thirsty", "too_hot"},
    "lettuce": {"thirsty", "too_hot"},
    "beans": {"leaning", "thirsty"},
    "sunflowers": {"leaning", "thirsty"},
}


def problem_fits_crop(crop: Crop, problem: Problem) -> bool:
    return problem.id in CROP_PROBLEMS.get(crop.id, set())


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def response_matches(problem: Problem, response: Response) -> bool:
    return problem.need == response.provides and response.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for crop_id, crop in CROPS.items():
        for problem_id, problem in PROBLEMS.items():
            if not problem_fits_crop(crop, problem):
                continue
            for response_id, response in RESPONSES.items():
                if response_matches(problem, response):
                    combos.append((crop_id, problem_id, response_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    problem = PROBLEMS[params.problem]
    response = RESPONSES[params.response]
    strength = problem.severity + params.delay
    return "recovered" if response.power >= strength else "faded"


def predict_outcome(problem: Problem, response: Response, delay: int) -> dict:
    return {
        "need": problem.need,
        "strength": problem.severity + delay,
        "works": response.power >= (problem.severity + delay),
    }


def introduce(world: World, hero: Entity, sidekick: Entity, crop: Crop) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"On Saturday morning, {hero.id} and {sidekick.id} hurried into the community garden "
        f"wearing towel capes over their shirts. They called themselves Captain Compost and "
        f"The Amazing Water Wing because every superhero team needs very large names."
    )
    world.say(
        f"The bean poles, paths, and raised beds stretched around them like a city of green blocks, "
        f"and the {crop.patch} looked important enough to guard."
    )


def spot_problem(world: World, hero: Entity, sidekick: Entity, crop: Crop, problem: Problem) -> None:
    patch = world.get("patch")
    patch.meters["trouble"] += 1
    patch.meters["droop"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {sidekick.id} stopped so fast that {hero.id}'s cape slid over one eye. "
        f'"Oh no," {sidekick.pronoun()} said. "The {crop.patch} looks wrong."'
    )
    world.say(
        f"The {crop.label} looked {problem.symptom} because {problem.cause}. "
        f"{problem.danger_line}"
    )


def silly_plan(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["bravado"] += 1
    world.say(
        f'{hero.id} puffed out {hero.pronoun("possessive")} chest. '
        f'"Never fear! I shall fix it with {problem.joke_idea}!"'
    )
    world.say(
        f"At that, the cape slipped off {hero.pronoun('possessive')} shoulder and landed in the mulch, "
        f"which made the superhero speech sound less mighty and more muddy."
    )


def flashback_and_prayer(world: World, sidekick: Entity, elder: Entity, problem: Problem) -> None:
    sidekick.memes["memory"] += 1
    sidekick.memes["hope"] += 1
    world.say(
        f"But {sidekick.id} remembered something. In a quick flashback, {sidekick.pronoun()} saw "
        f"{elder.label_word.capitalize()} {elder.id} from another garden day: {problem.flashback}"
    )
    world.say(
        f'{sidekick.id} touched the edge of the raised bed and whispered a small prayer. '
        f'"Dear God, please help us choose the kind way to help this garden."'
    )


def ask_adult(world: World, hero: Entity, sidekick: Entity, elder: Entity) -> None:
    hero.memes["humility"] += 1
    sidekick.memes["trust"] += 1
    world.say(
        f"Instead of charging ahead, the two superheroes waved for {elder.id}, the garden helper with "
        f"soil on {elder.pronoun('possessive')} knees and a smile ready for emergencies."
    )
    world.say(
        f'"Real heroes notice first and rush second," {elder.id} said. "Tell me what the plants need."'
    )


def choose_fix(world: World, hero: Entity, sidekick: Entity, crop: Crop, problem: Problem, response: Response, delay: int) -> None:
    pred = predict_outcome(problem, response, delay)
    world.facts["predicted_strength"] = pred["strength"]
    world.facts["predicted_works"] = pred["works"]
    patch = world.get("patch")
    patch.attrs["need"] = problem.need
    world.say(
        f"{sidekick.id} remembered the flashback, and {hero.id} looked at the plants more carefully. "
        f"They saw that the {crop.label} did not need a speech or a dramatic pose. They needed {problem.need}."
    )
    world.say(
        f"So the team chose {response.gift_line}. Even in superhero stories, the best power is often knowing what really helps."
    )


def do_fix(world: World, elder: Entity, crop: Crop, problem: Problem, response: Response, delay: int) -> None:
    patch = world.get("patch")
    patch.meters["helped"] += 1
    strength = problem.severity + delay
    patch.meters["strength"] = float(strength)
    if response.power >= strength:
        patch.meters["trouble"] = 0.0
        propagate(world, narrate=False)
        world.say(
            f"Together they {response.action_text}. Little by little, the {crop.label} stopped looking so worried."
        )
    else:
        patch.meters["trouble"] += 1
        propagate(world, narrate=False)
        world.say(
            f"They {response.fail_text}. It helped a little, but the trouble had been growing too long."
        )


def ending_recovered(world: World, hero: Entity, sidekick: Entity, elder: Entity, crop: Crop, response: Response) -> None:
    for kid in (hero, sidekick):
        kid.memes["joy"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"Soon the {crop.patch} lifted toward the sun again, and even the funniest cape could not compete with that sight."
    )
    world.say(
        f'{elder.id} gave a proud nod. "Now that," {elder.pronoun()} said, "is garden superhero work."'
    )
    world.say(
        f"{hero.id} saluted with a muddy glove, {sidekick.id} laughed, and the two of them walked on through the community garden "
        f"more gently than before, ready to save the next small thing the sensible way."
    )


def ending_faded(world: World, hero: Entity, sidekick: Entity, elder: Entity, crop: Crop, response: Response) -> None:
    for kid in (hero, sidekick):
        kid.memes["sadness"] += 1
        kid.memes["lesson"] += 1
        kid.memes["hope"] += 1
    world.say(
        f"The {crop.patch} did not stand all the way back up that day. Some leaves stayed tired, though a few still caught the light."
    )
    world.say(
        f'{elder.id} rested a hand on the bed. "We helped as soon as we understood," {elder.pronoun()} said. '
        f'"Next time we will notice faster."'
    )
    world.say(
        f"{hero.id} folded the cape instead of swishing it, and {sidekick.id} whispered another prayer for the garden. "
        f"Then they watered the paths nearby and promised to be the kind of superheroes who look closely before they leap."
    )


def tell(
    crop: Crop,
    problem: Problem,
    response: Response,
    hero_name: str = "Nia",
    hero_gender: str = "girl",
    sidekick_name: str = "Jude",
    sidekick_gender: str = "boy",
    elder_type: str = "mother",
    elder_name: str = "Ms. Rosa",
    delay: int = 0,
    hero_trait: str = "dramatic",
    sidekick_trait: str = "careful",
    mascot: str = "a very round worm"
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=[hero_trait],
    ))
    sidekick = world.add(Entity(
        id=sidekick_name,
        kind="character",
        type=sidekick_gender,
        role="sidekick",
        traits=[sidekick_trait],
    ))
    elder = world.add(Entity(
        id=elder_name,
        kind="character",
        type=elder_type,
        role="elder",
        label="the garden helper",
    ))
    garden = world.add(Entity(
        id="garden",
        kind="thing",
        type="garden",
        label="community garden",
        tags={"garden"},
    ))
    patch = world.add(Entity(
        id="patch",
        kind="thing",
        type="patch",
        label=crop.patch,
        phrase=crop.phrase,
        tags=set(crop.tags) | set(problem.tags),
    ))
    world.facts["mascot"] = mascot

    introduce(world, hero, sidekick, crop)
    if mascot:
        world.say(
            f"Near the gate, {hero.id} pointed at {mascot} on the path and declared it their silent sidekick, "
            f"which made {sidekick.id} laugh so hard that {sidekick.pronoun()} had to hold the watering can straight."
        )

    world.para()
    spot_problem(world, hero, sidekick, crop, problem)
    silly_plan(world, hero, problem)
    flashback_and_prayer(world, sidekick, elder, problem)
    ask_adult(world, hero, sidekick, elder)

    world.para()
    choose_fix(world, hero, sidekick, crop, problem, response, delay)
    do_fix(world, elder, crop, problem, response, delay)

    world.para()
    outcome = outcome_of(StoryParams(
        crop=crop.id,
        problem=problem.id,
        response=response.id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        elder_type=elder_type,
        elder_name=elder_name,
        delay=delay,
        hero_trait=hero_trait,
        sidekick_trait=sidekick_trait,
        mascot=mascot,
        seed=None,
    ))
    if outcome == "recovered":
        ending_recovered(world, hero, sidekick, elder, crop, response)
    else:
        ending_faded(world, hero, sidekick, elder, crop, response)

    world.facts.update(
        crop=crop,
        problem=problem,
        response=response,
        hero=hero,
        sidekick=sidekick,
        elder=elder,
        patch=patch,
        outcome=outcome,
        delay=delay,
        prayer_said=True,
        flashback_used=True,
    )
    return world


CROPS = {
    "tomatoes": Crop(
        id="tomatoes",
        label="tomatoes",
        phrase="a row of tomatoes",
        patch="tomato patch",
        color="red",
        tags={"tomatoes", "plants"},
    ),
    "lettuce": Crop(
        id="lettuce",
        label="lettuce",
        phrase="a bed of lettuce",
        patch="lettuce bed",
        color="green",
        tags={"lettuce", "plants"},
    ),
    "beans": Crop(
        id="beans",
        label="beans",
        phrase="a line of climbing beans",
        patch="bean row",
        color="green",
        tags={"beans", "plants"},
    ),
    "sunflowers": Crop(
        id="sunflowers",
        label="sunflowers",
        phrase="a stand of sunflowers",
        patch="sunflower bed",
        color="yellow",
        tags={"sunflowers", "plants"},
    ),
}

PROBLEMS = {
    "thirsty": Problem(
        id="thirsty",
        label="thirsty",
        need="water",
        severity=2,
        symptom="droopy and dusty",
        cause="the soil had turned pale and dry in the heat",
        danger_line="Their leaves curled at the edges as if they were too tired to wave.",
        flashback="showing how to push a finger into the dirt and saying, 'If the soil feels dry down there too, the roots are asking for water, not noise.'",
        joke_idea="a gusty cape-flap and three heroic whooshing sounds",
        tags={"water", "thirsty"},
    ),
    "too_hot": Problem(
        id="too_hot",
        label="too hot",
        need="shade",
        severity=2,
        symptom="limp and shiny with heat",
        cause="the noon sun was pressing on them without a break",
        danger_line="The leaves sagged like tiny green flags after a long parade.",
        flashback="stretching a bit of shade cloth over a bed and saying, 'Even brave plants need a cool rest sometimes.'",
        joke_idea="a silver pie tin helmet to reflect the sun away",
        tags={"shade", "heat"},
    ),
    "leaning": Problem(
        id="leaning",
        label="leaning",
        need="support",
        severity=3,
        symptom="tilted and tangled",
        cause="a rough wind had knocked stems against their stakes",
        danger_line="One more hard push from the breeze and a stem might snap.",
        flashback="tying a soft cloth strip around a bent stem and whispering, 'Gentle support helps more than a hard yank.'",
        joke_idea="a thunder voice that ordered the plants to stand up straight",
        tags={"support", "wind"},
    ),
}

RESPONSES = {
    "watering_can": Response(
        id="watering_can",
        sense=3,
        power=3,
        provides="water",
        action_text="carried two watering cans and poured slowly at the roots until the dark soil drank it in",
        fail_text="carried water to the roots, but the patch had already gone past an easy rescue",
        qa_text="They watered the roots slowly with watering cans.",
        gift_line="the big blue watering can from the tool shed",
        tags={"watering_can", "water"},
    ),
    "shade_cloth": Response(
        id="shade_cloth",
        sense=3,
        power=3,
        provides="shade",
        action_text="lifted a piece of shade cloth over the bed and clipped it in place so the harsh light softened",
        fail_text="hung up the shade cloth, but the plants had already been scorched for too long",
        qa_text="They stretched shade cloth over the bed to cool it.",
        gift_line="a folded piece of shade cloth and two garden clips",
        tags={"shade_cloth", "shade"},
    ),
    "soft_tie": Response(
        id="soft_tie",
        sense=3,
        power=4,
        provides="support",
        action_text="used soft cloth ties to fasten the stems gently back to their stakes",
        fail_text="tied the stems gently, but some had already bent too far to spring back fully",
        qa_text="They tied the stems gently back to their stakes.",
        gift_line="soft cloth ties and a patient pair of hands",
        tags={"soft_tie", "support"},
    ),
    "cape_fan": Response(
        id="cape_fan",
        sense=1,
        power=0,
        provides="wind",
        action_text="flapped their capes at the plants",
        fail_text="flapped their capes at the plants, which mostly stirred the mulch and accomplished nothing useful",
        qa_text="They only flapped their capes.",
        gift_line="a giant cape swirl",
        tags={"humor"},
    ),
    "megaphone": Response(
        id="megaphone",
        sense=1,
        power=0,
        provides="noise",
        action_text="shouted superhero orders through a toy megaphone",
        fail_text="shouted through a toy megaphone, and the leaves did not obey even a little",
        qa_text="They shouted through a toy megaphone.",
        gift_line="a toy megaphone",
        tags={"humor"},
    ),
    "lemonade": Response(
        id="lemonade",
        sense=1,
        power=0,
        provides="drink",
        action_text="splashed lemonade around the stems",
        fail_text="splashed lemonade around the stems, which made everything sticky instead of better",
        qa_text="They poured lemonade on the plants.",
        gift_line="a cup of lemonade",
        tags={"humor"},
    ),
}

GIRL_NAMES = ["Nia", "Maya", "Ava", "Lila", "Zoe", "Ruby", "Tessa", "Mina"]
BOY_NAMES = ["Jude", "Theo", "Max", "Eli", "Noah", "Finn", "Sam", "Leo"]
HERO_TRAITS = ["dramatic", "brave", "sparky", "bouncy", "eager"]
SIDEKICK_TRAITS = ["careful", "steady", "thoughtful", "gentle", "wise"]
MASCOTS = ["a very round worm", "a snail with excellent timing", "a beetle on a leaf", "a ladybug on the fence", ""]


@dataclass
class StoryParams:
    crop: str
    problem: str
    response: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    elder_type: str
    elder_name: str
    delay: int = 0
    hero_trait: str = "dramatic"
    sidekick_trait: str = "careful"
    mascot: str = ""
    seed: Optional[int] = None


KNOWLEDGE = {
    "water": [
        (
            "Why do plants need water?",
            "Plants need water to stay firm and alive. Water helps roots feed the rest of the plant, so leaves do not droop."
        )
    ],
    "shade": [
        (
            "Why can too much hot sun hurt plants?",
            "Very strong sun can make plants lose water too quickly. When they cannot keep up, their leaves can wilt and look tired."
        )
    ],
    "support": [
        (
            "Why do some garden plants need support?",
            "Tall or climbing plants can bend in wind or under their own weight. A stake or soft tie helps hold them up without hurting the stem."
        )
    ],
    "prayer": [
        (
            "What is a prayer?",
            "A prayer is when someone talks to God. A person can pray to ask for help, give thanks, or share what is in their heart."
        )
    ],
    "community_garden": [
        (
            "What is a community garden?",
            "A community garden is a place where neighbors grow plants together. People share the space and help care for it."
        )
    ],
    "watering_can": [
        (
            "What does a watering can do?",
            "A watering can carries water to plants in a gentle way. Its spout helps pour the water where the roots can use it."
        )
    ],
    "shade_cloth": [
        (
            "What is shade cloth for?",
            "Shade cloth is a light fabric that blocks part of the strong sun. It helps plants cool down without putting them in full darkness."
        )
    ],
    "soft_tie": [
        (
            "Why should you tie a plant softly?",
            "A soft tie holds the plant up without cutting into the stem. Plants need support that is gentle, not rough."
        )
    ],
    "tomatoes": [
        (
            "What do tomato plants grow?",
            "Tomato plants grow tomatoes, which start green and often turn red as they ripen."
        )
    ],
    "lettuce": [
        (
            "What is lettuce?",
            "Lettuce is a leafy garden plant that people often eat in salads or sandwiches."
        )
    ],
    "beans": [
        (
            "Why do beans often climb?",
            "Many bean plants climb upward as they grow. They use poles or strings to help reach the light."
        )
    ],
    "sunflowers": [
        (
            "Why are sunflowers tall?",
            "Sunflowers grow tall so their big flower heads can reach lots of sunlight."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "prayer",
    "community_garden",
    "water",
    "shade",
    "support",
    "watering_can",
    "shade_cloth",
    "soft_tie",
    "tomatoes",
    "lettuce",
    "beans",
    "sunflowers",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    crop = f["crop"]
    problem = f["problem"]
    outcome = f["outcome"]
    hero = f["hero"]
    sidekick = f["sidekick"]
    response = f["response"]
    mood = "happy" if outcome == "recovered" else "bittersweet"
    return [
        f'Write a short superhero story for a 3-to-5-year-old set in a community garden that includes the word "prayer".',
        f"Tell a funny garden rescue story where {hero.id} and {sidekick.id} act like superheroes, use a quick flashback to remember a lesson, and help some {crop.label} that are {problem.label}.",
        f"Write a {mood} story in which children first imagine a silly fix, then choose {response.gift_line} instead because real heroes help in the right way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    elder = f["elder"]
    crop = f["crop"]
    problem = f["problem"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {sidekick.id}, two children pretending to be superheroes in a community garden. {elder.id}, the garden helper, also guides them."
        ),
        (
            f"What problem did they find in the {crop.patch}?",
            f"They found that the {crop.label} looked {problem.symptom}. This happened because {problem.cause}."
        ),
        (
            "What made the story funny?",
            f"{hero.id} gave a huge superhero speech and suggested {problem.joke_idea}, but the cape slipped into the mulch. That silly moment made the rescue feel playful instead of frightening."
        ),
        (
            "Where was the flashback in the story?",
            f"The flashback came when {sidekick.id} remembered an earlier garden lesson from {elder.id}. That memory showed them what the plants really needed."
        ),
        (
            "Where was the prayer in the story, and why did they pray?",
            f"{sidekick.id} whispered a small prayer beside the raised bed before they chose a fix. The prayer asked God to help them choose the kind and sensible way to help the garden."
        ),
    ]
    if outcome == "recovered":
        qa.append(
            (
                f"How did they help the {crop.label}?",
                f"{response.qa_text} That matched the real problem, so the patch could recover instead of getting worse."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily, with the {crop.patch} looking stronger again. The children learned that a real hero notices what is needed and helps gently."
            )
        )
    else:
        qa.append(
            (
                f"Did their fix work in time for the {crop.patch}?",
                f"Not completely. {response.qa_text} It helped some, but the trouble had already gone on too long."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended in a gentle, bittersweet way. The children learned to notice plant trouble sooner and promised to be more careful superheroes next time."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"prayer", "community_garden", f["crop"].id}
    tags |= set(f["problem"].tags)
    if f["response"].sense >= SENSE_MIN:
        tags |= set(f["response"].tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
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
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        crop="tomatoes",
        problem="thirsty",
        response="watering_can",
        hero_name="Nia",
        hero_gender="girl",
        sidekick_name="Jude",
        sidekick_gender="boy",
        elder_type="mother",
        elder_name="Ms. Rosa",
        delay=0,
        hero_trait="dramatic",
        sidekick_trait="careful",
        mascot="a very round worm",
    ),
    StoryParams(
        crop="lettuce",
        problem="too_hot",
        response="shade_cloth",
        hero_name="Maya",
        hero_gender="girl",
        sidekick_name="Theo",
        sidekick_gender="boy",
        elder_type="father",
        elder_name="Mr. Ben",
        delay=0,
        hero_trait="bouncy",
        sidekick_trait="wise",
        mascot="a snail with excellent timing",
    ),
    StoryParams(
        crop="beans",
        problem="leaning",
        response="soft_tie",
        hero_name="Ava",
        hero_gender="girl",
        sidekick_name="Max",
        sidekick_gender="boy",
        elder_type="mother",
        elder_name="Ms. June",
        delay=0,
        hero_trait="eager",
        sidekick_trait="steady",
        mascot="a beetle on a leaf",
    ),
    StoryParams(
        crop="sunflowers",
        problem="leaning",
        response="soft_tie",
        hero_name="Leo",
        hero_gender="boy",
        sidekick_name="Ruby",
        sidekick_gender="girl",
        elder_type="father",
        elder_name="Mr. Luis",
        delay=2,
        hero_trait="brave",
        sidekick_trait="gentle",
        mascot="a ladybug on the fence",
    ),
]


def explain_problem(crop: Crop, problem: Problem) -> str:
    return (
        f"(No story: {problem.label} is not a good fit for the {crop.patch}. "
        f"This world only tells garden troubles that are plausible for that crop.)"
    )


def explain_response(problem: Problem, response: Response) -> str:
    if response.sense < SENSE_MIN:
        better = ", ".join(sorted(r.id for r in sensible_responses()))
        return (
            f"(Refusing response '{response.id}': it is a joke idea, not a sensible garden fix "
            f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    return (
        f"(No story: {response.id} gives {response.provides}, but this problem needs {problem.need}. "
        f"The fix must match the real need of the plants.)"
    )


ASP_RULES = r"""
crop_problem_ok(C, P) :- crop_problem(C, P).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
matches(P, R) :- problem(P), response(R), needs(P, N), provides(R, N).
valid(C, P, R) :- crop(C), problem(P), response(R),
                  crop_problem_ok(C, P), sensible(R), matches(P, R).

strength(V) :- chosen_problem(P), severity(P, S), delay(D), V = S + D.
outcome(recovered) :- chosen_response(R), power(R, P), strength(V), P >= V.
outcome(faded) :- chosen_response(R), power(R, P), strength(V), P < V.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for crop_id in sorted(CROPS):
        lines.append(asp.fact("crop", crop_id))
    for crop_id, problem_ids in sorted(CROP_PROBLEMS.items()):
        for problem_id in sorted(problem_ids):
            lines.append(asp.fact("crop_problem", crop_id, problem_id))
    for problem_id, problem in sorted(PROBLEMS.items()):
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("needs", problem_id, problem.need))
        lines.append(asp.fact("severity", problem_id, problem.severity))
    for response_id, response in sorted(RESPONSES.items()):
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("provides", response_id, response.provides))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("(Smoke test failed: empty story.)")
    _ = sample.to_dict()
    _ = format_qa(sample)


def asp_verify() -> int:
    rc = 0
    try:
        smoke_test()
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1

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

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} "
            f"python={sorted(python_sensible)}"
        )

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: garden superheroes, a flashback, a prayer, and a sensible rescue."
    )
    ap.add_argument("--crop", choices=sorted(CROPS))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--response", choices=sorted(RESPONSES))
    ap.add_argument("--elder-type", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the garden problem has gone on")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.crop and args.problem:
        crop = CROPS[args.crop]
        problem = PROBLEMS[args.problem]
        if not problem_fits_crop(crop, problem):
            raise StoryError(explain_problem(crop, problem))
    if args.problem and args.response:
        problem = PROBLEMS[args.problem]
        response = RESPONSES[args.response]
        if not response_matches(problem, response):
            raise StoryError(explain_response(problem, response))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        response = RESPONSES[args.response]
        dummy_problem = PROBLEMS[args.problem] if args.problem else next(iter(PROBLEMS.values()))
        raise StoryError(explain_response(dummy_problem, response))

    combos = [
        c for c in valid_combos()
        if (args.crop is None or c[0] == args.crop)
        and (args.problem is None or c[1] == args.problem)
        and (args.response is None or c[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    crop_id, problem_id, response_id = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    sidekick_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = _pick_name(rng, hero_gender)
    sidekick_name = _pick_name(rng, sidekick_gender, avoid=hero_name)
    elder_type = args.elder_type or rng.choice(["mother", "father"])
    elder_name = rng.choice(["Ms. Rosa", "Mr. Ben", "Ms. June", "Mr. Luis", "Ms. Alma"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    hero_trait = rng.choice(HERO_TRAITS)
    sidekick_trait = rng.choice(SIDEKICK_TRAITS)
    mascot = rng.choice(MASCOTS)

    return StoryParams(
        crop=crop_id,
        problem=problem_id,
        response=response_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        elder_type=elder_type,
        elder_name=elder_name,
        delay=delay,
        hero_trait=hero_trait,
        sidekick_trait=sidekick_trait,
        mascot=mascot,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        crop = CROPS[params.crop]
        problem = PROBLEMS[params.problem]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err

    if not problem_fits_crop(crop, problem):
        raise StoryError(explain_problem(crop, problem))
    if response.sense < SENSE_MIN or not response_matches(problem, response):
        raise StoryError(explain_response(problem, response))

    world = tell(
        crop=crop,
        problem=problem,
        response=response,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        sidekick_name=params.sidekick_name,
        sidekick_gender=params.sidekick_gender,
        elder_type=params.elder_type,
        elder_name=params.elder_name,
        delay=params.delay,
        hero_trait=params.hero_trait,
        sidekick_trait=params.sidekick_trait,
        mascot=params.mascot,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} valid (crop, problem, response) combos:\n")
        for crop, problem, response in combos:
            print(f"  {crop:11} {problem:9} {response}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero_name} & {p.sidekick_name}: {p.crop} / {p.problem} / "
                f"{p.response} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
