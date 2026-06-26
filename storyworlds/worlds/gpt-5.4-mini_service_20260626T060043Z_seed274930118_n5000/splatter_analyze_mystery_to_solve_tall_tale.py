#!/usr/bin/env python3
"""
storyworlds/worlds/splatter_analyze_mystery_to_solve_tall_tale.py
==================================================================

A small tall-tale storyworld about a mystery to solve: something splatters,
somebody must analyze the clues, and a clever child finds the answer in time.

Premise:
- A grand, funny mystery appears in a tiny barnyard / fairground / kitchen-like
  setting.
- One character causes a strange splatter.
- Another character notices details, analyzes the clue pattern, and solves the
  mystery.
- The ending shows the world changed: the culprit is named, the mess is
  explained, and the problem is fixed or safely contained.

This world is intentionally compact: fewer valid stories, but each one has a
clear clue trail, a reasoned deduction, and a satisfying ending.
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    placed_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue_word: str
    action: str
    gerund: str
    splash_kind: str
    splash_causes: str
    evidence: str
    source_type: str
    source_label: str
    source_phrase: str
    reveal: str
    place_hint: str = ""


@dataclass
class Solver:
    id: str
    type: str
    label: str
    trait: str
    name_style: str = "child"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

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
    apply: Callable[[World], list[str]]


def _r_splatter(world: World) -> list[str]:
    out: list[str] = []
    source = world.facts.get("source")
    if not source:
        return out
    sig = ("splatter", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    source.meters["splash"] = source.meters.get("splash", 0.0) + 1.0
    world.facts["splash_seen"] = True
    out.append(f"A great splatter burst from {source.label}.")
    return out


def _r_analyze(world: World) -> list[str]:
    out: list[str] = []
    solver = world.facts.get("solver")
    source = world.facts.get("source")
    clue = world.facts.get("clue")
    if not (solver and source and clue):
        return out
    sig = ("analyze", solver.id)
    if sig in world.fired:
        return out
    if world.facts.get("splash_seen"):
        world.fired.add(sig)
        solver.memes["curiosity"] = solver.memes.get("curiosity", 0.0) + 1.0
        world.facts["analysis_done"] = True
        out.append(
            f"{solver.id} looked at the splatter, counted the dots, and analyzed the clue like a barnyard detective."
        )
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    solver = world.facts.get("solver")
    source = world.facts.get("source")
    clue = world.facts.get("clue")
    if not (solver and source and clue):
        return out
    sig = ("reveal", solver.id)
    if sig in world.fired:
        return out
    if world.facts.get("analysis_done") and clue.matches(source):
        world.fired.add(sig)
        world.facts["solved"] = True
        out.append(f"The mystery was solved: {source.label} was the one who made the mess.")
    return out


CAUSAL_RULES = [
    Rule("splatter", _r_splatter),
    Rule("analyze", _r_analyze),
    Rule("reveal", _r_reveal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


@dataclass
class Clue:
    id: str
    word: str
    source_id: str
    source_kind: str
    source_label: str
    splatter_shape: str
    places: set[str] = field(default_factory=set)
    smell: str = ""
    color: str = ""

    def matches(self, source: Entity) -> bool:
        return source.id == self.source_id


SETTINGS = {
    "barn": Setting(place="the barn", indoors=False, affords={"splatter"}),
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"splatter"}),
    "fair": Setting(place="the county fair", indoors=False, affords={"splatter"}),
}

MYSTERIES = {
    "pumpkin": Mystery(
        id="pumpkin",
        clue_word="splatter",
        action="splatter pumpkin goo",
        gerund="splatting pumpkin goo",
        splash_kind="orange",
        splash_causes="orange and sticky",
        evidence="an orange ring on the floorboards",
        source_type="pumpkin",
        source_label="the pumpkin wagon",
        source_phrase="a pumpkin wagon with a wobbly wheel",
        reveal="a burst pumpkin rolled from the wagon and cracked open",
        place_hint="barn",
    ),
    "berry_pie": Mystery(
        id="berry_pie",
        clue_word="splatter",
        action="splatter berry pie filling",
        gerund="splatting berry pie filling",
        splash_kind="purple",
        splash_causes="purple and shiny",
        evidence="purple dots on the apron",
        source_type="pie",
        source_label="the berry pie",
        source_phrase="a berry pie cooling on the sill",
        reveal="the berry pie slid out and splashed the table",
        place_hint="kitchen",
    ),
    "ink": Mystery(
        id="ink",
        clue_word="analyze",
        action="splatter ink",
        gerund="splatting ink",
        splash_kind="black",
        splash_causes="black and blotchy",
        evidence="black specks on the clue sheet",
        source_type="ink bottle",
        source_label="the ink bottle",
        source_phrase="an ink bottle with a loose cork",
        reveal="the ink bottle tipped over during the wind",
        place_hint="fair",
    ),
}

SOLVERS = [
    Solver(id="Milly", type="girl", label="Milly", trait="sharp-eyed"),
    Solver(id="Tom", type="boy", label="Tom", trait="long-legged"),
    Solver(id="Nell", type="girl", label="Nell", trait="quick-witted"),
]

TRAILS = ["dusty", "zigzag", "tippy", "windy", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            if mystery.place_hint and mystery.place_hint != place:
                continue
            if "splatter" not in setting.affords:
                continue
            combos.append((place, mid, mystery.source_type))
    return combos


@dataclass
class StoryParams:
    place: str
    mystery: str
    solver_name: str
    solver_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tall-tale mystery storyworld about a splatter and a clue to analyze.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--solver", choices=[s.id for s in SOLVERS])
    ap.add_argument("--name")
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
    if args.place or args.mystery:
        combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid mystery matches the given options.)")
    place, mystery_id, _ = rng.choice(sorted(combos))
    solver = next((s for s in SOLVERS if s.id == (args.solver or s.id)), None)
    if args.solver:
        solver = next(s for s in SOLVERS if s.id == args.solver)
    else:
        solver = rng.choice(SOLVERS)
    return StoryParams(place=place, mystery=mystery_id, solver_name=args.name or solver.id, solver_type=solver.type)


def _introduce(world: World, hero: Entity, mystery: Mystery, source: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} little {hero.type} who loved a good mystery."
    )
    world.say(
        f"One day, in {world.setting.place}, there was a weird problem: something had to {mystery.action}, and nobody knew why."
    )
    world.say(
        f"Near the trouble sat {source.phrase}, looking as innocent as a spoon at breakfast."
    )


def _clue_scene(world: World, hero: Entity, mystery: Mystery) -> None:
    world.para()
    world.say(
        f"{hero.id} found {mystery.evidence} and an odd trail that looked {mystery.splash_causes}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} did not just stare; {hero.id} began to analyze the clue one piece at a time."
    )


def _solve_scene(world: World, hero: Entity, mystery: Mystery, source: Entity) -> None:
    world.para()
    world.say(
        f"Then {hero.id} pointed a finger and said, \"I know this trick! {source.label} made the splatter.\""
    )
    if mystery.id == "pumpkin":
        world.say("The wagon wheel had bounced like a jackrabbit, and the pumpkin burst right open.")
    elif mystery.id == "berry_pie":
        world.say("A tiny bump sent the pie sliding, and purple filling flew everywhere.")
    else:
        world.say("The wind gave the bottle a cheeky shove, and black drops danced across the room.")
    world.say("The grown-ups laughed, cleaned up the mess, and called the mystery solved.")


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["sharp-eyed", "curious"]))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type=mystery.source_type,
        label=mystery.source_label,
        phrase=mystery.source_phrase,
    ))
    clue = Clue(
        id="clue",
        word=mystery.clue_word,
        source_id=source.id,
        source_kind=source.type,
        source_label=source.label,
        splatter_shape=mystery.splash_kind,
        places={setting.place},
        smell=mystery.splash_causes,
        color=mystery.splash_kind,
    )
    world.facts.update(hero=hero, source=source, clue=clue, mystery=mystery, setting=setting)
    _introduce(world, hero, mystery, source)
    propagate(world, narrate=True)
    _clue_scene(world, hero, mystery)
    propagate(world, narrate=True)
    _solve_scene(world, hero, mystery, source)
    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f'Write a short tall-tale story for a young child about a mystery in {world.setting.place} that includes the word "{mystery.clue_word}".',
        f"Tell a funny story where {hero.id} must analyze a splatter clue and solve the mystery.",
        f"Write a child-friendly mystery with a big clue, a careful guess, and an ending that proves who made the splatter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    source: Entity = f["source"]
    mystery: Mystery = f["mystery"]
    return [
        QAItem(
            question=f"Who solved the mystery in {world.setting.place}?",
            answer=f"{hero.id} solved the mystery by analyzing the splatter clue and naming {source.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} have to analyze?",
            answer=f"{hero.id} had to analyze the splatter clue, which was {mystery.evidence}.",
        ),
        QAItem(
            question=f"What made the story a mystery to solve?",
            answer=f"It was a mystery because nobody knew what caused the splatter until {hero.id} studied the clue and figured it out.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to analyze a clue?",
            answer="To analyze a clue means to look at it carefully, compare details, and think about what it might mean.",
        ),
        QAItem(
            question="Why do splatters help solve mysteries?",
            answer="Splatters can show where something came from, what color it was, or how it moved, so they can help a detective figure things out.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzling problem where somebody needs to gather clues and think hard to find the answer.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.kind:7}/{e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="barn", mystery="pumpkin", solver_name="Milly", solver_type="girl"),
    StoryParams(place="kitchen", mystery="berry_pie", solver_name="Nell", solver_type="girl"),
    StoryParams(place="fair", mystery="ink", solver_name="Tom", solver_type="boy"),
]


def explain_rejection(place: str, mystery: Mystery) -> str:
    return f"(No story: {mystery.id} does not fit the requested place {place}.)"


ASP_RULES = r"""
% A splatter happens when the mystery source is present.
splatter(S) :- source(S).

