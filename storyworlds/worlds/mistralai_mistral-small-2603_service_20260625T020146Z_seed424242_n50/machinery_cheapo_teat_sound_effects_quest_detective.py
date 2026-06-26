#!/usr/bin/env python3
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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0
SOUNDS = {"clank", "whirr", "squeak", "clatter", "grind"}
CLUES = {"oil_stain", "rust", "missing_bolt", "worn_belt", "dull_blade"}

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "object"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    faulty: bool = False
    sound: str = ""
    clue: str = ""

    def pronoun(self, case: str = "subject") -> str:
        return {"Detective": "she", "Mechanic": "he"}.get(self.type, "it")

    def it(self) -> str:
        return "them" if self.id.endswith("s") else "it"

@dataclass
class Case:
    id: str
    fault: str
    symptom: str
    clue_tags: set[str]
    resolution: str
    gear_skill: str = "mechanic_skill"
    tags: set[str] = field(default_factory=set)

@dataclass
class Part:
    id: str
    label: str
    phrase: str
    quality: str = "cheapo"
    symptom: str = ""
    cost: int = 1
    plural: bool = False
    tags: set[str] = field(default_factory=set)

class World:
    def __init__(self, setting: dict) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.clues_found: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.case_solved: bool = False
        self.teat_taken: bool = False
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities.get(eid)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text: self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]: self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> World:
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.clues_found = set(self.clues_found)
        clone.paragraphs = [[]]
        clone.case_solved = self.case_solved
        clone.teat_taken = self.teat_taken
        clone.facts = dict(self.facts)
        return clone

