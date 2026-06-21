#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/division_jujube_external_problem_solving_superhero_story.py
===========================================================================================

A standalone storyworld for a tiny superhero tale about a child hero who uses
careful problem solving to handle a tricky external problem during a number
division lesson, with a jujube sweet as the memorable object in the middle.

The world is deliberately small:
- a hero, a helper, a teacher, and a problem object
- a lost jujube that rolls into an external crack or vent
- a division puzzle that must be solved to reach equal shares
- a calm, clever rescue that turns the situation around

The story is generated from simulated world state, not from fixed prose.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
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
        return self.label or self.type
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.get("problem").meters["solved"] < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("relief", "social", _r_relief)]


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
        for s in produced:
            world.say(s)
    return produced


@dataclass
class Setting:
    id: str
    scene: str
    place: str
    external: str
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


@dataclass
class Problem:
    id: str
    label: str
    clue: str
    kind: str
    urgency: int
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


@dataclass
class DivisionChallenge:
    id: str
    total: int
    groups: int
    share_name: str
    phrasing: str
    solve_text: str
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
class Tool:
    id: str
    label: str
    use_text: str
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


class StoryWorldError(StoryError):
    pass


def problem_risky(problem: Problem) -> bool:
    return problem.kind == "external"


def division_possible(challenge: DivisionChallenge) -> bool:
    return challenge.total >= challenge.groups and challenge.total % challenge.groups == 0


def good_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.id != "distract"]


def solve_problem(world: World, hero: Entity, helper: Entity, problem: Problem,
                  challenge: DivisionChallenge, tool: Tool) -> None:
    world.get("problem").meters["solved"] += 1
    world.get("problem").meters["calmed"] += 1
    hero.memes["focus"] += 1
    helper.memes["focus"] += 1
    world.say(
        f"{hero.id} and {helper.id} used {tool.label} to {tool.use_text}, while "
        f"working out the division puzzle {challenge.phrasing}."
    )
    world.say(
        f"{problem.label.capitalize()} stopped being a problem, because the external "
        f"trouble was handled step by step."
    )
    propagate(world, narrate=False)


def reveal_solution(world: World, hero: Entity, helper: Entity,
                    challenge: DivisionChallenge) -> None:
    share = challenge.total // challenge.groups
    world.say(
        f"{helper.id} pointed at the numbers and said there were {challenge.total} "
        f"pieces, so dividing them into {challenge.groups} groups meant {share} "
        f"in each group."
    )
    world.say(
        f"{hero.id} nodded, smiled, and called it the answer to the division puzzle."
    )


def ending(world: World, hero: Entity, helper: Entity, sweet: Entity) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"In the end, the jujube was safe in {hero.id}'s hand, the numbers were "
        f"sorted, and the two heroes stood taller than the external trouble."
    )
    world.say(
        f"They shared the sweet like a victory medal, and the room felt calm again."
    )


