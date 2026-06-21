#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hearth_inner_monologue_sound_effects_problem_solving.py
==================================================================================

A small folk-tale-flavored story world about a child, a cottage hearth, and a
problem that must be solved with calm thinking. The stories are driven by
simulated state: the hearth weakens or smokes, the child notices physical signs,
thinks the problem through, tries a sensible fix, and either solves it alone or
wisely fetches an elder to help.

Features from the seed:
- hearth
- inner monologue
- sound effects
- problem solving
- folk-tale style

Run it
------
    python storyworlds/worlds/gpt-5.4/hearth_inner_monologue_sound_effects_problem_solving.py
    python storyworlds/worlds/gpt-5.4/hearth_inner_monologue_sound_effects_problem_solving.py --weather rain --problem wet_wood
    python storyworlds/worlds/gpt-5.4/hearth_inner_monologue_sound_effects_problem_solving.py --method splash_water
    python storyworlds/worlds/gpt-5.4/hearth_inner_monologue_sound_effects_problem_solving.py --all
    python storyworlds/worlds/gpt-5.4/hearth_inner_monologue_sound_effects_problem_solving.py --qa --json
    python storyworlds/worlds/gpt-5.4/hearth_inner_monologue_sound_effects_problem_solving.py --verify
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)


@dataclass
class Weather:
    id: str
    open_text: str
    sound: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    symptom: str
    sound: str
    thought: str
    need: str
    severity: int
    adult_needed: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    sense: int
    fixes: set[str] = field(default_factory=set)
    action_text: str = ""
    result_text: str = ""
    qa_text: str = ""
    sound: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    want_text: str
    ending_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    weather: str
    problem: str
    method: str
    goal: str
    hero: str
    gender: str
    elder: str
    trait: str
    companion: str = ""
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        out = World()
        out.entities = copy.deepcopy(self.entities)
        out.paragraphs = [[]]
        out.fired = set(self.fired)
        out.facts = copy.deepcopy(self.facts)
        return out


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_room_reacts(world: World) -> list[str]:
    hearth = world.get("hearth")
    room = world.get("room")
    hero = world.get("hero")
    out: list[str] = []
    if hearth.meters["smoke"] >= THRESHOLD:
        sig = ("smoke",)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["smoky"] += 1
            hero.memes["worry"] += 1
            out.append("The little room grew dim, and the smoke stung the eyes.")
    if hearth.meters["warmth"] < THRESHOLD:
        sig = ("cold",)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["cold"] += 1
            hero.memes["worry"] += 1
            out.append("The air around the hearth felt thinner and colder than before.")
    return out


def _r_solution_comfort(world: World) -> list[str]:
    hearth = world.get("hearth")
    room = world.get("room")
    hero = world.get("hero")
    sig = ("comfort",)
    if hearth.meters["warmth"] >= 2 and hearth.meters["smoke"] <= 0 and sig not in world.fired:
        world.fired.add(sig)
        room.meters["cozy"] += 1
        hero.memes["relief"] += 1
        hero.memes["pride"] += 1
        return ["Soon the room felt close and golden again."]
    return []


