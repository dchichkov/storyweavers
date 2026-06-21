#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/consist_crumb_humongous_problem_solving_inner_monologue.py
==========================================================================================

A small whodunit-style storyworld about a crumb trail, a humongous puzzle, and
a child detective who solves the mystery by thinking it through.

The core premise:
- Something humongous gets out of place.
- A crumb appears where it should not.
- The detective notices details, follows inner monologue clues, and solves the
  problem with a concrete action.

This world includes the seed words "consist", "crumb", and "humongous", and it
keeps the prose child-facing, concrete, and state-driven.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        return self.label or self.id
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
class Clue:
    id: str
    label: str
    where: str
    kind: str
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
    parts: str
    misplaced: str
    fix: str
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
    label: str
    action: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy
        clone = World()
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    place: str
    problem: str
    clue: str
    solution: str
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
    "library": "the quiet library",
    "kitchen": "the kitchen",
    "playroom": "the playroom",
    "hall": "the hallway",
}

PROBLEMS = {
    "missing_cookie": Problem(
        id="missing_cookie",
        label="the missing cookie",
        parts="a plate of crumbs, a tilted jar, and a tiny sticky mark",
        misplaced="a jar on the counter",
        fix="look for who had flour on their hands",
        tags={"crumb", "whodunit"},
    ),
    "broken_model": Problem(
        id="broken_model",
        label="the humongous model",
        parts="a humongous model, a fallen tower, and a dusty floor",
        misplaced="a toy tower by the shelf",
        fix="check who moved the heavy pieces",
        tags={"humongous", "whodunit"},
    ),
    "lost_key": Problem(
        id="lost_key",
        label="the lost key",
        parts="a chair, a rug, and a crumb stuck to a pocket",
        misplaced="a key hook by the door",
        fix="follow the crumb and ask who was snacking",
        tags={"crumb", "whodunit"},
    ),
}

CLUES = {
    "crumb": Clue(id="crumb", label="a crumb", where="near the rug", kind="small food crumb", tags={"crumb"}),
    "dust": Clue(id="dust", label="dust", where="under the shelf", kind="gray dust", tags={"humongous"}),
    "smudge": Clue(id="smudge", label="a smudge", where="on the counter", kind="sticky smudge", tags={"crumb"}),
}

SOLUTIONS = {
    "follow": Solution(
        id="follow",
        label="follow the clue",
        action="follow the crumb trail",
        result="the trail led straight to the kitchen table",
        tags={"crumb", "whodunit"},
    ),
    "ask": Solution(
        id="ask",
        label="ask carefully",
        action="ask the helper a careful question",
        result="the helper remembered moving the heavy box",
        tags={"humongous", "whodunit"},
    ),
    "compare": Solution(
        id="compare",
        label="compare details",
        action="compare the tiny marks with the messy spot",
        result="the detective matched the clue to the right person",
        tags={"crumb", "humongous", "whodunit"},
    ),
}

