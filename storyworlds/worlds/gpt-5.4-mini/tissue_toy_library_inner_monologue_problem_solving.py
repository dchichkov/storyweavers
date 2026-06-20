#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tissue_toy_library_inner_monologue_problem_solving.py
====================================================================================

A standalone story world for a tiny nursery-rhyme-style domain: a child in a toy
library notices a problem, thinks through it in an inner monologue, and solves it
with a tissue and a careful plan.

The world is built as a small simulation with typed entities, physical meters,
emotional memes, a causal rule engine, QA generation, and an ASP twin.

Story seed:
- Setting: toy library
- Featured word: tissue
- Features: Inner Monologue, Problem Solving
- Style: Nursery Rhyme
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



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
    shelves: str
    mood: str

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
    trouble: str
    clue: str
    cause: str
    fix_hint: str
    needs: str
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
    phrase: str
    helps: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    problem = world.facts["problem"]
    shelf = world.get("shelf")
    if child.meters["trouble"] >= THRESHOLD and ("worry", problem.id) not in world.fired:
        world.fired.add(("worry", problem.id))
        shelf.memes["stillness"] += 1
        out.append("__worry__")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    problem = world.facts["problem"]
    if child.meters["helping"] >= THRESHOLD and ("fix", problem.id) not in world.fired:
        world.fired.add(("fix", problem.id))
        world.get("toy").meters["fixed"] += 1
        out.append("__fix__")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("fix", "physical", _r_fix),
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


def reasonableness_gate(problem: Problem, tool: Tool) -> bool:
    return problem.needs == tool.id


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, p in PROBLEMS.items():
            for tid, t in TOOLS.items():
                if reasonableness_gate(p, t):
                    combos.append((sid, pid, tid))
    return combos


def inner_monologue(world: World, child: Entity, problem: Problem) -> None:
    child.memes["thought"] += 1
    world.say(
        f"{child.id} looked at the {problem.trouble} and thought in a little hush, "
        f'"Oh dear, oh dear, what now shall I do?"'
    )
    world.say(
        f'Inside {child.id}\'s head, a tiny whisper chimed, '
        f'"First I see the clue, then I make a plan."'
    )


def notice_problem(world: World, child: Entity, problem: Problem, toy: Entity) -> None:
    child.meters["trouble"] += 1
    world.say(
        f"In the toy library, neat and bright, {child.id} saw the {toy.label} with "
        f"a {problem.trouble} in sight."
    )
    world.say(
        f"It was {problem.clue}, and the little one knew it needed care."
    )


def try_think(world: World, child: Entity, problem: Problem) -> None:
    child.memes["focus"] += 1
    world.say(
        f'{child.id} tapped {child.pronoun("possessive")} chin and said, '
        f'"If I find the cause, I can mend the flaw."'
    )
    world.say(
        f'"A tissue may help," {child.id} thought, "if the trouble is soft and small."'
    )


def solve(world: World, child: Entity, tool: Tool, toy: Entity, problem: Problem) -> None:
    child.meters["helping"] += 1
    child.memes["joy"] += 1
    toy.meters["neat"] += 1
    toy.meters["trouble"] = 0
    world.say(
        f"{child.id} found a {tool.label} and used it just so, following {child.pronoun('possessive')} "
        f"little plan with a tidy glow."
    )
    world.say(
        f"{tool.phrase.capitalize()} and careful hands made the {toy.label} clean and right."
    )
    world.say(
        f"Then {child.id} put the {toy.label} back on the shelf, snug and bright."
    )


def lesson(world: World, child: Entity, tool: Tool, setting: Setting) -> None:
    world.say(
        f'The {setting.place} stayed calm and snug, and {child.id} smiled a tiny smile. '
        f'"When I think, I can help," {child.id} said, "and that feels just fine."'
    )
    world.say(
        f"So the child and the toys were happy there, and the tissue did its kind little task."
    )


def story_intro(world: World, child: Entity, problem: Problem, toy: Entity) -> None:
    world.say(
        f"Once in a toy library, soft and small, {child.id} walked the shelves and saw it all."
    )
    world.say(
        f"{toy.label_word.capitalize()} was waiting, but {problem.trouble} had come to stay."
    )
    world.say(
        f"The room had {world.setting.mood}, and the books watched quietly all the day."
    )


