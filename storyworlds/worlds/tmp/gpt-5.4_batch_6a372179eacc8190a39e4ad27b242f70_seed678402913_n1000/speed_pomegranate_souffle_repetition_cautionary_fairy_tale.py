#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/speed_pomegranate_souffle_repetition_cautionary_fairy_tale.py
==========================================================================================

A small fairy-tale story world about a child in a kitchen tower who wants a
pomegranate soufflé right away. The world enforces a simple cautionary rule:
a soufflé only rises when delicate steps are done gently and in the right
order. Rushing for speed makes it fall, spill, or stay flat.

The domain uses repetition on purpose: the eager child tries the quick way
three times, each attempt worsens the batter's state, and then finally listens
to a calm helper and learns to slow down. The prose is state-driven rather than
slot-swapped: mixing, oven heat, foam strength, mess, fear, patience, and trust
all influence what gets told.

Run it
------
    python storyworlds/worlds/gpt-5.4/speed_pomegranate_souffle_repetition_cautionary_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/speed_pomegranate_souffle_repetition_cautionary_fairy_tale.py --hero hare --method whip_fast --finish listen
    python storyworlds/worlds/gpt-5.4/speed_pomegranate_souffle_repetition_cautionary_fairy_tale.py --fruit apple   # rejected
    python storyworlds/worlds/gpt-5.4/speed_pomegranate_souffle_repetition_cautionary_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/speed_pomegranate_souffle_repetition_cautionary_fairy_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/speed_pomegranate_souffle_repetition_cautionary_fairy_tale.py --verify
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
        female = {"girl", "mother", "fairy_godmother", "queen", "princess", "hen"}
        male = {"boy", "father", "king", "prince", "hare", "fox", "frog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class HeroSpec:
    id: str
    title: str
    type: str
    adjective: str
    home: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FruitSpec:
    id: str
    label: str
    jewel: str
    seeds_name: str
    good_for_souffle: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class MethodSpec:
    id: str
    label: str
    speed: int
    folds_gently: bool
    whips_steady: bool
    waits_for_oven: bool
    sense: int
    try_line: str
    warning: str
    success_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FinishSpec:
    id: str
    listens: bool
    helper_gives_hand: bool
    ending: str
    moral_tail: str
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


def _r_foam_breaks(world: World) -> list[str]:
    bowl = world.get("bowl")
    oven = world.get("oven")
    out: list[str] = []
    if bowl.meters["mixed"] < THRESHOLD:
        return out
    if bowl.meters["shaken"] >= THRESHOLD and ("foam_breaks",) not in world.fired:
        world.fired.add(("foam_breaks",))
        bowl.meters["foam"] = max(0.0, bowl.meters["foam"] - 1.0)
        bowl.meters["heavy"] += 1.0
        out.append("The shining foam lost its airy lift.")
    if bowl.meters["heavy"] >= THRESHOLD and ("not_risen",) not in world.fired:
        world.fired.add(("not_risen",))
        oven.meters["not_risen"] += 1.0
    return out


def _r_spill_makes_mess(world: World) -> list[str]:
    bowl = world.get("bowl")
    kitchen = world.get("kitchen")
    helper = world.get("helper")
    out: list[str] = []
    if bowl.meters["spilled"] >= THRESHOLD and ("spill",) not in world.fired:
        world.fired.add(("spill",))
        kitchen.meters["mess"] += 1.0
        helper.meters["workload"] += 1.0
        out.append("Ruby-red drops splashed over the table and the floor.")
    return out


def _r_hot_oven_burn_risk(world: World) -> list[str]:
    oven = world.get("oven")
    hero = world.get("hero")
    out: list[str] = []
    if oven.meters["too_hot"] >= THRESHOLD and ("hot_risk",) not in world.fired:
        world.fired.add(("hot_risk",))
        hero.memes["fear"] += 1.0
        out.append("The oven breathed such fierce heat that even the eager child stepped back.")
    return out


def _r_success(world: World) -> list[str]:
    bowl = world.get("bowl")
    oven = world.get("oven")
    hero = world.get("hero")
    if bowl.meters["foam"] >= THRESHOLD and oven.meters["ready"] >= THRESHOLD and bowl.meters["heavy"] < THRESHOLD:
        if ("success",) not in world.fired:
            world.fired.add(("success",))
            oven.meters["risen"] += 1.0
            hero.memes["relief"] += 1.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="foam_breaks", tag="physical", apply=_r_foam_breaks),
    Rule(name="spill_makes_mess", tag="physical", apply=_r_spill_makes_mess),
    Rule(name="hot_oven_burn_risk", tag="physical", apply=_r_hot_oven_burn_risk),
    Rule(name="success", tag="physical", apply=_r_success),
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


