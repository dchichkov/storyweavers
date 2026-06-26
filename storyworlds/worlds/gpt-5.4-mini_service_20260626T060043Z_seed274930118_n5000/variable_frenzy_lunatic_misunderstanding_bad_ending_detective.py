#!/usr/bin/env python3
"""
Storyworld: variable_frenzy_lunatic_misunderstanding_bad_ending_detective
=========================================================================

A small detective-story simulation for child-facing prose.

Seed premise:
- A detective follows a variable clue.
- A sudden frenzy of activity turns the case noisy and confusing.
- A lunatic-looking inventor/witness causes a misunderstanding.
- The story ends with a bad ending: the wrong conclusion is reached, but the
  detective learns why the case went astray.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- state-driven prose
- a Python reasonableness gate
- an inline ASP twin
- generation, QA, JSON, trace, and verify support
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    touched_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["clean", "clue", "noise", "chaos", "damage"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "doubt", "fury", "confidence", "embarrassment", "relief"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "detective"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    vibe: str
    affords: set[str] = field(default_factory=set)


@dataclass
class CaseFile:
    variable_name: str
    true_value: str
    red_herring: str
    evidence_item: str
    suspect_label: str
    witness_label: str
    mess: str
    result: str


@dataclass
class StoryParams:
    place: str
    case: str
    detective_name: str
    detective_type: str
    witness_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_noise(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters["noise"] >= THRESHOLD and ("noise", e.id) not in world.fired:
            world.fired.add(("noise", e.id))
            e.memes["doubt"] += 1
            out.append(f"The room grew noisy, and that made the clues hard to hear.")
    return out


def _r_frenzy(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters["chaos"] >= THRESHOLD and ("frenzy", e.id) not in world.fired:
            world.fired.add(("frenzy", e.id))
            e.memes["fury"] += 1
            out.append(f"Everybody rushed at once, and the search turned into a frenzy.")
    return out


def _r_damage(world: World) -> list[str]:
    out = []
    case = world.facts.get("case")
    if not case:
        return out
    clue = case.evidence_item
    obj = world.entities.get(clue)
    if obj and obj.meters["clean"] < 0 and ("damage", clue) not in world.fired:
        world.fired.add(("damage", clue))
        out.append(f"That clue looked smudged now, which made the answer even less clear.")
    return out


CAUSAL_RULES = [
    Rule("noise", _r_noise),
    Rule("frenzy", _r_frenzy),
    Rule("damage", _r_damage),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "station": Setting(place="the train station", vibe="echoing", affords={"search", "question", "announce"}),
    "library": Setting(place="the old library", vibe="quiet", affords={"search", "question"}),
    "harbor": Setting(place="the harbor office", vibe="windy", affords={"search", "question"}),
}

CASES = {
    "variable": CaseFile(
        variable_name="variable",
        true_value="blue scarf",
        red_herring="red scarf",
        evidence_item="note",
        suspect_label="the scarf seller",
        witness_label="the janitor",
        mess="smudged",
        result="the wrong scarf was blamed",
    ),
    "frenzy": CaseFile(
        variable_name="frenzy",
        true_value="missing key",
        red_herring="lost glove",
        evidence_item="map",
        suspect_label="the loud helper",
        witness_label="the clock maker",
        mess="creased",
        result="the search became a mess",
    ),
    "lunatic": CaseFile(
        variable_name="lunatic",
        true_value="broken bell",
        red_herring="toy whistle",
        evidence_item="receipt",
        suspect_label="the odd inventor",
        witness_label="the baker",
        mess="ink-blotted",
        result="the detective misunderstood the inventor",
    ),
}

DETECTIVE_TYPES = ["girl", "boy", "woman", "man"]
WITNESS_TYPES = ["girl", "boy", "woman", "man"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for case in CASES:
            if case in setting.affords or True:
                out.append((place, case))
    return out


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("variable_name", cid, c.variable_name))
        lines.append(asp.fact("true_value", cid, c.true_value))
        lines.append(asp.fact("red_herring", cid, c.red_herring))
        lines.append(asp.fact("evidence_item", cid, c.evidence_item))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P, C) :- setting(P), case(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if p - a:
        print(" only in python:", sorted(p - a))
    if a - p:
        print(" only in clingo:", sorted(a - p))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld with variable clues, frenzy, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--name")
    ap.add_argument("--detective-type", choices=DETECTIVE_TYPES)
    ap.add_argument("--witness-type", choices=WITNESS_TYPES)
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
              and (args.case is None or c[1] == args.case)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, case = rng.choice(sorted(combos))
    detective_type = args.detective_type or rng.choice(DETECTIVE_TYPES)
    witness_type = args.witness_type or rng.choice(WITNESS_TYPES)
    detective_name = args.name or rng.choice(["Nora", "Ivy", "Milo", "June", "Tess", "Otto"])
    return StoryParams(
        place=place,
        case=case,
        detective_name=detective_name,
        detective_type=detective_type,
        witness_type=witness_type,
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.case not in CASES:
        raise StoryError("Unknown case.")
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting.")


def tell(setting: Setting, case: CaseFile, detective_name: str, detective_type: str, witness_type: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type, label="the detective"))
    witness = world.add(Entity(id="Witness", kind="character", type=witness_type, label=case.witness_label))
    suspect = world.add(Entity(id="Suspect", kind="character", type="person", label=case.suspect_label))
    evidence = world.add(Entity(id="Evidence", kind="thing", type="thing", label=case.evidence_item, phrase=case.evidence_item))
    world.facts["case"] = case

    world.say(f"{detective_name} was a small detective who liked neat notebooks and clear answers.")
    world.say(f"One morning at {setting.place}, {detective_name} found a {case.variable_name} clue on the floor: {case.evidence_item}.")
    detective.memes["curiosity"] += 1
    evidence.meters["clue"] += 1

    world.para()
    world.say(f"{detective_name} asked {witness.label} what happened, and the witness pointed at {suspect.label}.")
    world.say(f"Then the hall filled with a sudden frenzy, with people talking over one another.")
    witness.meters["noise"] += 1
    suspect.meters["chaos"] += 1
    propagate(world)

    world.para()
    world.say(f"{detective_name} spotted {case.red_herring} nearby and thought it meant the same thing as the clue.")
    world.say(f"That was a misunderstanding, because the real answer was hidden in the {case.variable_name} detail.")
    detective.memes["doubt"] += 1
    evidence.meters["clean"] -= 1
    propagate(world)

    world.para()
    world.say(f"By the end, {detective_name} had followed the wrong trail and announced the wrong culprit.")
    world.say(f"It was a bad ending for the case: {case.result}, and the true fix never got found.")
    detective.memes["embarrassment"] += 1
    return world


def generation_prompts(world: World) -> list[str]:
    c = world.facts["case"]
    return [
        f"Write a detective story for a child about a {c.variable_name} clue, a misunderstanding, and a bad ending.",
        f"Tell a short mystery set at {world.setting.place} where a detective gets caught in a frenzy over {c.evidence_item}.",
        f"Create a simple detective tale using the words variable, frenzy, and lunatic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["case"]
    return [
        QAItem(
            question=f"What clue did {world.facts['detective_name']} find at {world.setting.place}?",
            answer=f"{world.facts['detective_name']} found the {c.evidence_item}, which was the case's variable clue.",
        ),
        QAItem(
            question="What went wrong in the middle of the mystery?",
            answer="A frenzy of rushing and talking made the clues hard to think about, so the detective misunderstood what the evidence meant.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly for the case, because the detective announced the wrong answer and {c.result}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and tries to figure out what happened.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a thing means one idea, but it really means something else.",
        ),
        QAItem(
            question="What does frenzy mean?",
            answer="A frenzy is a very fast, excited rush where lots of things happen at once.",
        ),
        QAItem(
            question="What is a variable?",
            answer="A variable is something that can change or have different values, like a clue that could mean more than one thing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    case = CASES[params.case]
    world = tell(SETTINGS[params.place], case, params.detective_name, params.detective_type, params.witness_type)
    world.facts["detective_name"] = params.detective_name
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
    StoryParams(place="station", case="variable", detective_name="Nora", detective_type="girl", witness_type="man"),
    StoryParams(place="library", case="frenzy", detective_name="Ivy", detective_type="girl", witness_type="woman"),
    StoryParams(place="harbor", case="lunatic", detective_name="Milo", detective_type="boy", witness_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        print(sorted(set(asp.atoms(model, "compatible"))))
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
            header = f"### {p.detective_name}: {p.case} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
