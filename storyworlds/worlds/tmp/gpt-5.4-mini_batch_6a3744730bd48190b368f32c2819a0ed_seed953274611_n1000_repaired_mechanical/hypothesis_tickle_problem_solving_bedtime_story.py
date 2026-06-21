#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hypothesis_tickle_problem_solving_bedtime_story.py
==================================================================================

A small bedtime storyworld about a child, a puzzling tickle, a calm hypothesis,
and a gentle problem-solving bedtime fix.

The world is designed to make a complete TinyStories-style scene:
- a bedtime setting
- a small problem that causes a tickly feeling or a tiny worry
- a hypothesis based on a clue
- a simple test
- a safe fix
- a soft ending image that proves the change

It supports the shared Storyweavers interface and an inline ASP twin.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
class ProblemType:
    id: str
    clue: str
    feeling: str
    cause: str
    test: str
    fix: str
    ending_image: str
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
    helps: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class StoryParams:
    problem: str
    tool: str
    child: str
    child_gender: str
    parent: str
    parent_gender: str
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


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.meters.get("sleepy", 0.0) >= THRESHOLD and child.memes.get("comfort", 0.0) >= THRESHOLD:
        sig = ("settle",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["rest"] = 1.0
            out.append("__settled__")
    return out


CAUSAL_RULES = [Rule("settle", "social", _r_settle)]


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


def reasonableness_gate(problem: ProblemType, tool: Tool) -> bool:
    return problem.id in PROBLEMS and tool.id in TOOLS and "gentle" in tool.tags and "bedtime" in problem.tags


def clue_matches(problem: ProblemType, clue: str) -> bool:
    return problem.clue == clue


def predict_fix(world: World, problem: ProblemType, tool: Tool) -> dict:
    sim = world.copy()
    _apply_problem(sim, narrate=False)
    _test_and_fix(sim, problem, tool, narrate=False)
    child = sim.get("child")
    return {
        "calm": child.memes.get("calm", 0.0),
        "sleepy": child.meters.get("sleepy", 0.0),
        "rest": child.meters.get("rest", 0.0),
    }


def _apply_problem(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    child.meters["trouble"] = 1.0
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    propagate(world, narrate=narrate)


def introduce(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"At bedtime, {child.id} was tucked under the quilt while {parent.id} sat nearby with a soft voice and a warm lamp."
    )
    world.say(
        f"{child.id} was just sleepy enough to yawn, but not sleepy enough to stop wondering about a tiny tickle."
    )


def problem_scene(world: World, problem: ProblemType) -> None:
    child = world.get("child")
    child.memes["curious"] = child.memes.get("curious", 0.0) + 1.0
    world.say(
        f"Then the little problem arrived: {problem.feeling}. {problem.clue}."
    )
    world.say(
        f"{child.id} wriggled and said, \"It feels like something is giving me a tickle.\""
    )


def hypothesis_scene(world: World, child: Entity, parent: Entity, problem: ProblemType) -> None:
    child.memes["hypothesis"] = child.memes.get("hypothesis", 0.0) + 1.0
    world.say(
        f"{child.id} put a finger on {child.pronoun('possessive')} chin and made a hypothesis."
    )
    world.say(
        f"\"Maybe {problem.cause},\" {child.id} whispered. {parent.id} nodded and said that was a good guess to test."
    )


def test_scene(world: World, problem: ProblemType, tool: Tool) -> None:
    world.say(
        f"Together they tried a small test: {problem.test}. That way they could learn what was really causing the tickle."
    )
    world.say(
        f"{parent_label(world)} reached for {tool.phrase} because it was gentle and good for bedtime."
    )


def _test_and_fix(world: World, problem: ProblemType, tool: Tool, narrate: bool = True) -> None:
    child = world.get("child")
    parent = world.get("parent")
    if not clue_matches(problem, problem.clue):
        return
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1.0
    child.meters["sleepy"] = child.meters.get("sleepy", 0.0) + 1.0
    child.meters["trouble"] = 0.0
    if narrate:
        world.say(
            f"The clue fit. {problem.fix.format(tool=tool.label)}"
        )
        world.say(
            f"Then {parent.id} smiled and helped {child.id} settle back down."
        )


def resolve_scene(world: World, problem: ProblemType, tool: Tool) -> None:
    child = world.get("child")
    parent = world.get("parent")
    world.say(
        f"{problem.ending_image} {child.id} sighed, the tickle was gone, and the room felt extra cozy."
    )
    world.say(
        f"{parent.id} tucked the blanket edge in just right, and soon {child.id} was breathing slow and even."
    )
    child.memes["comfort"] = child.memes.get("comfort", 0.0) + 1.0


def parent_label(world: World) -> str:
    return world.get("parent").label_word.capitalize()


def tell(problem: ProblemType, tool: Tool, child_name: str, child_gender: str, parent_name: str, parent_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    world.add(Entity(id="lamp", type="thing", label="lamp"))
    world.add(Entity(id="blanket", type="thing", label="blanket"))
    world.add(Entity(id="pillow", type="thing", label="pillow"))
    introduce(world, child, parent)
    world.para()
    problem_scene(world, problem)
    hypothesis_scene(world, child, parent, problem)
    test_scene(world, problem, tool)
    world.para()
    _apply_problem(world)
    _test_and_fix(world, problem, tool, narrate=True)
    resolve_scene(world, problem, tool)
    world.facts.update(
        child=child,
        parent=parent,
        problem=problem,
        tool=tool,
        outcome="solved",
        tickle=True,
        hypothesis=True,
    )
    return world


PROBLEMS = {
    "tag": ProblemType(
        id="tag",
        clue="The tickle came from a scratchy shirt tag near the neck",
        feeling="A tiny scratch kept poking at the back of the neck",
        cause="the shirt tag was rubbing their skin",
        test="they gently felt the collar and found the scratchy tag",
        fix="They clipped the tag off with {tool}.",
        ending_image="At last the collar felt smooth.",
        tags={"bedtime", "tickle"},
    ),
    "feather": ProblemType(
        id="feather",
        clue="A fluffy feather had slipped under the pillow",
        feeling="Something soft kept tickling the cheek",
        cause="a feather had slipped under the pillow",
        test="they lifted the pillow and checked the sheets",
        fix="They brushed the feather away with {tool}.",
        ending_image="The pillow looked puffy and still.",
        tags={"bedtime", "tickle"},
    ),
    "crumb": ProblemType(
        id="crumb",
        clue="A tiny cracker crumb hid in the blanket fold",
        feeling="A little prickle kept making the foot wiggle",
        cause="a crumb was trapped in the blanket fold",
        test="they shook the blanket and looked for the crumb",
        fix="They picked the crumb out carefully with {tool}.",
        ending_image="The blanket lay smooth and soft again.",
        tags={"bedtime", "tickle"},
    ),
}

TOOLS = {
    "scissors": Tool(id="scissors", label="small scissors", phrase="small scissors", helps="cut", tags={"gentle", "bedtime"}),
    "brush": Tool(id="brush", label="soft brush", phrase="a soft brush", helps="brush", tags={"gentle", "bedtime"}),
    "tweezers": Tool(id="tweezers", label="tiny tweezers", phrase="tiny tweezers", helps="pick", tags={"gentle", "bedtime"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Sam", "Theo", "Max"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for pid, problem in PROBLEMS.items():
        for tid, tool in TOOLS.items():
            if reasonableness_gate(problem, tool):
                combos.append((pid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld about a hypothesis, a tickle, and a gentle fix.")
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mom", "dad"])
    ap.add_argument("--parent-gender", choices=["mother", "father"])
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
    if args.problem and args.tool:
        if not reasonableness_gate(PROBLEMS[args.problem], TOOLS[args.tool]):
            raise StoryError("That tool does not make a gentle bedtime fix for that problem.")
    combos = [c for c in valid_combos()
              if (args.problem is None or c[0] == args.problem)
              and (args.tool is None or c[1] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    problem, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    parent = args.parent or ("Mom" if parent_gender == "mother" else "Dad")
    return StoryParams(problem=problem, tool=tool, child=child, child_gender=gender, parent=parent, parent_gender=parent_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle bedtime story that includes the words "hypothesis" and "tickle" and shows a child solving a tiny problem.',
        f"Tell a sleepy story where {f['child'].id} makes a hypothesis about a tickle and {f['parent'].id} helps test it.",
        f"Write a calm bedtime story about figuring out why something tickles, then fixing it with a small gentle tool.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    problem = f["problem"]
    tool = f["tool"]
    return [
        QAItem(
            question="What was the child trying to figure out?",
            answer=f"{child.id} was trying to figure out what was making the tickle at bedtime. The clue pointed to {problem.cause}, so the child and {parent.id} could test a guess instead of just worrying."
        ),
        QAItem(
            question="What was the hypothesis?",
            answer=f"The hypothesis was that {problem.cause}. {child.id} said it softly and {parent.id} agreed to test it because a calm guess is a good way to solve a small problem."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They tested the clue and used {tool.phrase} to fix the cause of the tickle. That made the bed feel comfortable again, so {child.id} could settle down and sleep."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hypothesis?",
            answer="A hypothesis is a guess you make when you want to explain something puzzling. You can test it to see if it is right."
        ),
        QAItem(
            question="What does tickle mean?",
            answer="A tickle is a light, funny feeling on your skin that can make you wiggle or laugh. It can come from something scratchy, soft, or tiny touching you."
        ),
        QAItem(
            question="Why is it good to test a guess?",
            answer="Testing a guess helps you find the real cause of a problem. That way you can choose a fix that actually works."
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T) :- problem(P), tool(T), gentle(T), bedtime(P).
settled :- child_sleepy, child_comforted.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("clue", pid, p.clue))
        lines.append(asp.fact("bedtime", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if "gentle" in t.tags:
            lines.append(asp.fact("gentle", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between ASP and Python valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(problem=None, tool=None, child=None, gender=None, parent=None, parent_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke-tested generate() successfully.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.problem not in PROBLEMS or params.tool not in TOOLS:
        raise StoryError("Invalid params.")
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    if not reasonableness_gate(problem, tool):
        raise StoryError("That combination does not make a gentle bedtime problem-solving story.")
    world = tell(problem, tool, params.child, params.child_gender, params.parent, params.parent_gender)
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


CURATED = [
    StoryParams(problem="tag", tool="scissors", child="Mia", child_gender="girl", parent="Mom", parent_gender="mother"),
    StoryParams(problem="feather", tool="brush", child="Leo", child_gender="boy", parent="Dad", parent_gender="father"),
    StoryParams(problem="crumb", tool="tweezers", child="Nora", child_gender="girl", parent="Mom", parent_gender="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid combos:")
        for p, t in asp_valid_combos():
            print(f"  {p} {t}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