CAUSAL_RULES = [
    Rule(name="room_reacts", tag="physical", apply=_r_room_reacts),
    Rule(name="solution_comfort", tag="physical", apply=_r_solution_comfort),
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
        for s in produced:
            world.say(s)
    return produced


WEATHERS = {
    "snow": Weather(
        id="snow",
        open_text="Snow lay over the fields like flour on a baker's board.",
        sound="Outside went hush-hush under the snow.",
        affords={"low_embers", "blocked_flue"},
        tags={"snow", "winter"},
    ),
    "wind": Weather(
        id="wind",
        open_text="The wind ran around the cottage and tugged at every crack.",
        sound="Whooo, sang the wind under the eaves.",
        affords={"low_embers", "blocked_flue"},
        tags={"wind"},
    ),
    "rain": Weather(
        id="rain",
        open_text="Rain tapped on the roof and silvered the yard beyond the door.",
        sound="Tap-tap, tap-tap, sang the rain.",
        affords={"wet_wood", "low_embers"},
        tags={"rain"},
    ),
}

PROBLEMS = {
    "low_embers": Problem(
        id="low_embers",
        label="sleepy embers",
        symptom="Only a few red eyes glowed beneath the ash.",
        sound="Crk... crk... went the faint little coals.",
        thought="If the fire falls asleep now, the cottage will lose its warm heart.",
        need="air",
        severity=1,
        adult_needed=False,
        tags={"embers", "hearth"},
    ),
    "wet_wood": Problem(
        id="wet_wood",
        label="wet wood",
        symptom="The new sticks only smoked and would not catch well.",
        sound="Hissss, sighed the damp wood.",
        thought="Wet wood drinks the fire instead of feeding it.",
        need="dry_fuel",
        severity=2,
        adult_needed=False,
        tags={"wood", "smoke", "hearth"},
    ),
    "blocked_flue": Problem(
        id="blocked_flue",
        label="a blocked chimney throat",
        symptom="The smoke curled back down instead of climbing out.",
        sound="Puff-puff, coughed the hearth into the room.",
        thought="Something is stopping the smoke on its way upward.",
        need="clear_flue",
        severity=3,
        adult_needed=True,
        tags={"chimney", "smoke", "hearth"},
    ),
}

METHODS = {
    "bellows": Method(
        id="bellows",
        label="bellows",
        phrase="the old bellows hanging by the hearth",
        sense=3,
        fixes={"air"},
        action_text="gave the embers a few patient breaths with the bellows",
        result_text="The coals woke with a red blink, and small flames licked up between the sticks.",
        qa_text="used the bellows to feed the embers a little air",
        sound="Puff, puff!",
        tags={"bellows", "air"},
    ),
    "dry_tinder": Method(
        id="dry_tinder",
        label="dry tinder",
        phrase="a bundle of dry birch curls from the shelf",
        sense=3,
        fixes={"dry_fuel"},
        action_text="slid dry birch curls under the smoking sticks and laid the damp wood aside",
        result_text="The curls caught at once, and the stronger little flame taught the bigger wood how to burn.",
        qa_text="used dry tinder and moved the wet wood aside until the fire was lively again",
        sound="Fffft-lick!",
        tags={"tinder", "wood"},
    ),
    "hearth_brush": Method(
        id="hearth_brush",
        label="hearth brush",
        phrase="the long hearth brush kept near the door",
        sense=3,
        fixes={"clear_flue"},
        action_text="pointed to the hearth brush and the dark chimney mouth",
        result_text="When the passage was cleared, the smoke flew upward the way smoke should.",
        qa_text="helped clear the chimney throat with the hearth brush",
        sound="Scrr-scrr!",
        tags={"brush", "chimney"},
    ),
    "splash_water": Method(
        id="splash_water",
        label="bucket of water",
        phrase="a bucket of water",
        sense=1,
        fixes=set(),
        action_text="splashed water into the hearth",
        result_text="The fire would only die and leave the room colder.",
        qa_text="threw water into the hearth",
        sound="Splash!",
        tags={"water"},
    ),
}

GOALS = {
    "soup": Goal(
        id="soup",
        want_text="A black pot of soup was meant to sing there before sunset.",
        ending_text="Soon the soup pot began to hum, and the whole cottage smelled of onions and thyme.",
        tags={"soup"},
    ),
    "mittens": Goal(
        id="mittens",
        want_text="A pair of wool mittens waited on a stool to be dried by the blaze.",
        ending_text="Soon the mittens steamed softly, and warm wool smell drifted through the cottage.",
        tags={"mittens"},
    ),
    "traveler": Goal(
        id="traveler",
        want_text="Before long, an old traveler was expected on the road and would need a warm place to sit.",
        ending_text="Soon the bench by the hearth shone golden, ready for a road-tired guest.",
        tags={"traveler"},
    ),
}

GIRL_NAMES = ["Mara", "Tessa", "Nella", "Elsa", "Anya", "Iris", "Mira", "Sela"]
BOY_NAMES = ["Tobin", "Milo", "Perrin", "Rowan", "Ivo", "Jon", "Alder", "Sime"]
TRAITS = ["patient", "careful", "steady", "thoughtful", "quick", "practical"]
COMPANIONS = ["the cat", "the little dog", "the brown hen", ""]


def method_matches(problem: Problem, method: Method) -> bool:
    return problem.need in method.fixes


def weather_supports(weather: Weather, problem: Problem) -> bool:
    return problem.id in weather.affords


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for weather_id, weather in WEATHERS.items():
        for problem_id, problem in PROBLEMS.items():
            if not weather_supports(weather, problem):
                continue
            for method_id, method in METHODS.items():
                if method.sense >= SENSE_MIN and method_matches(problem, method):
                    combos.append((weather_id, problem_id, method_id))
    return combos


def explain_rejection(weather: Weather, problem: Problem) -> str:
    if not weather_supports(weather, problem):
        return (
            f"(No story: {weather.id} weather does not naturally set up {problem.label}. "
            f"Choose a problem that fits the day.)"
        )
    return "(No story: this setup is not reasonable.)"


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in METHODS.values() if m.sense >= SENSE_MIN))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    problem = PROBLEMS[params.problem]
    return "helped" if problem.adult_needed else "solo"


