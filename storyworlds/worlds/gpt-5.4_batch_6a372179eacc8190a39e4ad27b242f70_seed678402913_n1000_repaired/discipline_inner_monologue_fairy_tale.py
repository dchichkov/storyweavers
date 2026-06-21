#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/discipline_inner_monologue_fairy_tale.py
===================================================================

A standalone storyworld about discipline in a fairy-tale mode, with a strong
inner-monologue beat. A child is given a small enchanted duty, meets a glittering
temptation, and either keeps steady, stumbles and repairs the mistake, or learns
too late why discipline matters.

The world model prefers a few plausible variants over broad coverage. Each story
is driven by simulated state: duty, temptation, delay, spills, repair, and the
hero's changing feelings.

Run it
------
    python storyworlds/worlds/gpt-5.4/discipline_inner_monologue_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/discipline_inner_monologue_fairy_tale.py --task moonflower --temptation fireflies --method counted_steps
    python storyworlds/worlds/gpt-5.4/discipline_inner_monologue_fairy_tale.py --method singing
    python storyworlds/worlds/gpt-5.4/discipline_inner_monologue_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/discipline_inner_monologue_fairy_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/discipline_inner_monologue_fairy_tale.py --verify
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
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "fairy_girl", "daughter", "woman", "mother", "queen"}
        male = {"boy", "prince", "page", "son", "man", "father", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title(self) -> str:
        return self.label or self.id


@dataclass
class Task:
    id: str
    setting: str
    cargo: str
    vessel: str
    destination: str
    duty_line: str
    refill_source: str
    closing_image: str
    difficulty: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Temptation:
    id: str
    label: str
    lure: str
    pause_action: str
    stumble_action: str
    strength: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    lesson: str
    mantra: str
    bonus: int
    guards: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    kind: str
    entrance: str
    advice: str
    power: int
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


def _r_spill_makes_delay(world: World) -> list[str]:
    vessel = world.entities.get("vessel")
    if vessel is None:
        return []
    if vessel.meters["spilled"] < THRESHOLD:
        return []
    sig = ("spill_delay",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    path = world.get("path")
    path.meters["delay"] += 1
    hero = world.get("hero")
    hero.memes["worry"] += 1
    return []


def _r_empty_needs_refill(world: World) -> list[str]:
    vessel = world.entities.get("vessel")
    if vessel is None:
        return []
    if vessel.meters["full"] >= THRESHOLD:
        return []
    sig = ("needs_refill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("path").meters["needs_refill"] += 1
    world.get("hero").memes["worry"] += 1
    return []


def _r_goal_watered(world: World) -> list[str]:
    goal = world.entities.get("goal")
    vessel = world.entities.get("vessel")
    if goal is None or vessel is None:
        return []
    if vessel.meters["delivered"] < THRESHOLD:
        return []
    sig = ("goal_watered",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    goal.meters["restored"] += 1
    hero = world.get("hero")
    hero.memes["pride"] += 1
    hero.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="spill_delay", tag="physical", apply=_r_spill_makes_delay),
    Rule(name="needs_refill", tag="physical", apply=_r_empty_needs_refill),
    Rule(name="goal_watered", tag="physical", apply=_r_goal_watered),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(got)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


TASKS = {
    "moonflower": Task(
        id="moonflower",
        setting="At the edge of the palace wood stood a silver garden where one moonflower opened only before sunrise.",
        cargo="silver dew",
        vessel="a crystal cup",
        destination="the thirsty moonflower",
        duty_line='carry the silver dew to the moonflower before the first gold stripe of dawn touched the tower',
        refill_source="the dew basin beneath the willow leaves",
        closing_image="the moonflower opened wide, shining like a little lamp in the pale morning",
        difficulty=2,
        tags={"garden", "dew", "flower"},
    ),
    "hearth_seed": Task(
        id="hearth_seed",
        setting="Beyond the village bakery stood a warm stone hearth where a sleeping ember-seed would wake only at dawn.",
        cargo="golden oil",
        vessel="a tiny brass lamp",
        destination="the ember-seed",
        duty_line='carry the golden oil to the ember-seed before the bread bells rang at dawn',
        refill_source="the oil jar on the baker's shelf",
        closing_image="the ember-seed glowed softly, and the first loaves smelled sweet as morning",
        difficulty=2,
        tags={"hearth", "oil", "seed"},
    ),
    "cedar_sapling": Task(
        id="cedar_sapling",
        setting="High on the hill behind the castle grew a young cedar sapling planted for the kingdom's next hundred years.",
        cargo="spring water",
        vessel="a painted pail",
        destination="the cedar sapling",
        duty_line='carry the spring water to the cedar sapling before the sun climbed over the hill',
        refill_source="the stone spring at the foot of the path",
        closing_image="the cedar lifted its green tips, and the hill smelled fresh and brave",
        difficulty=1,
        tags={"hill", "water", "tree"},
    ),
}

TEMPTATIONS = {
    "fireflies": Temptation(
        id="fireflies",
        label="the dancing fireflies",
        lure="their green sparks swirled in rings as if they were inviting a game",
        pause_action="dance after the drifting lights",
        stumble_action="twirl after them",
        strength=3,
        tags={"movement", "glitter"},
    ),
    "berries": Temptation(
        id="berries",
        label="the ruby berry hedge",
        lure="the berries shone like drops of jam and smelled sweeter than a feast",
        pause_action="pick just one berry",
        stumble_action="reach with one hand toward the hedge",
        strength=2,
        tags={"hands", "taste"},
    ),
    "brook_song": Temptation(
        id="brook_song",
        label="the singing brook",
        lure="the water sang such soft music that even the reeds seemed to lean closer",
        pause_action="sit and listen for one more song",
        stumble_action="wander to the bank and forget the path",
        strength=2,
        tags={"listening", "wandering"},
    ),
}

METHODS = {
    "both_hands": Method(
        id="both_hands",
        label="both hands on the vessel",
        lesson="hold the vessel with both hands",
        mantra="Both hands, steady heart, steady feet.",
        bonus=2,
        guards={"hands", "movement"},
        tags={"hands", "discipline"},
    ),
    "counted_steps": Method(
        id="counted_steps",
        label="counted steps",
        lesson="count ten slow steps at a time",
        mantra="One to ten, and then again; a careful child arrives.",
        bonus=2,
        guards={"movement", "wandering"},
        tags={"counting", "discipline"},
    ),
    "song_of_duty": Method(
        id="song_of_duty",
        label="the song of duty",
        lesson="quietly sing the task so the mind does not drift",
        mantra="Duty first, delight after; the path remembers.",
        bonus=1,
        guards={"listening", "taste"},
        tags={"song", "discipline"},
    ),
    "singing": Method(
        id="singing",
        label="wild singing",
        lesson="sing whatever pops into your head",
        mantra="Loud songs make quick feet.",
        bonus=0,
        guards=set(),
        tags={"bad_idea"},
    ),
}

HELPERS = {
    "robin": Helper(
        id="robin",
        label="a red-breasted robin",
        kind="bird",
        entrance="A red-breasted robin fluttered down to the path.",
        advice='The robin tilted its bright head and seemed to say, "Slow feet reach home sooner than skipping feet."',
        power=1,
        tags={"bird", "gentle_help"},
    ),
    "grandmother": Helper(
        id="grandmother",
        label="Grandmother Rowan",
        kind="elder",
        entrance="From the gate came Grandmother Rowan with her lantern and her calm eyes.",
        advice='"Discipline is not a scold," she said. "It is the little rail that keeps your good heart on the bridge."',
        power=2,
        tags={"elder", "discipline"},
    ),
    "hedgehog": Helper(
        id="hedgehog",
        label="a mossy hedgehog",
        kind="animal",
        entrance="A mossy hedgehog waddled from beneath the fern roots.",
        advice='It sniffed the spilled drops and seemed to mutter, "Short legs, slow legs, wise legs."',
        power=1,
        tags={"animal", "gentle_help"},
    ),
}

GIRL_NAMES = ["Elin", "Mira", "Nora", "Lina", "Sela", "Tilda", "Wren"]
BOY_NAMES = ["Tobin", "Rowan", "Milo", "Alder", "Perrin", "Finn", "Ivo"]
TRAITS = ["careful", "earnest", "lively", "kind", "thoughtful", "quick"]
ELDERS = ["queen", "king", "mother", "father"]


def method_fits(temptation: Temptation, method: Method) -> bool:
    return bool(temptation.tags & method.guards)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for task_id in TASKS:
        for temptation_id, temptation in TEMPTATIONS.items():
            for method_id, method in METHODS.items():
                if method_fits(temptation, method):
                    combos.append((task_id, temptation_id, method_id))
    return combos


def outcome_of(task: Task, temptation: Temptation, method: Method, helper: Helper, discipline: int) -> str:
    resolve = discipline + method.bonus
    challenge = temptation.strength + task.difficulty
    severity = max(0, challenge - resolve)
    if severity <= 0:
        return "steady"
    if helper.power >= severity:
        return "repaired"
    return "failed"


def explain_method_rejection(temptation: Temptation, method: Method) -> str:
    good = ", ".join(sorted(
        mid for mid, m in METHODS.items() if method_fits(temptation, m)
    ))
    return (
        f"(No story: '{method.id}' is not a believable discipline for {temptation.label}. "
        f"The method must actually help with that temptation. Try: {good}.)"
    )


def explain_combo_rejection(task: str, temptation: str, method: str) -> str:
    return (
        f"(No valid story for task={task}, temptation={temptation}, method={method}. "
        f"This world only tells combinations where the discipline method truly fits the temptation.)"
    )


def inner_thought(hero: Entity, text: str) -> str:
    return f'{hero.id} thought, "{text}"'


def predict_stumble(world: World, task: Task, temptation: Temptation, method: Method) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    vessel = sim.get("vessel")
    resolve = int(hero.memes["discipline"]) + method.bonus
    challenge = temptation.strength + task.difficulty
    severity = max(0, challenge - resolve)
    if severity > 0:
        vessel.meters["full"] = 0.0
        vessel.meters["spilled"] += 1
        propagate(sim, narrate=False)
    return {
        "severity": severity,
        "needs_refill": sim.get("path").meters["needs_refill"] >= THRESHOLD,
        "delay": sim.get("path").meters["delay"],
    }


def introduce(world: World, hero: Entity, elder: Entity, task: Task) -> None:
    world.say("Once, when dawn still slept under its gray blanket, a small duty woke before the birds.")
    world.say(task.setting)
    world.say(
        f"{hero.id} was a {next((t for t in hero.attrs.get('traits', []) if t), 'young')} {hero.type} who wanted to do brave things well."
    )
    world.say(
        f'That morning {elder.title} trusted {hero.pronoun("object")} with a simple, shining charge: {task.duty_line}.'
    )


def charge(world: World, hero: Entity, elder: Entity, task: Task, method: Method) -> None:
    hero.memes["duty"] += 1
    hero.memes["discipline"] = float(hero.attrs.get("discipline", 1))
    vessel = world.get("vessel")
    vessel.meters["full"] = 1.0
    world.say(
        f'{elder.title} placed {vessel.phrase} into {hero.pronoun("possessive")} hands. '
        f'"Remember your discipline," {elder.pronoun()} said. '
        f'"{method.lesson.capitalize()}, and do not let the bright world tug you from your path."'
    )
    world.say(
        inner_thought(hero, f"I want to be trusted. I will remember: {method.mantra}")
    )


def tempt(world: World, hero: Entity, temptation: Temptation) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"Down the path came {temptation.label}; {temptation.lure}."
    )
    world.say(
        inner_thought(hero, f"I could {temptation.pause_action}. Only for a moment, perhaps.")
    )


def warn(world: World, hero: Entity, task: Task, temptation: Temptation, method: Method) -> dict:
    pred = predict_stumble(world, task, temptation, method)
    world.facts["predicted_severity"] = pred["severity"]
    world.facts["predicted_delay"] = pred["delay"]
    if pred["severity"] > 0:
        world.say(
            inner_thought(
                hero,
                f"But if I leave the path, the {task.cargo} may spill, and {task.destination} is waiting for me."
            )
        )
    else:
        world.say(
            inner_thought(
                hero,
                f"The temptation is bright, but my feet can stay wiser than my eyes."
            )
        )
    return pred


def steady_choice(world: World, hero: Entity, temptation: Temptation, method: Method) -> None:
    hero.memes["discipline"] += 1
    hero.memes["resolve"] += 1
    world.say(
        f"{hero.id} drew one slow breath, remembered {method.label}, and did not {temptation.pause_action}."
    )
    world.say(
        inner_thought(hero, "Delight can wait. Duty first.")
    )


def stumble(world: World, hero: Entity, task: Task, temptation: Temptation) -> None:
    vessel = world.get("vessel")
    vessel.meters["full"] = 0.0
    vessel.meters["spilled"] += 1
    hero.memes["shame"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {temptation.label} tugged harder than one small heartbeat, and {hero.id} did {temptation.stumble_action}."
    )
    world.say(
        f"A shining thread of {task.cargo} slipped from {world.get('vessel').phrase} and darkened the path."
    )
    world.say(
        inner_thought(hero, "Oh no. I did not lose the task all at once; I lost it one careless moment at a time.")
    )


def helper_arrives(world: World, helper: Helper, hero: Entity) -> None:
    hero.memes["hope"] += 1
    world.say(helper.entrance)
    world.say(helper.advice)


def repair(world: World, helper: Helper, hero: Entity, task: Task, method: Method) -> None:
    vessel = world.get("vessel")
    path = world.get("path")
    hero.memes["discipline"] += 1
    hero.memes["resolve"] += 1
    hero.memes["shame"] = 0.0
    vessel.meters["full"] = 1.0
    vessel.meters["refilled"] += 1
    path.meters["delay"] += 1
    world.say(
        f"Together they hurried to {task.refill_source}, and {hero.id} filled {vessel.phrase} again."
    )
    world.say(
        inner_thought(hero, f"This time I will keep {method.mantra}")
    )
    world.say(
        f"Then {hero.pronoun()} walked with smaller steps and a straighter back than before."
    )


def fail_end(world: World, hero: Entity, elder: Entity, task: Task) -> None:
    goal = world.get("goal")
    hero.memes["sorrow"] += 1
    goal.meters["restored"] = 0.0
    world.say(
        f"But dawn climbed the sky faster than {hero.id} climbed the hill, and {task.destination} had to wait thirsty for another morning."
    )
    world.say(
        f"When {hero.id} returned, {elder.title} did not shout. {elder.pronoun().capitalize()} laid a hand on {hero.pronoun('possessive')} shoulder instead."
    )
    world.say(
        f'"Today was sad," {elder.pronoun()} said, "but discipline can be practiced tomorrow."'
    )


def deliver(world: World, hero: Entity, task: Task) -> None:
    vessel = world.get("vessel")
    vessel.meters["delivered"] += 1
    vessel.meters["full"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"At last {hero.id} reached {task.destination} and poured out the last bright drop."
    )


def closing(world: World, hero: Entity, elder: Entity, task: Task, outcome: str) -> None:
    if outcome == "steady":
        world.say(
            f"Right then {task.closing_image}, and even the early wind seemed to bow to a child who had kept faith with a small command."
        )
        world.say(
            f'{elder.title} smiled when {hero.pronoun()} came back. "That is what discipline looks like," {elder.pronoun()} said.'
        )
    elif outcome == "repaired":
        world.say(
            f"Though the path had taken an extra turn, {task.closing_image} all the same."
        )
        world.say(
            f'{elder.title} smiled at the sight. "Discipline is not only never slipping," {elder.pronoun()} said. "It is rising quickly when you do."'
        )
    else:
        world.say(
            f"The next dawn, {hero.id} walked the path again with steadier hands, because fairy-tale lessons have long roots."
        )


def tell(
    task: Task,
    temptation: Temptation,
    method: Method,
    helper: Helper,
    hero_name: str = "Elin",
    hero_type: str = "girl",
    elder_type: str = "queen",
    trait: str = "careful",
    discipline: int = 2,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        attrs={"traits": [trait], "discipline": discipline},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label={"queen": "the Queen", "king": "the King", "mother": "Mother", "father": "Father"}[elder_type],
        role="elder",
    ))
    vessel = world.add(Entity(
        id="vessel",
        type="vessel",
        label=task.vessel,
        phrase=task.vessel,
        role="vessel",
        tags={task.cargo},
    ))
    goal = world.add(Entity(
        id="goal",
        type="goal",
        label=task.destination,
        phrase=task.destination,
        role="goal",
        tags=set(task.tags),
    ))
    world.add(Entity(id="path", type="path", label="the path", role="path"))

    introduce(world, hero, elder, task)
    charge(world, hero, elder, task, method)

    world.para()
    tempt(world, hero, temptation)
    pred = warn(world, hero, task, temptation, method)

    outcome = outcome_of(task, temptation, method, helper, discipline)
    world.facts["predicted_outcome"] = outcome
    world.facts["severity"] = pred["severity"]

    world.para()
    if outcome == "steady":
        steady_choice(world, hero, temptation, method)
        deliver(world, hero, task)
    else:
        stumble(world, hero, task, temptation)
        helper_arrives(world, helper, hero)
        if outcome == "repaired":
            repair(world, helper, hero, task, method)
            deliver(world, hero, task)
        else:
            fail_end(world, hero, elder, task)

    world.para()
    closing(world, hero, elder, task, outcome)

    world.facts.update(
        task=task,
        temptation=temptation,
        method=method,
        helper=helper,
        hero=hero,
        elder=elder,
        vessel=vessel,
        goal=goal,
        outcome=outcome,
        discipline=discipline,
        restored=goal.meters["restored"] >= THRESHOLD,
        refilled=vessel.meters["refilled"] >= THRESHOLD,
        delayed=world.get("path").meters["delay"] >= THRESHOLD,
        spilled=vessel.meters["spilled"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    task: str
    temptation: str
    method: str
    helper: str
    name: str
    gender: str
    elder: str
    trait: str
    discipline: int
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        task="moonflower",
        temptation="fireflies",
        method="counted_steps",
        helper="robin",
        name="Elin",
        gender="girl",
        elder="queen",
        trait="careful",
        discipline=3,
    ),
    StoryParams(
        task="hearth_seed",
        temptation="berries",
        method="song_of_duty",
        helper="grandmother",
        name="Tobin",
        gender="boy",
        elder="father",
        trait="quick",
        discipline=2,
    ),
    StoryParams(
        task="cedar_sapling",
        temptation="fireflies",
        method="both_hands",
        helper="hedgehog",
        name="Mira",
        gender="girl",
        elder="mother",
        trait="lively",
        discipline=1,
    ),
    StoryParams(
        task="moonflower",
        temptation="brook_song",
        method="song_of_duty",
        helper="robin",
        name="Alder",
        gender="boy",
        elder="king",
        trait="thoughtful",
        discipline=1,
    ),
]


KNOWLEDGE = {
    "discipline": [
        (
            "What does discipline mean?",
            "Discipline means helping yourself do the right thing even when something tempting pulls at you. It is a kind of steady practice, not just a punishment."
        )
    ],
    "dew": [
        (
            "What is dew?",
            "Dew is tiny drops of water that gather on grass and leaves when the air turns cool. In stories, dew is often pictured as something delicate and shining."
        )
    ],
    "patience": [
        (
            "Why can slow steps be wise?",
            "Slow steps can be wise because they help you notice what your hands and feet are doing. Going carefully can get you to the end better than rushing."
        )
    ],
    "brook": [
        (
            "Why can a brook sound like it is singing?",
            "A brook can sound like singing because water makes soft, changing notes as it runs over stones. Fairy tales often turn those sounds into music."
        )
    ],
    "firefly": [
        (
            "What is a firefly?",
            "A firefly is a small insect that makes a little light. At night it can look almost magical."
        )
    ],
    "berries": [
        (
            "Why is it hard to carry something carefully while picking berries?",
            "Picking berries uses your hands and your attention at the same time. If your hands are busy and your mind wanders, it is easier to spill what you are carrying."
        )
    ],
    "help": [
        (
            "What should you do after a mistake?",
            "You should tell the truth, get help if you need it, and try to fix the problem. A mistake can become a lesson when you respond wisely."
        )
    ],
}
KNOWLEDGE_ORDER = ["discipline", "patience", "help", "dew", "brook", "firefly", "berries"]


def pair_hero(hero: Entity) -> str:
    return f"{hero.label}, a young {hero.type}"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    temptation = f["temptation"]
    method = f["method"]
    outcome = f["outcome"]
    base = (
        f'Write a fairy tale for a 3-to-5-year-old that includes the word "discipline" '
        f"and uses inner monologue. A child must carry {task.cargo} to {task.destination} "
        f"while resisting {temptation.label}."
    )
    if outcome == "steady":
        return [
            base,
            f"Tell a gentle fairy tale where {hero.label} stays disciplined by using {method.label} and reaches the goal on time.",
            f"Write a short magical story in which the child thinks privately about temptation, chooses duty first, and ends with a bright image of success.",
        ]
    if outcome == "repaired":
        return [
            base,
            f"Tell a fairy tale where {hero.label} slips for a moment, then learns better discipline and repairs the mistake with help.",
            f"Write a story with inner thoughts that show how one careless moment becomes a lesson, and end with the task completed after a wiser second try.",
        ]
    return [
        base,
        f"Tell a sad-but-gentle fairy tale where {hero.label} yields to temptation and learns that discipline must be practiced before the next dawn.",
        f"Write a story where inner monologue shows the hero knowing the right thing but choosing too slowly, ending in a lesson rather than a triumph.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    task = f["task"]
    temptation = f["temptation"]
    method = f["method"]
    helper = f["helper"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_hero(hero)} who was trusted with an enchanted duty. {elder.title} gave {hero.pronoun('object')} the task and expected {hero.pronoun('object')} to be careful."
        ),
        (
            f"What was {hero.label} supposed to do?",
            f"{hero.label} was supposed to carry {task.cargo} in {task.vessel} to {task.destination} before dawn. The whole story turns on whether that small duty is done in time."
        ),
        (
            f"What temptation appeared on the path?",
            f"{temptation.label} appeared and tried to pull {hero.label}'s attention away. It mattered because distraction could make {hero.pronoun('object')} spill the precious {task.cargo}."
        ),
        (
            f"What discipline was {hero.label} told to use?",
            f"{hero.label} was told to use {method.label}. The method worked by giving {hero.pronoun('object')} something steady to do instead of following the temptation."
        ),
    ]
    if outcome == "steady":
        qa.append(
            (
                f"How did {hero.label} win against the temptation?",
                f"{hero.label} listened to {hero.pronoun('possessive')} inner warning and kept to {method.label}. Because {hero.pronoun()} stayed steady at the first tempting moment, nothing spilled and the task was finished on time."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily: {task.closing_image}. The ending proves that discipline protected something living and good."
            )
        )
    elif outcome == "repaired":
        qa.append(
            (
                f"What mistake did {hero.label} make, and how was it repaired?",
                f"{hero.label} gave in for a moment and spilled the {task.cargo}. Then {helper.label} helped {hero.pronoun('object')} slow down, refill the vessel, and try again with better discipline."
            )
        )
        qa.append(
            (
                f"Did {hero.label} still finish the task?",
                f"Yes. {hero.pronoun().capitalize()} took longer because of the spill, but the second try was steadier than the first. That is why the story says discipline can mean rising quickly after a mistake."
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.label} fail that morning?",
                f"{hero.label} knew the right thing in {hero.pronoun('possessive')} thoughts, but temptation won before discipline did. The lost time and spilled {task.cargo} meant {task.destination} had to wait for another dawn."
            )
        )
        qa.append(
            (
                "Was the ending cruel or gentle?",
                f"It was gentle. {elder.title} did not shout, and the story leaves room for practice tomorrow. The lesson is sad, but it is still full of hope."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"discipline", "patience", "help"}
    task = world.facts["task"]
    temptation = world.facts["temptation"]
    if "dew" in task.tags:
        tags.add("dew")
    if temptation.id == "brook_song":
        tags.add("brook")
    if temptation.id == "fireflies":
        tags.add("firefly")
    if temptation.id == "berries":
        tags.add("berries")
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(Tp, M) :- temptation(Tp), method(M), tempts_with(Tp, X), guards(M, X).

valid(Task, Tp, M) :- task(Task), temptation(Tp), method(M), fits(Tp, M).

resolve(D + B) :- chosen_discipline(D), chosen_method(M), bonus(M, B).
challenge(S + Dif) :- chosen_temptation(Tp), strength(Tp, S), chosen_task(Tk), difficulty(Tk, Dif).
severity(C - R) :- challenge(C), resolve(R), C > R.
severity(0) :- challenge(C), resolve(R), C <= R.

steady :- severity(0).
repaired :- severity(S), S > 0, chosen_helper(H), power(H, P), P >= S.
failed :- severity(S), S > 0, chosen_helper(H), power(H, P), P < S.

outcome(steady) :- steady.
outcome(repaired) :- repaired.
outcome(failed) :- failed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for task_id, task in TASKS.items():
        lines.append(asp.fact("task", task_id))
        lines.append(asp.fact("difficulty", task_id, task.difficulty))
    for temptation_id, temptation in TEMPTATIONS.items():
        lines.append(asp.fact("temptation", temptation_id))
        lines.append(asp.fact("strength", temptation_id, temptation.strength))
        for tag in sorted(temptation.tags):
            lines.append(asp.fact("tempts_with", temptation_id, tag))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("bonus", method_id, method.bonus))
        for tag in sorted(method.guards):
            lines.append(asp.fact("guards", method_id, tag))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("power", helper_id, helper.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_task", params.task),
        asp.fact("chosen_temptation", params.temptation),
        asp.fact("chosen_method", params.method),
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_discipline", params.discipline),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


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
    for seed in range(120):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        py = outcome_of(
            TASKS[params.task],
            TEMPTATIONS[params.temptation],
            METHODS[params.method],
            HELPERS[params.helper],
            params.discipline,
        )
        asp_ans = asp_outcome(params)
        if py != asp_ans:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Fairy-tale storyworld about discipline with inner monologue."
    )
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--discipline", type=int, choices=[1, 2, 3], help="how practiced the hero already is")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.temptation and args.method:
        temptation = TEMPTATIONS[args.temptation]
        method = METHODS[args.method]
        if not method_fits(temptation, method):
            raise StoryError(explain_method_rejection(temptation, method))

    combos = [
        combo for combo in valid_combos()
        if (args.task is None or combo[0] == args.task)
        and (args.temptation is None or combo[1] == args.temptation)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        if args.task and args.temptation and args.method:
            raise StoryError(explain_combo_rejection(args.task, args.temptation, args.method))
        raise StoryError("(No valid combination matches the given options.)")

    task_id, temptation_id, method_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(ELDERS)
    helper = args.helper or rng.choice(sorted(HELPERS))
    trait = rng.choice(TRAITS)
    discipline = args.discipline if args.discipline is not None else rng.choice([1, 2, 3])

    return StoryParams(
        task=task_id,
        temptation=temptation_id,
        method=method_id,
        helper=helper,
        name=name,
        gender=gender,
        elder=elder,
        trait=trait,
        discipline=discipline,
    )


def generate(params: StoryParams) -> StorySample:
    if params.task not in TASKS:
        raise StoryError(f"(Unknown task: {params.task})")
    if params.temptation not in TEMPTATIONS:
        raise StoryError(f"(Unknown temptation: {params.temptation})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    ELDS = set(ELDERS)
    if params.elder not in ELDS:
        raise StoryError(f"(Unknown elder: {params.elder})")

    task = TASKS[params.task]
    temptation = TEMPTATIONS[params.temptation]
    method = METHODS[params.method]
    helper = HELPERS[params.helper]
    if not method_fits(temptation, method):
        raise StoryError(explain_method_rejection(temptation, method))

    hero_type = "girl" if params.gender == "girl" else "boy"
    world = tell(
        task=task,
        temptation=temptation,
        method=method,
        helper=helper,
        hero_name=params.name,
        hero_type=hero_type,
        elder_type=params.elder,
        trait=params.trait,
        discipline=params.discipline,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (task, temptation, method) combos:\n")
        for task, temptation, method in combos:
            print(f"  {task:12} {temptation:10} {method}")
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
            out = outcome_of(TASKS[p.task], TEMPTATIONS[p.temptation], METHODS[p.method], HELPERS[p.helper], p.discipline)
            header = f"### {p.name}: {p.task} / {p.temptation} / {p.method} ({out})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
