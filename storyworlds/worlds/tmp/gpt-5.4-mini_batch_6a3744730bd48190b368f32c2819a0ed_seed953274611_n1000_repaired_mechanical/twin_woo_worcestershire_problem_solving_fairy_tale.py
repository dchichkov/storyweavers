#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/twin_woo_worcestershire_problem_solving_fairy_tale.py
====================================================================================

A small fairy-tale storyworld about twin siblings, a missing supper sauce, and a
kind problem-solving turn. The seed words are woven into the world: twin, woo,
and worcestershire.

The story premise:
- In a little castle kitchen, two twin children want to help with supper.
- A royal sauce jar goes missing or gets stuck in an awkward place.
- The children try one mistaken idea, then solve the problem with a sensible tool.
- The ending proves the change: supper is saved, the twins are proud, and the
  kitchen becomes calm and bright again.

The world is intentionally small, state-driven, and child-facing.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman"}
        male = {"boy", "father", "king", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "king": "king", "queen": "queen"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    mood: str
    hazards: set[str] = field(default_factory=set)
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
    label: str
    need: str
    wrong_fix: str
    clue: str
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
    action: str
    power: int
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


def _r_worry(world: World) -> list[str]:
    out = []
    castle = world.entities.get("castle")
    for key in ("twina", "twinb"):
        ent = world.entities[key]
        if ent.memes["worry"] >= THRESHOLD:
            sig = ("worry", key)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            if castle:
                castle.meters["tension"] += 1
            out.append("")
    return out


def _r_solution(world: World) -> list[str]:
    out = []
    if world.facts.get("problem_solved") and world.get("queen").memes["relief"] < THRESHOLD:
        world.get("queen").memes["relief"] += 1
        out.append("")
    return out


RULES = [Rule("worry", _r_worry), Rule("solution", _r_solution)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend([s for s in sents if s])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(problem: Problem, tool: Tool) -> bool:
    return problem.id in {"sauce_stuck", "sauce_spill"} and tool.power >= 1


def solveable(problem: Problem, tool: Tool) -> bool:
    return problem.id == "sauce_stuck" and tool.power >= 2


def predict(world: World, problem_id: str, tool_id: str) -> dict:
    sim = world.copy()
    _do_problem(sim, sim.get(problem_id), narrate=False)
    _use_tool(sim, sim.get(tool_id), narrate=False)
    return {"solved": sim.facts.get("problem_solved", False)}


def _do_problem(world: World, problem: Entity, narrate: bool = True) -> None:
    problem.meters["stuck"] += 1
    world.get("twinb").memes["worry"] += 1
    world.get("twina").memes["worry"] += 1
    propagate(world, narrate=narrate)


def _use_tool(world: World, tool: Entity, narrate: bool = True) -> None:
    if tool.id == "wooden_spoon":
        world.get("sauce_jar").meters["reachable"] += 1
        world.facts["problem_solved"] = True
        if narrate:
            world.say("")


def tell(place: Place, problem: Problem, tool: Tool,
         twin_a: str = "Mina", twin_b: str = "Lina",
         parent: str = "queen", helper: str = "knight") -> World:
    world = World()
    a = world.add(Entity(id="twina", kind="character", type="girl", label=twin_a, role="twin", traits=["bold"]))
    b = world.add(Entity(id="twinb", kind="character", type="girl", label=twin_b, role="twin", traits=["gentle"]))
    q = world.add(Entity(id="queen", kind="character", type=parent, label="the queen", role="parent"))
    castle = world.add(Entity(id="castle", kind="place", type="place", label=place.label))
    sauce = world.add(Entity(id="sauce_jar", kind="thing", type="thing", label=problem.label))
    spoon = world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label))
    world.facts["place"] = place
    world.facts["problem"] = problem
    world.facts["tool"] = tool
    world.facts["helper"] = helper
    world.facts["castle"] = castle
    world.facts["sauce"] = sauce
    world.facts["spoon"] = spoon

    world.say(
        f"Once in a little castle kitchen, the twin sisters {a.label} and {b.label} tiptoed by the warm stove. "
        f"The hall smelled of honey bread and a pot of supper waited below the window."
    )
    world.say(
        f"The queen asked them to help with the supper, and the twins were glad to do it. "
        f"They wanted everything to be neat and bright."
    )
    world.para()
    world.say(
        f"But then the {problem.label} went missing behind a tall jar and the supper needed a touch of worcestershire. "
        f"{b.label} peered up and said, \"We need the sauce to woo the stew into tasting right.\""
    )
    world.say(
        f"{a.label} tried a wrong fix first and reached for a spoon that was too short, but the jar stayed stuck. "
        f"The queen frowned a little, because the stew still tasted plain."
    )
    world.para()
    if solveable(problem, tool):
        _do_problem(world, sauce, narrate=False)
        world.say(
            f"Then the twins remembered the wooden spoon. {a.label} hooked the jar gently, {b.label} steadied the bowl, "
            f"and together they pulled the worcestershire free."
        )
        world.say(
            f"The queen laughed softly. \"Well done, my twins,\" {q.label_word.capitalize()} said. "
            f"They stirred the sauce in, and the stew shone rich and brown."
        )
        world.say(
            f"At supper, everyone smiled. The twins sat straighter in their chairs, and the kitchen felt calm again, "
            f"as if the little problem had never been big at all."
        )
        world.facts["problem_solved"] = True
    else:
        world.say(
            f"The {problem.label} would not budge, and the twins had to call for the knight in the end. "
            f"The knight used a long hook, and the sauce was saved after all."
        )
        world.facts["problem_solved"] = True

    world.facts.update(solved=True)
    return world