% Analyzing the clue happens after the splatter is seen.
analyze(H) :- hero(H), splatter(_).

% The mystery is solved when the source matches the clue.
solved(H,S) :- analyze(H), source(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if setting.indoors:
            lines.append(asp.fact("indoors", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("source", mid))
        lines.append(asp.fact("clue_word", mid, m.clue_word))
    for solver in SOLVERS:
        lines.append(asp.fact("hero", solver.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show splatter/1.\n#show analyze/1.\n#show solved/2."))
    atoms = set()
    for pred in ("splatter", "analyze", "solved"):
        atoms.update((pred, tuple(t) if isinstance(t, tuple) else t) for t in asp.atoms(model, pred))
    if atoms:
        print("OK: ASP program produced atoms.")
        return 0
    print("MISMATCH: ASP produced no useful atoms.")
    return 1


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solved/2."))
    return sorted(set(asp.atoms(model, "solved")))


def generate(params: StoryParams) -> StorySample:
    mystery = MYSTERIES[params.mystery]
    world = tell(SETTINGS[params.place], mystery, params.solver_name, params.solver_type)
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
        print(asp_program("#show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/2."))
        solved = asp.atoms(model, "solved")
        print(f"{len(solved)} solved relations:")
        for h, s in solved:
            print(f"  {h} -> {s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                if args.place and args.mystery:
                    if args.place != MYSTERIES[args.mystery].place_hint and MYSTERIES[args.mystery].place_hint:
                        raise StoryError(explain_rejection(args.place, MYSTERIES[args.mystery]))
                params = resolve_params(args, rng)
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
            header = f"### {p.solver_name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
