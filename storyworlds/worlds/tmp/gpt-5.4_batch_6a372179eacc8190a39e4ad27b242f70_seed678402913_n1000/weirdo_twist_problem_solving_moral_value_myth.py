#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/weirdo_twist_problem_solving_moral_value_myth.py
============================================================================

A standalone story world about a child in a myth-like village tale: someone
mocked as a "weirdo" notices a hidden pattern in the world, solves a communal
problem, and teaches a moral about listening kindly before laughing.

The world model is small but classical:

* Physical meters track things like thirst, flooding, blocked water, and repair.
* Emotional memes track loneliness, doubt, hope, gratitude, and belonging.
* A simple causal engine pushes consequences forward.
* The prose follows premise -> tension -> twist -> resolution, driven by state.
* A reasonableness gate refuses combinations where the "odd" sign could not
  plausibly help solve the village problem.
* An inline ASP twin mirrors the compatibility gate and the outcome model.

Run it
------
    python storyworlds/worlds/gpt-5.4/weirdo_twist_problem_solving_moral_value_myth.py
    python storyworlds/worlds/gpt-5.4/weirdo_twist_problem_solving_moral_value_myth.py --problem drought --sign frogs
    python storyworlds/worlds/gpt-5.4/weirdo_twist_problem_solving_moral_value_myth.py --problem fire --tool reed_flute
    python storyworlds/worlds/gpt-5.4/weirdo_twist_problem_solving_moral_value_myth.py --all
    python storyworlds/worlds/gpt-5.4/weirdo_twist_problem_solving_moral_value_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/weirdo_twist_problem_solving_moral_value_myth.py --verify
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
USEFUL_MIN = 2


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
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "elder": "elder"}.get(self.type, self.type)


@dataclass
class Problem:
    id: str
    label: str
    omen: str
    risk: str
    need: str
    meter: str
    solved_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Sign:
    id: str
    label: str
    oddity: str
    meaning: str
    points_to: str
    useful_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    works_for: set[str] = field(default_factory=set)
    useful: int = 2
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    id: str
    village: str
    holy_place: str
    image: str
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