def predict_problem(world: World, problem: Problem) -> dict:
    sim = world.copy()
    apply_problem(sim, problem, narrate=False)
    return {
        "smoke": sim.get("hearth").meters["smoke"],
        "warmth": sim.get("hearth").meters["warmth"],
        "cold": sim.get("room").meters["cold"],
    }


def apply_problem(world: World, problem: Problem, narrate: bool = True) -> None:
    hearth = world.get("hearth")
    hearth.meters["warmth"] = max(0.0, hearth.meters["warmth"] - float(problem.severity))
    if problem.id in {"wet_wood", "blocked_flue"}:
        hearth.meters["smoke"] += 1
    propagate(world, narrate=narrate)


def use_method(world: World, method: Method, problem: Problem, by_elder: bool = False) -> None:
    hearth = world.get("hearth")
    actor = world.get("elder") if by_elder else world.get("hero")
    actor.memes["focus"] += 1
    world.say(f'{method.sound} {actor.id} {method.action_text}.')
    if problem.need == "air":
        hearth.meters["warmth"] += 2
    elif problem.need == "dry_fuel":
        hearth.meters["smoke"] = max(0.0, hearth.meters["smoke"] - 1)
        hearth.meters["warmth"] += 2
    elif problem.need == "clear_flue":
        hearth.meters["smoke"] = max(0.0, hearth.meters["smoke"] - 1)
        hearth.meters["warmth"] += 2
    propagate(world, narrate=False)
    world.say(method.result_text)


def opening(world: World, weather: Weather, goal: Goal, hero: Entity, companion: str) -> None:
    world.say(
        f"Once, in a little cottage with a stone hearth, {hero.id} kept watch while the day drew thin. "
        f"{weather.open_text} {weather.sound}"
    )
    world.say(goal.want_text)
    if companion:
        world.say(f"At {hero.pronoun('possessive')} feet curled {companion}, listening to the house sounds.")


def notice_problem(world: World, problem: Problem, hero: Entity) -> None:
    hero.memes["duty"] += 1
    world.say(problem.symptom)
    world.say(problem.sound)
    world.say(f'"{problem.thought}" {hero.id} thought.')


def ask_for_goal(world: World, hero: Entity, goal: Goal) -> None:
    world.say(
        f'{hero.id} looked at the hearth and thought, "If I am wise now, the house will keep its promise."'
    )
    if goal.id == "traveler":
        world.say("The child listened toward the road, thinking of tired boots and cold hands.")
    elif goal.id == "soup":
        world.say("The empty pot seemed to wait for its warm singing.")
    else:
        world.say("The mittens seemed to wait for a kinder fire.")