def tell(setting: Setting, problem: Problem, tool: Tool, child_name: str, child_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    shelf = world.add(Entity(id="shelf", type="shelf", label="shelf"))
    toy = world.add(Entity(id="toy", type="toy", label=problem.id))
    world.add(Entity(id="table", type="table", label="reading table"))
    world.facts["problem"] = problem
    world.facts["tool"] = tool

    story_intro(world, child, problem, toy)
    world.para()
    notice_problem(world, child, problem, toy)
    inner_monologue(world, child, problem)
    try_think(world, child, problem)
    world.para()
    if reasonableness_gate(problem, tool):
        solve(world, child, tool, toy, problem)
        propagate(world, narrate=False)
    else:
        raise StoryError("This tool does not match the problem in a reasonable way.")
    lesson(world, child, tool, setting)
    world.facts.update(child=child, toy=toy, shelf=shelf, setting=setting)
    return world


SETTINGS = {
    "toy_library": Setting(
        "toy_library",
        "the toy library",
        "shelves of toys",
        "soft and merry",
    )
}

PROBLEMS = {
    "teddy": Problem(
        "teddy",
        "a dusty patch",
        "the dust was on the teddy bear's nose",
        "a sneezy shelf day",
        "wipe it with a tissue",
        "tissue",
        tags={"tissue", "cleaning"},
    ),
    "bunny": Problem(
        "bunny",
        "a smudge",
        "the smudge was on the bunny's ear",
        "sticky hands from play",
        "wipe it with a tissue",
        "tissue",
        tags={"tissue", "cleaning"},
    ),
    "train": Problem(
        "train",
        "a tiny crumb trail",
        "crumbs had fallen into the train car",
        "snack time",
        "wipe it with a tissue",
        "tissue",
        tags={"tissue", "cleaning"},
    ),
}

TOOLS = {
    "tissue": Tool(
        "tissue",
        "tissue",
        "a tissue",
        "wipe softly and cleanly",
        tags={"tissue"},
    ),
    "cloth": Tool(
        "cloth",
        "soft cloth",
        "a soft cloth",
        "wipe softly and cleanly",
        tags={"tissue"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ella", "Rose"]
BOY_NAMES = ["Finn", "Theo", "Ben", "Max", "Leo"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    child: str
    gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Toy library tissue story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.problem and args.tool and not reasonableness_gate(PROBLEMS[args.problem], TOOLS[args.tool]):
        raise StoryError("This toy-library problem needs tissue, so that combination is not reasonable.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(setting, problem, tool, child, gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a nursery-rhyme-style story set in a toy library where a child notices a small problem and thinks through a fix.",
        f"Tell a gentle story about {f['child'].id} in the toy library using the word tissue and ending with a careful solution.",
        "Write a story with an inner monologue and problem solving, keeping the tone soft, rhythmic, and child-friendly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    problem = f["problem"]
    toy = f["toy"]
    return [
        QAItem(
            question=f"What did {child.id} notice in the toy library?",
            answer=f"{child.id} noticed that {toy.label} had {problem.trouble}. The child saw the problem and knew it needed a gentle fix."
        ),
        QAItem(
            question=f"What did {child.id} think about before solving it?",
            answer=f"{child.id} thought about the clue, the cause, and how to make the toy clean again. Then the child chose a tissue and used a careful plan."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the toy clean, the shelf neat, and {child.id} feeling proud. The tissue helped solve the problem in a small, calm way."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tissue?",
            answer="A tissue is a soft paper used to wipe little messes, tears, or smudges gently."
        ),
        QAItem(
            question="What is a toy library?",
            answer="A toy library is a place where toys are kept on shelves so children can visit them and play carefully."
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means noticing what is wrong, thinking about the cause, and choosing a good way to fix it."
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(P,T) :- problem(P), tool(T), needs(P,T).
answer(P) :- reasonable(P,T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("needs", pid, p.needs))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) == set((p, t) for _, p, t in valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        params = resolve_params(argparse.Namespace(setting=None, problem=None, tool=None, child=None, gender=None), _random.Random(7))
        sample = generate(params)
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


CURATED = [
    StoryParams("toy_library", "teddy", "tissue", "Mia", "girl"),
    StoryParams("toy_library", "bunny", "tissue", "Finn", "boy"),
    StoryParams("toy_library", "train", "tissue", "Lily", "girl"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        TOOLS[params.tool],
        params.child,
        params.gender,
    )
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
        print(asp_program("", "#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible problem/tool combos:")
        for p, t in asp_valid_combos():
            print(f"  {p} {t}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