def _r_problem_bites(world: World) -> list[str]:
    out: list[str] = []
    village = world.get("village")
    child = world.get("child")
    problem = world.facts.get("problem_cfg")
    if village.meters.get(problem.meter, 0.0) < THRESHOLD:
        return out
    sig = ("problem_bites", problem.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    village.memes["fear"] += 1
    out.append("__risk__")
    return out


def _r_mock_hurts(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["mocked"] < THRESHOLD:
        return out
    sig = ("mock_hurts", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["lonely"] += 1
    out.append("__lonely__")
    return out


def _r_solution_repairs(world: World) -> list[str]:
    out: list[str] = []
    village = world.get("village")
    if village.meters["repairing"] < THRESHOLD:
        return out
    problem = world.facts.get("problem_cfg")
    sig = ("solution_repairs", problem.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    village.meters[problem.meter] = 0.0
    village.meters["peace"] += 1
    village.memes["relief"] += 1
    out.append("__solved__")
    return out


CAUSAL_RULES = [
    Rule(name="problem_bites", tag="physical", apply=_r_problem_bites),
    Rule(name="mock_hurts", tag="social", apply=_r_mock_hurts),
    Rule(name="solution_repairs", tag="physical", apply=_r_solution_repairs),
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


PROBLEMS = {
    "drought": Problem(
        id="drought",
        label="drought",
        omen="the well showed only a dark ring of mud",
        risk="The jars were growing light, and even the goats nosed empty troughs.",
        need="find the hidden spring",
        meter="thirst",
        solved_image="Water sang again into the well, and every jar in the square caught a silver gleam.",
        tags={"water", "spring"},
    ),
    "flood": Problem(
        id="flood",
        label="flood",
        omen="the river was climbing the bank step by step",
        risk="If nothing changed, the water would crawl into the grain sheds by night.",
        need="open a safe side channel",
        meter="flooding",
        solved_image="The angry water bent into a new channel, and the grain sheds stood dry beneath the moon.",
        tags={"river", "water"},
    ),
    "fire": Problem(
        id="fire",
        label="hillside fire",
        omen="a red line of flame was nibbling through the dry grass",
        risk="Sparks were hopping toward the olive trees and the little clay roofs below.",
        need="smother the fire before it reaches the village",
        meter="burning",
        solved_image="Soon only a ribbon of smoke remained, and the hillside lay black and quiet instead of bright with danger.",
        tags={"fire", "smoke"},
    ),
}

SIGNS = {
    "frogs": Sign(
        id="frogs",
        label="the frogs",
        oddity="sat in a ring at noon and croaked toward a hill no one watched",
        meaning="frogs gather where hidden water still whispers under stone",
        points_to="the hidden spring beneath the hill",
        useful_for={"drought"},
        tags={"frogs", "water"},
    ),
    "ants": Sign(
        id="ants",
        label="the ants",
        oddity="carried their eggs in a hurried shining line uphill",
        meaning="ants flee the path that floodwater is about to take",
        points_to="the bank where a side channel should be cut",
        useful_for={"flood"},
        tags={"ants", "river"},
    ),
    "smoke_birds": Sign(
        id="smoke_birds",
        label="the birds",
        oddity="wheeled away from one patch of grass and would not land there",
        meaning="birds feel heat and smoke before people do",
        points_to="the narrow place where the fire can be beaten back",
        useful_for={"fire"},
        tags={"birds", "fire"},
    ),
}

TOOLS = {
    "spade": Tool(
        id="spade",
        label="spade",
        phrase="an old bronze spade",
        action="cut a narrow trench through the soft earth",
        works_for={"drought", "flood"},
        useful=3,
        tags={"digging", "earth"},
    ),
    "reed_flute": Tool(
        id="reed_flute",
        label="reed flute",
        phrase="a reed flute",
        action="call the goats together and lead them where their hooves could help stamp",
        works_for={"fire"},
        useful=2,
        tags={"music", "goats"},
    ),
    "wet_blankets": Tool(
        id="wet_blankets",
        label="wet blankets",
        phrase="wet wool blankets",
        action="beat down sparks and smother the low flames",
        works_for={"fire"},
        useful=3,
        tags={"water", "fire"},
    ),
    "baskets": Tool(
        id="baskets",
        label="baskets",
        phrase="woven baskets",
        action="carry away mud and stones until the hidden path was clear",
        works_for={"drought", "flood"},
        useful=2,
        tags={"carrying", "earth"},
    ),
}

SETTINGS = {
    "valley": Setting(
        id="valley",
        village="the Valley of Reeds",
        holy_place="the hill shrine",
        image="reed roofs, goat bells, and a white path between fig trees",
        tags={"valley"},
    ),
    "riverbend": Setting(
        id="riverbend",
        village="Riverbend",
        holy_place="the stone ford",
        image="round clay houses and a river that shone like hammered silver",
        tags={"river"},
    ),
    "sun_hill": Setting(
        id="sun_hill",
        village="Sun-Hill",
        holy_place="the old olive terrace",
        image="sun-baked terraces, dusty steps, and jars cooling in shadow",
        tags={"hill"},
    ),
}

GIRL_NAMES = ["Nila", "Tala", "Mira", "Suri", "Ira", "Luma"]
BOY_NAMES = ["Aren", "Tarin", "Ivo", "Belen", "Koro", "Sami"]
TRAITS = ["quiet", "curious", "patient", "watchful", "strange", "thoughtful"]


def sign_fits_problem(sign: Sign, problem: Problem) -> bool:
    return problem.id in sign.useful_for


def tool_helps_problem(tool: Tool, problem: Problem) -> bool:
    return problem.id in tool.works_for and tool.useful >= USEFUL_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for problem_id, problem in PROBLEMS.items():
            for sign_id, sign in SIGNS.items():
                for tool_id, tool in TOOLS.items():
                    if sign_fits_problem(sign, problem) and tool_helps_problem(tool, problem):
                        combos.append((setting_id, problem_id, sign_id, tool_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    problem: str
    sign: str
    tool: str
    child_name: str
    child_gender: str
    elder_type: str
    trait: str
    crowd_mood: str
    seed: Optional[int] = None


def introduce(world: World, setting: Setting, child: Entity, elder: Entity) -> None:
    world.say(
        f"In the days when people still listened for answers in wind, water, and hoofbeats, "
        f"there stood {setting.village}, a place of {setting.image}."
    )
    world.say(
        f"There lived a {child.traits[0]} child named {child.id}. Because {child.pronoun()} noticed "
        f"odd little things before anyone else did, the other children sometimes called "
        f"{child.pronoun('object')} a weirdo."
    )
    world.say(
        f"Only the village {elder.label_word}, who had seen many seasons, watched {child.id} with patient eyes."
    )


def trouble_rises(world: World, problem: Problem, child: Entity, crowd_line: str) -> None:
    village = world.get("village")
    village.meters[problem.meter] += 1
    child.memes["mocked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"One morning, {problem.omen}. {problem.risk}"
    )
    world.say(
        f'In the square, people muttered, "{crowd_line}" and no one knew how to {problem.need}.'
    )


def notice_sign(world: World, sign: Sign, child: Entity) -> None:
    child.memes["insight"] += 1
    world.say(
        f"But {child.id} saw that {sign.label} {sign.oddity}. To everyone else it looked silly. "
        f"To {child.id}, it looked like a message."
    )


def dismissal(world: World, child: Entity, elder: Entity, sign: Sign) -> None:
    child.memes["lonely"] += 1
    elder.memes["attention"] += 1
    world.say(
        f'"The weirdo is listening to {sign.label} again," some villagers said with nervous laughs.'
    )
    world.say(
        f'Yet the {elder.label_word} lifted a hand. "Sometimes the world speaks softly," '
        f'{elder.pronoun()} said. "Let the child finish."'
    )


def follow_sign(world: World, sign: Sign, problem: Problem, tool: Tool, child: Entity, elder: Entity, setting: Setting) -> None:
    world.say(
        f"{child.id} led the {elder.label_word} and a few doubtful villagers toward {setting.holy_place}, "
        f"because {child.pronoun()} believed that {sign.meaning}."
    )
    world.say(
        f"There, beneath stones and roots, {child.id} found {sign.points_to}."
    )
    world.say(
        f"Then {child.pronoun()} seized {tool.phrase} and showed everyone how to {tool.action}."
    )


def apply_solution(world: World, problem: Problem, child: Entity, elder: Entity) -> None:
    village = world.get("village")
    child.memes["hope"] += 1
    elder.memes["trust"] += 1
    village.meters["repairing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At first the grown-ups only copied {child.id} because the {elder.label_word} told them to. "
        f"But soon the work itself began to answer the danger."
    )
    world.say(problem.solved_image)


def resolution(world: World, child: Entity, elder: Entity, problem: Problem) -> None:
    village = world.get("village")
    child.memes["belonging"] += 1
    child.memes["lonely"] = 0.0
    village.memes["gratitude"] += 1
    world.say(
        f"The people of the village stood very still. The child they had called a weirdo had saved them "
        f"by noticing what they had laughed at."
    )
    world.say(
        f'The {elder.label_word} rested a hand on {child.id}\'s shoulder and said, '
        f'"A strange eye is not a foolish eye. Kindness listens before it judges."'
    )
    world.say(
        f"After that day, when {child.id} pointed at a ripple, a feather, or a trail of tiny feet, "
        f"people came to look beside {child.pronoun('object')} instead of laughing first."
    )


def tell(setting: Setting, problem: Problem, sign: Sign, tool: Tool,
         child_name: str = "Nila", child_gender: str = "girl",
         elder_type: str = "elder", trait: str = "watchful",
         crowd_mood: str = "We are lost") -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="hero",
        traits=[trait],
        attrs={"display_name": child_name},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type="elder",
        label=elder_type,
        phrase=f"the {elder_type}",
        role="helper",
    ))
    village = world.add(Entity(
        id="village",
        kind="thing",
        type="village",
        label=setting.village,
        phrase=setting.village,
    ))

    world.facts.update(
        setting=setting,
        problem_cfg=problem,
        sign_cfg=sign,
        tool_cfg=tool,
        child=child,
        elder=elder,
        village=village,
        crowd_mood=crowd_mood,
    )

    introduce(world, setting, child, elder)
    world.para()
    trouble_rises(world, problem, child, crowd_mood)
    notice_sign(world, sign, child)
    dismissal(world, child, elder, sign)
    world.para()
    follow_sign(world, sign, problem, tool, child, elder, setting)
    apply_solution(world, problem, child, elder)
    world.para()
    resolution(world, child, elder, problem)

    world.facts.update(
        solved=village.meters[problem.meter] < THRESHOLD and village.meters["peace"] >= THRESHOLD,
        mocked=child.memes["mocked"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "frogs": [(
        "Why might frogs help people find water?",
        "Frogs need damp places to live, so they often gather where water is close by. People who watch animals carefully can learn useful clues from them."
    )],
    "ants": [(
        "Why do ants move their eggs before a flood?",
        "Ants carry their eggs away from danger when the ground is about to get wet. They are tiny, but they are good at noticing changes before people do."
    )],
    "birds": [(
        "Why might birds fly away from a fire first?",
        "Birds can sense heat, smoke, and danger quickly. They often leave an unsafe place before people understand what is coming."
    )],
    "spring": [(
        "What is a spring?",
        "A spring is water that comes up from the ground. It can feed a stream or a well."
    )],
    "channel": [(
        "What does a channel do in water?",
        "A channel gives water a path to follow. If people guide water carefully, they can help keep fields and homes safe."
    )],
    "fire": [(
        "Why is a grass fire dangerous?",
        "Dry grass can burn fast, and sparks can jump to trees or houses. That is why people must act quickly and carefully around fire."
    )],
    "kindness": [(
        "Why is it wrong to call someone a weirdo to be mean?",
        "Calling someone names can hurt their feelings and make them feel alone. A kinder choice is to listen and learn what they are trying to say."
    )],
    "myth": [(
        "What makes a story feel like a myth?",
        "A myth often sounds old and wise, and it connects people to nature, signs, and big lessons. It usually ends by teaching why something matters."
    )],
}
KNOWLEDGE_ORDER = ["frogs", "ants", "birds", "spring", "channel", "fire", "kindness", "myth"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    problem = f["problem_cfg"]
    sign = f["sign_cfg"]
    tool = f["tool_cfg"]
    setting = f["setting"]
    return [
        f'Write a short myth-like story for a young child that includes the word "weirdo" and ends with a moral about kindness.',
        f"Tell a myth set in {setting.village} where a child mocked as a weirdo solves a {problem.label} by understanding what {sign.label} mean.",
        f"Write a story with a twist where everyone laughs at {child.attrs['display_name']}, but the strange clue leads to the right answer and {tool.label} helps save the village.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    problem = f["problem_cfg"]
    sign = f["sign_cfg"]
    tool = f["tool_cfg"]
    setting = f["setting"]
    name = child.attrs["display_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a child named {name} in {setting.village}. The village {elder.label_word} also matters because {elder.pronoun()} is the first grown-up to listen."
        ),
        (
            f"Why did people call {name} a weirdo?",
            f"They called {name} a weirdo because {child.pronoun()} noticed strange little signs that other people ignored. The name was unkind, and it made {name} feel lonely."
        ),
        (
            f"What problem was the village facing?",
            f"The village was facing a {problem.label}. {problem.risk}"
        ),
        (
            f"What unusual sign did {name} notice?",
            f"{name} noticed that {sign.label} {sign.oddity}. {name} believed this odd thing meant that {sign.meaning}."
        ),
        (
            f"How did {name} solve the problem?",
            f"{name} led people to {sign.points_to} and used {tool.phrase} to {tool.action}. The twist is that the clue everyone laughed at was the clue that saved them."
        ),
        (
            "What is the moral of the story?",
            "The moral is that people should listen kindly before judging someone as strange. A person who seems odd may still see something true and important."
        ),
    ]
    if f.get("solved"):
        qa.append((
            "How did the story end?",
            f"It ended with the danger gone and the village safe again. Afterward, people looked at {name} with respect instead of laughter."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sign = f["sign_cfg"]
    problem = f["problem_cfg"]
    tags: set[str] = {"kindness", "myth"}
    if sign.id == "frogs":
        tags |= {"frogs", "spring"}
    elif sign.id == "ants":
        tags |= {"ants", "channel"}
    elif sign.id == "smoke_birds":
        tags |= {"birds", "fire"}
    if problem.id == "fire":
        tags.add("fire")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="valley",
        problem="drought",
        sign="frogs",
        tool="spade",
        child_name="Nila",
        child_gender="girl",
        elder_type="elder",
        trait="watchful",
        crowd_mood="The gods have hidden the water from us",
    ),
    StoryParams(
        setting="riverbend",
        problem="flood",
        sign="ants",
        tool="baskets",
        child_name="Aren",
        child_gender="boy",
        elder_type="elder",
        trait="quiet",
        crowd_mood="The river will swallow our grain",
    ),
    StoryParams(
        setting="sun_hill",
        problem="fire",
        sign="smoke_birds",
        tool="wet_blankets",
        child_name="Mira",
        child_gender="girl",
        elder_type="elder",
        trait="curious",
        crowd_mood="The hillside is already burning toward us",
    ),
    StoryParams(
        setting="valley",
        problem="fire",
        sign="smoke_birds",
        tool="reed_flute",
        child_name="Tarin",
        child_gender="boy",
        elder_type="elder",
        trait="thoughtful",
        crowd_mood="The wind is carrying sparks down the slope",
    ),
]


def explain_rejection(problem: Problem, sign: Sign, tool: Tool) -> str:
    if not sign_fits_problem(sign, problem):
        return (
            f"(No story: {sign.label} do not give a useful clue for {problem.label}. "
            f"The sign must point to a believable answer for the village's danger.)"
        )
    if not tool_helps_problem(tool, problem):
        return (
            f"(No story: {tool.label} is not a sensible way to handle {problem.label}. "
            f"Pick a tool that could honestly help solve the problem.)"
        )
    return "(No story: this combination does not form a reasonable myth.)"


ASP_RULES = r"""
sign_fits(P, S) :- useful_for(S, P).
tool_helps(P, T) :- works_for(T, P), useful(T, U), useful_min(M), U >= M.
valid(Set, P, S, T) :- setting(Set), problem(P), sign(S), tool(T), sign_fits(P, S), tool_helps(P, T).

solved :- chosen_problem(P), chosen_sign(S), chosen_tool(T), sign_fits(P, S), tool_helps(P, T).
outcome(saved) :- solved.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for sid, sign in SIGNS.items():
        lines.append(asp.fact("sign", sid))
        for p in sorted(sign.useful_for):
            lines.append(asp.fact("useful_for", sid, p))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("useful", tid, tool.useful))
        for p in sorted(tool.works_for):
            lines.append(asp.fact("works_for", tid, p))
    lines.append(asp.fact("useful_min", USEFUL_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_sign", params.sign),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "saved" if sign_fits_problem(SIGNS[params.sign], PROBLEMS[params.problem]) and tool_helps_problem(TOOLS[params.tool], PROBLEMS[params.problem]) else "?"


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

    for params in CURATED:
        a = asp_outcome(params)
        p = outcome_of(params)
        if a != p:
            rc = 1
            print(f"MISMATCH in outcome for {params}: asp={a} python={p}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke-tested normal story generation.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Myth-like story world: a mocked child notices a sign, solves a village problem, and teaches kindness."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["elder"])
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
    if args.problem and args.sign and not sign_fits_problem(SIGNS[args.sign], PROBLEMS[args.problem]):
        raise StoryError(explain_rejection(PROBLEMS[args.problem], SIGNS[args.sign], TOOLS[args.tool] if args.tool else next(iter(TOOLS.values()))))
    if args.problem and args.tool and not tool_helps_problem(TOOLS[args.tool], PROBLEMS[args.problem]):
        raise StoryError(explain_rejection(PROBLEMS[args.problem], SIGNS[args.sign] if args.sign else next(iter(SIGNS.values())), TOOLS[args.tool]))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.problem is None or c[1] == args.problem)
        and (args.sign is None or c[2] == args.sign)
        and (args.tool is None or c[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, problem_id, sign_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    elder_type = args.elder or "elder"
    trait = rng.choice(TRAITS)
    crowd_mood = {
        "drought": "The gods have hidden the water from us",
        "flood": "The river will swallow our grain",
        "fire": "The hillside flame is hunting our homes",
    }[problem_id]
    return StoryParams(
        setting=setting_id,
        problem=problem_id,
        sign=sign_id,
        tool=tool_id,
        child_name=name,
        child_gender=gender,
        elder_type=elder_type,
        trait=trait,
        crowd_mood=crowd_mood,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.sign not in SIGNS:
        raise StoryError(f"(Unknown sign: {params.sign})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    problem = PROBLEMS[params.problem]
    sign = SIGNS[params.sign]
    tool = TOOLS[params.tool]
    if not sign_fits_problem(sign, problem) or not tool_helps_problem(tool, problem):
        raise StoryError(explain_rejection(problem, sign, tool))

    world = tell(
        setting=SETTINGS[params.setting],
        problem=problem,
        sign=sign,
        tool=tool,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        trait=params.trait,
        crowd_mood=params.crowd_mood,
    )

    story_text = world.render().replace("child named child", f"child named {params.child_name}")
    story_text = story_text.replace(" child saved", f" {params.child_name} saved")
    story_text = story_text.replace("child's", f"{params.child_name}'s")
    story_text = story_text.replace("the child", params.child_name, 1)

    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, problem, sign, tool) combos:\n")
        for setting_id, problem_id, sign_id, tool_id in combos:
            print(f"  {setting_id:10} {problem_id:8} {sign_id:12} {tool_id}")
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
            header = f"### {p.child_name}: {p.problem} in {p.setting} ({p.sign}, {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