def inner_plan(world: World, problem: Problem, method: Method, hero: Entity) -> None:
    if problem.need == "air":
        plan = f'"It does not need scolding," {hero.id} thought. "It needs a little air, and {method.phrase} can give it that."'
    elif problem.need == "dry_fuel":
        plan = f'"The fire is not greedy," {hero.id} thought. "It only needs drier food, and I know where to find some."'
    else:
        plan = f'"This is a taller trouble," {hero.id} thought. "I can name it, and then I can fetch the right help."'
    world.say(plan)


def fetch_elder(world: World, elder: Entity, hero: Entity, companion: str) -> None:
    hero.memes["wisdom"] += 1
    elder.memes["care"] += 1
    world.say(
        f'{hero.id} did not pretend to be bigger than the trouble. {hero.pronoun().capitalize()} went to call {elder.label_word}, '
        f'and quick steps came back across the floorboards.'
    )
    if companion:
        world.say(f"{companion.capitalize()} padded after them as if it too wanted the smoke sent away.")


def elder_guides(world: World, elder: Entity, hero: Entity, method: Method) -> None:
    world.say(
        f'{elder.label_word.capitalize()} knelt beside the hearth and nodded. '
        f'"You saw the true problem," {elder.pronoun()} said. "Now we mend it the safe way."'
    )
    world.say(
        f'{hero.id} held {method.phrase} ready while {elder.label_word} showed where the hand should go and where it should never go.'
    )


def closing(world: World, goal: Goal, hero: Entity, elder: Entity, outcome: str, companion: str) -> None:
    hero.memes["joy"] += 1
    world.say(goal.ending_text)
    if outcome == "helped":
        world.say(
            f'{elder.label_word.capitalize()} smiled at {hero.id}. "A wise child is not the one who knows everything," '
            f'{elder.pronoun()} said. "A wise child is the one who knows when to ask."'
        )
    else:
        world.say(
            f'{hero.id} put both hands around the warmth and smiled. '
            f'"A small thought can mend a large moment," {hero.pronoun()} whispered.'
        )
    if companion:
        world.say(f"{companion.capitalize()} stretched in the firelight as if agreeing.")


def tell(
    weather: Weather,
    problem: Problem,
    method: Method,
    goal: Goal,
    hero_name: str = "Mara",
    hero_type: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "patient",
    companion: str = "",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        role="hero",
        traits=[trait],
        label=hero_name,
    ))
    elder = world.add(Entity(
        id=elder_type.capitalize(),
        kind="character",
        type=elder_type,
        role="elder",
        label=f"the {elder_type}",
    ))
    hearth = world.add(Entity(
        id="hearth",
        type="hearth",
        label="hearth",
        phrase="the stone hearth",
        tags={"hearth"},
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label="cottage room",
    ))
    hearth.meters["warmth"] = 3
    room.meters["cozy"] = 1
    world.facts["companion"] = companion

    opening(world, weather, goal, hero, companion)
    ask_for_goal(world, hero, goal)

    world.para()
    notice_problem(world, problem, hero)
    apply_problem(world, problem, narrate=True)
    inner_plan(world, problem, method, hero)

    world.para()
    if problem.adult_needed:
        fetch_elder(world, elder, hero, companion)
        elder_guides(world, elder, hero, method)
        use_method(world, method, problem, by_elder=True)
        outcome = "helped"
    else:
        use_method(world, method, problem, by_elder=False)
        outcome = "solo"

    world.para()
    closing(world, goal, hero, elder, outcome, companion)

    world.facts.update(
        weather=weather,
        problem=problem,
        method=method,
        goal=goal,
        hero=hero,
        elder=elder,
        hearth=hearth,
        room=room,
        outcome=outcome,
        solved=hearth.meters["warmth"] >= 2 and hearth.meters["smoke"] <= 0,
    )
    return world