THEMES = {
    "castle": Place(id="castle", label="castle kitchen", mood="warm", hazards={"stuck"}, tags={"castle", "kitchen"}),
    "tower": Place(id="tower", label="tower pantry", mood="quiet", hazards={"stuck"}, tags={"tower", "pantry"}),
}

PROBLEMS = {
    "sauce_stuck": Problem(
        id="sauce_stuck",
        label="worcestershire",
        need="the stew needed a splash of worcestershire",
        wrong_fix="a spoon that was too short",
        clue="a tall jar hid behind the sugar",
        tags={"worcestershire", "sauce", "problem_solving"},
    ),
    "ribbon_tied": Problem(
        id="ribbon_tied",
        label="ribbon",
        need="the ribbon tied the treasure box shut",
        wrong_fix="pulling with bare hands",
        clue="the knot would not loosen",
        tags={"problem_solving"},
    ),
}

TOOLS = {
    "wooden_spoon": Tool(id="wooden_spoon", label="wooden spoon", action="hook", power=2, tags={"tool", "sauce"}),
    "long_hook": Tool(id="long_hook", label="long hook", action="reach", power=3, tags={"tool"}),
}

@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    twin_a: str = "Mina"
    twin_b: str = "Lina"
    parent: str = "queen"
    helper: str = "knight"
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
        place="castle",
        problem="sauce_stuck",
        tool="wooden_spoon",
        twin_a="Mina",
        twin_b="Lina",
        parent="queen",
        helper="knight",
        seed=None,
    ),
    StoryParams(
        place="tower",
        problem="sauce_stuck",
        tool="wooden_spoon",
        twin_a="Tess",
        twin_b="Nell",
        parent="queen",
        helper="knight",
        seed=None,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id in THEMES:
        for prob_id, prob in PROBLEMS.items():
            for tool_id, tool in TOOLS.items():
                if reasonableness_gate(prob, tool) and solveable(prob, tool):
                    combos.append((place_id, prob_id, tool_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    p = world.facts["problem"]
    return [
        f'Write a fairy tale about twin sisters who try to solve a {p.label} problem in a castle kitchen.',
        f"Tell a child-friendly story that includes the words twin, woo, and worcestershire, and shows the twins solving a kitchen problem.",
        f"Write a gentle problem-solving story where a stuck worcestershire jar is freed by clever twins.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    p = world.facts["problem"]
    a = world.get("twina")
    b = world.get("twinb")
    return [
        ("Who is the story about?",
         f"It is about twins {a.label} and {b.label}, who help in a castle kitchen."),
        ("What problem did they have?",
         f"They needed the worcestershire for supper, but the jar was stuck behind other things."),
        ("How did they solve it?",
         f"They used a wooden spoon to hook the jar free. They worked together, so the sauce could woo the stew and make supper taste right."),
        ("Why was the ending happy?",
         f"The twins solved the problem without making a bigger mess, and the queen could serve supper at once."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a twin?",
         "Twins are two children born at about the same time. They often look alike and can work together very well."),
        ("What is worcestershire?",
         "Worcestershire is a savory sauce that grown-ups sometimes add to soups, stews, or other cooked food."),
        ("What does it mean to solve a problem?",
         "To solve a problem means to find a good answer or fix so things can go right again."),
    ]


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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Pr, T) :- place(P), problem(Pr), tool(T), problem_needs(Pr, N), tool_power(T, Pow), Pow >= 2.
solved :- chosen_problem(Pr), chosen_tool(T), tool_power(T, Pow), Pow >= 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in THEMES:
        lines.append(asp.fact("place", pid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_needs", pid, p.need))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_power", tid, t.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    ok = set(asp_valid_combos()) == set(valid_combos())
    if not ok:
        print("MISMATCH in valid combos")
        return 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("SMOKE TEST FAILED: empty story")
            return 1
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP matches Python and generate() smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about twins and a problem to solve.")
    ap.add_argument("--place", choices=THEMES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--name2")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, tool = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        problem=problem,
        tool=tool,
        twin_a=args.name or rng.choice(["Mina", "Tess", "Lia", "Nia", "Rose"]),
        twin_b=args.name2 or rng.choice(["Lina", "Nell", "Pip", "Wren", "June"]),
        parent="queen",
        helper="knight",
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in THEMES or params.problem not in PROBLEMS or params.tool not in TOOLS:
        raise StoryError("Invalid parameters.")
    world = tell(THEMES[params.place], PROBLEMS[params.problem], TOOLS[params.tool],
                 twin_a=params.twin_a, twin_b=params.twin_b, parent=params.parent, helper=params.helper)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("", "#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
