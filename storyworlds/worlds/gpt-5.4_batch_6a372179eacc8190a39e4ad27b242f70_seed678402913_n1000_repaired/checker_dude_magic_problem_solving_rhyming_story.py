#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/checker_dude_magic_problem_solving_rhyming_story.py
===============================================================================

A standalone story world about a child solving a small magical path puzzle in a
gentle rhyming style. The world is built to satisfy seed words "checker" and
"dude" while keeping the story concrete, child-facing, and state-driven.

Premise
-------
A child nicknamed the "checker dude" faces a magic checker path that blocks the
way to something useful. A magical tool reveals a pattern. The child either
solves the puzzle smoothly or makes one hasty mistake, pauses, thinks, and then
solves it. The ending image proves what changed: puzzlement becomes confidence,
and the needed object is used to help.

Run it
------
    python storyworlds/worlds/gpt-5.4/checker_dude_magic_problem_solving_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/checker_dude_magic_problem_solving_rhyming_story.py --place garden --problem sleepy_squares --tool star_chalk
    python storyworlds/worlds/gpt-5.4/checker_dude_magic_problem_solving_rhyming_story.py --problem echo_gap --tool star_chalk
    python storyworlds/worlds/gpt-5.4/checker_dude_magic_problem_solving_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/checker_dude_magic_problem_solving_rhyming_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/checker_dude_magic_problem_solving_rhyming_story.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root. This file lives under storyworlds/worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CAREFUL_TRAITS = {"careful", "patient", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
class Place:
    id: str
    label: str
    scene: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    challenge: str
    clue_need: str
    hint_line: str
    solve_line: str
    steps: int
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    reveals: str
    action: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    use_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    goal: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_clue_makes_plan(world: World) -> list[str]:
    hero = world.get("hero")
    problem = world.facts.get("problem_cfg")
    tool = world.facts.get("tool_cfg")
    if problem is None or tool is None:
        return []
    if hero.meters["clue"] < THRESHOLD:
        return []
    sig = ("plan", problem.id, tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["plan"] += 1
    hero.memes["hope"] += 1
    return ["__plan__"]


def _r_plan_advances(world: World) -> list[str]:
    hero = world.get("hero")
    problem = world.facts.get("problem_cfg")
    if problem is None:
        return []
    if hero.meters["plan"] < THRESHOLD:
        return []
    sig = ("progress", problem.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["progress"] += float(problem.steps)
    hero.memes["fear"] = 0.0
    hero.memes["confidence"] += 1
    return ["__progress__"]


def _r_progress_reaches_goal(world: World) -> list[str]:
    hero = world.get("hero")
    prize = world.get("goal")
    if hero.meters["progress"] < THRESHOLD:
        return []
    sig = ("reached", prize.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    prize.meters["reached"] += 1
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    return ["__reached__"]


CAUSAL_RULES = [
    Rule(name="clue_makes_plan", tag="problem_solving", apply=_r_clue_makes_plan),
    Rule(name="plan_advances", tag="physical", apply=_r_plan_advances),
    Rule(name="progress_reaches_goal", tag="physical", apply=_r_progress_reaches_goal),
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
            if sent == "__plan__":
                world.say("The clue and the child clicked together, neat as a lock and key.")
            elif sent == "__progress__":
                world.say("Step by step the plan held true, and the brave little feet knew what to do.")
            elif sent == "__reached__":
                world.say("Across the checker path at last, the worried moment slipped right past.")
    return produced


def tool_fits(problem: Problem, tool: MagicTool) -> bool:
    return problem.clue_need == tool.reveals


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for problem_id in sorted(place.affords):
            problem = PROBLEMS[problem_id]
            for tool_id, tool in TOOLS.items():
                if tool_fits(problem, tool):
                    combos.append((place_id, problem_id, tool_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    problem = PROBLEMS[params.problem]
    if params.trait in CAREFUL_TRAITS or problem.steps <= 4:
        return "smooth"
    return "learned"


def predict_solution(problem: Problem, tool: MagicTool, trait: str) -> dict:
    return {
        "fits": tool_fits(problem, tool),
        "outcome": "smooth" if trait in CAREFUL_TRAITS or problem.steps <= 4 else "learned",
    }


def introduce(world: World, hero: Entity, helper: Entity, parent: Entity, goal: Goal) -> None:
    world.say(
        f"{hero.id} wore a checkered sweater with bright little squares, "
        f"so {hero.pronoun('possessive')} {parent.label_word} liked to grin and say, "
        f'"There goes my checker dude, with puzzle dreams to share."'
    )
    world.say(
        f"{helper.id} skipped beside {hero.pronoun('object')}, and together they came to "
        f"{world.place.scene} where {goal.phrase} waited on the far side."
    )


def name_need(world: World, hero: Entity, goal: Goal) -> None:
    hero.memes["care"] += 1
    world.say(
        f"They needed {goal.phrase}, and they needed it soon. "
        f"{goal.use_line}"
    )


def reveal_problem(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["fear"] += 1
    hero.meters["stuck"] += 1
    world.say(
        f"But between them and the prize lay {problem.challenge}. "
        f"It looked like a game at first, then a tangle, then a tiny riddle in disguise."
    )


def choose_tool(world: World, hero: Entity, helper: Entity, tool: MagicTool, problem: Problem) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f'"Wait," said {helper.id}, "don\'t rush through. '
        f'Try {tool.phrase} and see what it can do."'
    )
    world.say(
        f"{hero.id} lifted {tool.phrase}, and {tool.glow}. "
        f"{problem.hint_line}"
    )
    hero.meters["clue"] += 1
    world.facts["predicted"] = predict_solution(problem, tool, hero.traits[0] if hero.traits else "")
    propagate(world, narrate=False)


def hasty_misstep(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["fear"] += 1
    hero.memes["confusion"] += 1
    world.say(
        f"{hero.id} nearly bounded ahead too fast, but the first odd tile gave a grumble and a gasp. "
        f"{helper.id} caught {hero.pronoun('object')} sleeve and whispered, "
        f'"Slow, don\'t stew. A puzzle likes thinking more than a hop and a shoo."'
    )


def solve(world: World, hero: Entity, helper: Entity, tool: MagicTool, problem: Problem, learned: bool) -> None:
    hero.meters["stuck"] = 0.0
    if learned:
        world.say(
            f"So {hero.id} took one deep breath, then two, and watched what {tool.label} showed was true."
        )
    else:
        world.say(
            f"{hero.id} nodded at once, calm and bright, ready to follow the pattern just right."
        )
    world.say(problem.solve_line)
    propagate(world, narrate=True)


def celebrate(world: World, hero: Entity, helper: Entity, goal: Goal, parent: Entity) -> None:
    world.say(
        f"{hero.id} reached {goal.phrase}, held it high, and laughed a small, relieved laugh under the sky."
    )
    world.say(goal.use_line)
    world.say(
        f'{parent.label_word.capitalize()} clapped softly. "You did not fuss or blindly zoom. '
        f'You used your magic and your mind to clear the room."'
    )
    world.say(goal.ending_image)


def tell(
    place: Place,
    problem: Problem,
    tool: MagicTool,
    goal: Goal,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World(place=place)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=[trait],
        attrs={"name": hero_name},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_gender,
        label=helper_name,
        phrase=helper_name,
        role="helper",
        attrs={"name": helper_name},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        phrase=parent_type,
        role="parent",
    ))
    prize = world.add(Entity(
        id="goal",
        kind="thing",
        type="goal",
        label=goal.label,
        phrase=goal.phrase,
        role="goal",
    ))
    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        goal=prize,
        place_cfg=place,
        problem_cfg=problem,
        tool_cfg=tool,
        goal_cfg=goal,
    )

    introduce(world, hero, helper, parent, goal)
    name_need(world, hero, goal)
    world.para()
    reveal_problem(world, hero, problem)
    choose_tool(world, hero, helper, tool, problem)
    world.para()

    learned = outcome_of(StoryParams(
        place=place.id,
        problem=problem.id,
        tool=tool.id,
        goal=goal.id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent_type,
        trait=trait,
        seed=None,
    )) == "learned"
    if learned:
        hasty_misstep(world, hero, helper, problem)

    solve(world, hero, helper, tool, problem, learned)
    world.para()
    celebrate(world, hero, helper, goal, parent)

    world.facts.update(
        solved=prize.meters["reached"] >= THRESHOLD,
        outcome="learned" if learned else "smooth",
        learned=learned,
        clue_found=hero.meters["clue"] >= THRESHOLD,
    )
    return world


PLACES = {
    "garden": Place(
        id="garden",
        label="garden path",
        scene="a garden path stitched with checker stones",
        affords={"sleepy_squares", "hush_tiles"},
        tags={"garden", "checker"},
    ),
    "porch": Place(
        id="porch",
        label="moon porch",
        scene="a moonlit porch with a checker floor",
        affords={"echo_gap", "sleepy_squares"},
        tags={"porch", "checker"},
    ),
    "hall": Place(
        id="hall",
        label="library hall",
        scene="a hush-soft hall with checker tiles that shone like toast",
        affords={"hush_tiles", "echo_gap"},
        tags={"hall", "checker"},
    ),
}

PROBLEMS = {
    "sleepy_squares": Problem(
        id="sleepy_squares",
        label="sleepy squares",
        challenge="a checker path where every other square yawned shut",
        clue_need="count",
        hint_line='Tiny star marks winked on every other square, as if the floor were saying, "Count with care."',
        solve_line="One, skip one, one, skip one: the safe squares made a tidy run.",
        steps=5,
        tags={"counting", "pattern"},
    ),
    "hush_tiles": Problem(
        id="hush_tiles",
        label="hush tiles",
        challenge="a checker path where only matching colors stayed awake",
        clue_need="match",
        hint_line='The pale tiles glowed in pairs, and the dark ones hummed back, as if the path were asking for a match.',
        solve_line="Light to light and dark to dark, the path made room with every mark.",
        steps=4,
        tags={"matching", "pattern"},
    ),
    "echo_gap": Problem(
        id="echo_gap",
        label="echo gap",
        challenge="a checker path with a small dark gap where hidden stones came only to a rhyme",
        clue_need="sound",
        hint_line='A soft beat answered from below: tap-tap, rhyme-rhyme, and stepping stones began to show.',
        solve_line='Tap, rhyme, tap, rhyme: the bridge came back in time.',
        steps=3,
        tags={"sound", "rhyme"},
    ),
}

TOOLS = {
    "star_chalk": MagicTool(
        id="star_chalk",
        label="star chalk",
        phrase="the star chalk",
        reveals="count",
        action="draws bright dots on safe steps",
        glow="silver sparks skipped from the tip in a twinkly stripe",
        tags={"magic", "counting"},
    ),
    "color_lantern": MagicTool(
        id="color_lantern",
        label="color lantern",
        phrase="the color lantern",
        reveals="match",
        action="makes matching colors glow together",
        glow="soft bands of blue and gold slid over the tiles",
        tags={"magic", "matching"},
    ),
    "hum_drum": MagicTool(
        id="hum_drum",
        label="hum drum",
        phrase="the hum drum",
        reveals="sound",
        action="beats out a rhyme that wakes hidden stones",
        glow="warm little notes bobbed up like bubbles in a tune",
        tags={"magic", "sound"},
    ),
}

GOALS = {
    "water_pail": Goal(
        id="water_pail",
        label="watering pail",
        phrase="the little watering pail",
        use_line="The tulips by the gate were drooping low, so the pail had to go where the thirsty flowers could glow.",
        ending_image="Soon the tulips stood up straighter, and the path looked less like trouble and more like later.",
        tags={"flowers", "helping"},
    ),
    "bell": Goal(
        id="bell",
        label="silver bell",
        phrase="the silver bell",
        use_line="The tiny parade cart had lost its cheerful ring, so the bell was needed to make it sing.",
        ending_image="A bright ding-ding skipped through the air, and even the checker floor seemed pleased to be there.",
        tags={"music", "helping"},
    ),
    "ribbon": Goal(
        id="ribbon",
        label="sky ribbon",
        phrase="the sky-blue ribbon",
        use_line="A torn kite tail needed one last tie, so the ribbon was needed before the kite could fly.",
        ending_image="Soon the kite rose up with a flutter and swoop, and the worried faces turned into a happy little group.",
        tags={"kite", "helping"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Maya", "Nora"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Eli", "Noah"]
TRAITS = ["careful", "patient", "steady", "eager", "bouncy", "quick"]


KNOWLEDGE = {
    "checker": [(
        "What does checker mean in a floor pattern?",
        "A checker pattern is made of squares in two colors that alternate, one after another. It looks neat because the colors take turns."
    )],
    "magic": [(
        "What is magic in a story like this?",
        "Magic in a story is a special make-believe power that can reveal hidden things or help solve a problem. In this world, the magic does not replace thinking; it helps the child notice the pattern."
    )],
    "counting": [(
        "How can counting help solve a puzzle?",
        "Counting helps you notice order, like every other step or how many moves come next. When you count carefully, a confusing problem can turn into a clear plan."
    )],
    "matching": [(
        "What does matching mean in a pattern puzzle?",
        "Matching means finding things that go together, like two tiles with the same color. Using matches helps you see the rule the puzzle wants you to follow."
    )],
    "sound": [(
        "How can sound help with a puzzle?",
        "A sound can act like a clue or a rhythm to follow. A steady beat helps your mind slow down and notice what comes next."
    )],
    "rhyme": [(
        "What is a rhyme?",
        "A rhyme is when words have the same or almost the same ending sound, like bell and well. Rhymes make language playful and easier to remember."
    )],
    "helping": [(
        "Why is it nice to solve a problem in order to help someone or something?",
        "Helping gives the problem a reason that matters. When you solve a puzzle to care for flowers or fix a toy, your thinking turns into kindness."
    )],
}
KNOWLEDGE_ORDER = ["checker", "magic", "counting", "matching", "sound", "rhyme", "helping"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    problem = world.facts["problem_cfg"]
    tool = world.facts["tool_cfg"]
    goal = world.facts["goal_cfg"]
    outcome = world.facts["outcome"]
    name = hero.attrs.get("name", hero.label)
    helper_name = helper.attrs.get("name", helper.label)
    prompts = [
        'Write a short rhyming story for a 3-to-5-year-old that includes the words "checker" and "dude."',
        f"Tell a gentle magic problem-solving story where {name} is called a checker dude and uses {tool.label} to solve {problem.label}.",
        f"Write a child-facing rhyme about crossing a checker path to reach {goal.phrase}, with a clear beginning, puzzle turn, and helpful ending.",
    ]
    if outcome == "learned":
        prompts.append(
            f"Include one small hasty mistake before {name} slows down, listens to {helper_name}, and follows the clue correctly."
        )
    else:
        prompts.append(
            f"Make {name} calm and observant, so the puzzle is solved smoothly once the magic clue appears."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    parent = world.facts["parent"]
    problem = world.facts["problem_cfg"]
    tool = world.facts["tool_cfg"]
    goal = world.facts["goal_cfg"]
    name = hero.attrs.get("name", hero.label)
    helper_name = helper.attrs.get("name", helper.label)
    parent_word = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a child playfully called a checker dude, and {helper_name}, who stays nearby while the puzzle is solved. The grown-up at the end is {name}'s {parent_word}."
        ),
        (
            "What problem did the child face?",
            f"{name} had to cross {problem.challenge} to reach {goal.phrase}. The path looked simple at first, but it only became safe when the hidden rule was understood."
        ),
        (
            f"How did {tool.label} help?",
            f"{tool.label.capitalize()} gave a clue instead of doing the whole job. It showed the pattern {name} needed to notice, which turned a confusing path into a plan."
        ),
        (
            f"Why did {name} need {goal.phrase}?",
            goal.use_line
        ),
    ]
    if world.facts.get("outcome") == "learned":
        qa.append((
            f"Did {name} solve the problem right away?",
            f"No. {name} almost rushed ahead, and the path grumbled back, which showed that guessing would not work. Then {name} slowed down, listened, and used the clue step by step."
        ))
    else:
        qa.append((
            f"Did {name} rush or think carefully?",
            f"{name} thought carefully. Because the child stayed calm and watched the clue, the puzzle opened without a false start."
        ))
    qa.append((
        "How did the story end?",
        f"{name} reached {goal.phrase} and used it to help. The ending image shows the world changing for the better: {goal.ending_image}"
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"checker", "magic", "helping"}
    problem = world.facts["problem_cfg"]
    tool = world.facts["tool_cfg"]
    goal = world.facts["goal_cfg"]
    tags |= set(problem.tags)
    tags |= set(tool.tags)
    tags |= set(goal.tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden",
        problem="sleepy_squares",
        tool="star_chalk",
        goal="water_pail",
        hero_name="Ben",
        hero_gender="boy",
        helper_name="Mia",
        helper_gender="girl",
        parent="mother",
        trait="eager",
        seed=None,
    ),
    StoryParams(
        place="hall",
        problem="hush_tiles",
        tool="color_lantern",
        goal="bell",
        hero_name="Lily",
        hero_gender="girl",
        helper_name="Theo",
        helper_gender="boy",
        parent="father",
        trait="careful",
        seed=None,
    ),
    StoryParams(
        place="porch",
        problem="echo_gap",
        tool="hum_drum",
        goal="ribbon",
        hero_name="Max",
        hero_gender="boy",
        helper_name="Nora",
        helper_gender="girl",
        parent="mother",
        trait="patient",
        seed=None,
    ),
]


def explain_rejection(place: Optional[Place], problem: Problem, tool: MagicTool) -> str:
    if not tool_fits(problem, tool):
        return (
            f"(No story: {tool.label} reveals {tool.reveals}, but {problem.label} needs "
            f"{problem.clue_need}. Pick a tool that fits the puzzle's hidden rule.)"
        )
    if place is not None and problem.id not in place.affords:
        return (
            f"(No story: {problem.label} does not belong in {place.label}. "
            f"Choose a place that can honestly hold that kind of puzzle.)"
        )
    return "(No story: this combination does not fit the world.)"


ASP_RULES = r"""
fits(P, T) :- need(P, N), reveals(T, N).
valid(Place, P, T) :- affords(Place, P), fits(P, T).

smooth :- chosen_trait(Tr), careful_trait(Tr).
smooth :- chosen_problem(P), steps(P, S), S <= 4.

outcome(smooth) :- smooth.
outcome(learned) :- not smooth.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for problem_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, problem_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("need", problem_id, problem.clue_need))
        lines.append(asp.fact("steps", problem_id, problem.steps))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("reveals", tool_id, tool.reveals))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
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
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    for s in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        if "{" in smoke.story or "}" in smoke.story:
            raise StoryError("Smoke test found unresolved braces in story text.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a checker-path magic puzzle solved in a gentle rhyming style."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.tool:
        problem = PROBLEMS[args.problem]
        tool = TOOLS[args.tool]
        place = PLACES[args.place] if args.place else None
        if not tool_fits(problem, tool) or (place is not None and args.problem not in place.affords):
            raise StoryError(explain_rejection(place, problem, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.problem is None or combo[1] == args.problem)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, problem_id, tool_id = rng.choice(sorted(combos))
    goal_id = args.goal or rng.choice(sorted(GOALS))
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=hero_name)

    return StoryParams(
        place=place_id,
        problem=problem_id,
        tool=tool_id,
        goal=goal_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Invalid problem: {params.problem})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Invalid tool: {params.tool})")
    if params.goal not in GOALS:
        raise StoryError(f"(Invalid goal: {params.goal})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Invalid parent: {params.parent})")
    if params.hero_gender not in {"girl", "boy"} or params.helper_gender not in {"girl", "boy"}:
        raise StoryError("(Invalid gender choice.)")
    if params.trait not in TRAITS:
        raise StoryError(f"(Invalid trait: {params.trait})")

    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    if problem.id not in place.affords or not tool_fits(problem, tool):
        raise StoryError(explain_rejection(place, problem, tool))

    world = tell(
        place=place,
        problem=problem,
        tool=tool,
        goal=GOALS[params.goal],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, tool) combos:\n")
        for place, problem, tool in combos:
            print(f"  {place:8} {problem:16} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name}: {p.problem} at {p.place} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
