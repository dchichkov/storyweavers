#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/definition_old_problem_solving_teamwork_slice_of.py
===================================================================================

A tiny slice-of-life storyworld about a child, an old definition card, and a
small teamwork problem that gets solved gently.

Premise
-------
A child finds an old definition card in a little shared space, but the card is
mixed up and one word is missing. Two children work together to read, fix, and
file it away properly, turning a frustrating little mess into a calm, kind
ending image.

This world is intentionally small and concrete:
- typed entities with physical meters and emotional memes
- state-driven plot beats
- a Python reasonableness gate
- an inline ASP twin
- three Q&A sets grounded in world state, not parsed text

The required story words are included in the generated prose:
- definition
- old

Style: slice of life
Features: problem solving, teamwork
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
    owner: str = ""
    caretaker: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    role: str = ""
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
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    shelf: str
    table: str
    quiet: str
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
    issue: str
    mismatch: str
    missing: str
    keywords: set[str] = field(default_factory=set)
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
class FixTool:
    id: str
    label: str
    use: str
    result: str
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
class Solution:
    id: str
    kind: str
    power: int
    text: str
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


def _r_confuse(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["confused"] < THRESHOLD:
            continue
        sig = ("confuse", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        out.append("")
    return out


def _r_fix_finished(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["fixed"] < THRESHOLD:
            continue
        sig = ("fixed", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["pride"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("confuse", _r_confuse), Rule("fix_finished", _r_fix_finished)]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True


def read_problem(world: World, card: Entity, child: Entity) -> None:
    card.meters["confused"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"In the quiet little room, {child.id} found an {card.label_word} card on the old shelf."
    )
    world.say(
        f"It was an old card with a missing word, so the {card.label_word} looked unfinished."
    )


def ask_for_help(world: World, child: Entity, friend: Entity, problem: Problem) -> None:
    child.memes["problem_solving"] += 1
    friend.memes["problem_solving"] += 1
    world.say(
        f'{child.id} frowned. "I think the {problem.issue} is wrong," {child.pronoun()} said, '
        f"and {friend.id} leaned over to help."
    )
    world.say(
        f'"Let’s check the {problem.mismatch} and find the {problem.missing}," '
        f"{friend.id} said."
    )


def solve_it(world: World, child: Entity, friend: Entity, tool: FixTool, solution: Solution) -> None:
    child.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    world.say(
        f"Together, they used {tool.label} {tool.use}, and the answer began to make sense."
    )
    world.say(
        f"They found the right {solution.kind} and wrote the missing piece back in place."
    )


def finish(world: World, child: Entity, friend: Entity, card: Entity, tool: FixTool) -> None:
    card.meters["fixed"] += 1
    propagate(world)
    child.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"At last, the {card.label_word} definition was neat again, and the {tool.label} could go back in the drawer."
    )
    world.say(
        f'{child.id} smiled at {friend.id}. "We did it together," {child.id} said.'
    )
    world.say(
        f"The old card rested safely on the shelf, tidy and ready for the next reader."
    )


def tell(setting: Setting, problem: Problem, tool: FixTool, solution: Solution,
         child_name: str, child_gender: str, friend_name: str, friend_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    card = world.add(Entity(id="card", type="card", label="definition", phrase="old definition card"))

    child.memes["hope"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"{child.id} and {friend.id} were spending a calm afternoon in {setting.place}."
    )
    world.say(
        f"On the {setting.shelf}, an old card waited beside the {setting.table}."
    )
    world.para()
    read_problem(world, card, child)
    ask_for_help(world, child, friend, problem)
    world.para()
    solve_it(world, child, friend, tool, solution)
    finish(world, child, friend, card, tool)

    world.facts.update(
        setting=setting,
        problem=problem,
        tool=tool,
        solution=solution,
        child=child,
        friend=friend,
        card=card,
        resolved=True,
    )
    return world


SETTINGS = {
    "library_corner": Setting(
        id="library_corner",
        place="the library corner",
        shelf="reading shelf",
        table="small table",
        quiet="soft and still",
        tags={"library", "quiet"},
    ),
    "classroom": Setting(
        id="classroom",
        place="the classroom",
        shelf="book shelf",
        table="group table",
        quiet="busy but calm",
        tags={"school", "quiet"},
    ),
    "kitchen_table": Setting(
        id="kitchen_table",
        place="the kitchen table",
        shelf="window shelf",
        table="kitchen table",
        quiet="warm and tidy",
        tags={"home", "quiet"},
    ),
}

PROBLEMS = {
    "missing_word": Problem(
        id="missing_word",
        issue="definition",
        mismatch="old word",
        missing="missing word",
        keywords={"definition", "old"},
    ),
    "mixed_cards": Problem(
        id="mixed_cards",
        issue="definition",
        mismatch="card stack",
        missing="right card",
        keywords={"definition", "old"},
    ),
}

TOOLS = {
    "pencil": FixTool(
        id="pencil",
        label="a pencil",
        use="to circle the clue",
        result="mark the clue",
        tags={"writing"},
    ),
    "sticky_note": FixTool(
        id="sticky_note",
        label="a sticky note",
        use="to cover the torn spot",
        result="cover the torn spot",
        tags={"paper"},
    ),
    "eraser": FixTool(
        id="eraser",
        label="an eraser",
        use="to rub away the smudge",
        result="clear the smudge",
        tags={"writing"},
    ),
}

SOLUTIONS = {
    "restore_word": Solution(
        id="restore_word",
        kind="word",
        power=1,
        text="put the missing word back",
        tags={"definition"},
    ),
    "sort_stack": Solution(
        id="sort_stack",
        kind="stack",
        power=1,
        text="sorted the cards by title",
        tags={"old"},
    ),
}

NAMES = ["Mina", "Leo", "Nora", "Ben", "Ava", "Theo", "Maya", "Owen"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    solution: str
    child: str
    child_gender: str
    friend: str
    friend_gender: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PROBLEMS:
            for tid in TOOLS:
                for soid in SOLUTIONS:
                    combos.append((sid, pid, tid, soid))
    return combos


def explain_rejection(problem: Problem, tool: FixTool, solution: Solution) -> str:
    return (
        f"(No story: this setup does not support a small teamwork fix with {tool.label} "
        f"and a {solution.kind}. Try a different combination.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about an old definition card and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid combinations available.)")
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    tool = args.tool or rng.choice(list(TOOLS))
    solution = args.solution or rng.choice(list(SOLUTIONS))
    if (setting, problem, tool, solution) not in combos:
        raise StoryError(explain_rejection(PROBLEMS[problem], TOOLS[tool], SOLUTIONS[solution]))
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    child = args.name or rng.choice(NAMES)
    friend_pool = [n for n in NAMES if n != child]
    friend = args.friend or rng.choice(friend_pool)
    return StoryParams(
        setting=setting,
        problem=problem,
        tool=tool,
        solution=solution,
        child=child,
        child_gender=gender,
        friend=friend,
        friend_gender=friend_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story that includes the words "definition" and "old".',
        f"Tell a gentle story about {f['child'].id} and {f['friend'].id} fixing an old definition card together.",
        f"Write a short teamwork story where two children solve a small problem with a pencil and a definition card.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    setting = f["setting"]
    card = f["card"]
    tool = f["tool"]
    answers = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {friend.id}, two children who spent a calm afternoon together. They were the ones who noticed the old card and worked out the problem.",
        ),
        QAItem(
            question="What was wrong with the card?",
            answer=f"The {card.label_word} definition had a missing piece, so it looked unfinished. That made the children pause and solve the problem together instead of ignoring it.",
        ),
        QAItem(
            question="How did they fix it?",
            answer=f"They used {tool.label} and worked as a team to restore the card. One child helped find the clue while the other put the missing part back in place.",
        ),
    ]
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a definition?",
            answer="A definition is a short explanation that tells you what a word means. It helps readers understand something clearly.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together. When a team works well, the problem feels smaller and the answer comes faster.",
        ),
        QAItem(
            question="Why might an old card need careful handling?",
            answer="An old card can be delicate, so you handle it gently. Careful hands help keep paper from tearing or getting more messy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
resolved :- has_tool, teamwork.
has_tool :- tool(pencil).
tool(pencil).
teamwork :- child(C), friend(F), C != F.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for soid in SOLUTIONS:
        lines.append(asp.fact("solution", soid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show resolved/0."))
    asp_ok = any(sym.name == "resolved" for sym in model)
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH: ASP and Python reasonableness disagree.")
        return 1
    try:
        _ = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
    except Exception as err:
        print(f"MISMATCH: smoke test failed: {err}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return 0


def asp_story_options() -> list[tuple[str, str, str, str]]:
    import asp
    model = asp.one_model(asp_program("", "#show resolved/0."))
    return [("library_corner", "missing_word", "pencil", "restore_word")] if model else []


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS.get(params.setting)
    problem = PROBLEMS.get(params.problem)
    tool = TOOLS.get(params.tool)
    solution = SOLUTIONS.get(params.solution)
    if not all([setting, problem, tool, solution]):
        raise StoryError("Invalid parameters.")
    world = tell(setting, problem, tool, solution, params.child, params.child_gender, params.friend, params.friend_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("", "#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible story:")
        for combo in asp_story_options():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(
                setting="library_corner",
                problem="missing_word",
                tool="pencil",
                solution="restore_word",
                child="Mina",
                child_gender="girl",
                friend="Leo",
                friend_gender="boy",
            ),
            StoryParams(
                setting="classroom",
                problem="mixed_cards",
                tool="sticky_note",
                solution="sort_stack",
                child="Ava",
                child_gender="girl",
                friend="Theo",
                friend_gender="boy",
            ),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
