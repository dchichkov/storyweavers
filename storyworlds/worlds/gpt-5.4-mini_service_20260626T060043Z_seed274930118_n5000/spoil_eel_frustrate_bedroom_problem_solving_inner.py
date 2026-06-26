#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/spoil_eel_frustrate_bedroom_problem_solving_inner.py
===============================================================================================================================

A small adventure-style story world in a bedroom: a child faces a spoiled
mess, a slippery eel, and a frustrating problem, then solves it through
careful thinking and an inner monologue.
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

ROOMS = {
    "bedroom": {
        "place": "the bedroom",
        "indoors": True,
    }
}

OBJECTS = {
    "jar": {
        "label": "glass jar",
        "phrase": "a round glass jar with a tight lid",
    },
    "bucket": {
        "label": "bucket",
        "phrase": "a small blue bucket",
    },
    "blanket": {
        "label": "blanket",
        "phrase": "a soft striped blanket",
    },
    "lamp": {
        "label": "lamp",
        "phrase": "a little lamp with a yellow shade",
    },
    "bed": {
        "label": "bed",
        "phrase": "a cozy bed with a wooden frame",
    },
}

NAMES = ["Mina", "Toby", "Rin", "Pia", "Owen", "Lena", "Jude", "Nora"]
TRAITS = ["brave", "curious", "careful", "clever", "bold", "restless"]

ASP_RULES = r"""
problem(A) :- wants(A, Goal), blocked(Goal).
frustrated(A) :- problem(A), cares(A, Goal), blocked(Goal).
solved(A) :- problem(A), finds(A, Fix), fix_for(Fix, Goal), blocked(Goal).
"""

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    moved_to: Optional[str] = None
    spoiled: bool = False
    broken: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

@dataclass
class Setting:
    place: str = "the bedroom"
    indoors: bool = True

@dataclass
class StoryParams:
    setting: str = "bedroom"
    hero_name: str = "Mina"
    hero_trait: str = "curious"
    seed: Optional[int] = None

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld in a bedroom with problem solving and inner monologue.")
    ap.add_argument("--setting", choices=ROOMS.keys(), default="bedroom")
    ap.add_argument("--name", choices=NAMES)
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

