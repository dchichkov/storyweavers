#!/usr/bin/env python3
"""
A standalone story world for a bedtime-story style tale about exposure, burden,
bravery, and a mystery to solve.

Premise:
- A small child notices a strange sound or sign at bedtime.
- The child is briefly exposed to a cold or dark place while helping search.
- A small burden is carried during the search.
- Bravery turns the suspense into a solved mystery and a safe ending.

This script follows the Storyweavers world contract:
- typed entities with meters and memes
- state-driven prose
- story QA and world QA
- inline ASP twin with parity verification
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"exposure": 0.0, "burden": 0.0}
        if not self.memes:
            self.memes = {"bravery": 0.0, "suspense": 0.0, "relief": 0.0, "curiosity": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def subj(self) -> str:
        return self.id


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    revealed: str
    source: str
    suspicion: str
    exposure_kind: str
    burden_kind: str
    risk_region: str
    reason: str


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    helps: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_exposure(world: World) -> list[str]:
    out = []
    child = world.get(world.facts["child"].id)
    if child.meters["exposure"] < THRESHOLD:
        return out
    sig = ("exposed", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["suspense"] += 1
    out.append("The night felt bigger when the child stepped into it.")
    return out


def _r_burden(world: World) -> list[str]:
    out = []
    child = world.get(world.facts["child"].id)
    if child.meters["burden"] < THRESHOLD:
        return out
    sig = ("burden", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["bravery"] += 1
    out.append("The little bundle was heavy, but it made the search feel important.")
    return out


CAUSAL_RULES = [_r_exposure, _r_burden]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    outs: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                outs.extend(sents)
    if narrate:
        for s in outs:
            world.say(s)


def _mystery_turns(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["curiosity"] += 1
    child.memes["suspense"] += 1
    world.say(
        f"At bedtime, {child.id} heard a soft {mystery.clue} from {world.setting.place} and wondered what it could be."
    )


def _take_burden(world: World, child: Entity, burden: Entity) -> None:
    burden.carried_by = child.id
    child.meters["burden"] += 1
    world.say(
        f"{child.id} picked up {burden.phrase} and held it close, even though it was a little heavy."
    )
    propagate(world)


def _step_into_exposure(world: World, child: Entity, mystery: Mystery) -> None:
    child.meters["exposure"] += 1
    world.say(
        f"{child.id} tiptoed to the door, where a cool breeze brushed {child.pronoun('object')} cheeks."
    )
    propagate(world)


def _brave_search(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} took a brave breath and followed the clue, one quiet step at a time."
    )


def _solve(world: World, child: Entity, mystery: Mystery, answer: Entity) -> None:
    child.memes["relief"] += 1
    child.memes["suspense"] = 0.0
    world.say(
        f"Under the moonlight, {child.id} found {answer.phrase}: the mystery was only {mystery.revealed}."
    )
    world.say(
        f"The room felt cozy again, and {child.id} smiled because the strange little secret had been solved."
    )


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    burden = world.add(Entity(id="lantern", type="thing", label="lantern", phrase="a small lantern"))
    answer = world.add(Entity(id="answer", type="thing", label="answer", phrase=mystery.source))
    blanket = world.add(Entity(id="blanket", type="thing", label="blanket", phrase="a soft blanket", protective=True, covers={"shoulders"}))

    world.facts.update(child=child, parent=parent, burden=burden, answer=answer, mystery=mystery, blanket=blanket)

    world.say(f"{child.id} was a little {hero_type} who liked bedtime stories and soft lamp-light.")
    world.say(f"Every night, {child.id} listened closely, because small mysteries felt brave when solved kindly.")
    world.para()
    _mystery_turns(world, child, mystery)
    _step_into_exposure(world, child, mystery)
    _take_burden(world, child, burden)
    _brave_search(world, child, mystery)
    world.para()
    world.say(
        f"{parent.id} stayed nearby, saying, \"You can be brave for one more little look.\""
    )
    _solve(world, child, mystery, answer)
    world.say(
        f"After that, {child.id} tucked back under the blanket, warm and safe, with the mystery all finished."
    )
    return world


SETTINGS = {
    "hallway": Setting(place="the hallway", indoors=True, affords={"listening", "searching"}),
    "garden_gate": Setting(place="the garden gate", indoors=False, affords={"listening", "searching"}),
    "attic_stairs": Setting(place="the attic stairs", indoors=True, affords={"listening", "searching"}),
}

MYSTERIES = {
    "tap": Mystery(
        id="tap",
        clue="tap-tap sound",
        revealed="the branch of a tree tapping the window",
        source="a twig knocking on the glass",
        suspicion="someone outside",
        exposure_kind="night air",
        burden_kind="lantern",
        risk_region="shoulders",
        reason="the child had to peek into the dark place to find it",
    ),
    "rustle": Mystery(
        id="rustle",
        clue="rustling sound",
        revealed="the curtain moving in the breeze",
        source="a curtain fluttering by the open door",
        suspicion="a hidden mouse",
        exposure_kind="cool air",
        burden_kind="basket",
        risk_region="hands",
        reason="the child had to carry a little light to search safely",
    ),
    "hum": Mystery(
        id="hum",
        clue="soft humming sound",
        revealed="the night-light buzzing gently",
        source="a sleepy lamp making a tiny hum",
        suspicion="a secret machine",
        exposure_kind="cold floor",
        burden_kind="lantern",
        risk_region="feet",
        reason="the child had to cross the quiet room carefully",
    ),
}

GEAR = {
    "blanket": Gear(id="blanket", label="a blanket", covers={"shoulders"}, helps={"night air", "cool air"}, prep="wrap up in a blanket", tail="wrapped up in the blanket"),
    "slippers": Gear(id="slippers", label="slippers", covers={"feet"}, helps={"cold floor"}, prep="put on slippers", tail="slipped into the slippers"),
}


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Sam", "Finn", "Noah", "Eli"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: exposure, burden, bravery, and a solved mystery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting and args.mystery:
        if (args.setting, args.mystery) not in combos:
            raise StoryError("No valid story matches that setting and mystery.")
    picks = [(s, m) for s, m in combos if (not args.setting or s == args.setting) and (not args.mystery or m == args.mystery)]
    if not picks:
        raise StoryError("No valid combination matches the given options.")
    setting, mystery = rng.choice(picks)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], params.name, params.gender, params.parent)
    story = world.render()
    prompts = [
        f"Write a gentle bedtime story about a child named {params.name} who meets a small mystery.",
        f"Tell a cozy story where a {params.gender} child shows bravery, carries a small burden, and solves a mystery.",
        "Write a bedtime story with a quiet suspenseful middle and a warm ending.",
    ]
    f = world.facts
    child = f["child"]
    mystery = f["mystery"]
    story_qa = [
        QAItem(
            question=f"What mystery did {child.id} hear in {world.setting.place}?",
            answer=f"{child.id} heard a {mystery.clue} and wanted to know what it meant.",
        ),
        QAItem(
            question=f"What burden did {child.id} carry while searching?",
            answer=f"{child.id} carried {f['burden'].phrase}, and it made the search feel important.",
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f"{child.id} solved the mystery, felt relieved, and went back to bed warm and safe.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or scary while still trying your best.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something you do not understand yet, so you look for clues.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type}, meters={dict(e.meters)}, memes={dict(e.memes)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
% A story is valid when a setting and mystery are chosen.
valid_story(S, M) :- setting(S), mystery(M).

% A mystery is suspenseful when it creates exposure and burden.
suspenseful(M) :- mystery(M), exposure(M), burden(M).

% A solved story must include bravery, suspense, and a resolution clue.
solved(S, M) :- valid_story(S, M), suspenseful(M), brave(M), resolved(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m, obj in MYSTERIES.items():
        lines.append(asp.fact("mystery", m))
        lines.append(asp.fact("exposure", m))
        lines.append(asp.fact("burden", m))
        lines.append(asp.fact("brave", m))
        lines.append(asp.fact("resolved", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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
    StoryParams(setting="hallway", mystery="tap", name="Lily", gender="girl", parent="mother"),
    StoryParams(setting="garden_gate", mystery="rustle", name="Leo", gender="boy", parent="father"),
    StoryParams(setting="attic_stairs", mystery="hum", name="Nora", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for s, m in combos:
            print(s, m)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