KNOWLEDGE = {
    "hearth": [
        (
            "What is a hearth?",
            "A hearth is the place in a home where the fire burns. It warms the room and is often made of stone or brick.",
        )
    ],
    "chimney": [
        (
            "What does a chimney do?",
            "A chimney gives smoke a path to go up and out of the house. If it is blocked, the smoke can come back into the room.",
        )
    ],
    "bellows": [
        (
            "What are bellows for?",
            "Bellows push puffs of air onto a fire. That extra air can wake sleepy embers and help the flames grow.",
        )
    ],
    "tinder": [
        (
            "What is tinder?",
            "Tinder is very dry material that catches fire easily. People use it to help a bigger piece of wood start burning.",
        )
    ],
    "smoke": [
        (
            "Why is smoke a problem inside a house?",
            "Smoke can sting eyes and make it hard to breathe. That is why a fire needs a clear path for smoke to leave the house.",
        )
    ],
    "winter": [
        (
            "Why do people keep a fire going in winter?",
            "A fire gives warmth, light, and a place to cook. In cold weather, it helps the whole house stay comfortable.",
        )
    ],
}
KNOWLEDGE_ORDER = ["hearth", "smoke", "bellows", "tinder", "chimney", "winter"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    goal = f["goal"]
    outcome = f["outcome"]
    if outcome == "helped":
        return [
            'Write a folk-tale style story for a young child that includes the word "hearth", inner monologue, sound effects, and a problem solved by wise help.',
            f"Tell a cottage story where {hero.id} notices {problem.label} at the hearth, thinks carefully, and fetches an elder to solve the problem safely.",
            f"Write a warm folk tale about a child keeping a house ready for {goal.id}, with smoke sounds, thoughtful inner speech, and a lesson about asking for help.",
        ]
    return [
        'Write a folk-tale style story for a young child that includes the word "hearth", inner monologue, sound effects, and gentle problem solving.',
        f"Tell a cottage story where {hero.id} notices {problem.label} at the hearth and solves it by thinking calmly.",
        f"Write a simple fireside tale in which a child listens to the sounds of the house, reasons out a problem, and restores warmth before {goal.id}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    problem = f["problem"]
    method = f["method"]
    goal = f["goal"]
    outcome = f["outcome"]
    companion = f.get("companion", "")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child watching over a cottage hearth. The story also includes {elder.label_word} and the small trouble in the fire.",
        ),
        (
            "What problem did the child notice at the hearth?",
            f"{hero.id} noticed {problem.label}. {problem.symptom} That is why the fire stopped behaving the way a good hearth should.",
        ),
        (
            f"What did {hero.id} think to {hero.pronoun('object')}self?",
            f'{hero.id} thought about what the fire truly needed instead of panicking. The inner thought helped {hero.pronoun("object")} name the problem before trying to fix it.',
        ),
    ]
    if outcome == "solo":
        qa.append(
            (
                f"How did {hero.id} solve the problem?",
                f"{hero.id} {method.qa_text}. That worked because the real problem was {problem.need.replace('_', ' ')}, not bad luck or magic.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.id} call {elder.label_word}?",
                f"{hero.id} called {elder.label_word} because the trouble was bigger than a child should handle alone. The wise choice was to understand the problem first and then ask for safe help.",
            )
        )
        qa.append(
            (
                f"How did {hero.id} and {elder.label_word} fix the hearth?",
                f"Together they {method.qa_text}. Once the chimney path was clear, the smoke could rise and the room grew warm again.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the hearth warm again and the cottage ready for {goal.id}. {goal.ending_text}",
        )
    )
    if companion:
        qa.append(
            (
                f"What did {companion} do in the story?",
                f"{companion.capitalize()} stayed near the child and the firelight. That small companion helped make the cottage feel lived-in and calm at the end.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"hearth"} | set(world.facts["problem"].tags) | set(world.facts["method"].tags)
    tags |= set(world.facts["weather"].tags)
    out: list[tuple[str, str]] = []
    mapping = {
        "hearth": "hearth",
        "smoke": "smoke",
        "bellows": "bellows",
        "tinder": "tinder",
        "chimney": "chimney",
        "winter": "winter",
    }
    for key in KNOWLEDGE_ORDER:
        source = mapping[key]
        if source in tags:
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        weather="rain",
        problem="wet_wood",
        method="dry_tinder",
        goal="soup",
        hero="Mara",
        gender="girl",
        elder="grandmother",
        trait="patient",
        companion="the cat",
    ),
    StoryParams(
        weather="rain",
        problem="low_embers",
        method="bellows",
        goal="mittens",
        hero="Tobin",
        gender="boy",
        elder="grandfather",
        trait="steady",
        companion="the little dog",
    ),
    StoryParams(
        weather="wind",
        problem="blocked_flue",
        method="hearth_brush",
        goal="traveler",
        hero="Nella",
        gender="girl",
        elder="grandmother",
        trait="thoughtful",
        companion="the brown hen",
    ),
]