def valid_combo(hero: HeroSpec, fruit: FruitSpec, method: MethodSpec, finish: FinishSpec) -> bool:
    return fruit.good_for_souffle and method.sense >= 2


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for hero_id, hero in HEROES.items():
        for fruit_id, fruit in FRUITS.items():
            for method_id, method in METHODS.items():
                for finish_id, finish in FINISHES.items():
                    if valid_combo(hero, fruit, method, finish):
                        combos.append((hero_id, fruit_id, method_id, finish_id))
    return combos


def explain_fruit(fruit: FruitSpec) -> str:
    return (
        f"(No story: {fruit.label.capitalize()} is known in this world, but it does not make a "
        f"good fairy-tale soufflé here. Pick pomegranate, whose bright juice belongs in this tale.)"
    )


def explain_method(method: MethodSpec) -> str:
    return (
        f"(No story: '{method.id}' is too foolish for this world. A cautionary tale may include haste, "
        f"but the chosen method still has to be recognizable kitchen behavior.)"
    )


def predict_attempt(method: MethodSpec, fruit: FruitSpec) -> dict:
    world = base_world(HEROES["hare"], fruit)
    do_attempt(world, method, attempt_no=1, narrate=False)
    return {
        "mess": world.get("kitchen").meters["mess"],
        "fear": world.get("hero").memes["fear"],
        "risen": world.get("oven").meters["risen"] >= THRESHOLD,
        "not_risen": world.get("oven").meters["not_risen"] >= THRESHOLD,
    }


def base_world(hero_spec: HeroSpec, fruit_spec: FruitSpec) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_spec.type,
        label=hero_spec.title,
        phrase=f"{hero_spec.title} the {hero_spec.type}",
        role="hero",
        traits=[hero_spec.adjective],
        tags=set(hero_spec.tags),
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="fairy_godmother",
        label="the kitchen fairy",
        phrase="the kitchen fairy with flour on her silver sleeves",
        role="helper",
        traits=["patient", "kind"],
        tags={"helper", "fairy"},
    ))
    bowl = world.add(Entity(
        id="bowl",
        type="bowl",
        label="bowl",
        phrase="the moon-white mixing bowl",
        tags={"batter"},
    ))
    oven = world.add(Entity(
        id="oven",
        type="oven",
        label="oven",
        phrase="the little brass oven",
        tags={"oven", "heat"},
    ))
    fruit = world.add(Entity(
        id="fruit",
        type="fruit",
        label=fruit_spec.label,
        phrase=f"the {fruit_spec.label}",
        tags=set(fruit_spec.tags),
    ))
    kitchen = world.add(Entity(
        id="kitchen",
        type="room",
        label="kitchen",
        phrase=hero_spec.home,
        tags={"kitchen"},
    ))
    hero.memes["desire"] = 1.0
    hero.memes["impatience"] = 2.0
    helper.memes["care"] = 1.0
    fruit.meters["ripe"] = 1.0
    world.facts["tries"] = []
    return world


def introduce(world: World, hero_spec: HeroSpec, fruit_spec: FruitSpec) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    world.say(
        f"In {hero_spec.home}, where the pans rang like tiny bells at dawn, lived "
        f"{hero_spec.title} the {hero_spec.type}, a {hero_spec.adjective} child who loved bright treats."
    )
    world.say(
        f"One morning {hero.pronoun()} found a {fruit_spec.label} split open on the table, "
        f"its {fruit_spec.seeds_name} glowing like {fruit_spec.jewel} in a crown."
    )
    world.say(
        f'"I shall bake a pomegranate soufflé before the window light climbs the wall," '
        f'{hero.pronoun()} declared. The kitchen fairy looked up from her flour and smiled a careful smile.'
    )


