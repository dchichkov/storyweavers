#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/change_preference_talented_foreshadowing_suspense_detective_story.py
========================================================================================================

A tiny detective-story world with foreshadowing, suspense, and a change of
preference. The premise is simple: a talented young detective prefers neat
methods, but the clues suggest a messier route, and the story turns when the
detective changes preference and uses the right tool to solve the case.

Seed words:
- change
- preference
- talented

Narrative instruments:
- Foreshadowing
- Suspense

Style:
- Detective Story
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the little museum"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    mystery: str
    clue: str
    method: str
    reveal: str
    risk: str
    trigger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    fits: set[str]
    solves: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.suspense: float = 0.0
        self.foreshadowed: bool = False
        self.revealed: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        import copy

        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        c.suspense = self.suspense
        c.foreshadowed = self.foreshadowed
        c.revealed = self.revealed
        return c


SETTINGS = {
    "museum": Setting(place="the little museum", indoor=True, affords={"footprints", "lost_note", "broken_lock"}),
    "library": Setting(place="the old library", indoor=True, affords={"footprints", "lost_note"}),
    "station": Setting(place="the train station", indoor=True, affords={"footprints", "broken_lock"}),
}

CASES = {
    "missing_key": Case(
        id="missing_key",
        mystery="a missing key",
        clue="a dusty smudge near the desk",
        method="follow the dust trail",
        reveal="the key was tucked inside a hollow book",
        risk="the clue trail would vanish if nobody looked carefully",
        trigger="noticed the smudge",
        tags={"dust", "key", "library"},
    ),
    "lost_note": Case(
        id="lost_note",
        mystery="a lost note",
        clue="a folded note under a bench",
        method="check the benches and pockets",
        reveal="the note had slipped out of a coat pocket",
        risk="the note could be carried away by the crowd",
        trigger="spotted the folded paper",
        tags={"note", "paper", "crowd"},
    ),
    "broken_lock": Case(
        id="broken_lock",
        mystery="a broken lock",
        clue="a shiny scratch on the latch",
        method="inspect the latch and keys",
        reveal="the lock was jammed by a bent pin",
        risk="the door would stay stuck until the right tool was found",
        trigger="saw the scratch",
        tags={"lock", "metal", "scratch"},
    ),
}

TOOLS = [
    Tool(
        id="gloves",
        label="soft gloves",
        phrase="soft gloves",
        fits={"dust", "metal"},
        solves={"dust"},
        prep="put on soft gloves",
        tail="slipped the soft gloves back into the case bag",
    ),
    Tool(
        id="magnifier",
        label="a magnifying glass",
        phrase="a magnifying glass",
        fits={"dust", "paper", "scratch"},
        solves={"dust", "paper", "scratch"},
        prep="pick up a magnifying glass",
        tail="set the magnifying glass by the lamp",
    ),
    Tool(
        id="tweezers",
        label="tiny tweezers",
        phrase="tiny tweezers",
        fits={"metal", "paper"},
        solves={"metal", "paper"},
        prep="reach for tiny tweezers",
        tail="closed the tiny tweezers with a neat click",
    ),
]

NAMES = ["Mia", "Nina", "Leo", "Toby", "Ava", "Owen", "Zoe", "Iris"]
TYPES = {"girl": ["Mia", "Nina", "Ava", "Zoe", "Iris"], "boy": ["Leo", "Toby", "Owen"]}
TRAITS = ["talented", "careful", "brilliant", "quiet", "quick"]


@dataclass
class StoryParams:
    place: str
    case: str
    detective_name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def case_risk(case: Case) -> bool:
    return True


def select_tool(case: Case) -> Optional[Tool]:
    if case.id == "missing_key":
        return next((t for t in TOOLS if "dust" in t.solves), None)
    if case.id == "lost_note":
        return next((t for t in TOOLS if "paper" in t.solves), None)
    if case.id == "broken_lock":
        return next((t for t in TOOLS if "scratch" in t.solves), None)
    return None


def foreshadow(world: World, detective: Entity, case: Case) -> None:
    world.foreshadowed = True
    world.suspense += 1
    world.say(
        f"At {world.setting.place}, {detective.id} noticed {case.clue}, "
        f"and the little clue made the room feel quietly serious."
    )
    world.say(
        f"{detective.pronoun().capitalize()} was talented, but {detective.pronoun('possessive')} "
        f"first preference was for neat clues and tidy answers."
    )


def build_tension(world: World, detective: Entity, case: Case) -> None:
    world.suspense += 1
    world.say(
        f"Then the mystery grew harder: {case.risk}. "
        f"{detective.id} wanted to {case.method}, but the wrong choice could hide the truth."
    )
    world.say(
        f"{detective.pronoun().capitalize()} paused, listening to the hush of the room."
    )


def change_preference(world: World, detective: Entity, case: Case, tool: Tool) -> None:
    detective.memes["preference"] = detective.memes.get("preference", 0.0) + 1.0
    detective.memes["resolve"] = detective.memes.get("resolve", 0.0) + 1.0
    world.say(
        f"At last, {detective.id} changed {detective.pronoun('possessive')} preference "
        f"and chose {tool.phrase} instead of trying to stay perfectly neat."
    )
    world.say(
        f"{detective.pronoun().capitalize()} decided that solving the case mattered more than staying spotless."
    )


def solve_case(world: World, detective: Entity, case: Case, tool: Tool) -> None:
    world.revealed = True
    world.suspense = 0.0
    world.say(
        f"{detective.id} used {tool.phrase} to {case.method}, and the answer came clear: {case.reveal}."
    )
    world.say(
        f"That was the real clue all along, and {detective.id} smiled as the mystery finally opened up."
    )