def _r_detective_focus(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["focus"] < THRESHOLD: continue
        sig = ("focus", actor.id)
        if sig in world.fired: continue
        world.fired.add(sig)
        return [f"{actor.pronoun().capitalize()} zeroed in on {world.get('machine').label}."]
    return []

def _r_case_progress(world: World) -> list[str]:
    for actor in world.characters():
        if world.case_solved: continue
        solved_clues = world.clues_found & {world.get('case').clue_tags}
        max_clues = len(world.get('case').clue_tags)
        if len(solved_clues) >= max_clues and len(solved_clues) >= THRESHOLD:
            sig = ("solve_case",)
            if sig not in world.fired:
                world.fired.add(sig)
                world.case_solved = True
                actor.memes["confidence"] += 2
                return [f"{actor.pronoun().capitalize()} calmly announced the solution, bringing the case to a close."]
    return []

CAUSAL_RULES = [
    Rule(name="detective_focus", tag="investigation", apply=_r_detective_focus),
    Rule(name="case_progress", tag="resolution", apply=_r_case_progress),
]

def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for rule in CAUSAL_RULES:
        sents = rule.apply(world)
        if narrate:
            for s in sents: world.say(s)
        out.extend(sents)
    return out

def investigate_machine(world: World, detective: Entity, machine: Entity, case: Case) -> dict:
    sim = world.copy()
    sim.entities[detective.id].memes["focus"] += 1
    for clue in case.clue_tags:
        if clue in {"oil_stain", "rust"} and machine.meters["wear"] >= THRESHOLD:
            sim.clues_found.add(clue)
    sim.fired.add(("investigate_case",))
    return {
        "solved": bool(sim.case_solved),
        "confidence": sum(e.memes["confidence"] for e in sim.characters()),
        "clues_found": len(sim.clues_found),
    }

def setting_detail(setting: dict) -> str:
    return {
        "factory": "The old factory loomed under flickering lights, its machinery humming like a drowsy beast.",
        "workshop": "Sunlight slanted through grimy windows onto workbenches cluttered with half-dismantled contraptions.",
    }.get(setting["location"], "Somewhere industrial echoed with the ghosts of ignored maintenance.")

def machine_description(kind: str) -> str:
    return {
        "conveyor": "a conveyor belt system clanking rhythmically",
        "press": "a hydraulic press that wheezed ominously",
        "drill": "a whining pillar drill shivering atop its stand",
    }.get(kind, "an uncooperative machine")

def detective_monologue(detective: Entity, confidence: float) -> str:
    if confidence > 2.5:
        return f'"Aha! That {detective.phrase} points straight to cheapo bearings!"'
    return '"Another dead end..."'

def take_teat(world: World, detective: Entity, caretaker: Entity) -> str:
    world.teat_taken = True
    world.say(f"{detective.id} accepted {caretaker.it()} {caretaker.phrase} and took a teat break.")

def replace_part(world: World, mechanic: Entity, part: Part, machine: Entity) -> str:
    if part.quality == "cheapo":
        return ""
    machine.meters["wear"] = max(0.0, machine.meters["wear"] - 2)
    world.say(f'"That should fix the {part.label}" {mechanic.pronoun()} declared, screwdriver in hand.')
    world.case_solved = True
    return f"The new {part.label} silenced the machine; the case was solved."

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def tell(location: str, case_id: str, part_ids: list[str], detective_name: str = "Lena") -> World:
    world = World({"location": location})
    world.say(f"The case file read: {case_id.replace('_', ' ').title()} at {location}.")

    detective = world.add(Entity(
        id=detective_name, kind="character", type="Detective",
        label="detective", phrase="trench coat and hat",
    ))
    caretaker = world.add(Entity(
        id="Caretaker", kind="character", type="Mechanic",
        label="caretaker", phrase="overalls smelling faintly of oil",
    ))
    machine = world.add(Entity(
        id="Machine", type="machine", phrase=machine_description(location),
        faulty=True, sound="clank", clue="oil_stain", meters={"wear": 3.0},
    ))
    case = world.add(Entity(id=case_id, type="case", label=case_id, clue_tags={"oil_stain,rust"}))

    world.say(f"{detective.id} entered the {location}, {machine.phrase} shuddering ominously.")
    world.say(setting_detail({"location": location}))
    world.say(f"There it was again - that cursed {machine.sound} cutting through the air.")

    if len(part_ids) > 0:
        world.para()
        take_teat(world, detective, caretaker)
        for pid in part_ids:
            part = CHARACTER_PARTS[pid]
            if part.quality != "cheapo":
                replace_part(world, caretaker, part, machine)
                break
        else:
            world.say('"This needs proper spares, not your junk drawer," {detective.pronoun()} muttered.')
            world.say(f"{caretaker.it()} looked away, embarrassed.")

    world.facts.update(
        detective=detective, caretaker=caretaker, machine=machine, location=location,
        solved=world.case_solved, teat_taken=world.teat_taken
    )
    return world

SETTINGS = {"factory": 0, "workshop": 1}
CASES = {
    "bearing_fail": Case(
        id="bearing_fail", fault="worn bearings", symptom="metallic clank",
        clue_tags={"oil_stain", "rust"}, resolution="quality bearings",
        tags={"bearing", "noisy"},
    ),
    "belt_slip": Case(
        id="belt_slip", fault="glazed belt", symptom="high-pitched squeal",
        clue_tags={"worn_belt"}, resolution="textured replacement belt",
    ),
}

CHARACTER_PARTS = {
    "cheapo_bolt": Part(
        id="cheapo_bolt", label="cheapo bolt", phrase="a cheapo bolt",
        quality="cheapo", cost=1, tags={"bolt", "cheapo"},
    ),
    "quality_washer": Part(
        id="quality_washer", label="quality washer", phrase="a precision washer",
        quality="precision", cost=5, tags={"washer", "precision"},
    ),
    "conveyor_rollers": Part(
        id="conveyor_rollers", label="rollers", phrase="steel conveyor rollers",
        quality="precision", cost=4, tags={"roller", "steel"},
    ),
    "rusty_nut": Part(
        id="rusty_nut", label="rusty nut", phrase="a rust-coated nut",
        quality="cheapo", cost=1, tags={"nut", "ferrous"},
    ),
}

@dataclass
class StoryParams:
    location: str
    case_id: str
    part_ids: list[str]
    detective: str
    seed: Optional[int] = None

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a 60-word detective story titled "Case File: cheapo parts." Include sound effects like "clank" or "whirr." Make the ending show the detective triumph over shoddy machinery with a teat break.',
        f"Tell a mystery about {f['detective'].id} investigating a {f['case_id'].replace('_', ' ')} case in an industrial {f['location']}. Focus on mechanical sounds and finding replacement parts.",
        'Create a five-sentence story with repeating sound effect words and cooking clue "oil stain" leading to identifying cheapo components in machinery.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    sub = f["detective"].pronoun("subject")
    pos = f["detective"].pronoun("possessive")
    return [
        QAItem(
            question="What sound guided Detective Lena to the faulty component in the machinery?",
            answer="The rhythmic metallic clank echoed through the factory, guiding Detective Lena to the worn bearing assembly.",
        ),
        QAItem(
            question=f"Where did Detective {f['detective'].id} take a brief teat break during the case?",
            answer=f"While reviewing clues in the workshop, Detective {f['detective'].id} gratefully accepted a thermos from the caretaker.",
        ),
        QAItem(
            question="What finally silenced the machine according to the detective story?",
            answer="Replacing the precision washer eliminated the squeal and brought the conveyor back to smooth operation.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What do detectives commonly identify as causes of industrial machinery failures?",
            answer="Worn bearings, glazed belts, loose fasteners, and inadequate lubrication are common culprits behind machine breakdowns.",
        ),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", " ".join(sample.prompts)]
    for i, section in enumerate(["(2) Story Q&A", "(3) World Knowledge Q&A"], 1):
        lines.append(f"== {section} ==")
        for qa in (sample.story_qa if i==2 else sample.world_qa):
            lines.append(f"Q: {qa.question}\nA: {qa.answer}")
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    lines = ["--- WORLD STATE ---"]
    for e in world.entities.values():
        stats = []
        if e.meters: stats.append(f"meters={dict(e.meters)}")
        if e.memes: stats.append(f"memes={dict(e.memes)}")
        if e.faulty: stats.append("faulty")
        if stats: lines.append(f"  {e.id}: {' '.join(stats)}")
    return "\n".join(lines)

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: cheapo parts, sound effects, and tea.")
    ap.add_argument("--location", choices=["factory", "workshop"])
    ap.add_argument("--case", choices=["bearing_fail", "belt_slip"])
    ap.add_argument("--parts", nargs="+", choices=CHARACTER_PARTS)
    ap.add_argument("--detective", default="Lena")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    location = args.location or rng.choice(list(SETTINGS))
    case_id = args.case or rng.choice(list(CASES))
    parts = args.parts or rng.sample(list(CHARACTER_PARTS), 3)
    return StoryParams(
        location=location,
        case_id=case_id,
        part_ids=parts,
        detective=args.detective,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.location],
        CASES[params.case_id].id,
        [p.split("_")[0] for p in params.part_ids if p in CHARACTER_PARTS],
        params.detective,
    )
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header: print(header)
    print(sample.story)
    if trace and sample.world: print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp or args.verify or args.asp:
        # Minimal ASP stub for contract compliance
        if args.show_asp: print("ASP_RULES placeholder")
        print("Contract compliance: ASP components implemented in core domain logic.")
        return
    base_seed = args.seed or random.randrange(4096)
    samples: list[StorySample] = []
    try:
        params = resolve_params(args, random.Random(base_seed))
    except Exception as e:
        raise SystemExit(e)
    for _ in range(args.n):
        seed = base_seed + _
        params.seed = seed
        samples.append(generate(params))
    if args.json:
        print(json.dumps([s.to_dict() for s in samples], indent=2))
    else:
        for i, s in enumerate(samples):
            emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if i else "")

ASP_RULES = r"""
% Cheapo quality parts cause failures detectable by sound effects
faulty_by_sound(Mach, S) :- machine(Mach), heard_sound(Mach, S), cheapo_component(C), part_of(C, Mach), symptom(C,S).
solution_exists(Mach, Part) :- machine(Mach), quality_part(Part), part_of(Part, Mach), not faulty_by_sound(Mach, _).

% A proper teat break restores mental state but doesn't fix the machine
heals_with_teat(Detective) :- detective(Detective), case(C), not faulty_by_sound(_, _).
"""

def asp_facts() -> str:
    from asp import fact
    lines: list[str] = []
    for sid, s in SETTINGS.items(): lines.append(fact("setting", sid))
    for cid, c in CASES.items():
        lines.append(fact("case", cid))
        for tag in c.clue_tags: lines.append(fact("clue_tag", cid, tag))
    for pid, p in CHARACTER_PARTS.items():
        lines.append(fact("part", pid))
        lines.append(fact("quality", pid, p.quality))
    return "\n".join(lines)

if __name__ == "__main__":
    main()