def tell(setting: Setting, problem: Problem, challenge: DivisionChallenge, tool: Tool,
         hero_name: str, hero_gender: str, helper_name: str, helper_gender: str,
         teacher_name: str, teacher_gender: str, sweet_name: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    teacher = world.add(Entity(id=teacher_name, kind="character", type=teacher_gender, role="teacher"))
    sweet = world.add(Entity(id="jujube", kind="thing", type="thing", label=sweet_name))
    prob = world.add(Entity(id="problem", kind="thing", type=problem.kind, label=problem.label))
    world.facts["setting"] = setting
    world.facts["problem_cfg"] = problem
    world.facts["challenge"] = challenge
    world.facts["tool"] = tool
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["teacher"] = teacher
    world.facts["sweet"] = sweet

    world.say(
        f"On a bright afternoon, {hero.id} and {helper.id} trained in {setting.scene}. "
        f"{teacher.id} had set up a division puzzle on the table."
    )
    world.say(
        f"Near the window sat a shiny {sweet.label}, and {problem.clue}."
    )

    world.para()
    world.say(
        f"{hero.id} reached for the jujube, but the sweet slipped away and rolled "
        f"toward an {setting.external} opening."
    )
    world.say(
        f'"We need to solve this fast," {helper.id} said, because the external problem '
        f'was getting worse.'
    )

    world.para()
    reveal_solution(world, hero, helper, challenge)
    solve_problem(world, hero, helper, problem, challenge, tool)

    world.para()
    ending(world, hero, helper, sweet)

    world.facts["outcome"] = "solved"
    world.facts["sweet"] = sweet
    world.facts["problem"] = prob
    return world


SETTINGS = {
    "classroom": Setting(id="classroom", scene="the math corner", place="classroom", external="door crack"),
    "hall": Setting(id="hall", scene="the hallway station", place="hall", external="floor vent"),
    "lab": Setting(id="lab", scene="the practice lab", place="lab", external="wall gap"),
}

PROBLEMS = {
    "wind": Problem(id="wind", label="the windy draft", clue="a cold draft was tugging papers toward the gap", kind="external", urgency=2),
    "spill": Problem(id="spill", label="the spill", clue="water had spread near the opening and made the floor slippery", kind="external", urgency=3),
    "noise": Problem(id="noise", label="the noise outside", clue="a loud rumble from outside was shaking the little shelf", kind="external", urgency=1),
}

CHALLENGES = {
    "two_by_two": DivisionChallenge(id="two_by_two", total=4, groups=2, share_name="two equal piles",
                                    phrasing="where 4 cards must be split into 2 equal piles",
                                    solve_text="4 divided by 2 makes 2", tags={"division"}),
    "three_shares": DivisionChallenge(id="three_shares", total=6, groups=3, share_name="three equal shares",
                                      phrasing="where 6 stickers must be split into 3 equal shares",
                                      solve_text="6 divided by 3 makes 2", tags={"division"}),
    "four_shares": DivisionChallenge(id="four_shares", total=8, groups=4, share_name="four equal groups",
                                     phrasing="where 8 shells must be split into 4 equal groups",
                                     solve_text="8 divided by 4 makes 2", tags={"division"}),
}

TOOLS = {
    "magnifier": Tool(id="magnifier", label="a magnifying glass", use_text="spot the tiny clue"),
    "marker": Tool(id="marker", label="a bright marker", use_text="mark the groups clearly"),
    "rope": Tool(id="rope", label="a short rope", use_text="keep the safe path open"),
    "distract": Tool(id="distract", label="a loud toy", use_text="make noise", tags={"bad"}),
}

HERO_NAMES = ["Nova", "Ray", "Mika", "Jett", "Aria", "Zane", "Pippa", "Tari"]
HELPER_NAMES = ["Bolt", "Luna", "Comet", "Spark", "Echo", "Quill"]
TEACHER_NAMES = ["Ms. Vale", "Coach Finn", "Dr. Mira", "Captain Reed"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    challenge: str
    tool: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    teacher_name: str
    teacher_gender: str
    sweet_name: str = "jujube"
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


CURATED = [
    StoryParams(
        setting="classroom",
        problem="wind",
        challenge="two_by_two",
        tool="magnifier",
        hero_name="Nova",
        hero_gender="girl",
        helper_name="Bolt",
        helper_gender="boy",
        teacher_name="Ms. Vale",
        teacher_gender="woman",
        sweet_name="jujube",
    ),
    StoryParams(
        setting="hall",
        problem="spill",
        challenge="three_shares",
        tool="marker",
        hero_name="Ray",
        hero_gender="boy",
        helper_name="Luna",
        helper_gender="girl",
        teacher_name="Coach Finn",
        teacher_gender="man",
        sweet_name="jujube",
    ),
    StoryParams(
        setting="lab",
        problem="noise",
        challenge="four_shares",
        tool="rope",
        hero_name="Mika",
        hero_gender="girl",
        helper_name="Echo",
        helper_gender="boy",
        teacher_name="Dr. Mira",
        teacher_gender="woman",
        sweet_name="jujube",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for c in CHALLENGES:
                if problem_risky(PROBLEMS[p]) and division_possible(CHALLENGES[c]):
                    combos.append((s, p, c))
    return combos


def explain_rejection(problem: Problem, challenge: DivisionChallenge, tool: Tool) -> str:
    if problem.kind != "external":
        return "(No story: the problem is not external enough for this tiny superhero tale.)"
    if not division_possible(challenge):
        return "(No story: the division puzzle does not split evenly, so the heroes cannot solve it cleanly.)"
    if tool.id == "distract":
        return "(No story: this tool is too noisy and does not help the heroes solve the problem.)"
    return "(No story: the requested combination is not reasonable.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny superhero storyworld with division, jujube, and an external problem."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--teacher-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.tool == "distract":
        raise StoryError("(No story: the chosen tool does not help solve the problem.)")
    if args.problem and args.challenge:
        if not (problem_risky(PROBLEMS[args.problem]) and division_possible(CHALLENGES[args.challenge])):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], CHALLENGES[args.challenge], TOOLS.get(args.tool or "magnifier", TOOLS["magnifier"])))
    combos = [c for c in valid_combos()
              if args.setting in (None, c[0])
              and args.problem in (None, c[1])
              and args.challenge in (None, c[2])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, challenge = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(k for k in TOOLS if k != "distract"))
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if hero_gender == "girl" else "girl"
    return StoryParams(
        setting=setting,
        problem=problem,
        challenge=challenge,
        tool=tool,
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        hero_gender=hero_gender,
        helper_name=args.helper_name or rng.choice(HELPER_NAMES),
        helper_gender=helper_gender,
        teacher_name=args.teacher_name or rng.choice(TEACHER_NAMES),
        teacher_gender=rng.choice(["woman", "man"]),
        sweet_name="jujube",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story for a young child that includes the words division, jujube, and external.",
        f"Tell a story where {f['hero'].id} and {f['helper'].id} solve a division puzzle while a jujube causes an external problem.",
        f"Write a gentle superhero story that ends with a smart solution and a calm victory image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    teacher = f["teacher"]
    challenge = f["challenge"]
    problem = f["problem_cfg"]
    qa = [
        ("Who are the heroes?",
         f"The heroes are {hero.id} and {helper.id}. They work together like a small superhero team."),
        ("What problem did they face?",
         f"They had an external problem: {problem.label}. It made the scene harder until they solved it."),
        ("What was the division puzzle about?",
         f"It was {challenge.phrasing}. The answer showed how to split the pieces evenly."),
        ("How did they solve the problem?",
         f"They used careful problem solving, followed the division clue, and used a helpful tool instead of panicking."),
    ]
    qa.append((
        "Why did the story feel like a superhero story?",
        f"{hero.id}, {helper.id}, and {teacher.id} acted bravely and calmly. They used their minds as the real superpower."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does division mean?",
         "Division means splitting one amount into equal groups. It helps you share things fairly."),
        ("What is a jujube?",
         "A jujube is a small chewy sweet or fruit snack. In a story, it can be the little thing everyone wants to keep safe."),
        ("What does external mean?",
         "External means coming from outside. An external problem is something outside the hero that causes trouble."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
external_problem(P) :- problem(P), kind(P, external).
even_division(C) :- challenge(C), total(C, T), groups(C, G), 0 = T \ G.
valid(S, P, C) :- setting(S), external_problem(P), even_division(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("kind", pid, p.kind))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("total", cid, c.total))
        lines.append(asp.fact("groups", cid, c.groups))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH between clingo and valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: ordinary story generation smoke test passed.")
    except Exception as err:
        print(f"FAIL: smoke test crashed: {err}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.challenge not in CHALLENGES or params.tool not in TOOLS:
        raise StoryError("(Invalid parameters for this storyworld.)")
    if params.tool == "distract":
        raise StoryError("(No story: the chosen tool does not help solve the problem.)")
    world = tell(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        CHALLENGES[params.challenge],
        TOOLS[params.tool],
        params.hero_name,
        params.hero_gender,
        params.helper_name,
        params.helper_gender,
        params.teacher_name,
        params.teacher_gender,
        params.sweet_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, problem, challenge) combos:")
        for s, p, c in combos:
            print(f"  {s:10} {p:10} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
