#!/usr/bin/env python3
"""
storyworlds/worlds/relevant_pitch_defy_mystery_to_solve_adventure.py
====================================================================

A standalone story world: a small adventure-mystery in which children follow
a relevant clue, make a pitch, and either obey or defy a warning while solving
what happened to a missing thing.

Seed idea:
---
A child explorer finds a note with the word "relevant" on it, makes a pitch to
solve the mystery, and defies a noisy shortcut. The team follows the clue trail,
discovers who moved the key object, and ends with the mystery solved and the
right thing back in place.

The world uses typed entities with physical meters and emotional memes, a
forward-chaining causal rule engine, a reasonableness gate, and an inline ASP
twin. Stories are short, child-facing, and state-driven.
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
    plural: bool = False
    owner: str = ""
    location: str = ""
    moved_from: str = ""
    moved_by: str = ""
    hints: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

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
class Place:
    id: str
    label: str
    clue_kind: str
    is_outdoor: bool = False
    detail: str = ""
    meter: str = ""


@dataclass
class Clue:
    id: str
    word: str
    where: str
    points_to: str
    relevant_to: str
    pitch_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    missing_label: str
    item_type: str
    item_name: str
    usual_place: str
    risky_place: str
    reason: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    method: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_clue(world: World) -> list[str]:
    out = []
    clue = world.facts["clue"]
    hero = world.get("hero")
    if hero.memes.get("curious", 0.0) >= THRESHOLD and clue.word not in hero.hints:
        sig = ("clue", clue.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.hints.append(clue.word)
        hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
        out.append(f"{hero.id} noticed that the clue looked relevant.")
    return out


def _r_move(world: World) -> list[str]:
    out = []
    problem = world.facts["problem"]
    fix = world.facts["fix"]
    key = world.get("key")
    if key.location == problem.risky_place:
        sig = ("move", problem.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        key.location = problem.usual_place
        key.meters["found"] = 1
        out.append("__moved__")
    if key.location == problem.usual_place and not world.facts.get("solved"):
        world.fired.add((fix.id, "solved"))
        world.facts["solved"] = True
        out.append("__solved__")
    return out


CAUSAL_RULES = [Rule("clue", _r_clue), Rule("move", _r_move)]


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


def follows_clue(problem: Problem, clue: Clue) -> bool:
    return clue.relevant_to == problem.id


def can_pitch(clue: Clue, place: Place) -> bool:
    return clue.where == place.id and clue.word in {"relevant", "pitch"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for clue in CLUES:
            for problem in PROBLEMS:
                if follows_clue(problem, clue) and can_pitch(clue, place):
                    combos.append((place.id, clue.id, problem.id))
    return combos


@dataclass
class StoryParams:
    place: str = "dock"
    clue: str = "note"
    problem: str = "missing_box"
    hero_name: str = "Mia"
    hero_gender: str = "girl"
    helper_name: str = "Noah"
    helper_gender: str = "boy"
    adult_name: str = "Aunt May"
    seed: Optional[int] = None


PLACES = [
    Place(id="dock", label="the dock", clue_kind="note", is_outdoor=True, detail="The water lapped below the boards.", meter="dock"),
    Place(id="library", label="the library", clue_kind="map", detail="Tall shelves made the room feel like a maze.", meter="shelf"),
    Place(id="trail", label="the trail", clue_kind="mark", is_outdoor=True, detail="The trail bent between pines and stones.", meter="stone"),
]

CLUES = [
    Clue(id="note", word="relevant", where="dock", points_to="dock", relevant_to="missing_box", pitch_text="That note feels relevant to the missing box.", tags={"relevant", "note"}),
    Clue(id="map", word="pitch", where="library", points_to="library", relevant_to="missing_map", pitch_text="I can make a pitch for the map trail.", tags={"pitch", "map"}),
    Clue(id="mark", word="relevant", where="trail", points_to="trail", relevant_to="missing_key", pitch_text="That mark is relevant because it points to the key.", tags={"relevant", "mark"}),
]

PROBLEMS = [
    Problem(id="missing_box", missing_label="the tide box", item_type="box", item_name="box", usual_place="shed", risky_place="dock", reason="the box had been left near the water", tags={"box", "missing"}),
    Problem(id="missing_map", missing_label="the paper map", item_type="map", item_name="map", usual_place="bench", risky_place="library", reason="the map had slipped into a book cart", tags={"map", "missing"}),
    Problem(id="missing_key", missing_label="the brass key", item_type="key", item_name="key", usual_place="hook", risky_place="trail", reason="the key had fallen from a pocket on the walk", tags={"key", "missing"}),
]

FIXES = [
    Fix(id="search", label="careful search", method="searched one place at a time", result="found what had been hidden", tags={"search"}),
    Fix(id="ask", label="asking around", method="asked the right grown-up a clear question", result="learned where it had gone", tags={"ask"}),
    Fix(id="follow", label="following the clue", method="followed the clue trail without hurrying", result="solved the mystery", tags={"follow", "mystery"}),
]

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ivy"]
BOY_NAMES = ["Noah", "Eli", "Leo", "Max", "Ben", "Theo"]
TRAITS = ["curious", "brave", "patient", "steady", "smart"]


def reason_rejection(place: Place, clue: Clue, problem: Problem) -> str:
    if not follows_clue(problem, clue):
        return "(No story: the clue does not lead to that missing thing, so the mystery would not be honest.)"
    if not can_pitch(clue, place):
        return "(No story: that clue does not fit this setting, so there is no clear pitch to make.)"
    return "(No story: this combination does not produce a relevant clue mystery.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure-style mystery story world.")
    ap.add_argument("--place", choices=[p.id for p in PLACES])
    ap.add_argument("--clue", choices=[c.id for c in CLUES])
    ap.add_argument("--problem", choices=[p.id for p in PROBLEMS])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--adult-name")
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
              and (args.clue is None or c[1] == args.clue)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, problem = rng.choice(list(combos))
    return StoryParams(
        place=place,
        clue=clue,
        problem=problem,
        hero_name=args.hero_name or rng.choice(GIRL_NAMES),
        hero_gender="girl",
        helper_name=args.helper_name or rng.choice(BOY_NAMES),
        helper_gender="boy",
        adult_name=args.adult_name or rng.choice(["Aunt May", "Dad", "Mom"]),
    )


def choose_place(eid: str) -> Place:
    for p in PLACES:
        if p.id == eid:
            return p
    raise StoryError("unknown place")


def choose_clue(eid: str) -> Clue:
    for c in CLUES:
        if c.id == eid:
            return c
    raise StoryError("unknown clue")


def choose_problem(eid: str) -> Problem:
    for p in PROBLEMS:
        if p.id == eid:
            return p
    raise StoryError("unknown problem")


def tell(place: Place, clue: Clue, problem: Problem, params: StoryParams) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper_name))
    adult = world.add(Entity(id="adult", kind="character", type="mother" if "Mom" in params.adult_name else "father", label=params.adult_name))
    key = world.add(Entity(id="key", type="key", label=problem.item_name, location=problem.risky_place))
    world.add(Entity(id="clue", type="clue", label=clue.word))
    world.facts.update(hero=hero, helper=helper, adult=adult, key=key, clue=clue, problem=problem, fix=FIXES[2], solved=False)

    hero.memes["curious"] = 1.0
    helper.memes["curious"] = 1.0
    hero.memes["brave"] = 1.0
    helper.memes["brave"] = 1.0

    world.say(f"{params.hero_name} and {params.helper_name} reached {place.label} with a mystery to solve.")
    world.say(f"{place.detail}")
    world.say(f"They found a clue with the word “{clue.word}” on it, and {clue.pitch_text}")
    world.para()
    if clue.word == "relevant":
        hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1
        world.say(f'"That clue is relevant," said {params.hero_name}. "I can make a pitch: we should look where the missing {problem.item_name} was last seen."')
    else:
        world.say(f'{params.hero_name} made a pitch to follow the clue trail anyway.')
    world.say(f"{params.helper_name} wanted to take a shortcut, but {params.hero_name} chose to defy the rush and keep looking carefully.")
    world.para()
    if clue.word == "relevant":
        world.say(f"So they followed the clue to {problem.usual_place}, because that was where the missing thing belonged.")
    propagate(world)
    if not world.facts["solved"]:
        key.location = problem.usual_place
        key.meters["found"] = 1
        world.facts["solved"] = True
    world.para()
    world.say(f"At last they found the {problem.item_name} where it should have been, and the mystery was solved.")
    world.say(f"{params.adult_name} smiled when they brought it back, and the little adventure ended with the right thing in the right place.")
    world.facts.update(place=place, story_clue=clue, story_problem=problem)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure mystery story for a young child that uses the word "{f["clue"].word}" and ends with the mystery solved.',
        f"Tell a short adventure where {f['hero'].label} makes a pitch to solve a missing-{f['problem'].item_name} mystery.",
        f'Write a child-facing mystery story that includes the words "relevant", "pitch", and "defy".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, adult = f["hero"], f["helper"], f["adult"]
    clue, problem = f["clue"], f["problem"]
    return [
        QAItem(
            question=f"What did {hero.label} and {helper.label} want to solve?",
            answer=f"They wanted to solve the mystery of the missing {problem.item_name}. They followed a clue and looked in the place that clue pointed to.",
        ),
        QAItem(
            question=f"Why did {hero.label} say the clue was relevant?",
            answer=f"{hero.label} said that because the clue pointed to the place where the missing {problem.item_name} belonged. That made it useful for solving the mystery.",
        ),
        QAItem(
            question=f"What did {hero.label} make before they searched?",
            answer=f"{hero.label} made a pitch: they suggested a plan for where to look next. The pitch helped the group stay on the clue trail instead of rushing away.",
        ),
        QAItem(
            question=f"How did {hero.label} respond when {helper.label} wanted a shortcut?",
            answer=f"{hero.label} chose to defy the shortcut and keep searching carefully. That choice let them follow the clue all the way to the answer.",
        ),
        QAItem(
            question=f"How did the story end for {problem.item_name}?",
            answer=f"It ended with the {problem.item_name} found and put back where it should be. {adult.label} was glad because the mystery was solved and the little adventure was over well.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does relevant mean?",
            answer="Relevant means something matters to the thing you are trying to solve. A relevant clue helps because it points to useful information.",
        ),
        QAItem(
            question="What is a pitch?",
            answer="A pitch is a plan or suggestion you make to other people. In an adventure story, a child might make a pitch for how to solve a mystery.",
        ),
        QAItem(
            question="What does defy mean?",
            answer="Defy means to refuse a push or rule and choose your own way. A child can defy a bad shortcut and keep doing the safer, smarter thing.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle about what happened or where something went. People solve it by looking for clues and checking ideas one by one.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hints:
            bits.append(f"hints={e.hints}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,M) :- place(P), clue(C), problem(M), follows(C,M), fit(P,C).
solved :- clue_word(relevant), follow_clue, found_key.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p.id))
    for c in CLUES:
        lines.append(asp.fact("clue", c.id))
        lines.append(asp.fact("clue_word", c.word))
    for m in PROBLEMS:
        lines.append(asp.fact("problem", m.id))
    lines.append(asp.fact("follows", "note", "missing_box"))
    lines.append(asp.fact("follows", "mark", "missing_key"))
    lines.append(asp.fact("fit", "dock", "note"))
    lines.append(asp.fact("fit", "trail", "mark"))
    lines.append(asp.fact("fit", "library", "map"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between Python and ASP.")
        if py - cl:
            print("only in python:", sorted(py - cl))
        if cl - py:
            print("only in clingo:", sorted(cl - py))
        return 1
    sample = generate(resolve_params(argparse.Namespace(place=None, clue=None, problem=None, hero_name=None, helper_name=None, adult_name=None), random.Random(777)))
    if not sample.story or "mystery solved" not in sample.story:
        print("Story smoke test failed.")
        return 1
    print(f"OK: {len(py)} combos; story smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    place = choose_place(params.place)
    clue = choose_clue(params.clue)
    problem = choose_problem(params.problem)
    if not follows_clue(problem, clue) or not can_pitch(clue, place):
        raise StoryError(reason_rejection(place, clue, problem))
    world = tell(place, clue, problem, params)
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
    StoryParams(place="dock", clue="note", problem="missing_box", hero_name="Mia", helper_name="Noah", adult_name="Aunt May"),
    StoryParams(place="trail", clue="mark", problem="missing_key", hero_name="Lily", helper_name="Eli", adult_name="Dad"),
    StoryParams(place="library", clue="map", problem="missing_map", hero_name="Zoe", helper_name="Leo", adult_name="Mom"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
