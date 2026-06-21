#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bureaucracy_system_problem_solving_humor_twist_slice.py
========================================================================================

A small slice-of-life storyworld about a friendly local bureaucracy system:
forms, stamps, queues, and one ordinary problem that gets solved in a slightly
funny way with a twist.

The world keeps the story grounded in simulated state. A misplaced form creates
real pressure, helpers have meters and memes, and the ending proves what changed.
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "clerk", "aunt"}
        male = {"boy", "man", "father", "uncle", "assistant"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Desk:
    id: str
    label: str
    queue_name: str
    forms: list[str] = field(default_factory=list)
    stamps: list[str] = field(default_factory=list)
    twist: str = ""
    helps_with: set[str] = field(default_factory=set)
    fixes: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Problem:
    id: str
    label: str
    document: str
    missing: str
    ask: str
    hassle: str
    fixable_by: set[str]
    comic: str
    twist: str
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
class SystemTool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    fixes: set[str]
    funny: str
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


def _r_rush(world: World) -> list[str]:
    out: list[str] = []
    clerk = world.entities.get("clerk")
    if clerk and clerk.meters["stressed"] >= THRESHOLD and clerk.meters["queue"] >= THRESHOLD:
        sig = ("rush",)
        if sig not in world.fired:
            world.fired.add(sig)
            clerk.memes["flustered"] += 1
            out.append("The front desk got a little too busy for its own good.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    problem = world.entities.get("problem")
    tool = world.entities.get("tool")
    if not problem or not tool:
        return out
    if problem.meters["solved"] >= THRESHOLD:
        sig = ("fix", problem.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("The line suddenly made more sense.")
    return out


CAUSAL_RULES = [Rule("rush", _r_rush), Rule("fix", _r_fix)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(problem: Problem, tool: SystemTool) -> bool:
    return problem.id in tool.fixes or problem.label in tool.fixes


def sensible_tools() -> list[SystemTool]:
    return [t for t in TOOLS.values() if t.helps and t.fixes]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, p in PROBLEMS.items():
        for tid, t in TOOLS.items():
            if reasonableness_gate(p, t):
                combos.append((pid, tid))
    return combos


def predict(world: World, problem_id: str, tool_id: str) -> dict:
    sim = world.copy()
    p = sim.get("problem_cfg")
    t = sim.get("tool_cfg")
    _resolve_problem(sim, sim.get("clerk"), p, t, narrate=False)
    return {
        "solved": sim.get("problem").meters["solved"] >= THRESHOLD,
        "confusion": sim.get("hall").meters["confusion"],
    }


def _resolve_problem(world: World, clerk: Entity, problem: Problem, tool: SystemTool, narrate: bool = True) -> None:
    problem_ent = world.get("problem")
    hall = world.get("hall")
    clerk.meters["queue"] += 1
    clerk.memes["duty"] += 1
    clerk.meters["stressed"] += 1
    problem_ent.meters["attention"] += 1
    if narrate:
        world.say(
            f"At the little office, {clerk.id} stood behind the desk while the queue kept growing. "
            f"Someone had brought in {problem.document}, and the whole system seemed to be missing {problem.missing}."
        )
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"{clerk.id} squinted at the papers, then reached for {tool.label}. "
            f"{tool.funny.capitalize()} {tool.phrase}."
        )
    problem_ent.meters["solved"] += 1
    hall.meters["confusion"] = 0
    clerk.meters["stressed"] = 0
    clerk.memes["relief"] += 1
    hall.memes["order"] += 1
    if narrate:
        world.say(
            f"The stamp landed with a cheerful thump, and the {problem.label} was fixed without any drama."
        )


def setup(world: World, clerk: Entity, neighbor: Entity, problem: Problem) -> None:
    clerk.memes["kindness"] += 1
    neighbor.memes["hope"] += 1
    world.say(
        f"{clerk.id} worked the front desk of the neighborhood office, where the queue was small and the tea was bad. "
        f"{neighbor.id} arrived with a small family problem and a face that said the morning had already been long."
    )
    world.say(
        f"The issue was {problem.label}: the form said {problem.document}, but the system was missing {problem.missing}."
    )


def joke(world: World, neighbor: Entity, problem: Problem) -> None:
    neighbor.memes["humor"] += 1
    world.say(
        f'{neighbor.id} whispered, "This bureaucracy runs on coffee, ink, and three people apologizing at once." '
        f"Even the waiting chair seemed to agree."
    )
    world.say(
        f"{problem.comic.capitalize()} {problem.ask}."
    )


def twist(world: World, clerk: Entity, tool: SystemTool, problem: Problem) -> None:
    clerk.memes["surprise"] += 1
    world.say(
        f"Then the twist arrived: the missing piece was not lost at all. It was tucked into the back of the printer tray, "
        f"where yesterday's flyer had pressed it flat."
    )
    world.say(
        f'{clerk.id} blinked, laughed once, and said, "Well, that explains the system." '
        f"{tool.funny.capitalize()}."
    )


def ending(world: World, clerk: Entity, neighbor: Entity, problem: Problem) -> None:
    world.say(
        f"By lunchtime, the line was moving again. {clerk.id} slid the approved paper across the counter, and {neighbor.id} "
        f"slipped it into a folder before it could escape."
    )
    world.say(
        f"The office looked ordinary again: stamps, cups, a humming printer, and one less problem than before."
    )


def tell(problem: Problem, tool: SystemTool, clerk_name: str = "Mara", clerk_type: str = "clerk",
         neighbor_name: str = "Ben", neighbor_type: str = "boy") -> World:
    world = World()
    clerk = world.add(Entity(id="clerk", kind="character", type=clerk_type, label=clerk_name, role="clerk"))
    neighbor = world.add(Entity(id="neighbor", kind="character", type=neighbor_type, label=neighbor_name, role="neighbor"))
    hall = world.add(Entity(id="hall", type="place", label="the hallway"))
    p = world.add(Entity(id="problem", type="problem", label=problem.label))
    t = world.add(Entity(id="tool", type="tool", label=tool.label))
    world.facts.update(problem_cfg=problem, tool_cfg=tool)

    setup(world, clerk, neighbor, problem)
    world.para()
    joke(world, neighbor, problem)
    world.say(
        f"{clerk.id} checked the forms, tapped the folder twice, and called it a system problem rather than a disaster."
    )
    world.para()
    _resolve_problem(world, clerk, problem, tool)
    world.para()
    twist(world, clerk, tool, problem)
    ending(world, clerk, neighbor, problem)

    world.facts.update(
        clerk=clerk, neighbor=neighbor, hall=hall, problem=p, tool=t,
        solved=p.meters["solved"] >= THRESHOLD
    )
    return world


@dataclass
class StoryParams:
    problem: str
    tool: str
    clerk_name: str = "Mara"
    clerk_type: str = "clerk"
    neighbor_name: str = "Ben"
    neighbor_type: str = "boy"
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


PROBLEMS = {
    "permit": Problem(
        id="permit",
        label="a permit request",
        document="a permit request",
        missing="the date stamp",
        ask="Who forgot the date stamp?",
        hassle="the paper looked right but could not move without a date",
        fixable_by={"date_stamp", "index_card"},
        comic="The poor file had all the confidence of a sandwich in the rain",
        twist="the date stamp was hiding under a flyer",
        tags={"bureaucracy", "system"},
    ),
    "library_card": Problem(
        id="library_card",
        label="a library card form",
        document="a library card form",
        missing="the address line",
        ask="Why does every line on this form have a line of its own?",
        hassle="the page could not enter the system without an address",
        fixable_by={"address_label", "sticky_note"},
        comic="The printer made a noise like it had just heard a joke about taxes",
        twist="the address was on a sticker folded inside the envelope",
        tags={"bureaucracy", "system"},
    ),
    "parcel": Problem(
        id="parcel",
        label="a parcel slip",
        document="a parcel slip",
        missing="the apartment number",
        ask="How can a box know where to go if the number is playing hide and seek?",
        hassle="the delivery system needed one tiny number before it could continue",
        fixable_by={"apartment_label", "sticky_note"},
        comic="The line looked like it had grown roots and settled in for the week",
        twist="the apartment number was written on the back of the receipt",
        tags={"bureaucracy", "system"},
    ),
}

TOOLS = {
    "date_stamp": SystemTool(
        id="date_stamp", label="the date stamp", phrase="it clicked neatly onto the paper",
        helps={"permit"}, fixes={"permit"}, funny="With a tiny thunk", tags={"bureaucracy"}
    ),
    "address_label": SystemTool(
        id="address_label", label="an address label", phrase="it stuck on straight and true",
        helps={"library_card"}, fixes={"library_card"}, funny="With a peel and a grin", tags={"system"}
    ),
    "sticky_note": SystemTool(
        id="sticky_note", label="a sticky note", phrase="it perched on the corner like a polite bird",
        helps={"library_card", "parcel"}, fixes={"library_card", "parcel"}, funny="With a bright yellow wink", tags={"humor"}
    ),
    "index_card": SystemTool(
        id="index_card", label="an index card", phrase="it slipped into place as a backup copy",
        helps={"permit"}, fixes={"permit"}, funny="With a very serious little shuffle", tags={"problem-solving"}
    ),
    "apartment_label": SystemTool(
        id="apartment_label", label="an apartment label", phrase="it went on like it had always belonged there",
        helps={"parcel"}, fixes={"parcel"}, funny="With a careful press", tags={"system"}
    ),
}

CURATED = [
    StoryParams(problem="permit", tool="date_stamp", clerk_name="Mara", neighbor_name="Ben", clerk_type="woman", neighbor_type="boy"),
    StoryParams(problem="library_card", tool="sticky_note", clerk_name="Ivy", neighbor_name="Noah", clerk_type="woman", neighbor_type="boy"),
    StoryParams(problem="parcel", tool="apartment_label", clerk_name="Tess", neighbor_name="Lina", clerk_type="woman", neighbor_type="girl"),
]


KNOWLEDGE = {
    "bureaucracy": [("What is bureaucracy?",
                     "Bureaucracy is a system of offices, forms, and rules that helps people keep things organized. It can be slow, but it also helps everyone follow the same steps.")],
    "system": [("What is a system?",
                "A system is a set of parts that work together to do a job. If one small part is missing, the whole thing can get stuck.")],
    "stamp": [("What does a stamp do at an office?",
               "A stamp marks paper quickly, so a clerk can show that the paper was checked or approved.")],
    "queue": [("Why do people wait in a queue?",
               "People wait in a queue so each person can be helped in order. That keeps things fair and calm.")],
    "printer": [("Why can a printer be funny in a story?",
                  "Printers can make strange noises, get tired, or hide important papers in silly places.")],
    "sticky_note": [("What is a sticky note?",
                     "A sticky note is a small piece of paper with a strip of glue on one side. It can stick to a page and remind people about something.")],
}


def valid_story_params() -> list[tuple[str, str]]:
    return valid_combos()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: Problem = f["problem_cfg"]
    t: SystemTool = f["tool_cfg"]
    return [
        f'Write a slice-of-life story about {p.label} in a small office that includes the words "bureaucracy" and "system".',
        f"Tell a gentle office story where a clerk solves {p.label} with {t.label}, with a funny twist and a calm ending.",
        f"Write a story where a tiny bureaucracy problem is fixed by paying attention to one missing detail, and the joke lands without anyone being mean.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    clerk: Entity = f["clerk"]
    neighbor: Entity = f["neighbor"]
    problem_cfg: Problem = f["problem_cfg"]
    tool: SystemTool = f["tool_cfg"]
    qa = [
        ("Who is the story about?",
         f"It is about {clerk.id}, who works at the office, and {neighbor.id}, who came in with a small problem."),
        ("What was the problem?",
         f"It was {problem_cfg.label}. The form had one missing detail, so the system could not move it forward at first."),
        ("How did they solve it?",
         f"{clerk.id} used {tool.label} and checked the paperwork carefully. That fixed the missing piece and let the form pass through the system."),
        ("What was the twist?",
         f"The missing piece was not lost at all; it had been tucked into the printer tray or hidden on the back of the paper. That meant the answer was right there in the office the whole time."),
        ("How did the ending feel?",
         f"The office went back to its ordinary rhythm, and the line started moving again. The problem was solved without fuss, which made the whole scene feel quietly funny."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["problem_cfg"].tags) | set(world.facts["tool_cfg"].tags)
    out = []
    for key in ["bureaucracy", "system", "stamp", "queue", "printer", "sticky_note"]:
        if key in tags or key in {"bureaucracy", "system"}:
            out.extend(KNOWLEDGE.get(key, []))
    return out


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


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for fix in sorted(t.fixes):
            lines.append(asp.fact("fixes", tid, fix))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P,T) :- problem(P), tool(T), fixes(T,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH between ASP and Python valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small bureaucracy storyworld with a problem-solving twist.")
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--clerk-name")
    ap.add_argument("--neighbor-name")
    ap.add_argument("--clerk-type", choices=["woman", "man", "clerk", "assistant"])
    ap.add_argument("--neighbor-type", choices=["girl", "boy", "woman", "man"])
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
    if args.problem and args.tool and (args.problem, args.tool) not in combos:
        raise StoryError("That tool does not fit that problem in this office.")
    pool = [c for c in combos if (args.problem is None or c[0] == args.problem) and (args.tool is None or c[1] == args.tool)]
    if not pool:
        raise StoryError("(No valid combination matches the given options.)")
    problem, tool = rng.choice(sorted(pool))
    clerk_name = args.clerk_name or rng.choice(["Mara", "Ivy", "Tess", "June", "Nina"])
    neighbor_name = args.neighbor_name or rng.choice(["Ben", "Lina", "Owen", "Mina", "Noah"])
    clerk_type = args.clerk_type or rng.choice(["woman", "assistant", "clerk"])
    neighbor_type = args.neighbor_type or rng.choice(["boy", "girl"])
    return StoryParams(
        problem=problem,
        tool=tool,
        clerk_name=clerk_name,
        clerk_type=clerk_type,
        neighbor_name=neighbor_name,
        neighbor_type=neighbor_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.problem not in PROBLEMS or params.tool not in TOOLS:
        raise StoryError("Invalid params.")
    if (params.problem, params.tool) not in valid_combos():
        raise StoryError("That tool does not fit that problem in this office.")
    world = tell(PROBLEMS[params.problem], TOOLS[params.tool],
                 clerk_name=params.clerk_name, clerk_type=params.clerk_type,
                 neighbor_name=params.neighbor_name, neighbor_type=params.neighbor_type)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
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
            print(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (problem, tool) combos:\n")
        for problem, tool in combos:
            print(f"  {problem:14} {tool}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.problem} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