def need_patience(world: World) -> None:
    helper = world.get("helper")
    world.say(
        f'"A soufflé is a proud little cloud," said {helper.label_word}. '
        f'"It rises for gentle hands, not for wild speed."'
    )


def do_attempt(world: World, method: MethodSpec, attempt_no: int, narrate: bool = True) -> None:
    hero = world.get("hero")
    bowl = world.get("bowl")
    oven = world.get("oven")

    hero.memes["impatience"] += 1.0
    hero.memes["defiance"] += 1.0
    bowl.meters["mixed"] += 1.0
    oven.meters["opened"] += 1.0

    if method.speed >= 3:
        bowl.meters["shaken"] += 1.0
    if not method.whips_steady:
        bowl.meters["shaken"] += 1.0
    if not method.folds_gently:
        bowl.meters["heavy"] += 1.0
    if method.waits_for_oven:
        oven.meters["ready"] += 1.0
    else:
        oven.meters["too_hot"] += 1.0

    if method.speed >= 4 and attempt_no == 2:
        bowl.meters["spilled"] += 1.0
    if method.speed >= 4 and attempt_no == 3:
        bowl.meters["spilled"] += 1.0
        bowl.meters["heavy"] += 1.0

    if narrate:
        world.say(f'"Faster, faster, faster," said the child for the {ordinal(attempt_no)} time.')
        world.say(method.try_line)
    propagate(world, narrate=narrate)


def attempt_result(world: World, attempt_no: int) -> str:
    bowl = world.get("bowl")
    oven = world.get("oven")
    if oven.meters["risen"] >= THRESHOLD:
        return "rose"
    if bowl.meters["spilled"] >= THRESHOLD and attempt_no >= 2:
        return "spilled"
    if oven.meters["too_hot"] >= THRESHOLD:
        return "scorched"
    return "fell"


def narrate_attempt_failure(world: World, fruit_spec: FruitSpec, attempt_no: int) -> None:
    result = attempt_result(world, attempt_no)
    if result == "spilled":
        world.say(
            f"The batter slopped against the rim, and {fruit_spec.jewel} drops of {fruit_spec.label} "
            f"ran down the bowl like little red tears."
        )
    elif result == "scorched":
        world.say(
            "The oven puffed too hot and too soon. The top browned before the middle could learn to lift."
        )
    else:
        world.say(
            "Into the oven went the hopeful dish, and out it came low and sad, as flat as a hat left in the rain."
        )


def ordinal(n: int) -> str:
    return {1: "first", 2: "second", 3: "third"}.get(n, f"{n}th")


def three_quick_tries(world: World, method: MethodSpec, fruit_spec: FruitSpec) -> None:
    for attempt_no in (1, 2, 3):
        if attempt_no > 1:
            world.say(
                f"Still the child muttered, 'Speed can surely do in a blink what patience does in an hour.'"
            )
        do_attempt(world, method, attempt_no=attempt_no, narrate=True)
        narrate_attempt_failure(world, fruit_spec, attempt_no)
        world.facts["tries"].append(
            {
                "attempt": attempt_no,
                "mess": world.get("kitchen").meters["mess"],
                "fear": world.get("hero").memes["fear"],
                "result": attempt_result(world, attempt_no),
            }
        )


def helper_intervenes(world: World, method: MethodSpec) -> None:
    helper = world.get("helper")
    hero = world.get("hero")
    helper.memes["care"] += 1.0
    hero.memes["trust"] += 1.0
    world.say(
        f'At last {helper.label_word} laid a cool hand on the spoon and said, "{method.warning}"'
    )
    world.say(
        f'"Speed may chase a rabbit across a field," {helper.pronoun()} went on, '
        f'"but it cannot teach a soufflé to float."'
    )


