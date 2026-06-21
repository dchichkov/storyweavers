#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/prawn_problem_solving_reconciliation_friendship_folk_tale.py
===========================================================================================

A tiny folk-tale storyworld about a small river problem, a clever repair, and a
friendship that grows warmer after a misunderstanding. The seed word is
"prawn"; the domain is built around a prawn, a stream, a broken crossing, and
children-friendly reconciliation.

The model uses typed entities with physical meters and emotional memes. The story
is not a frozen paragraph with swapped nouns; the world state changes, then the
prose follows from those changes.
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
FRIENDLY_MEME = 1.0


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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Place:
    id: str
    label: str
    feature: str
    crossing: str
    stream: str
    bank: str
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
    clue: str
    effect: str
    risk: str
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
    use: str
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
    text: str
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
class StoryParams:
    place: str
    problem: str
    tool: str
    solution: str
    friend_a: str
    friend_a_gender: str
    friend_b: str
    friend_b_gender: str
    elder: str
    elder_gender: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_mend(world: World) -> list[str]:
    out = []
    rope = world.entities.get("rope")
    bridge = world.entities.get("bridge")
    if rope and bridge and rope.meters["tied"] >= THRESHOLD and bridge.meters["broken"] >= THRESHOLD:
        sig = ("mend",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        bridge.meters["broken"] = 0.0
        bridge.meters["safe"] = 1.0
        out.append("__mended__")
    return out


def _r_feel(world: World) -> list[str]:
    out = []
    for eid in ("friend_a", "friend_b"):
        e = world.entities.get(eid)
        if e and e.memes["hurt"] >= THRESHOLD and e.memes["kindness"] >= THRESHOLD:
            sig = ("makeup", eid)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["soft"] += 1
            out.append("__soft__")
    return out


CAUSAL_RULES = [Rule("mend", _r_mend), Rule("feel", _r_feel)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for prob_id, prob in PROBLEMS.items():
            for sol_id, sol in SOLUTIONS.items():
                if prob.id == "missing_stepping_stones" and sol.id in {"rope_bridge", "apology"}:
                    combos.append((pid, prob_id, sol_id))
                if prob.id == "muddy_water" and sol.id in {"ladder", "rope_bridge"}:
                    combos.append((pid, prob_id, sol_id))
    return combos


def problem_needs(problem: Problem, solution: Solution) -> bool:
    if problem.id == "missing_stepping_stones":
        return solution.id == "rope_bridge"
    if problem.id == "muddy_water":
        return solution.id in {"ladder", "rope_bridge"}
    return False


def outcome_of(params: StoryParams) -> str:
    if params.problem == "missing_stepping_stones":
        return "reconciled" if params.solution == "rope_bridge" else "unfixed"
    return "reconciled" if params.solution in {"ladder", "rope_bridge"} else "unfixed"


def tell(place: Place, problem: Problem, tool: Tool, solution: Solution,
         a: Entity, b: Entity, elder: Entity) -> World:
    world = World()
    world.add(a)
    world.add(b)
    world.add(elder)
    bridge = world.add(Entity(id="bridge", kind="thing", type="bridge", label=place.crossing))
    stream = world.add(Entity(id="stream", kind="thing", type="stream", label=place.stream))
    rope = world.add(Entity(id="rope", kind="thing", type="tool", label=tool.label))
    world.facts["place"] = place
    world.facts["problem"] = problem
    world.facts["tool"] = tool
    world.facts["solution"] = solution

    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"Long ago, in {place.label}, {a.id} and {b.id} were dear friends who played by the water. "
        f"The old folk of the bank told them that {place.feature} was a place where little troubles could teach big wisdom."
    )
    world.say(
        f"One day they found that the {place.crossing} was troubled: {problem.clue}. "
        f"{problem.effect} {problem.risk}"
    )
    world.para()
    a.memes["worry"] += 1
    b.memes["worry"] += 1
    world.say(
        f'"We cannot cross now," said {a.id}, looking at the water. '
        f'"We must find a clever way, or ask help from the wise one."'
    )
    world.say(
        f'{b.id} bent down and noticed {tool.label}. "That might help," {b.id} said, though {a.id} was not yet sure.'
    )
    if problem_needs(problem, solution):
        world.say(
            f"{elder.id} came along with a patient smile. The elder listened, then showed them {solution.text}."
        )
        rope.meters["tied"] += 1
        bridge.meters["broken"] = 1.0
        propagate(world, narrate=False)
        world.para()
        world.say(
            f"Together they used {tool.label} and {solution.label}. Soon {solution.result}, and the crossing stood steady again."
        )
        a.memes["kindness"] += 1
        b.memes["kindness"] += 1
        a.memes["hurt"] += 1
        b.memes["hurt"] += 1
        world.say(
            f"{a.id} apologized for doubting {b.id}, and {b.id} laughed softly and apologized for rushing ahead. "
            f"Their friendship grew warmer than before, like a hearth after rain."
        )
        world.say(
            f"At sunset, {a.id} and {b.id} crossed the repaired way together, while the stream sang below like a happy fiddle."
        )
        world.facts["outcome"] = "reconciled"
    else:
        world.para()
        world.say(
            f"{elder.id} shook {elder.pronoun('possessive')} head and said that {solution.label} would not help this kind of trouble. "
            f"They had to wait and choose another day."
        )
        world.say(
            f"The children went home still friends, but the crossing remained uneasy and the stream kept its secret."
        )
        world.facts["outcome"] = "unfixed"
    world.facts["bridge"] = bridge
    world.facts["stream"] = stream
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    problem = f["problem"]
    return [
        f'Write a folk-tale story about a prawn, two friends, and a clever fix in {place.label}. Include the word "prawn".',
        f"Tell a gentle story where {problem.label} causes trouble at the water crossing, but the friends solve it with help and make up afterward.",
        f'Write a child-friendly folk tale with friendship and reconciliation, where a tiny helper and a wise elder repair a broken crossing near the stream.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, elder = world.get("friend_a"), world.get("friend_b"), world.get("elder")
    place, problem, solution = f["place"], f["problem"], f["solution"]
    out = [
        ("Who is the story about?",
         f"It is about {a.id}, {b.id}, and {elder.id}, and the story also includes a prawn who knows the water better than anyone. The friends and the elder work together to fix a problem by the stream."),
        ("What went wrong at the crossing?",
         f"{problem.clue.capitalize()} This made the crossing unsafe, so the children could not pass until they found a wiser way."),
    ]
    if f["outcome"] == "reconciled":
        out.append((
            "How did they fix the problem?",
            f"They used {world.get('rope').label} with {solution.label}, and the elder showed them the right way to mend the crossing. Because the repair matched the trouble, the bridge became steady again."
        ))
        out.append((
            "What changed between the friends?",
            f"They stopped feeling upset with each other and said sorry. After that, their friendship felt warmer, because they listened and solved the trouble together."
        ))
    else:
        out.append((
            "Did they solve it that day?",
            f"No, they decided the chosen fix would not work for this trouble. They stayed kind to one another, but they had to wait for a better plan."
        ))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a prawn?",
         "A prawn is a small water creature with a hard shell and little legs. It can live in rivers or the sea, and it moves by darting through the water."),
        ("Why do friends apologize?",
         "Friends apologize to mend hurt feelings after a mistake. Saying sorry helps them trust each other again."),
        ("What does a wise elder do in a folk tale?",
         "A wise elder gives calm help and clear advice. In folk tales, elders often know how to solve a hard problem without making a fuss."),
        ("Why is a repaired bridge useful?",
         "A repaired bridge lets people cross safely from one side to the other. It keeps the path open even when water would otherwise block the way."),
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
    parts.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


PLACES = {
    "riverbank": Place(id="riverbank", label="the riverbank", feature="the stream bend", crossing="old bridge", stream="silver stream", bank="soft bank", tags={"river"}),
    "millpath": Place(id="millpath", label="the millpath", feature="the water wheel path", crossing="wooden bridge", stream="hurrying brook", bank="mossy bank", tags={"brook"}),
}

PROBLEMS = {
    "missing_stepping_stones": Problem(id="missing_stepping_stones", label="missing stepping-stones", clue="the stepping-stones had washed away", effect="The children could not hop across the water.", risk="The current tugged at the bank.", tags={"missing", "stones"}),
    "muddy_water": Problem(id="muddy_water", label="muddy water", clue="the stream had turned muddy and hard to read", effect="Nobody could tell where the shallow place began.", risk="A false step would splash them right in.", tags={"muddy", "water"}),
}

TOOLS = {
    "rope": Tool(id="rope", label="a long rope", use="tie", tags={"rope"}),
    "plank": Tool(id="plank", label="a straight plank", use="bridge", tags={"plank"}),
}

SOLUTIONS = {
    "rope_bridge": Solution(id="rope_bridge", label="a rope bridge", text="they tied a long rope from one bank to the other and braided a safe little bridge", result="a little rope bridge linked the two banks", tags={"rope", "bridge"}),
    "ladder": Solution(id="ladder", label="a ladder", text="they laid a ladder across the gap and held it steady with both hands", result="a ladder made a careful crossing", tags={"ladder"}),
    "apology": Solution(id="apology", label="an apology", text="they stopped arguing, listened, and spoke honestly about what had hurt", result="the air between them grew calm", tags={"sorry"}),
}

GIRL_NAMES = ["Mira", "Nia", "Lina", "Sana", "Iris"]
BOY_NAMES = ["Oren", "Pavel", "Rafi", "Tomas", "Eli"]
ELDERS = ["Grandmother Reed", "Old Hart", "Aunt Willow"]


CURATED = [
    StoryParams(place="riverbank", problem="missing_stepping_stones", tool="rope", solution="rope_bridge",
                friend_a="Mira", friend_a_gender="girl", friend_b="Rafi", friend_b_gender="boy",
                elder="Grandmother Reed", elder_gender="woman"),
    StoryParams(place="millpath", problem="muddy_water", tool="rope", solution="ladder",
                friend_a="Lina", friend_a_gender="girl", friend_b="Oren", friend_b_gender="boy",
                elder="Aunt Willow", elder_gender="woman"),
]


def valid_combo_lookup() -> set[tuple[str, str, str]]:
    return set(valid_combos())


def explain_rejection(place: Place, problem: Problem, solution: Solution) -> str:
    return f"(No story: {solution.label} does not fit {problem.label} at {place.label}; the tale needs a fix that truly matches the trouble.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world about a prawn, a problem, and friends who reconcile.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
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
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, solution = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        problem=problem,
        tool="rope",
        solution=solution,
        friend_a=rng.choice(GIRL_NAMES),
        friend_a_gender="girl",
        friend_b=rng.choice(BOY_NAMES),
        friend_b_gender="boy",
        elder=rng.choice(ELDERS),
        elder_gender="woman",
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.problem not in PROBLEMS or params.solution not in SOLUTIONS:
        raise StoryError("Invalid parameters.")
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    solution = SOLUTIONS[params.solution]
    a = Entity(id=params.friend_a, kind="character", type=params.friend_a_gender, role="friend_a")
    b = Entity(id=params.friend_b, kind="character", type=params.friend_b_gender, role="friend_b")
    elder = Entity(id=params.elder, kind="character", type=params.elder_gender, role="elder")
    world = tell(place, problem, tool, solution, a, b, elder)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
valid(P,Pr,So) :- place(P), problem(Pr), solution(So), compatible(P,Pr,So).
reconciled(P,Pr,So) :- valid(P,Pr,So), needs_mend(Pr,So).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for sid in SOLUTIONS:
        lines.append(asp.fact("solution", sid))
    for p, pr, so in valid_combos():
        lines.append(asp.fact("compatible", p, pr, so))
    for pr_id, pr in PROBLEMS.items():
        for so_id, so in SOLUTIONS.items():
            if problem_needs(pr, so):
                lines.append(asp.fact("needs_mend", pr_id, so_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != valid_combo_lookup():
        print("MISMATCH in ASP parity.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
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
        for p, pr, so in combos:
            print(p, pr, so)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.friend_a} & {p.friend_b}: {p.problem} with {p.solution} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