ASP_RULES = r"""
supports(W, P) :- weather(W), problem(P), affords(W, P).
reasonable_method(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
matches(P, M) :- problem_need(P, Need), fixes(M, Need).
valid(W, P, M) :- supports(W, P), reasonable_method(M), matches(P, M).

outcome(helped) :- chosen_problem(P), adult_needed(P).
outcome(solo)   :- chosen_problem(P), not adult_needed(P).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for wid, weather in WEATHERS.items():
        lines.append(asp.fact("weather", wid))
        for pid in sorted(weather.affords):
            lines.append(asp.fact("affords", wid, pid))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_need", pid, problem.need))
        if problem.adult_needed:
            lines.append(asp.fact("adult_needed", pid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        for fix in sorted(method.fixes):
            lines.append(asp.fact("fixes", mid, fix))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_problem", params.problem)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    scenarios = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        scenarios.append(params)

    bad = 0
    for params in scenarios:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(scenarios)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale hearth storyworld with inner monologue, sound effects, and problem solving."
    )
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("--hero")
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
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))
    if args.weather and args.problem:
        if not weather_supports(WEATHERS[args.weather], PROBLEMS[args.problem]):
            raise StoryError(explain_rejection(WEATHERS[args.weather], PROBLEMS[args.problem]))
    if args.problem and args.method:
        if not method_matches(PROBLEMS[args.problem], METHODS[args.method]):
            raise StoryError(
                f"(No story: {METHODS[args.method].label} does not solve {PROBLEMS[args.problem].label}. "
                f"The fix must match the real trouble.)"
            )

    combos = [
        combo for combo in valid_combos()
        if (args.weather is None or combo[0] == args.weather)
        and (args.problem is None or combo[1] == args.problem)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    weather_id, problem_id, method_id = rng.choice(sorted(combos))
    goal_id = args.goal or rng.choice(sorted(GOALS))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    companion = rng.choice(COMPANIONS)
    return StoryParams(
        weather=weather_id,
        problem=problem_id,
        method=method_id,
        goal=goal_id,
        hero=hero,
        gender=gender,
        elder=elder,
        trait=trait,
        companion=companion,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        weather = WEATHERS[params.weather]
        problem = PROBLEMS[params.problem]
        method = METHODS[params.method]
        goal = GOALS[params.goal]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if method.sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))
    if not weather_supports(weather, problem):
        raise StoryError(explain_rejection(weather, problem))
    if not method_matches(problem, method):
        raise StoryError(
            f"(No story: {method.label} does not solve {problem.label}. The fix must match the real trouble.)"
        )

    world = tell(
        weather=weather,
        problem=problem,
        method=method,
        goal=goal,
        hero_name=params.hero,
        hero_type=params.gender,
        elder_type=params.elder,
        trait=params.trait,
        companion=params.companion,
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
        print(f"{len(combos)} compatible (weather, problem, method) combos:\n")
        for weather, problem, method in combos:
            print(f"  {weather:6} {problem:13} {method}")
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
            header = f"### {p.hero}: {p.problem} in {p.weather} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