def gentle_recovery(world: World, finish: FinishSpec, method: MethodSpec, fruit_spec: FruitSpec) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    bowl = world.get("bowl")
    oven = world.get("oven")
    kitchen = world.get("kitchen")

    if finish.listens:
        hero.memes["patience"] += 2.0
        hero.memes["defiance"] = 0.0
        hero.memes["relief"] += 1.0
        hero.memes["trust"] += 1.0
        bowl.meters["shaken"] = 0.0
        bowl.meters["heavy"] = 0.0
        bowl.meters["mixed"] = 1.0
        bowl.meters["foam"] = 1.0
        bowl.meters["spilled"] = 0.0
        oven.meters["too_hot"] = 0.0
        oven.meters["ready"] = 1.0
        kitchen.meters["mess"] = max(0.0, kitchen.meters["mess"] - 1.0)
        propagate(world, narrate=False)
        world.say(
            f"Together they split more {fruit_spec.label} seeds, counted their breaths, and moved the spoon softly."
        )
        world.say(method.success_line)
        world.say(
            f"This time the pomegranate soufflé rose in the brass oven like a pink dawn cloud."
        )
        world.say(
            f"When {hero.pronoun()} tasted it, {hero.pronoun()} laughed a smaller, wiser laugh than before."
        )
    else:
        hero.memes["fear"] += 1.0
        hero.memes["regret"] += 1.0
        world.say(
            f"But the child would not listen. The bowl sat sticky, the oven sighed, and no pomegranate soufflé graced the table that day."
        )


def ending_image(world: World, finish: FinishSpec) -> None:
    hero = world.get("hero")
    kitchen = world.get("kitchen")
    if finish.listens:
        world.say(finish.ending)
        if kitchen.meters["mess"] >= THRESHOLD:
            world.say("Even the red drops left on the table looked less like a disaster and more like a lesson remembered.")
    else:
        world.say(finish.ending)
    world.say(finish.moral_tail)
    world.facts["moral"] = finish.moral_tail


def tell(hero_spec: HeroSpec, fruit_spec: FruitSpec, method: MethodSpec, finish: FinishSpec) -> World:
    world = base_world(hero_spec, fruit_spec)
    introduce(world, hero_spec, fruit_spec)
    need_patience(world)

    world.para()
    predicted = predict_attempt(method, fruit_spec)
    world.facts["predicted"] = predicted
    world.say(
        f"The child heard the warning, yet the thought of speed glittered like a shortcut through the woods."
    )
    three_quick_tries(world, method, fruit_spec)

    world.para()
    helper_intervenes(world, method)
    gentle_recovery(world, finish, method, fruit_spec)

    world.para()
    ending_image(world, finish)

    world.facts.update(
        hero=world.get("hero"),
        helper=world.get("helper"),
        fruit=world.get("fruit"),
        bowl=world.get("bowl"),
        oven=world.get("oven"),
        kitchen=world.get("kitchen"),
        hero_spec=hero_spec,
        fruit_spec=fruit_spec,
        method=method,
        finish=finish,
        success=world.get("oven").meters["risen"] >= THRESHOLD,
        mess=world.get("kitchen").meters["mess"],
    )
    return world


HEROES = {
    "hare": HeroSpec(
        id="hare",
        title="Pip",
        type="hare",
        adjective="swift-footed",
        home="a round kitchen tower at the edge of the king's orchard",
        tags={"hare", "speed"},
    ),
    "frog": HeroSpec(
        id="frog",
        title="Moss",
        type="frog",
        adjective="quick-hearted",
        home="a green-windowed bakery by the lily pond",
        tags={"frog", "speed"},
    ),
    "girl": HeroSpec(
        id="girl",
        title="Nella",
        type="girl",
        adjective="bright-eyed",
        home="a high stone kitchen beside the castle plum trees",
        tags={"child", "speed"},
    ),
}

FRUITS = {
    "pomegranate": FruitSpec(
        id="pomegranate",
        label="pomegranate",
        jewel="garnets",
        seeds_name="ruby seeds",
        good_for_souffle=True,
        tags={"pomegranate", "fruit"},
    ),
    "apple": FruitSpec(
        id="apple",
        label="apple",
        jewel="amber",
        seeds_name="pale apple bits",
        good_for_souffle=False,
        tags={"apple", "fruit"},
    ),
}

