#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T034914Z_seed1855084837_n10/tweezers_twist_repetition_nursery_rhyme.py
===============================================================================================================

A small nursery-rhyme storyworld about a child, a tiny problem, and a twist:
someone wants to use tweezers to fix something delicate, tries the wrong way
first, then repeats the careful motion until the problem is solved.

The world keeps typed entities with physical meters and emotional memes, a small
forward simulation, a reasonableness gate, and an inline ASP twin.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    tool_for: str = ""
    fragile: bool = False
    sharp: bool = False
    safe: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    traits: list = field(default_factory=list)
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
    gender: str
    helper: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None
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
class Place:
    id: str
    label: str
    cozy: str
    affords: set[str] = field(default_factory=set)
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
    phrase: str
    tiny: bool
    delicate: bool
    repeats: int
    fixable_by: str
    safe_method: str
    twist: str
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
class Tool:
    id: str
    label: str
    phrase: str
    careful: str
    wrong_move: str
    finish: str
    plural: bool = False
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    problem = world.get("problem")
    if child.meters["attempt"] < THRESHOLD:
        return out
    sig = ("repeat", child.id, problem.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if problem.meters["stuck"] > 0:
        problem.meters["stuck"] = max(0.0, problem.meters["stuck"] - 1.0)
    problem.meters["progress"] += 1
    child.memes["focus"] += 1
    out.append("__repeat__")
    return out


CAUSAL_RULES = [_r_repeat]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def choose_tool(problem: Problem) -> bool:
    return problem.fixable_by == "tweezers"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES:
        for pid, p in PROBLEMS.items():
            for tid, t in TOOLS.items():
                if p.fixable_by == tid and tid == "tweezers" and "nursery" in place.cozy:
                    combos.append((place.id, pid, tid))
    return combos


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return f"(No story: {tool.label} cannot make a gentle fix for {problem.label}. This storyworld wants tweezers doing a tiny, careful job.)"


def predict_fix(world: World, tool: Tool, problem: Problem) -> dict[str, object]:
    sim = world.copy()
    child = sim.get("child")
    child.meters["attempt"] += 1
    child.meters["attempt"] += 1
    propagate(sim, narrate=False)
    return {
        "progress": sim.get("problem").meters["progress"],
        "done": sim.get("problem").meters["progress"] >= problem.repeats,
    }


def setup(world: World, child: Entity, helper: Entity, problem: Entity, tool: Entity) -> None:
    child.memes["want"] += 1
    helper.memes["care"] += 1
    world.say(f"{child.id} was a little one in {world.place.label}, with a tiny task to do.")
    world.say(f"{child.id} liked {problem.label}, for {problem.phrase} needed a careful fix.")
    world.say(f"{helper.id} was nearby, singing, \"Soft and slow, and soft and slow,\" while {tool.label} lay ready on the sill.")


def wants_fix(world: World, child: Entity, problem: Entity, tool: Entity) -> None:
    world.say(f"{child.id} wanted to use {tool.label} on {problem.label}, to make the little trouble go.")
    world.say(f"\"One little turn, one little turn,\" {child.id} said, and reached out with a grin.")


def warn(world: World, helper: Entity, child: Entity, problem: Entity, tool: Entity) -> None:
    pred = predict_fix(world, tool, problem.meters and world.get("problem") or problem)
    world.facts["pred_done"] = bool(pred["done"])
    world.say(f"\"Not so fast,\" {helper.id} said. \"{tool.label} is for a tiny, careful touch.\"")
    world.say(f"\"If you rush, {problem.label} may only get more stuck.\"")


def twist(world: World, child: Entity, helper: Entity, problem: Entity, tool: Entity) -> None:
    child.meters["attempt"] += 1
    child.memes["determination"] += 1
    world.say(f"{child.id} tried once, then tried again, but the first try only made the tiny knot spin.")
    world.say(f"Then came the twist: {helper.id} showed {child.id} the steady way, not the hurried way.")
    world.say(f"\"Little turn, little turn,\" they sang together, and the tweezers touched the right spot.")


def finish(world: World, child: Entity, helper: Entity, problem: Entity, tool: Entity) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    problem.meters["stuck"] = 0.0
    problem.meters["progress"] = max(problem.meters["progress"], float(problem.attrs.get("need", 2)))
    world.say(f"At last, {tool.label} did the job, and {problem.label} came free with a tiny pop.")
    world.say(f"{child.id} clapped, {helper.id} laughed, and the room felt bright and light again.")
    world.say(f"With {problem.label} fixed, {child.id} tucked {tool.label} away and hummed the song once more.")


def tell(place: Place, problem_cfg: Problem, tool_cfg: Tool, name: str, gender: str,
         helper_name: str, helper_gender: str, trait: str) -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=gender, label=name, traits=[trait]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, traits=["gentle"]))
    problem = world.add(Entity(id="problem", type=problem_cfg.id, label=problem_cfg.label, phrase=problem_cfg.phrase, fragile=problem_cfg.delicate, attrs={"need": problem_cfg.repeats}, tags=set(problem_cfg.tags)))
    tool = world.add(Entity(id="tool", type="tool", label=tool_cfg.label, phrase=tool_cfg.phrase, sharp=True, safe=True, plural=tool_cfg.plural, tags=set(tool_cfg.tags)))
    child.meters["attempt"] = 0.0
    problem.meters["stuck"] = float(problem_cfg.repeats)
    problem.meters["progress"] = 0.0
    world.facts["need"] = problem_cfg.repeats
    setup(world, child, helper, problem, tool)
    world.para()
    wants_fix(world, child, problem, tool)
    warn(world, helper, child, problem, tool)
    world.para()
    twist(world, child, helper, problem, tool)
    propagate(world, narrate=False)
    world.para()
    finish(world, child, helper, problem, tool)
    world.facts.update(child=child, helper=helper, problem=problem, tool=tool, place=place, problem_cfg=problem_cfg, tool_cfg=tool_cfg, trait=trait)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story that uses the word "{f["tool_cfg"].label}" and ends with a tiny fix.',
        f"Tell a gentle story where {f['child'].label} wants to use {f['tool_cfg'].label} for {f['problem_cfg'].label}, but learns the careful way with a twist and a repeated song.",
        f'Write a rhyme-like story about a small problem in {f["place"].label} that gets solved by repeating a slow, careful motion with tweezers.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    problem: Entity = f["problem"]
    tool: Entity = f["tool"]
    place: Place = f["place"]
    need = f["problem_cfg"].repeats
    return [
        QAItem(
            question=f"What was {child.label} trying to do in {place.label}?",
            answer=f"{child.label} was trying to fix {problem.label} with {tool.label}. It took a careful touch, because {problem.phrase} needed {need} gentle turns.",
        ),
        QAItem(
            question=f"Who helped {child.label} when the first try did not work?",
            answer=f"{helper.label} helped {child.label}. {helper.label} slowed the motion down, and that was the little twist that made the job work.",
        ),
        QAItem(
            question=f"Why did the story repeat the slow motion more than once?",
            answer=f"It repeated because the tiny problem was still stuck after the first try. Each careful repeat made a little more progress until {problem.label} came free.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are tweezers for?",
            answer="Tweezers are small tools for picking up or moving tiny things. They help when a child or grown-up needs a careful pinch instead of a big grab.",
        ),
        QAItem(
            question="What does it mean to repeat something?",
            answer="To repeat something means to do it again and again. Repeating a small action can help when a task needs patience.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a change that surprises you a little. It makes the story turn in a new direction before the ending.",
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
        bits: list[str] = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p.id))
        lines.append(asp.fact("cozy", p.id, p.cozy))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", p.id, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("fixable_by", pid, p.fixable_by))
        lines.append(asp.fact("repeats", pid, p.repeats))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.safe:
            lines.append(asp.fact("safe", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Pr, T) :- place(P), problem(Pr), tool(T), fixable_by(Pr, T), cozy(P, nursery).
done(Pr) :- repeats(Pr, N), N >= 1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH between ASP and Python valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, problem=None, tool=None, name=None, gender=None, helper=None, helper_gender=None, trait=None, seed=None), random.Random(777)))
        if not sample.story.strip():
            ok = False
            print("Empty story from smoke test")
    except Exception as exc:
        ok = False
        print(f"Smoke test failed: {exc}")
    print("OK" if ok else "FAIL")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about tweezers, a tiny fix, and a twist.")
    ap.add_argument("--place", choices=[p.id for p in PLACES])
    ap.add_argument("--problem", choices=list(PROBLEMS))
    ap.add_argument("--tool", choices=list(TOOLS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy", "mother", "father"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy", "mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.tool and args.tool != "tweezers":
        raise StoryError("(No story: this world only tells the tweezers tale.)")
    choices = [c for c in valid_combos() if (args.place is None or c[0] == args.place) and (args.problem is None or c[1] == args.problem) and (args.tool is None or c[2] == args.tool)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, tool = rng.choice(sorted(choices))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice([n for n in NAMES if n != name])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, tool=tool, name=name, gender=gender, helper=helper, helper_gender=helper_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.tool != "tweezers":
        raise StoryError("(No story: the tool must be tweezers.)")
    if params.place not in PLACES_BY_ID or params.problem not in PROBLEMS or params.tool not in TOOLS:
        raise StoryError("(No story: invalid params.)")
    world = tell(PLACES_BY_ID[params.place], PROBLEMS[params.problem], TOOLS[params.tool], params.name, params.gender, params.helper, params.helper_gender, params.trait)
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


TRAITS = ["gentle", "careful", "tidy", "patient"]
NAMES = ["Mia", "Lily", "Ava", "Noah", "Owen", "Theo", "Nora", "Ruby"]
PLACES = [
    Place(id="nursery", label="the nursery", cozy="nursery", affords={"care"}),
    Place(id="playroom", label="the playroom", cozy="nursery", affords={"care"}),
    Place(id="bedroom", label="the bedroom", cozy="nursery", affords={"care"}),
]
PLACES_BY_ID = {p.id: p for p in PLACES}
PROBLEMS = {
    "splinter": Problem(id="splinter", label="a splinter", phrase="a tiny splinter sat in a finger", tiny=True, delicate=True, repeats=2, fixable_by="tweezers", safe_method="careful pinch", twist="steady hands", tags={"tiny", "wood"}),
    "crumb": Problem(id="crumb", label="a crumb", phrase="a crumb hid in a toy seam", tiny=True, delicate=False, repeats=3, fixable_by="tweezers", safe_method="careful pinch", twist="repeat the pinch", tags={"tiny", "crumb"}),
    "spool": Problem(id="spool", label="a thread spool", phrase="a thread spool had a loose end to tug free", tiny=True, delicate=True, repeats=2, fixable_by="tweezers", safe_method="careful pinch", twist="slow and sure", tags={"thread", "tiny"}),
}
TOOLS = {
    "tweezers": Tool(id="tweezers", label="tweezers", phrase="little silver tweezers", careful="careful pinch", wrong_move="a rushed grab", finish="set them down softly", plural=True, tags={"tweezers", "tiny"}),
}


def asp_verify_smoke() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify_smoke())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="nursery", problem="splinter", tool="tweezers", name="Mia", gender="girl", helper="Nora", helper_gender="girl", trait="gentle"),
            StoryParams(place="playroom", problem="crumb", tool="tweezers", name="Noah", gender="boy", helper="Lily", helper_gender="girl", trait="patient"),
            StoryParams(place="bedroom", problem="spool", tool="tweezers", name="Ava", gender="girl", helper="Owen", helper_gender="boy", trait="careful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
