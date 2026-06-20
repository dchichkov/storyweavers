#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/shea_salvation_nopsu_moral_value_lesson_learned.py
===================================================================================

A small fable-style storyworld about kindness, problem solving, and a hard-earned
moral lesson. Two small neighbors face a practical problem, choose a clever
solution, and end with a concrete image that shows how they changed.

Seed words:
- shea
- salvation
- nopsu

Features:
- Moral Value
- Lesson Learned
- Problem Solving

Style:
- Fable
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "owl", "deer"}
        male = {"boy", "father", "dad", "man", "fox", "rabbit"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    scene: str
    has_bridge: bool = False
    has_water: bool = False
    has_wind: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    danger: str
    need: str
    avoid: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    use: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    shea: str
    shea_type: str
    nopsu: str
    nopsu_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


PLACES = {
    "meadow": Place("meadow", "the meadow", "a sunlit meadow", has_wind=True, tags={"meadow", "wind"}),
    "river": Place("river", "the riverbank", "a riverbank with a quick stream", has_bridge=True, has_water=True, tags={"river", "water"}),
    "orchard": Place("orchard", "the orchard", "an orchard with low branches and fallen apples", has_wind=True, tags={"orchard", "wind"}),
}

PROBLEMS = {
    "stuck_boat": Problem("stuck_boat", "a tiny boat stuck in the reeds", "water", "help it reach the stream", "leave it be", tags={"water", "help"}),
    "broken_bridge": Problem("broken_bridge", "a broken bridge plank", "gap", "cross safely", "fall into the water", tags={"bridge", "repair"}),
    "lost_seed": Problem("lost_seed", "a lost seed pouch in the grass", "search", "find the pouch before night", "give up", tags={"search", "kindness"}),
}

TOOLS = {
    "reed": Tool("reed", "a long reed", "hook and pull", tags={"help", "water"}),
    "rope": Tool("rope", "a sturdy rope", "tie and lift", tags={"bridge", "repair"}),
    "lantern": Tool("lantern", "a little lantern", "light the path", tags={"search", "light"}),
}

GIRL_NAMES = ["Shea", "Mina", "Lina", "Mara", "Tessa", "Rina"]
BOY_NAMES = ["Nopsu", "Timo", "Bren", "Milo", "Arlo", "Pico"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for prob_id, prob in PROBLEMS.items():
            for tool_id, tool in TOOLS.items():
                if prob.id == "stuck_boat" and tool.id == "reed" and place.has_water:
                    combos.append((pid, prob_id, tool_id))
                elif prob.id == "broken_bridge" and tool.id == "rope" and place.has_bridge:
                    combos.append((pid, prob_id, tool_id))
                elif prob.id == "lost_seed" and tool.id == "lantern":
                    combos.append((pid, prob_id, tool_id))
    return combos


def reasonableness_ok(problem: Problem, tool: Tool, place: Place) -> bool:
    if problem.id == "stuck_boat":
        return tool.id == "reed" and place.has_water
    if problem.id == "broken_bridge":
        return tool.id == "rope" and place.has_bridge
    if problem.id == "lost_seed":
        return tool.id == "lantern"
    return False


def outcome_of(params: StoryParams) -> str:
    if params.problem == "lost_seed":
        return "solved"
    return "solved"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable about moral value, lesson learned, and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
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


def _name_pair(rng: random.Random) -> tuple[str, str, str, str]:
    shea = "Shea"
    nopsu = "Nopsu"
    return shea, "girl", nopsu, "boy"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    if args.problem and args.tool:
        if not reasonableness_ok(PROBLEMS[args.problem], TOOLS[args.tool], PLACES[args.place or combos[0][0]]):
            raise StoryError("That tool cannot solve that problem in this place.")
    place, problem, tool = rng.choice(sorted(combos))
    shea, shea_type, nopsu, nopsu_type = _name_pair(rng)
    return StoryParams(place, problem, tool, shea, shea_type, nopsu, nopsu_type)


def tell(place: Place, problem: Problem, tool: Tool, shea_name: str, shea_type: str, nopsu_name: str, nopsu_type: str) -> World:
    world = World()
    shea = world.add(Entity(id=shea_name, kind="character", type=shea_type, role="helper", traits=["kind", "careful"]))
    nopsu = world.add(Entity(id=nopsu_name, kind="character", type=nopsu_type, role="thinker", traits=["brave", "quick"]))
    elder = world.add(Entity(id="Elder", kind="character", type="owl", label="the old owl", role="guide"))
    world.add(Entity(id="place", type="place", label=place.label))
    world.add(Entity(id="problem", type="problem", label=problem.label))
    world.add(Entity(id="tool", type="tool", label=tool.label))

    shea.memes["kindness"] += 1
    nopsu.memes["hope"] += 1
    world.say(f"At {place.label}, Shea and Nopsu lived like two small friends in a fable. {place.scene}.")
    world.say(f"One morning they found {problem.label}, and both felt the weight of the trouble.")
    world.para()
    world.say(f'"We should help," said Shea. "That would be the right thing to do."')
    world.say(f'Nopsu nodded. "But how?" {nopsu_name} asked, because the way was not simple.')
    if problem.id == "stuck_boat":
        world.say(f"They found {tool.label} by the reeds. Shea used it to hook the boat gently back to shore.")
    elif problem.id == "broken_bridge":
        world.say(f"They found {tool.label} beside the path. Together they tied the plank, and the bridge held.")
    else:
        world.say(f"They lifted {tool.label} and shone it across the grass. The lost pouch gleamed at the edge of the field.")
    world.para()
    shea.meters["helped"] += 1
    nopsu.meters["helped"] += 1
    shea.memes["pride"] += 1
    nopsu.memes["joy"] += 1
    world.say(f"The problem was solved, and {problem.need} was no longer hard. {shea_name} and {nopsu_name} stood side by side.")
    world.say(f"The old owl said, \"Remember this lesson: a good heart is strongest when it also thinks clearly.\"")
    world.say(f"Shea and Nopsu looked at one another and smiled. In that little meadow of time, salvation meant helping before boasting.")
    world.facts.update(place=place, problem=problem, tool=tool, shea=shea, nopsu=nopsu, elder=elder)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable for a child that includes the words "shea", "salvation", and "nopsu", and teaches a moral value through problem solving.',
        f"Tell a short fable where {f['shea'].id} and {f['nopsu'].id} face {f['problem'].label} and discover that salvation comes from a clever, kind action.",
        f'Write a gentle animal-story with a lesson learned at the end, using the word "{f["tool"].label}" as part of the solution.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place, problem, tool = f["place"], f["problem"], f["tool"]
    qa = [
        QAItem(question="Who are the story about?", answer=f"The story is about Shea and Nopsu at {place.label}. They are small friends in a fable, and they learn how to do the right thing."),
        QAItem(question="What problem did they face?", answer=f"They faced {problem.label}. It was a real problem, so they had to slow down and think before they acted."),
        QAItem(question="How did they solve it?", answer=f"They used {tool.label} and worked together. The tool fit the problem, so the solution was practical instead of rushed."),
        QAItem(question="What lesson did they learn?", answer="They learned that kindness is not enough by itself; it should be joined with clear thinking. That is the moral value the story leaves behind."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a fable?", answer="A fable is a short story that often uses animals or small characters to teach a moral lesson."),
        QAItem(question="What does salvation mean in this story?", answer="Here, salvation means being saved from trouble by a good and clever choice."),
        QAItem(question="Why is problem solving important?", answer="Problem solving helps you choose a safe and useful action when something is hard."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("river", "stuck_boat", "reed", "Shea", "girl", "Nopsu", "boy"),
    StoryParams("river", "broken_bridge", "rope", "Shea", "girl", "Nopsu", "boy"),
    StoryParams("meadow", "lost_seed", "lantern", "Shea", "girl", "Nopsu", "boy"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.has_bridge:
            lines.append(asp.fact("has_bridge", pid))
        if p.has_water:
            lines.append(asp.fact("has_water", pid))
        if p.has_wind:
            lines.append(asp.fact("has_wind", pid))
    for prob_id in PROBLEMS:
        lines.append(asp.fact("problem", prob_id))
    for tool_id in TOOLS:
        lines.append(asp.fact("tool", tool_id))
    lines.append(asp.fact("shea", "shea"))
    lines.append(asp.fact("nopsu", "nopsu"))
    return "\n".join(lines)


ASP_RULES = r"""
solvable(P, Pr, T) :- place(P), problem(Pr), tool(T), ok(P, Pr, T).
ok(P, stuck_boat, reed) :- has_water(P).
ok(P, broken_bridge, rope) :- has_bridge(P).
ok(P, lost_seed, lantern).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/3."))
    return sorted(set(asp.atoms(model, "solvable")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, problem=None, tool=None), random.Random(1)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PROBLEMS[params.problem], TOOLS[params.tool],
                 params.shea, params.shea_type, params.nopsu, params.nopsu_type)
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
        print(asp_program("#show solvable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as exc:
                print(exc)
                return
            params.seed = base_seed + i
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