METHODS = {
    "whip_fast": MethodSpec(
        id="whip_fast",
        label="whip fast",
        speed=4,
        folds_gently=False,
        whips_steady=False,
        waits_for_oven=False,
        sense=2,
        try_line="The spoon flew so fast that the batter spun in dizzy circles, and the child pushed it into the heat before the oven was truly ready.",
        warning="Slow hands make strong bubbles. Fast hands break them.",
        success_line="The fairy counted to three, and the child folded the foam as gently as laying a blanket over a sleeping bird.",
        tags={"speed", "souffle", "whisk"},
    ),
    "skip_rest": MethodSpec(
        id="skip_rest",
        label="skip the waiting",
        speed=3,
        folds_gently=True,
        whips_steady=True,
        waits_for_oven=False,
        sense=2,
        try_line="The batter was made neatly enough, but the child kept peeking, poking, and hurrying it toward heat before its airy heart was settled.",
        warning="Some things hurry only by seeming to rest.",
        success_line="When the child finally let the oven warm first and kept the door closed, the little cake learned to rise without fright.",
        tags={"speed", "souffle", "oven"},
    ),
    "steady_spoon": MethodSpec(
        id="steady_spoon",
        label="steady spoon",
        speed=1,
        folds_gently=True,
        whips_steady=True,
        waits_for_oven=True,
        sense=3,
        try_line="Even eager hands can remember softness; the child breathed once and stirred as if listening to a lullaby in the bowl.",
        warning="You already know the safe way. Keep doing it.",
        success_line="No rush touched the spoon now, and each bright fold kept its air.",
        tags={"souffle", "patience"},
    ),
    "throw_it": MethodSpec(
        id="throw_it",
        label="throw everything together",
        speed=5,
        folds_gently=False,
        whips_steady=False,
        waits_for_oven=False,
        sense=1,
        try_line="The child dumped and thumped and sent flour flying.",
        warning="That is not baking at all.",
        success_line="At last the spoon moved properly.",
        tags={"bad_idea"},
    ),
}

FINISHES = {
    "listen": FinishSpec(
        id="listen",
        listens=True,
        helper_gives_hand=True,
        ending="From then on, whenever haste whispered in the kitchen, the child answered, 'Not for a soufflé, not for a soufflé, not for a soufflé.'",
        moral_tail="So the fairy-tale cooks of that tower said that speed is useful on the road, but patience must wear the crown in the oven.",
        tags={"listen", "moral"},
    ),
    "refuse": FinishSpec(
        id="refuse",
        listens=False,
        helper_gives_hand=False,
        ending="All evening the tower smelled of sweetness that might have been, and the empty dish looked like a warning in silver.",
        moral_tail="And that is why wise folk say that a proud wish for speed can leave even a rich kitchen hungry.",
        tags={"refuse", "moral"},
    ),
}


@dataclass
class StoryParams:
    hero: str
    fruit: str
    method: str
    finish: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(hero="hare", fruit="pomegranate", method="whip_fast", finish="listen"),
    StoryParams(hero="frog", fruit="pomegranate", method="skip_rest", finish="listen"),
    StoryParams(hero="girl", fruit="pomegranate", method="steady_spoon", finish="listen"),
    StoryParams(hero="hare", fruit="pomegranate", method="whip_fast", finish="refuse"),
]


