#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/zoologic_made_inner_monologue_teamwork_fable.py
============================================================================

A standalone story world about a small animal team learning that careful
thinking and shared work solve a problem better than pride does.

Seed constraints satisfied
--------------------------
- Includes the words "zoologic" and "made"
- Features inner monologue and teamwork
- Style stays close to a child-facing fable

Premise
-------
The animals of a little meadow school have made a tiny "zoologic club" for
solving nature problems. When food is stuck in a high or hard place, one animal
first tries to solve it alone. Their private thoughts tug them toward pride or
worry. Then a second animal offers a complementary skill, and together they
reach the food safely. The ending states the moral through changed behavior.

Run it
------
    python storyworlds/worlds/gpt-5.4/zoologic_made_inner_monologue_teamwork_fable.py
    python storyworlds/worlds/gpt-5.4/zoologic_made_inner_monologue_teamwork_fable.py --all
    python storyworlds/worlds/gpt-5.4/zoologic_made_inner_monologue_teamwork_fable.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/zoologic_made_inner_monologue_teamwork_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4/zoologic_made_inner_monologue_teamwork_fable.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "squirrel", "mouse", "beaver", "tortoise", "fox", "crow", "hedgehog", "otter"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    image: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Problem:
    id: str
    need: str
    object_label: str
    object_the: str
    location: str
    challenge: str
    risk: str
    success_image: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class AnimalSpec:
    id: str
    type: str
    title: str
    skill: str
    method: str
    limitation: str
    thought_style: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Strategy:
    id: str
    sense: int
    solo_only: bool
    text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_strain(world: World) -> list[str]:
    out: list[str] = []
    actor = world.entities.get("hero")
    if actor is None:
        return out
    if actor.meters["solo_attempt"] < THRESHOLD:
        return out
    if world.facts.get("solvable_solo", False):
        return out
    sig = ("strain", actor.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    actor.meters["stuck"] += 1
    actor.memes["worry"] += 1
    out.append("__strain__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("helper_joined") is not True:
        return out
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    goal = world.entities.get("goal")
    if hero is None or helper is None or goal is None:
        return out
    sig = ("team", hero.id, helper.id, goal.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    goal.meters["reached"] += 1
    hero.memes["gratitude"] += 1
    helper.memes["gratitude"] += 1
    hero.memes["pride"] = 0.0
    out.append("__team_success__")
    return out


CAUSAL_RULES = [
    Rule(name="strain", tag="physical", apply=_r_strain),
    Rule(name="teamwork", tag="social", apply=_r_teamwork),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def complementary(hero: AnimalSpec, helper: AnimalSpec, problem: Problem) -> bool:
    need = PROBLEM_NEEDS[problem.id]
    skills = {hero.skill, helper.skill}
    return need.issubset(skills) and hero.id != helper.id


def sensible_strategies() -> list[Strategy]:
    return [s for s in STRATEGIES.values() if s.sense >= SENSE_MIN]


def best_strategy() -> Strategy:
    return max(STRATEGIES.values(), key=lambda s: s.sense)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for problem_id, problem in PROBLEMS.items():
            for hero_id, hero in ANIMALS.items():
                for helper_id, helper in ANIMALS.items():
                    if complementary(hero, helper, problem):
                        combos.append((setting_id, problem_id, hero_id, helper_id))
    return combos


def strategy_works(strategy: Strategy, hero: AnimalSpec, helper: AnimalSpec, problem: Problem) -> bool:
    if strategy.sense < SENSE_MIN:
        return False
    if strategy.solo_only:
        return PROBLEM_SOLO.get((problem.id, hero.skill), False)
    return complementary(hero, helper, problem)


def predict_solo(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["solo_attempt"] += 1
    propagate(sim, narrate=False)
    return {
        "stuck": hero.meters["stuck"] >= THRESHOLD,
        "worry": hero.memes["worry"],
    }


def club_opening(world: World, setting: Setting, hero: Entity, helper: Entity) -> None:
    hero.memes["hope"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"In {setting.place}, where {setting.image}, {hero.id} and {helper.id} had made a tiny zoologic club. "
        f"They liked to watch the meadow closely and solve little nature puzzles together."
    )


def spot_problem(world: World, hero: Entity, problem: Problem) -> None:
    world.say(
        f"That morning, {hero.id} found {problem.object_the} {problem.location}. "
        f"{problem.challenge}"
    )


def first_desire(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["pride"] += 1
    world.say(
        f'{hero.id} drew a breath and thought, "I can do this myself. If I hurry, '
        f"I can {problem.need} before anyone else comes."
    )


def solo_attempt(world: World, hero: Entity, strategy: Strategy, problem: Problem) -> None:
    hero.meters["solo_attempt"] += 1
    propagate(world, narrate=False)
    if hero.meters["stuck"] >= THRESHOLD:
        world.say(
            f"{hero.id} {strategy.fail_text.format(object=problem.object_label, location=problem.location)}"
        )
    else:
        world.say(
            f"{hero.id} {strategy.text.format(object=problem.object_label, location=problem.location)}"
        )


def inner_doubt(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    pred = predict_solo(world)
    world.facts["predicted_stuck"] = pred["stuck"]
    if pred["stuck"]:
        world.say(
            f'Then a quieter thought came to {hero.id}: "If I keep trying alone, {problem.risk}. '
            f"Perhaps being small is not the same as being helpless."
        )
    else:
        world.say(
            f'{hero.id} wondered, "Maybe I could finish, but it would still be easier with a friend."'
        )
    helper.memes["care"] += 1


def offer_help(world: World, helper: Entity, hero: Entity, helper_spec: AnimalSpec, hero_spec: AnimalSpec) -> None:
    world.say(
        f'{helper.id} saw the trouble and stepped closer. "{hero.id}," {helper.pronoun()} said, '
        f'"you know {hero_spec.skill}, and I know {helper_spec.skill}. Let us put our strengths together."'
    )


def accept_help(world: World, hero: Entity, helper: Entity) -> None:
    world.facts["helper_joined"] = True
    hero.memes["humility"] += 1
    world.say(
        f'{hero.id} lowered {hero.pronoun("possessive")} ears for a moment, then smiled. '
        f'"Yes," {hero.pronoun()} said. "Two careful minds may do what one proud mind cannot."'
    )


def solve_together(world: World, hero: Entity, helper: Entity, hero_spec: AnimalSpec,
                   helper_spec: AnimalSpec, strategy: Strategy, problem: Problem) -> None:
    propagate(world, narrate=False)
    world.say(
        f"First, {hero.id} used {hero_spec.method}. Then {helper.id} used {helper_spec.method}. "
        f"Together they {strategy.qa_text.format(object=problem.object_label, location=problem.location)}."
    )
    world.say(problem.success_image)


def close_fable(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f"From that day on, whenever a task looked too tall, too tucked away, or too heavy for one pair of paws, "
        f"the little club did not boast. {hero.id} and {helper.id} called each other first."
    )
    world.say(
        "And so the meadow learned a gentle truth: the creature who listens to a wise inner voice and welcomes help "
        "often reaches the sweetest prize."
    )
@dataclass
class StoryParams:
    setting: str
    problem: str
    hero: str
    helper: str
    strategy: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when two or more people or animals share a job and help each other do it. One friend may do the part another friend cannot."
        )
    ],
    "inner_voice": [
        (
            "What is an inner voice?",
            "An inner voice is the quiet thought inside your mind that helps you notice feelings and choices. It can remind you to slow down and make a wiser plan."
        )
    ],
    "rabbit": [
        (
            "Why is a rabbit good at reaching high things?",
            "A rabbit can jump quickly with strong back legs. That helps it spring upward, even if it still cannot do every job alone."
        )
    ],
    "tortoise": [
        (
            "Why can a tortoise help in a careful job?",
            "A tortoise moves slowly and stays steady. That makes it good at holding still when patience matters."
        )
    ],
    "mouse": [
        (
            "Why can a mouse open small hard things?",
            "A mouse has tiny sharp teeth and can nibble very carefully. That helps with little cracks and tight spaces."
        )
    ],
    "beaver": [
        (
            "Why is a beaver strong?",
            "A beaver has strong paws and a sturdy body built for hard work. It can brace and hold things while another helper does a finer job."
        )
    ],
    "squirrel": [
        (
            "Why is a squirrel nimble?",
            "A squirrel moves lightly and quickly through branches and stems. Nimble means able to move in a fast, careful way."
        )
    ],
    "otter": [
        (
            "How can an otter carry things cleverly?",
            "An otter is good with its forepaws and can balance objects with care. In a story, that makes it a helpful carrier."
        )
    ],
}
KNOWLEDGE_ORDER = ["teamwork", "inner_voice", "rabbit", "tortoise", "mouse", "beaver", "squirrel", "otter"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    setting = f["setting"]
    return [
        f'Write a short fable for a 3-to-5-year-old that includes the word "zoologic" and the word "made". Set it in {setting.place}.',
        f"Tell a gentle animal fable where {hero.id} first thinks privately about solving a problem alone, then learns to work with {helper.id} to reach some {problem.object_label}.",
        "Write a simple story with inner monologue and teamwork, ending in a clear moral that sharing strengths is wiser than showing off.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    strategy = f["strategy"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {helper.id}, two small meadow friends in a zoologic club. They find a problem that is too hard for one animal alone."
        ),
        (
            f"What problem did {hero.id} find?",
            f"{hero.id} found {problem.object_the} {problem.location}. The trouble was that {problem.challenge.lower()}"
        ),
        (
            f"What did {hero.id} think at first?",
            f"{hero.id} first thought about solving the problem alone. That private thought shows the inner monologue that pushed {hero.pronoun()} toward pride before wisdom."
        ),
        (
            f"Why did {hero.id} stop trying alone?",
            f"{hero.id} could feel that working alone was not enough. The quieter thought inside warned that {problem.risk}, so {hero.pronoun()} became ready to listen."
        ),
        (
            f"How did {helper.id} help?",
            f"{helper.id} offered a different skill, and that matched what the problem needed. Together they {strategy.qa_text.format(object=problem.object_label, location=problem.location)}, which neither one could do as well alone."
        ),
        (
            "What is the moral of the story?",
            "The moral is that a wise heart listens to good thoughts inside and accepts help from others. Teamwork turns two small strengths into one strong answer."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"teamwork", "inner_voice", f["hero_spec"].id, f["helper_spec"].id}
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  facts: teamwork={world.facts.get('teamwork')} moral={world.facts.get('moral_learned')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="orchard_edge",
        problem="apple_branch",
        hero="rabbit",
        helper="tortoise",
        strategy="pair_work",
        hero_name="Pip",
        helper_name="Shell",
    ),
    StoryParams(
        setting="pond_bank",
        problem="nut_crack",
        hero="mouse",
        helper="beaver",
        strategy="pair_work",
        hero_name="Thimble",
        helper_name="Birch",
    ),
    StoryParams(
        setting="meadow",
        problem="berries_reeds",
        hero="squirrel",
        helper="otter",
        strategy="pair_work",
        hero_name="Hazel",
        helper_name="Ripple",
    ),
]


def explain_rejection(problem: Problem, hero: AnimalSpec, helper: AnimalSpec) -> str:
    return (
        f"(No story: {hero.title} and {helper.title} do not cover the skills needed for {problem.id}. "
        f"This fable only tells teamwork pairs whose strengths truly fit the problem.)"
    )


ASP_RULES = r"""
sense_min(2).

need(apple_branch, leap).
need(apple_branch, steady).
need(nut_crack, gnaw).
need(nut_crack, brace).
need(berries_reeds, nimble).
need(berries_reeds, carry).

complementary(P,H,Hp) :- need(P,S1), has_skill(H,S1), need(P,S2), has_skill(Hp,S2), H != Hp.
valid(Setting,P,H,Hp) :- setting(Setting), problem(P), animal(H), animal(Hp), complementary(P,H,Hp).

sensible(St) :- strategy(St), sense(St,S), sense_min(M), S >= M.
works(P,H,Hp,St) :- valid(_,P,H,Hp), sensible(St), not solo_only(St).

outcome(team_success) :- chosen_problem(P), chosen_hero(H), chosen_helper(Hp), chosen_strategy(St), works(P,H,Hp,St).
#show valid/4.
#show sensible/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for problem_id in PROBLEMS:
        lines.append(asp.fact("problem", problem_id))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        lines.append(asp.fact("has_skill", animal_id, animal.skill))
    for strategy_id, strategy in STRATEGIES.items():
        lines.append(asp.fact("strategy", strategy_id))
        lines.append(asp.fact("sense", strategy_id, strategy.sense))
        if strategy.solo_only:
            lines.append(asp.fact("solo_only", strategy_id))
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
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_problem", params.problem),
            asp.fact("chosen_hero", params.hero),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_strategy", params.strategy),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if not complementary(ANIMALS[params.hero], ANIMALS[params.helper], PROBLEMS[params.problem]):
        return "invalid"
    if not strategy_works(STRATEGIES[params.strategy], ANIMALS[params.hero], ANIMALS[params.helper], PROBLEMS[params.problem]):
        return "invalid"
    return "team_success"


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

    c_sens = set(asp_sensible())
    p_sens = {s.id for s in sensible_strategies()}
    if c_sens == p_sens:
        print(f"OK: sensible strategies match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible strategies: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure on seed {seed}.")
            break

    bad = 0
    for params in cases:
        ao = asp_outcome(params)
        po = outcome_of(params)
        if ao != po:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        emit(smoke, trace=False, qa=False)
        print("OK: smoke generation/emit passed.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny animal fable about inner monologue and teamwork."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--helper", choices=ANIMALS)
    ap.add_argument("--strategy", choices=STRATEGIES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_names(hero_id: str, helper_id: str, rng: random.Random) -> tuple[str, str]:
    hero_name = rng.choice(NAME_OPTIONS[hero_id])
    helper_pool = [n for n in NAME_OPTIONS[helper_id] if n != hero_name]
    helper_name = rng.choice(helper_pool)
    return hero_name, helper_name


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hero and args.helper and args.hero == args.helper:
        raise StoryError("(No story: the hero and helper must be different animals.)")
    if args.problem and args.hero and args.helper:
        if not complementary(ANIMALS[args.hero], ANIMALS[args.helper], PROBLEMS[args.problem]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], ANIMALS[args.hero], ANIMALS[args.helper]))
    if args.strategy and STRATEGIES[args.strategy].sense < SENSE_MIN:
        raise StoryError(
            f"(Refusing strategy '{args.strategy}': it scores too low on common sense "
            f"(sense={STRATEGIES[args.strategy].sense} < {SENSE_MIN}).)"
        )

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.problem is None or combo[1] == args.problem)
        and (args.hero is None or combo[2] == args.hero)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, problem_id, hero_id, helper_id = rng.choice(sorted(combos))
    strategy_id = args.strategy or best_strategy().id
    hero_name, helper_name = pick_names(hero_id, helper_id, rng)

    return StoryParams(
        setting=setting_id,
        problem=problem_id,
        hero=hero_id,
        helper=helper_id,
        strategy=strategy_id,
        hero_name=hero_name,
        helper_name=helper_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(No story: unknown problem '{params.problem}'.)")
    if params.hero not in ANIMALS:
        raise StoryError(f"(No story: unknown hero '{params.hero}'.)")
    if params.helper not in ANIMALS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if params.strategy not in STRATEGIES:
        raise StoryError(f"(No story: unknown strategy '{params.strategy}'.)")

    world = tell(
        setting=SETTINGS[params.setting],
        problem=PROBLEMS[params.problem],
        hero_spec=ANIMALS[params.hero],
        helper_spec=ANIMALS[params.helper],
        strategy=STRATEGIES[params.strategy],
        hero_name=params.hero_name,
        helper_name=params.helper_name,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible strategies: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, problem, hero, helper) combos:\n")
        for setting_id, problem_id, hero_id, helper_id in combos:
            print(f"  {setting_id:12} {problem_id:14} {hero_id:10} {helper_id}")
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
            header = f"### {p.hero_name} and {p.helper_name}: {p.problem} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(setting: Setting, problem: Problem, hero_spec: AnimalSpec, helper_spec: AnimalSpec,
         strategy: Strategy, hero_name: str, helper_name: str) -> World:
    if not complementary(hero_spec, helper_spec, problem):
        raise StoryError(
            f"(No story: {hero_spec.title} and {helper_spec.title} do not have the complementary skills needed for {problem.id}.)"
        )
    if strategy.sense < SENSE_MIN:
        raise StoryError(
            f"(Refusing strategy '{strategy.id}': it scores too low on common sense "
            f"(sense={strategy.sense} < {SENSE_MIN}). Try a teamwork strategy instead.)"
        )
    if not strategy_works(strategy, hero_spec, helper_spec, problem):
        raise StoryError(
            f"(No story: strategy '{strategy.id}' cannot reasonably solve {problem.id} with {hero_spec.id} and {helper_spec.id}.)"
        )

    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_spec.type, label=hero_spec.title, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_spec.type, label=helper_spec.title, role="helper"))
    goal = world.add(Entity(id="goal", kind="thing", type="food", label=problem.object_label))
    world.facts["solvable_solo"] = strategy.solo_only and PROBLEM_SOLO.get((problem.id, hero_spec.skill), False)
    world.facts["helper_joined"] = False

    club_opening(world, setting, hero, helper)
    spot_problem(world, hero, problem)

    world.para()
    first_desire(world, hero, problem)
    solo_attempt(world, hero, STRATEGIES["reach_alone"], problem)
    inner_doubt(world, hero, helper, problem)

    world.para()
    offer_help(world, helper, hero, helper_spec, hero_spec)
    accept_help(world, hero, helper)
    solve_together(world, hero, helper, hero_spec, helper_spec, strategy, problem)

    world.para()
    close_fable(world, hero, helper, problem)

    world.facts.update(
        setting=setting,
        problem=problem,
        hero=hero,
        helper=helper,
        hero_spec=hero_spec,
        helper_spec=helper_spec,
        strategy=strategy,
        teamwork=goal.meters["reached"] >= THRESHOLD,
        moral_learned=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "meadow": Setting(
        id="meadow",
        place="a sunlit meadow by the reeds",
        image="dew shone on the grass and the brook talked softly to the stones",
        tags={"meadow", "brook"},
    ),
    "orchard_edge": Setting(
        id="orchard_edge",
        place="the quiet edge of an old orchard",
        image="wind moved through the leaves like a whispering choir",
        tags={"orchard", "tree"},
    ),
    "pond_bank": Setting(
        id="pond_bank",
        place="a pond bank under broad willow branches",
        image="the water held round clouds as still as silver plates",
        tags={"pond", "willow"},
    ),
}

PROBLEMS = {
    "apple_branch": Problem(
        id="apple_branch",
        need="get the apple down",
        object_label="apple",
        object_the="the reddest apple",
        location="on a thin branch above the path",
        challenge="It swayed just out of jumping reach.",
        risk="I will only shake the branch and tire myself",
        success_image="At last the apple dropped into the moss, bright and whole, and both friends laughed before sharing it.",
        tags={"apple", "high"},
    ),
    "nut_crack": Problem(
        id="nut_crack",
        need="open the nut",
        object_label="nut",
        object_the="a fat brown nut",
        location="between two roots",
        challenge="Its shell was hard as a little wooden door.",
        risk="I will strain and still leave the shell closed",
        success_image="Soon the shell gave a neat crack, and the sweet nut inside was enough for two tidy bites.",
        tags={"nut", "hard"},
    ),
    "berries_reeds": Problem(
        id="berries_reeds",
        need="bring the berries back",
        object_label="berries",
        object_the="a cluster of purple berries",
        location="deep among bending reeds over soft mud",
        challenge="The ground near them wobbled, and the stems tugged at small feet.",
        risk="I may slip in the mud before I carry anything home",
        success_image="When they returned, the berries rested safely in a leaf tray, and the whole path smelled sweet.",
        tags={"berries", "mud"},
    ),
}

PROBLEM_NEEDS = {
    "apple_branch": {"leap", "steady"},
    "nut_crack": {"gnaw", "brace"},
    "berries_reeds": {"nimble", "carry"},
}

PROBLEM_SOLO = {
    ("apple_branch", "leap"): False,
    ("nut_crack", "gnaw"): False,
    ("berries_reeds", "nimble"): False,
}

ANIMALS = {
    "rabbit": AnimalSpec(
        id="rabbit",
        type="rabbit",
        title="the rabbit",
        skill="leap",
        method="a springy jump",
        limitation="cannot hold a branch steady alone",
        thought_style="quick and hopeful",
        tags={"rabbit", "jump"},
    ),
    "tortoise": AnimalSpec(
        id="tortoise",
        type="tortoise",
        title="the tortoise",
        skill="steady",
        method="patient weight and a firm back",
        limitation="cannot jump high",
        thought_style="slow and thoughtful",
        tags={"tortoise", "steady"},
    ),
    "mouse": AnimalSpec(
        id="mouse",
        type="mouse",
        title="the mouse",
        skill="gnaw",
        method="small sharp teeth and careful nibbling",
        limitation="cannot brace heavy things alone",
        thought_style="nervous but exact",
        tags={"mouse", "teeth"},
    ),
    "beaver": AnimalSpec(
        id="beaver",
        type="beaver",
        title="the beaver",
        skill="brace",
        method="a flat tail and strong paws",
        limitation="cannot make tiny cuts in narrow places",
        thought_style="practical and calm",
        tags={"beaver", "strong"},
    ),
    "squirrel": AnimalSpec(
        id="squirrel",
        type="squirrel",
        title="the squirrel",
        skill="nimble",
        method="light steps and quick climbing",
        limitation="cannot carry much at once",
        thought_style="bright and busy",
        tags={"squirrel", "nimble"},
    ),
    "otter": AnimalSpec(
        id="otter",
        type="otter",
        title="the otter",
        skill="carry",
        method="clever forepaws and a broad leaf used like a tray",
        limitation="is slower in reeds than on open ground",
        thought_style="playful and kind",
        tags={"otter", "carry"},
    ),
}

STRATEGIES = {
    "reach_alone": Strategy(
        id="reach_alone",
        sense=1,
        solo_only=True,
        text="stretched and strained until the {object} almost slipped within reach",
        fail_text="stretched and strained at the {object}, but could not manage it alone.",
        qa_text="managed to reach the {object}",
        tags={"solo"},
    ),
    "pair_work": Strategy(
        id="pair_work",
        sense=3,
        solo_only=False,
        text="worked together well",
        fail_text="tried, but did not yet know how to work together.",
        qa_text="brought the {object} safely free from {location}",
        tags={"teamwork"},
    ),
}

NAME_OPTIONS = {
    "rabbit": ["Pip", "Moss", "Juniper"],
    "tortoise": ["Shell", "Hush", "Pebble"],
    "mouse": ["Nip", "Poppy", "Thimble"],
    "beaver": ["Birch", "Paddle", "Oak"],
    "squirrel": ["Hazel", "Skip", "Tansy"],
    "otter": ["Ripple", "Reed", "Brook"],
}

if __name__ == "__main__":
    main()