NAMES_GIRL = ["Mia", "Lina", "Zoe", "Ava", "Nora", "June"]
NAMES_BOY = ["Eli", "Noah", "Theo", "Ben", "Max", "Leo"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, prob in PROBLEMS.items():
        for cid, clue in CLUES.items():
            for sid, sol in SOLUTIONS.items():
                if prob.tags & clue.tags and prob.tags & sol.tags:
                    out.append((pid, cid, sid))
    return out


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for sid in SOLUTIONS:
        lines.append(asp.fact("solution", sid))
    for pid, prob in PROBLEMS.items():
        for t in sorted(prob.tags):
            lines.append(asp.fact("problem_tag", pid, t))
    for cid, clue in CLUES.items():
        for t in sorted(clue.tags):
            lines.append(asp.fact("clue_tag", cid, t))
    for sid, sol in SOLUTIONS.items():
        for t in sorted(sol.tags):
            lines.append(asp.fact("solution_tag", sid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, C, S) :- problem(P), clue(C), solution(S),
                  problem_tag(P, T), clue_tag(C, T),
                  solution_tag(S, U), problem_tag(P, U).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Whodunit storyworld about crumbs, a humongous puzzle, and problem solving."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.problem and args.clue and args.clue not in {"crumb", "dust", "smudge"}:
        raise StoryError("That clue does not fit the mystery.")
    combos = [
        c for c in valid_combos()
        if (args.problem is None or c[0] == args.problem)
        and (args.clue is None or c[1] == args.clue)
        and (args.solution is None or c[2] == args.solution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    pid, cid, sid = rng.choice(sorted(combos))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if detective_gender == "girl" else "girl")
    detective = args.detective or rng.choice(NAMES_GIRL if detective_gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(NAMES_GIRL if helper_gender == "girl" else NAMES_BOY)
    place = args.place or rng.choice(list(PLACES))
    return StoryParams(
        detective=detective,
        detective_gender=detective_gender,
        helper=helper,
        helper_gender=helper_gender,
        place=place,
        problem=pid,
        clue=cid,
        solution=sid,
    )


def tell(params: StoryParams) -> World:
    if params.problem not in PROBLEMS or params.clue not in CLUES or params.solution not in SOLUTIONS:
        raise StoryError("Invalid params.")
    prob = PROBLEMS[params.problem]
    clue = CLUES[params.clue]
    sol = SOLUTIONS[params.solution]
    world = World()
    det = world.add(Entity(id=params.detective, kind="character", type=params.detective_gender, role="detective"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    room = world.add(Entity(id="room", type="place", label=PLACES[params.place]))
    det.memes["curiosity"] = 1
    helper.memes["nervous"] = 1

    world.say(
        f"{det.id} was a little detective who liked puzzles. "
        f"In {PLACES[params.place]}, the mystery seemed to consist of {prob.parts}."
    )
    world.say(
        f"{det.id} looked at the scene and thought, 'Someone moved something humongous, "
        f"but this crumb is tiny. The two clues do not match yet.'"
    )
    world.para()
    world.say(
        f"{det.id} noticed {clue.label} {clue.where}. "
        f"Inside {det.pronoun('possessive')} head, {det.id} thought, "
        f"'If I follow the small detail, the big answer may appear.'"
    )
    if clue.id == "crumb":
        world.say("The crumb was too small to matter by itself, so the detective kept thinking.")
    elif clue.id == "dust":
        world.say("The dust clung to a heavy spot, which made the humongous thing stand out.")
    else:
        world.say("The smudge was sticky, and sticky marks usually tell a story.")
    world.para()
    world.say(
        f"{det.id} decided to {sol.action}. "
        f"Inside {det.pronoun('possessive')} head, {det.id} whispered, "
        f"'Stay calm. Look again. The answer is not hiding; it is waiting.'"
    )
    if sol.id == "follow":
        world.say("The crumb trail curved around a chair leg and pointed to the kitchen table.")
    elif sol.id == "ask":
        world.say(f"{helper.id} remembered moving the heavy box because it was humongous and in the way.")
    else:
        world.say(f"{det.id} compared the tiny marks, and the clue fit exactly.")
    world.para()
    world.say(
        f"{det.id} solved it: {sol.result}. "
        f"The mystery was no longer strange; it made sense at last."
    )
    world.say(
        f"In the end, the humongous thing was back where it belonged, "
        f"and the crumb had helped tell the truth."
    )

    world.facts.update(
        detective=det,
        helper=helper,
        room=room,
        problem=prob,
        clue=clue,
        solution=sol,
        place=params.place,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit-style story for a child that includes the word "consist" and solves a mystery with a tiny clue.',
        f"Tell a detective story where {f['detective'].id} notices a crumb near a humongous problem and thinks through the answer.",
        f'Write a short mystery that uses the words "crumb" and "humongous" and ends with a clear solved problem.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det, helper, prob, clue, sol = f["detective"], f["helper"], f["problem"], f["clue"], f["solution"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer="It is a whodunit-style mystery, where the detective pays attention to clues and reasons out the answer."
        ),
        QAItem(
            question=f"What did {det.id} notice?",
            answer=f"{det.id} noticed {clue.label} and thought carefully about how it might connect to {prob.label}. That tiny detail helped lead to the solution."
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"The detective used {sol.label} and found the answer by thinking step by step. The clue made the humongous mystery make sense."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crumb?",
            answer="A crumb is a tiny piece of food that falls off bread, cookies, or cake."
        ),
        QAItem(
            question="What does humongous mean?",
            answer="Humongous means extremely big, much bigger than ordinary."
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find the answer or fix what is wrong."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(
        detective="Mia",
        detective_gender="girl",
        helper="Ben",
        helper_gender="boy",
        place="library",
        problem="missing_cookie",
        clue="crumb",
        solution="follow",
    ),
    StoryParams(
        detective="Theo",
        detective_gender="boy",
        helper="Ava",
        helper_gender="girl",
        place="kitchen",
        problem="broken_model",
        clue="dust",
        solution="ask",
    ),
    StoryParams(
        detective="Nora",
        detective_gender="girl",
        helper="Eli",
        helper_gender="boy",
        place="hall",
        problem="lost_key",
        clue="smudge",
        solution="compare",
    ),
]


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a != p:
        print("MISMATCH between ASP and Python gate.")
        if a - p:
            print(" only in ASP:", sorted(a - p))
        if p - a:
            print(" only in Python:", sorted(p - a))
        return 1
    print(f"OK: ASP gate matches Python ({len(a)} combos).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: generation smoke test crashed: {exc}")
        return 1
    print("OK: generation smoke test passed.")
    return 0


def build_asp_show() -> str:
    return asp_program()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(build_asp_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (problem, clue, solution) combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
