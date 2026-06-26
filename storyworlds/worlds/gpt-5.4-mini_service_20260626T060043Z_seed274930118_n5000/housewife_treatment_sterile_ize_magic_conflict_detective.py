#!/usr/bin/env python3
"""
Standalone storyworld: a detective-story domain about a housewife, a treatment,
and a careful sterile-ize step that solves a magic conflict.

The premise is small and classical: a household mystery leaves someone worried
that a treatment may be unsafe or contaminated, so a detective-like helper
follows the clues, checks the facts, and discovers a simple magical fix that
makes the treatment sterile and trustworthy again.
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


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "wife", "housewife", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "husband", "father", "detective"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little house"
    afford_magic: bool = True
    afford_conflict: bool = True


@dataclass
class Case:
    id: str
    clue: str
    treatment: str
    risk: str
    resolution: str
    mess: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}
        self.trace_notes: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "house": Setting(place="the little house", afford_magic=True, afford_conflict=True),
    "clinic": Setting(place="the quiet clinic", afford_magic=True, afford_conflict=True),
    "garden_room": Setting(place="the sunlit garden room", afford_magic=True, afford_conflict=True),
}

CASES = {
    "bandage": Case(
        id="bandage",
        clue="a bandage on the table",
        treatment="bandage treatment",
        risk="dusty",
        resolution="sterile-ized",
        mess="dust",
        keyword="sterile-ize",
        tags={"sterile", "treatment"},
    ),
    "salve": Case(
        id="salve",
        clue="a salve jar with a loose lid",
        treatment="salve treatment",
        risk="unclean",
        resolution="sterile-ized",
        mess="smudge",
        keyword="housewife",
        tags={"treatment"},
    ),
    "tea": Case(
        id="tea",
        clue="a cup of herbal tea beside the sink",
        treatment="magic tea treatment",
        risk="questionable",
        resolution="sterile-ized",
        mess="spill",
        keyword="magic",
        tags={"magic", "treatment"},
    ),
}

TOOLS = {
    "spark": Tool(
        id="spark",
        label="a silver spark",
        phrase="a silver spark of magic",
        solves={"dust", "smudge", "spill"},
        prep="lift the spark over the treatment",
        tail="let the spark dance over the rim until it shone clean",
    ),
    "lamp": Tool(
        id="lamp",
        label="a bright lamp",
        phrase="a bright lamp for careful work",
        solves={"dust"},
        prep="shine the lamp across the table",
        tail="inspect the treatment under the lamp until every speck was gone",
    ),
    "cloth": Tool(
        id="cloth",
        label="a fresh white cloth",
        phrase="a fresh white cloth",
        solves={"smudge", "spill"},
        prep="wrap the cloth around the jar",
        tail="wipe the outside until it looked neat again",
    ),
}

NAMES = ["Mira", "Lena", "Nora", "Ivy", "Clara", "June"]
DETECTIVES = ["Inspector Vale", "Detective Morrow", "Officer Finch", "Miss Reed"]
TRAITS = ["careful", "curious", "calm", "sharp-eyed", "patient"]


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
case_risk(C) :- case(C), risk(C, R), mess(C, R).
tool_suitable(T, C) :- tool(T), case_risk(C), solves(T, R), risk(C, R).
valid(C, T) :- case_risk(C), tool_suitable(T, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, c in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("risk", cid, c.mess))
        lines.append(asp.fact("mess", cid, c.mess))
        for tag in sorted(c.tags):
            lines.append(asp.fact("tag", cid, tag))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for s in sorted(t.solves):
            lines.append(asp.fact("solves", tid, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for cid, c in CASES.items():
        for tid, t in TOOLS.items():
            if c.mess in t.solves:
                out.append((cid, tid))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python reasonableness gate")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    case: str
    tool: str
    housewife_name: str
    detective_name: str
    trait: str
    seed: Optional[int] = None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.case and args.tool:
        c = CASES[args.case]
        t = TOOLS[args.tool]
        if c.mess not in t.solves:
            raise StoryError(
                f"(No story: {t.label} cannot make the {c.id} treatment sterile-ized; "
                f"try a tool that solves {c.mess}.)"
            )
    combos = [x for x in valid_combos()
              if (args.case is None or x[0] == args.case)
              and (args.tool is None or x[1] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    case_id, tool_id = rng.choice(sorted(combos))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    return StoryParams(
        setting=setting,
        case=case_id,
        tool=tool_id,
        housewife_name=args.housewife_name or rng.choice(NAMES),
        detective_name=args.detective_name or rng.choice(DETECTIVES),
        trait=args.trait or rng.choice(TRAITS),
    )


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    housewife = world.add(Entity(
        id=params.housewife_name,
        kind="character",
        type="housewife",
        label="housewife",
        memes={"worry": 0.0, "hope": 0.0, "conflict": 0.0},
    ))
    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type="detective",
        label="detective",
        memes={"focus": 0.0, "confidence": 0.0},
    ))
    case = world.add(Entity(
        id="case",
        type="treatment",
        label=CASES[params.case].treatment,
        phrase=CASES[params.case].clue,
        caretaker=housewife.id,
        meters={"dirty": 1.0, CASES[params.case].mess: 1.0},
        memes={"risk": 1.0},
    ))
    tool_def = TOOLS[params.tool]
    tool = world.add(Entity(
        id=tool_def.id,
        type="tool",
        label=tool_def.label,
        phrase=tool_def.phrase,
        owner=detective.id,
        meters={"magic": 1.0},
    ))
    world.facts.update(
        housewife=housewife,
        detective=detective,
        case=case,
        tool=tool,
        case_def=CASES[params.case],
        tool_def=tool_def,
        params=params,
    )
    return world


def narrate_story(world: World) -> None:
    f = world.facts
    hw: Entity = f["housewife"]
    det: Entity = f["detective"]
    case: Entity = f["case"]
    cdef: Case = f["case_def"]
    tool_def: Tool = f["tool_def"]

    world.say(
        f"In {world.setting.place}, {hw.id} was a {f['params'].trait} housewife who kept "
        f"every shelf in order."
    )
    world.say(
        f"One morning she found {case.phrase}, and the little treatment looked uneasy, as if it had forgotten how to be safe."
    )
    world.para()
    world.say(
        f"{det.id} arrived like a detective in a quiet mystery, looked at the clue, and said, "
        f'"This case smells of {cdef.mess}."'
    )
    hw.memes["worry"] += 1
    det.memes["focus"] += 1
    world.say(
        f"{hw.id} worried that the treatment would stay {cdef.risk}, because nobody wanted an unsafe cure in the house."
    )
    world.say(
        f"{hw.id} asked whether the treatment could still be fixed without throwing it away."
    )
    world.para()
    world.say(
        f"{det.id} took out {tool_def.phrase} and said, \"We can {cdef.keyword} it.\""
    )
    world.say(f"He followed the clue step by step: {tool_def.prep}, then {tool_def.tail}.")
    case.meters["dirty"] = 0.0
    case.meters[cdef.mess] = 0.0
    case.memes["risk"] = 0.0
    case.label = f"{cdef.resolution} treatment"
    hw.memes["worry"] = 0.0
    hw.memes["hope"] += 1
    det.memes["confidence"] += 1
    world.say(
        f"In the end, the treatment was {cdef.resolution}, {hw.id} smiled, and the house felt calm again."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    return [
        f'Write a short detective story with the words "housewife", "treatment", and "sterile-ize".',
        f"Tell a gentle mystery where {params.housewife_name} the housewife needs a {CASES[params.case].treatment}, "
        f"and {params.detective_name} solves the problem with magic.",
        f"Write a child-friendly detective tale in which a treatment is made sterile-ized and the conflict goes away.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    hw: Entity = f["housewife"]
    det: Entity = f["detective"]
    case: Entity = f["case"]
    cdef: Case = f["case_def"]
    tool_def: Tool = f["tool_def"]
    return [
        QAItem(
            question=f"Who was the housewife in the story?",
            answer=f"The housewife was {hw.id}, and she was careful about the treatment in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did the detective notice about the treatment?",
            answer=f"{det.id} noticed that the treatment looked {cdef.mess} and needed to be sterile-ized.",
        ),
        QAItem(
            question=f"How did the detective fix the problem?",
            answer=f"{det.id} used {tool_def.label} and followed a magical method to sterile-ize the treatment, so it became safe again.",
        ),
        QAItem(
            question=f"Why was {hw.id} worried at first?",
            answer=f"{hw.id} worried because the treatment was {cdef.risk}, and that made the little mystery feel serious.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully for clues, asks questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What does sterile mean?",
            answer="Sterile means clean and free from germs, so something safer is ready to use.",
        ),
        QAItem(
            question="What is a treatment?",
            answer="A treatment is care that helps someone or something get better or stay safe.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a surprising special power that can change what happens in a story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="house", case="bandage", tool="lamp", housewife_name="Mira", detective_name="Inspector Vale", trait="careful"),
    StoryParams(setting="clinic", case="salve", tool="cloth", housewife_name="Nora", detective_name="Detective Morrow", trait="curious"),
    StoryParams(setting="garden_room", case="tea", tool="spark", housewife_name="Clara", detective_name="Miss Reed", trait="patient"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective storyworld with magic, conflict, and sterile-ize.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--housewife-name")
    ap.add_argument("--detective-name")
    ap.add_argument("--trait", choices=TRAITS)
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


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    narrate_story(world)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} valid case/tool combos:")
        for c, t in combos:
            print(f"  {c} + {t}")
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
            except StoryError as e:
                print(e)
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
            header = f"### {p.housewife_name}: {p.case} with {p.tool} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