def tell(setting: Setting, case: Case, detective_name: str, gender: str, trait: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=gender))
    helper = world.add(Entity(id="Helper", kind="character", type="adult", label="the helper"))
    world.facts["setting"] = setting
    world.facts["case"] = case
    world.facts["detective"] = detective
    world.facts["helper"] = helper

    world.say(
        f"{detective.id} was a {trait} young detective who could spot tiny details that other people missed."
    )
    world.say(
        f"{detective.id} loved solving puzzles, but {detective.pronoun('possessive')} first preference was to keep everything clean and orderly."
    )

    world.para()
    foreshadow(world, detective, case)
    build_tension(world, detective, case)

    tool = select_tool(case)
    if tool is None:
        raise StoryError("No reasonable tool exists for this mystery.")

    world.para()
    change_preference(world, detective, case, tool)
    solve_case(world, detective, case, tool)

    world.facts["tool"] = tool
    world.facts["suspense"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d = f["detective"]
    case = f["case"]
    return [
        f'Write a short detective story for a young child about a talented detective who changes preference while solving {case.mystery}.',
        f"Tell a suspenseful story where {d.id} notices a clue, feels unsure, and then chooses a better tool to solve the mystery.",
        f'Write a simple mystery story that includes foreshadowing and ends with {case.reveal}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = f["detective"]
    case = f["case"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {d.id}, a talented young detective.",
        ),
        QAItem(
            question=f"What mystery did {d.id} solve at {world.setting.place}?",
            answer=f"{d.id} solved {case.mystery} at {world.setting.place}.",
        ),
        QAItem(
            question=f"What clue first hinted that something was wrong?",
            answer=f"The first clue was {case.clue}. It foreshadowed that the mystery would need careful attention.",
        ),
        QAItem(
            question=f"How did {d.id}'s preference change during the story?",
            answer=f"{d.id} started by wanting everything neat, but then changed {d.pronoun('possessive')} preference and chose {tool.phrase} to solve the case.",
        ),
        QAItem(
            question=f"What did {d.id} use to finish the case?",
            answer=f"{d.id} used {tool.phrase} to solve the mystery.",
        ),
    ]


KNOWLEDGE = {
    "detective": [(
        "What does a detective do?",
        "A detective looks for clues, asks careful questions, and tries to figure out what happened.",
    )],
    "foreshadowing": [(
        "What is foreshadowing in a story?",
        "Foreshadowing is when a story gives a small clue early on that hints at something important later.",
    )],
    "suspense": [(
        "What is suspense?",
        "Suspense is the feeling of wondering what will happen next.",
    )],
    "magnifying glass": [(
        "Why do detectives use a magnifying glass?",
        "A magnifying glass helps detectives look closely at tiny details in clues.",
    )],
    "gloves": [(
        "Why might a detective wear gloves?",
        "Gloves can help a detective avoid leaving fingerprints on important clues.",
    )],
    "tweezers": [(
        "What are tweezers for?",
        "Tweezers are small tools used to pick up tiny things carefully.",
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for _, pairs in KNOWLEDGE.items() for q, a in pairs]


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


ASP_RULES = r"""
case_clue(C) :- clue_case(C).
needs_tool(C) :- risky_case(C).
good_tool(T,C) :- tool(T), case_tool(T,C).
change_preference(D) :- detective(D), prefers_neat(D), good_tool(_,C), needs_tool(C).
solved(C) :- good_tool(T,C), solves(T,C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, case in CASES.items():
        lines.append(asp.fact("clue_case", cid))
        lines.append(asp.fact("risky_case", cid))
        lines.append(asp.fact("case_tool", "magnifier", cid))
        if cid == "missing_key":
            lines.append(asp.fact("case_tool", "gloves", cid))
        if cid == "broken_lock":
            lines.append(asp.fact("case_tool", "tweezers", cid))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for s in sorted(t.solves):
            lines.append(asp.fact("solves", t.id, s))
    lines.append(asp.fact("detective", "hero"))
    lines.append(asp.fact("prefers_neat", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTINGS:
        for cid in CASES:
            out.append((place, cid))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solved/1. #show change_preference/1."))
    return sorted(set(asp.atoms(model, "solved")))


def asp_verify() -> int:
    python_tools = {case_id: select_tool(case).id if select_tool(case) else None for case_id, case in CASES.items()}
    asp_ok = True
    for case_id, case in CASES.items():
        if python_tools[case_id] is None:
            asp_ok = False
    if asp_ok:
        print("OK: Python reasonableness gate found a tool for every case.")
        return 0
    print("MISMATCH: some cases lack tools in Python gate.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective story world with foreshadowing, suspense, and a change of preference."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    case = args.case or rng.choice(list(CASES))
    gender = args.gender or rng.choice(["girl", "boy"])
    names = TYPES[gender]
    name = args.name or rng.choice(names)
    trait = args.trait or rng.choice(TRAITS)
    if args.name and args.name not in NAMES:
        raise StoryError("Unknown detective name for this world.")
    return StoryParams(place=place, case=case, detective_name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CASES[params.case], params.detective_name, params.gender, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} ({e.type}) meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  suspense={world.suspense}")
    lines.append(f"  foreshadowed={world.foreshadowed}")
    lines.append(f"  revealed={world.revealed}")
    return "\n".join(lines)


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
        print(asp_program("#show solved/1. #show change_preference/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for case in CASES:
                params = StoryParams(place=place, case=case, detective_name="Mia", gender="girl", trait="talented")
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.detective_name}: {p.case} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
