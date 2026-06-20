#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/magnum_rainded_stuffy_dialogue_problem_solving_tall.py
======================================================================================

A standalone story world for a tiny Tall Tale domain: a child-sized mystery about
a magnum crate, a rainded trail, and a stuffy room that needs smart talking and
quick problem solving. The stories are built from simulated state: a boastful
setup, a problem, a chatty turn where characters test ideas, and a resolution
that changes the room and the characters' feelings.

The seed words are intentionally woven into the world:
- magnum: the big, important crate or marker of the problem
- rainded: a made-up child voice for "rain-drenched" / "rainded" mud and cloth
- stuffy: a cramped, airless room or attic

The style stays close to Tall Tale: slightly larger-than-life, but still grounded
in concrete actions, dialogue, and a problem-solving ending image.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    is_stuffy: bool
    contains: str
    exit: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Problem:
    id: str
    label: str
    cause: str
    sign: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Tool:
    id: str
    label: str
    action: str
    effect: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    setting: Setting
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for line in out:
            world.say(line)
    return out


def _r_stuffy(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    if room.meters["sealed"] >= THRESHOLD and room.meters["air"] < THRESHOLD:
        sig = ("stuffy",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        room.meters["stuffy"] = 1
        for kid in ("child", "helper"):
            world.get(kid).memes["uncomfortable"] += 1
        out.append("The room grew stuffy as a hat box on a hot shelf.")
    return out


def _r_mud(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    crate = world.get("crate")
    if child.meters["wet"] < THRESHOLD:
        return []
    if crate.meters["covered"] >= THRESHOLD:
        return []
    sig = ("mud",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crate.meters["muddy"] += 1
    out.append("The rainded mud on the child's boots splashed the magnum crate.")
    return out


def _r_problem(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    if room.meters["stuffy"] >= THRESHOLD and room.meters["stuck"] < THRESHOLD:
        sig = ("problem",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        room.meters["stuck"] = 1
        world.get("helper").memes["worry"] += 1
        out.append("__problem__")
    return out


CAUSAL_RULES = [Rule("stuffy", _r_stuffy), Rule("mud", _r_mud), Rule("problem", _r_problem)]


def tell_dialogue(world: World, child: Entity, helper: Entity, setting: Setting, problem: Problem, tool: Tool) -> None:
    child.memes["wonder"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On a wide, wind-gnawed afternoon, {child.id} and {helper.id} reached "
        f"{setting.place}. There sat the magnum crate, big as a wagon wheel and "
        f"twice as stubborn."
    )
    world.say(
        f'"This place feels stuffy," {child.id} said. "Like a room that forgot how '
        f'to breathe."'
    )
    world.say(
        f'"That crate looks rainded," {helper.id} answered. "And if we leave it '
        f"covered up, the whole story will stay stuck inside."
    )
    room = world.get("room")
    room.meters["sealed"] += 1
    room.meters["air"] -= 1


def raise_problem(world: World, child: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"The trouble was plain: {problem.cause}. {problem.sign.capitalize()}, and "
        f"the answer had to be more than wishful thinking."
    )
    child.memes["worry"] += 1
    helper.memes["worry"] += 1


def try_idea(world: World, child: Entity, helper: Entity, tool: Tool) -> None:
    world.say(
        f'"Maybe we can use the {tool.label}," {child.id} said. "{tool.action}?"'
    )
    world.say(
        f'"That might do," {helper.id} said, "if we keep our heads and work the '
        f"problem from the side."
    )
    helper.memes["hope"] += 1


def solve(world: World, child: Entity, helper: Entity, tool: Tool) -> None:
    room = world.get("room")
    crate = world.get("crate")
    room.meters["sealed"] = 0
    room.meters["air"] = 2
    crate.meters["covered"] = 1
    crate.meters["muddy"] = 0
    child.memes["pride"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f'"Then let us do it proper," {helper.id} said. They {tool.effect}, and the '
        f"stuffy air began to move."
    )
    world.say(
        f"The magnum crate was wiped clean, the window was propped open, and the "
        f"rainded smell of storm-wet mud gave way to fresh evening air."
    )
    world.say(
        f'"Well now," {child.id} said, looking at the bright room, "that was a big '
        f'problem, but a small pair of hands solved it just fine."'
    )


def tell(setting: Setting, problem: Problem, tool: Tool, child_name: str, helper_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(child_name, kind="character", type="boy", role="child"))
    helper = world.add(Entity(helper_name, kind="character", type="girl", role="helper"))
    room = world.add(Entity("room", type="room", label=setting.place))
    crate = world.add(Entity("crate", type="thing", label="magnum crate"))
    child.memes["worry"] = 0
    helper.memes["care"] = 1

    tell_dialogue(world, child, helper, setting, problem, tool)
    world.para()
    raise_problem(world, child, helper, problem)
    try_idea(world, child, helper, tool)
    propagate(world, narrate=True)
    world.para()
    solve(world, child, helper, tool)

    world.facts.update(
        child=child,
        helper=helper,
        room=room,
        crate=crate,
        setting=setting,
        problem=problem,
        tool=tool,
        solved=True,
    )
    return world


SETTINGS = {
    "attic": Setting("attic", "the old attic", True, "a high window", "the roof hatch"),
    "cabin": Setting("cabin", "the little cabin", True, "a cracked pane", "the front door"),
    "shed": Setting("shed", "the tool shed", True, "a side slit", "the back door"),
}

PROBLEMS = {
    "stuffy": Problem(
        "stuffy",
        "stuffy air",
        "the window was shut and the storm had left the room like a closed-up jar",
        "The room felt stuffy",
        "open a path for fresh air",
        tags={"stuffy", "air"},
    ),
    "muddy": Problem(
        "muddy",
        "rainded mud",
        "the crate had been dragged through storm-soaked ground",
        "The magnum crate was rainded with mud",
        "wipe and cover the crate",
        tags={"rainded", "mud"},
    ),
    "mixed": Problem(
        "mixed",
        "rainded mud and stuffy air",
        "the crate was muddy and the room held still, thick air",
        "The problem was both rainded and stuffy",
        "clean the crate and open the room",
        tags={"rainded", "stuffy", "mud", "air"},
    ),
}

TOOLS = {
    "cloth": Tool("cloth", "clean cloth", "wipe the crate clean", "wiped the crate and opened the window", tags={"clean"}),
    "hook": Tool("hook", "window hook", "lift the latch and crack the window", "lifted the latch and let fresh air in", tags={"air"}),
    "both": Tool("both", "cloth and hook", "wipe the crate and crack the window", "wiped the crate, then lifted the latch", tags={"clean", "air"}),
}

NAMES_BOY = ["Jasper", "Tommy", "Eli", "Bram", "Ned", "Hank"]
NAMES_GIRL = ["Mabel", "Sally", "June", "Ada", "Penny", "Ruby"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, prob in PROBLEMS.items():
            for tid, tool in TOOLS.items():
                if prob.id == "stuffy" and "air" in tool.tags:
                    combos.append((sid, pid, tid))
                elif prob.id == "muddy" and "clean" in tool.tags:
                    combos.append((sid, pid, tid))
                elif prob.id == "mixed" and {"air", "clean"} <= tool.tags:
                    combos.append((sid, pid, tid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    child: str
    helper: str
    child_gender: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale problem solving with magnum, rainded, and stuffy.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--helper")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for tag in sorted(tool.tags):
            lines.append(asp.fact("tool_tag", tid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,T) :- setting(S), problem(P), tool(T), problem_tag(P,"stuffy"), tool_tag(T,"air").
valid(S,P,T) :- setting(S), problem(P), tool(T), problem_tag(P,"rainded"), tool_tag(T,"clean").
valid(S,P,T) :- setting(S), problem(P), tool(T), problem_tag(P,"stuffy"), problem_tag(P,"rainded"), tool_tag(T,"air"), tool_tag(T,"clean").
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return f"(No story: the tool '{tool.label}' does not fit the problem '{problem.label}' in a way this world can honestly solve.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.tool:
        prob = PROBLEMS[args.problem]
        tool = TOOLS[args.tool]
        ok = False
        if prob.id == "stuffy" and "air" in tool.tags:
            ok = True
        elif prob.id == "muddy" and "clean" in tool.tags:
            ok = True
        elif prob.id == "mixed" and {"air", "clean"} <= tool.tags:
            ok = True
        if not ok:
            raise StoryError(explain_rejection(prob, tool))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(sorted(combos))
    cg = rng.choice(["boy", "girl"])
    hg = "girl" if cg == "boy" else "boy"
    child = args.child or rng.choice(NAMES_BOY if cg == "boy" else NAMES_GIRL)
    helper = args.helper or rng.choice(NAMES_GIRL if hg == "girl" else NAMES_BOY)
    return StoryParams(setting, problem, tool, child, helper, cg, hg)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a child that uses the words "magnum", "rainded", and "stuffy" and includes dialogue.',
        f"Tell a problem-solving story where {f['child'].id} and {f['helper'].id} face a stuffy room and a rainded mess, then think their way out of it.",
        f"Write a lively story about a magnum crate in a stuffy place, where talking through the trouble leads to a smart fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, setting, problem, tool = f["child"], f["helper"], f["setting"], f["problem"], f["tool"]
    return [
        QAItem("Who are the story about?", f"The story is about {child.id} and {helper.id}, who work together in {setting.place}."),
        QAItem("What was the problem?", f"The problem was {problem.label}, because {problem.cause}."),
        QAItem("How did they solve it?", f'They used the {tool.label} and talked it through until the room was fixed and the magnum crate was safe.'),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does stuffy mean?", "Stuffy means the air feels closed up and hard to breathe comfortably in."),
        QAItem("What does rainded suggest?", "Rainded suggests something got soaked by rain and left wet mud or damp marks behind."),
        QAItem("What is a magnum crate in this story?", "It is the big important crate that marks the problem and gets cared for carefully."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "", "== (2) Story questions -- answerable from the story text =="]
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], TOOLS[params.tool], params.child, params.helper)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("attic", "stuffy", "hook", "Jasper", "Mabel", "boy", "girl"),
    StoryParams("cabin", "muddy", "cloth", "Ned", "Ruby", "boy", "girl"),
    StoryParams("shed", "mixed", "both", "Tommy", "June", "boy", "girl"),
]


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos")
        print("python-only:", sorted(py - cl))
        print("asp-only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test story generation succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(t)
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
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
