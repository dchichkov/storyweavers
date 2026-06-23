#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T034914Z_seed1855084837_n10/avalanche_problem_solving_teamwork_comedy.py
===============================================================================================================

A small standalone story world about a comic avalanche problem that a team
solves together with planning, tools, and teamwork.

The seed premise is simple: a cheerful mountain day turns silly when an
avalanche blocks a trail, and the people must work together to solve the
problem without turning the story into a frozen template.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    team: str = ""
    owner: Optional[str] = None
    carries: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    scene: str
    risky: set[str] = field(default_factory=set)
    supports: set[str] = field(default_factory=set)
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
    danger: str
    mess: str
    blocked_by: str
    fix_hint: str
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
    phrase: str
    use: str
    helps: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.history: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.blocked: bool = False
        self.resolved: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.history = list(self.history)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.blocked = self.blocked
        clone.resolved = self.resolved
        return clone


@dataclass
class StoryParams:
    place: str
    problem: str
    team_size: int
    leader: str
    helper: str
    tool: str
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


PLACES = {
    "mountain_trail": Place(
        id="mountain_trail",
        label="the mountain trail",
        scene="a bright mountain trail with a crooked sign and a snack bench",
        risky={"avalanche"},
        supports={"avalanche"},
    ),
    "ski_hut": Place(
        id="ski_hut",
        label="the ski hut",
        scene="a cozy ski hut with boots, maps, and a window full of snow",
        risky={"avalanche"},
        supports={"avalanche"},
    ),
}

PROBLEMS = {
    "avalanche": Problem(
        id="avalanche",
        label="avalanche",
        danger="a snowy rumble can bury the path",
        mess="snow all over the trail",
        blocked_by="a deep snowbank",
        fix_hint="clear a safe route and make noise together",
        tags={"avalanche", "snow", "teamwork", "problem_solving", "mountain"},
    ),
}

TOOLS = {
    "shovels": Tool(
        id="shovels",
        label="shovels",
        phrase="two sturdy shovels",
        use="shovel",
        helps={"avalanche"},
        tags={"shovels", "snow", "teamwork"},
        plural=True,
    ),
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a long rope",
        use="rope",
        helps={"avalanche"},
        tags={"rope", "teamwork"},
    ),
    "whistle": Tool(
        id="whistle",
        label="whistle",
        phrase="a shiny whistle",
        use="whistle",
        helps={"avalanche"},
        tags={"whistle", "teamwork"},
    ),
}