def asp_facts() -> str:
    import asp
    lines = []
    for sid in ROOMS:
        lines.append(asp.fact("setting", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    lines.append(asp.fact("wants", "hero", "goal"))
    lines.append(asp.fact("blocked", "goal"))
    lines.append(asp.fact("finds", "hero", "bucket"))
    lines.append(asp.fact("fix_for", "bucket", "goal"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    prog = asp_program("#show problem/1. #show frustrated/1. #show solved/1.")
    model = asp.one_model(prog)
    atoms = set(asp.atoms(model, "problem")) | set(asp.atoms(model, "frustrated")) | set(asp.atoms(model, "solved"))
    expected = {("hero",)}
    if {("hero",)} <= atoms:
        print("OK: ASP twin grounded and solved the simple problem pattern.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected atoms.")
    return 1

def _inner_monologue(world: World, hero: Entity, issue: str) -> None:
    world.say(
        f"{hero.id} stared at the mess and thought, \"I can fix this if I stay calm and look closely.\""
    )
    world.say(
        f"\"The problem is {issue},\" {hero.id} told {hero.pronoun('object')}self in a quiet inner voice."
    )

def tell(setting: Setting, hero_name: str, hero_trait: str) -> World:
    w = World(setting)
    hero = w.add(Entity(id=hero_name, kind="character", type="child", label=hero_name, phrase=f"a {hero_trait} child"))
    jar = w.add(Entity(id="eel_jar", type="jar", label="jar", phrase=OBJECTS["jar"]["phrase"], owner=hero.id))
    eel = w.add(Entity(id="eel", type="eel", label="eel", phrase="a silver eel", owner=hero.id))
    bed = w.add(Entity(id="bed", type="bed", label="bed", phrase=OBJECTS["bed"]["phrase"]))
    blanket = w.add(Entity(id="blanket", type="blanket", label="blanket", phrase=OBJECTS["blanket"]["phrase"], owner=hero.id))
    bucket = w.add(Entity(id="bucket", type="bucket", label="bucket", phrase=OBJECTS["bucket"]["phrase"], owner=hero.id))

    hero.memes["curiosity"] = 1
    hero.memes["frustration"] = 0
    jar.meters["water"] = 1
    blanket.spoiled = True
    blanket.meters["wet"] = 1
    w.facts.update(hero=hero, jar=jar, eel=eel, bed=bed, blanket=blanket, bucket=bucket)

    w.say(f"{hero.id} was a {hero_trait} child in {setting.place}, where every small thing could feel like an expedition.")
    w.say(f"{hero.id} kept a silver eel in a {jar.phrase}, because {hero.id} thought it looked like a tiny river creature from a far-off cave.")
    w.say(f"One evening, the lid slipped. Water splashed across the bed and {blanket.label}, and the room went from cozy to messy in a blink.")
    w.say(f"{hero.id} frowned. The spill had spoiled {blanket.label}, and that was exactly the kind of trouble that could frustrate a young adventurer.")
    w.para()
    _inner_monologue(w, hero, "the eel water spreading over the bed")
    w.say(f"{hero.id} looked at the jar, then at the {bucket.label}, and made a plan.")
    w.say(f"First, {hero.id} lifted the eel carefully with both hands and guided {eel.label} into the {bucket.label}.")
    w.say(f"Then {hero.id} moved the wet jar off the bed and spread the blanket near the lamp so it could dry.")
    w.say(f"The room felt different after that. The bed was safe again, the eel had a steadier home, and {hero.id} was no longer frustrated.")
    w.para()
    w.say(f"Before long, {hero.id} smiled at the neat rescue scene and thought, \"A real adventure can be quiet, careful, and clever.\"")
    w.say(f"The bedroom was still small, but now it felt like a place where problems could be solved.")

    w.facts["resolved"] = True
    return w

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short adventure story set in a bedroom about a spoiled mess, an eel, and a careful fix.',
        f"Tell a child-friendly story where {f['hero'].id} must solve a bedroom problem after an eel spills water on the bed.",
        "Write a simple story that includes an inner monologue and ends with the mess cleaned up and the problem solved.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    return [
        QAItem(
            question=f"Where does {hero.id}'s adventure happen?",
            answer=f"It happens in the bedroom, where the bed, blanket, jar, and bucket are all part of the problem."
        ),
        QAItem(
            question=f"What made {hero.id} frustrated?",
            answer=f"The eel's water spilled out and spoiled the blanket and bed, which made the room messy and upset {hero.id}."
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} moved the eel into the bucket, took the jar off the bed, and let the wet blanket dry safely."
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an eel?",
            answer="An eel is a long, slippery fish that can wriggle like a ribbon in water."
        ),
        QAItem(
            question="What does it mean to spoil something?",
            answer="To spoil something means to make it messy, damaged, or no longer fresh and nice."
        ),
        QAItem(
            question="What does it mean to think with an inner monologue?",
            answer="It means a character quietly talks to themself inside their own mind while they decide what to do."
        ),
        QAItem(
            question="Why is problem solving helpful?",
            answer="Problem solving is helpful because it lets you look at trouble, choose a plan, and make things better."
        ),
    ]

def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.spoiled:
            bits.append("spoiled=True")
        lines.append(f"{e.id}: {' '.join(bits) if bits else 'plain'}")
    return "\n".join(lines)

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or "bedroom"
    if setting not in ROOMS:
        raise StoryError("This world only supports the bedroom setting.")
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, hero_name=name, hero_trait=trait, seed=args.seed)

def generate(params: StoryParams) -> StorySample:
    world = tell(Setting(place=ROOMS[params.setting]["place"], indoors=True), params.hero_name, params.hero_trait)
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
        print(asp_program("#show problem/1. #show frustrated/1. #show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show problem/1. #show frustrated/1. #show solved/1."))
        print(asp.atoms(model, "problem"))
        print(asp.atoms(model, "frustrated"))
        print(asp.atoms(model, "solved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    seen: set[str] = set()

    if args.all:
        params = [StoryParams(setting="bedroom", hero_name=n, hero_trait=t) for n in NAMES[:5] for t in TRAITS[:1]]
        samples = [generate(p) for p in params[:5]]
    else:
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