KNOWLEDGE = {
    "pomegranate": [
        (
            "What is a pomegranate?",
            "A pomegranate is a round fruit with many shiny red seeds inside. People eat the juicy seeds, and they burst with sweet-tart juice.",
        )
    ],
    "souffle": [
        (
            "What is a soufflé?",
            "A soufflé is a light baked dish made with lots of air folded into it. If the air stays trapped, it puffs up tall in the oven.",
        )
    ],
    "speed": [
        (
            "Why can too much speed be a problem when you cook?",
            "Some foods need gentle steps and waiting time, so going too fast can spoil them. Speed is good for running, but not for every job.",
        )
    ],
    "oven": [
        (
            "Why should an oven be ready before a delicate dish goes in?",
            "A delicate batter needs the right heat at the right time. If the oven is wrong or the door keeps opening, the dish may not rise well.",
        )
    ],
    "foam": [
        (
            "Why do gentle folds matter in a soufflé?",
            "Gentle folds keep the tiny bubbles inside the batter. Those bubbles help the soufflé rise like a soft cloud.",
        )
    ],
    "patience": [
        (
            "What does patience mean?",
            "Patience means waiting calmly and doing careful steps without rushing. It helps people do delicate work well.",
        )
    ],
}

KNOWLEDGE_ORDER = ["pomegranate", "souffle", "speed", "oven", "foam", "patience"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    method = f["method"]
    finish = f["finish"]
    mood = "learns patience after three failed tries" if finish.listens else "refuses advice and ends hungry"
    return [
        'Write a fairy tale for a 3-to-5-year-old that includes the words "speed", "pomegranate", and "souffle".',
        f"Tell a cautionary kitchen fairy tale where {hero.phrase} wants a pomegranate soufflé too quickly, repeats the same mistake three times, and {mood}.",
        f"Write a repetitive story with the line 'faster, faster, faster' where a child tries {method.label} and learns that speed is not the same as wisdom.",
    ]


def pair_try_summary(tries: list[dict]) -> str:
    parts = []
    for item in tries:
        parts.append(f"the {ordinal(item['attempt'])} try {item['result']}")
    if not parts:
        return "no tries were made"
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + ", and " + parts[-1]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    fruit = f["fruit"]
    method = f["method"]
    tries = f["tries"]
    success = f["success"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.phrase}, who wanted to make a pomegranate soufflé, and {helper.label_word}, who tried to guide {hero.pronoun('object')} gently.",
        ),
        (
            "What did the child want to make?",
            f"{hero.pronoun().capitalize()} wanted to bake a pomegranate soufflé. The bright {fruit.label} made the treat feel magical and special.",
        ),
        (
            "Why was speed a problem in the story?",
            f"Speed made the child rush delicate cooking steps. In this kitchen, a soufflé rises only when the batter is treated gently and the oven is handled with care.",
        ),
        (
            "What happened three times?",
            f"The child kept trying the quick way again and again: {pair_try_summary(tries)}. The repetition shows that the same hurried mistake kept bringing trouble instead of success.",
        ),
    ]
    if success:
        qa.append(
            (
                f"How did {hero.label_word} finally make the soufflé rise?",
                f"{hero.pronoun().capitalize()} listened to {helper.label_word}, slowed down, and handled the batter gently. That protected the airy foam, so the pomegranate soufflé could rise at last.",
            )
        )
        qa.append(
            (
                "What lesson did the ending show?",
                f"The ending showed that patience can do what speed cannot. The tall soufflé became the proof that wise, careful work changed the outcome.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.label_word} end without a soufflé?",
                f"{hero.pronoun().capitalize()} kept refusing the warning and stayed with the rushed method. Because the child never changed the careful steps, the kitchen had sweetness and mess but no rising soufflé.",
            )
        )
        qa.append(
            (
                "What lesson did the sad ending teach?",
                "It taught that repeating a reckless choice does not turn it into a good one. The empty table at the end shows the cost of ignoring patient advice.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"pomegranate", "souffle", "speed", "oven", "foam"}
    if world.get("hero").memes["patience"] >= THRESHOLD:
        tags.add("patience")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
good_fruit(F) :- fruit(F), fruit_good(F).
sensible(M) :- method(M), sense(M,S), sense_min(K), S >= K.
valid(H,F,M,Fin) :- hero(H), finish(Fin), good_fruit(F), sensible(M).

quick(M) :- method(M), speed(M,S), S >= 3.
rise(M)  :- method(M), gentle(M), steady(M), waits(M).

sad(Fin)   :- finish(Fin), not listens(Fin).
happy(Fin) :- finish(Fin), listens(Fin).

outcome(H,F,M,Fin,success) :- valid(H,F,M,Fin), rise(M), happy(Fin).
outcome(H,F,M,Fin,failure) :- valid(H,F,M,Fin), sad(Fin).
outcome(H,F,M,Fin,success) :- valid(H,F,M,Fin), not quick(M), happy(Fin).
outcome(H,F,M,Fin,failure) :- valid(H,F,M,Fin), quick(M), happy(Fin), not rise(M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hero_id in HEROES:
        lines.append(asp.fact("hero", hero_id))
    for fruit_id, fruit in FRUITS.items():
        lines.append(asp.fact("fruit", fruit_id))
        if fruit.good_for_souffle:
            lines.append(asp.fact("fruit_good", fruit_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("speed", method_id, method.speed))
        lines.append(asp.fact("sense", method_id, method.sense))
        if method.folds_gently:
            lines.append(asp.fact("gentle", method_id))
        if method.whips_steady:
            lines.append(asp.fact("steady", method_id))
        if method.waits_for_oven:
            lines.append(asp.fact("waits", method_id))
    for finish_id, finish in FINISHES.items():
        lines.append(asp.fact("finish", finish_id))
        if finish.listens:
            lines.append(asp.fact("listens", finish_id))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen", params.hero, params.fruit, params.method, params.finish),
            f"selected_outcome(O) :- chosen(H,F,M,Fin), outcome(H,F,M,Fin,O).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show selected_outcome/1."))
    atoms = asp.atoms(model, "selected_outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if params.hero not in HEROES or params.fruit not in FRUITS or params.method not in METHODS or params.finish not in FINISHES:
        raise StoryError("(Invalid params: unknown key.)")
    fruit = FRUITS[params.fruit]
    method = METHODS[params.method]
    finish = FINISHES[params.finish]
    if not valid_combo(HEROES[params.hero], fruit, method, finish):
        raise StoryError("(Invalid params: combination rejected by world logic.)")
    if not finish.listens:
        return "failure"
    if method.waits_for_oven and method.folds_gently and method.whips_steady:
        return "success"
    if method.speed < 3:
        return "success"
    return "failure"


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

    cases = list(CURATED)
    for seed in range(25):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            continue

    mismatches = 0
    for params in cases:
        py = outcome_of(params)
        asp_out = asp_outcome(params)
        if py != asp_out:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Empty story from smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - defensive
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: an eager child learns that speed cannot force a pomegranate soufflé to rise."
    )
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--fruit", choices=FRUITS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--finish", choices=FINISHES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fruit is not None and not FRUITS[args.fruit].good_for_souffle:
        raise StoryError(explain_fruit(FRUITS[args.fruit]))
    if args.method is not None and METHODS[args.method].sense < 2:
        raise StoryError(explain_method(METHODS[args.method]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.hero is None or combo[0] == args.hero)
        and (args.fruit is None or combo[1] == args.fruit)
        and (args.method is None or combo[2] == args.method)
        and (args.finish is None or combo[3] == args.finish)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hero, fruit, method, finish = rng.choice(sorted(combos))
    return StoryParams(hero=hero, fruit=fruit, method=method, finish=finish)


def generate(params: StoryParams) -> StorySample:
    if params.hero not in HEROES or params.fruit not in FRUITS or params.method not in METHODS or params.finish not in FINISHES:
        raise StoryError("(Invalid params: unknown key.)")
    hero = HEROES[params.hero]
    fruit = FRUITS[params.fruit]
    method = METHODS[params.method]
    finish = FINISHES[params.finish]
    if not valid_combo(hero, fruit, method, finish):
        if not fruit.good_for_souffle:
            raise StoryError(explain_fruit(fruit))
        raise StoryError(explain_method(method))
    world = tell(hero, fruit, method, finish)
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
        print(asp_program("", "#show valid/4.\n#show outcome/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hero, fruit, method, finish) combos:\n")
        for hero, fruit, method, finish in combos:
            print(f"  {hero:6} {fruit:12} {method:12} {finish}")
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
            header = f"### {p.hero}: {p.fruit} / {p.method} / {p.finish} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