NAMES = ["Mia", "Noah", "Lena", "Kai", "Ivy", "Owen", "Pia", "Zane", "Tia", "Beau"]
TRAITS = ["curious", "brave", "silly", "cheerful", "clever", "bouncy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES:
        for problem in PROBLEMS:
            for tool in TOOLS:
                if problem in TOOLS[tool].helps and problem in PLACES[place].supports:
                    combos.append((place, problem, tool))
    return combos


def explain_rejection(place: str, problem: str, tool: str) -> str:
    return f"(No story: {tool} does not plausibly help solve {problem} at {place}.)"


def _r_clear_path(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("snowbank_cleared"):
        return out
    if world.facts.get("path_open"):
        return out
    world.facts["path_open"] = True
    out.append("The snow shifted enough to open the trail.")
    return out


def _r_team_cheer(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("path_open"):
        return out
    if ("cheer",) in world.fired:
        return out
    world.fired.add(("cheer",))
    for ent in world.characters():
        ent.memes["joy"] += 1
        ent.memes["pride"] += 1
    out.append("The team cheered because their plan actually worked.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_clear_path, _r_team_cheer):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


ASP_RULES = r"""
supported(P, A, T) :- place(P), problem(A), tool(T), helps(T, A), supports(P, A).
valid(P, A, T) :- supported(P, A, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for p in sorted(place.supports):
            lines.append(asp.fact("supports", pid, p))
    for aid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", aid))
        for t in sorted(problem.tags):
            lines.append(asp.fact("problem_tag", aid, t))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comic avalanche teamwork storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--leader")
    ap.add_argument("--helper")
    ap.add_argument("--team-size", type=int)
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
    team_size = args.team_size if args.team_size is not None else rng.choice([2, 3, 4])
    if team_size < 2:
        raise StoryError("team size must be at least 2 for teamwork.")
    leader = args.leader or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != leader])
    return StoryParams(place=place, problem=problem, team_size=team_size, leader=leader, helper=helper, tool=tool)


def tell(place: Place, problem: Problem, tool: Tool, leader_name: str, helper_name: str, team_size: int) -> World:
    world = World(place)
    leader = world.add(Entity(id=leader_name, kind="character", type="boy" if leader_name in {"Noah", "Kai", "Owen", "Zane", "Beau"} else "girl", role="leader", team="team"))
    helper = world.add(Entity(id=helper_name, kind="character", type="boy" if helper_name in {"Noah", "Kai", "Owen", "Zane", "Beau"} else "girl", role="helper", team="team"))
    gear = world.add(Entity(id=tool.id, kind="thing", type=tool.label, label=tool.label, phrase=tool.phrase, plural=tool.plural))
    world.facts["problem"] = problem.id
    world.facts["tool"] = tool.id
    world.facts["place"] = place.id
    world.facts["team_size"] = team_size
    world.facts["snowbank_cleared"] = False
    world.facts["path_open"] = False

    leader.memes["worry"] += 1
    helper.memes["worry"] += 1
    world.say(f"{leader.id} and {helper.id} reached {place.label}, where {problem.danger}.")
    world.say(f"Their plan looked funny at first, because even the sign seemed to lean in and listen.")
    world.para()
    world.say(f"{leader.id} pointed at {problem.blocked_by}. {helper.id} held up {tool.phrase} and said they should think first.")
    world.say(f"{leader.id} had an idea: use {tool.label} together, one on each side, so the snow would move without anyone doing a faceplant.")
    world.facts["snowbank_cleared"] = True
    prop = propagate(world, narrate=False)
    if prop:
        world.say(f"They worked in a silly little rhythm, and soon the snow gave up and slid aside.")
    world.para()
    world.say(f"Then the whole team laughed when a tiny bird hopped onto the newly open trail like it had been waiting for a performance.")
    world.say(f"In the end, {leader.id} and {helper.id} solved the avalanche problem together, and {place.label} was open again.")
    world.resolved = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a young child about an {f["problem"]} that blocks {f["place"]}, and the friends solve it together.',
        f"Tell a comedy story where {world.get('leader').id} and {world.get('helper').id} use {f['tool']} to fix an {f['problem']} problem.",
        f'Write a short teamwork story that includes the word "avalanche" and ends with the trail open again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    leader = world.get(world.facts["leader"]) if "leader" in world.facts else None
    helper = world.get(world.facts["helper"]) if "helper" in world.facts else None
    place = PLACES[world.facts["place"]]
    problem = PROBLEMS[world.facts["problem"]]
    tool = TOOLS[world.facts["tool"]]
    return [
        QAItem(
            question=f"Who worked together to solve the {problem.label} problem at {place.label}?",
            answer=f"{leader.id} and {helper.id} worked together, and that teamwork is what made the fix happen. They used {tool.phrase} and kept talking until the snowy blockage moved.",
        ),
        QAItem(
            question=f"What was blocking the trail in {place.label}?",
            answer=f"An {problem.label} blocked the trail. It made the path look dramatic, but the team treated it like a problem to solve instead of a disaster to panic over.",
        ),
        QAItem(
            question=f"How did {leader.id} and {helper.id} solve the problem?",
            answer=f"They used {tool.label} together and cleared a safe route. Because they planned as a team, the snow moved aside and the trail opened again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an avalanche?",
            answer="An avalanche is a fast rush of snow sliding down a mountain. It can block roads and trails, so people have to be careful around it.",
        ),
        QAItem(
            question="Why is teamwork helpful when a problem is big?",
            answer="Teamwork helps because two or more people can share the work, share ideas, and keep each other calm. Big problems often get smaller when everyone does a little part.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means noticing what is wrong and trying different ideas until one works. It is like being a clever helper for the situation.",
        ),
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
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="mountain_trail", problem="avalanche", team_size=2, leader="Mia", helper="Kai", tool="shovels"),
    StoryParams(place="ski_hut", problem="avalanche", team_size=3, leader="Noah", helper="Ivy", tool="rope"),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.problem not in PROBLEMS or params.tool not in TOOLS:
        raise StoryError("invalid params")
    if params.problem not in PLACES[params.place].supports or params.problem not in TOOLS[params.tool].helps:
        raise StoryError(explain_rejection(params.place, params.problem, params.tool))
    world = tell(PLACES[params.place], PROBLEMS[params.problem], TOOLS[params.tool], params.leader, params.helper, params.team_size)
    world.facts["leader"] = params.leader
    world.facts["helper"] = params.helper
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


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    rc = 0
    if clingo_set == python_set:
        print(f"OK: ASP matches valid_combos() ({len(clingo_set)} combos).")
    else:
        print("MISMATCH between ASP and Python combos.")
        print("only in ASP:", sorted(clingo_set - python_set))
        print("only in Python:", sorted(python_set - clingo_set))
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test story generation worked.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, problem, tool in combos:
            print(f"  {place:14} {problem:10} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
