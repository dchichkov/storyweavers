#!/usr/bin/env python3
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
    caregiver: Optional[str] = None
    worn_by: Optional[str] = None
    contains: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id

@dataclass
class Setting:
    place: str = "the workshop"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)

@dataclass
class StoryParams:
    place: str
    concept: str
    vessel: str
    hero: str
    hero_type: str
    mentor: str
    seed: Optional[int] = None

class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary fable about a concept, a mug, and an architectural mistake.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

SETTINGS = {
    "workshop": Setting(place="the workshop", indoors=True, affords={"sketch"}),
    "studio": Setting(place="the studio", indoors=True, affords={"sketch"}),
    "courtyard": Setting(place="the courtyard", indoors=False, affords={"sketch"}),
}

CONCEPTS = {
    "mughouse": {
        "label": "mug-house concept",
        "phrase": "a clever mug-house concept",
        "risk": "top-heavy",
        "lesson": "a home should be strong before it is fancy",
        "danger": "the roof could crack and spill rain inside",
        "shape": "mug-shaped",
    },
    "spoutgate": {
        "label": "spout-gate concept",
        "phrase": "a shiny spout-gate concept",
        "risk": "easy to tip",
        "lesson": "a door must open safely, not just cleverly",
        "danger": "the gate could swing too far and knock over the plan",
        "shape": "spout-shaped",
    },
}

VESSELS = {
    "mug": {
        "label": "mug",
        "phrase": "a bright blue mug",
        "use": "hold warm tea",
        "risk": "can break if dropped",
    }
}

GIRL_NAMES = ["Mina", "Lena", "Nora", "Tia", "Ivy"]
BOY_NAMES = ["Leo", "Omar", "Ben", "Finn", "Arlo"]
TRAITS = ["careful", "proud", "curious", "brave", "thoughtful"]

ASP_RULES = r"""
#show valid/2.
valid(C,V) :- concept(C), vessel(V), allowed(C,V).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for cid in CONCEPTS:
        lines.append(asp.fact("concept", cid))
    for vid in VESSELS:
        lines.append(asp.fact("vessel", vid))
    for cid, cv in CONCEPTS.items():
        for vid in VESSELS:
            if cid == "mughouse":
                lines.append(asp.fact("allowed", cid, vid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def valid_combos() -> list[tuple[str, str]]:
    return [("mughouse", "mug")]

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    concept = "mughouse"
    vessel = "mug"
    hero_type = rng.choice(["girl", "boy"])
    hero = rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    mentor = "the mason"
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    return StoryParams(place=place, concept=concept, vessel=vessel, hero=hero, hero_type=hero_type, mentor=mentor)

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    w = World(setting)
    concept = CONCEPTS[params.concept]
    vessel = VESSELS[params.vessel]

    hero = w.add(Entity(id=params.hero, kind="character", type=params.hero_type, label=params.hero))
    mentor = w.add(Entity(id="mentor", kind="character", type="father", label=params.mentor))
    mug = w.add(Entity(id="mug", type="mug", label=vessel["label"], phrase=vessel["phrase"], owner=hero.id))
    plan = w.add(Entity(id="plan", type="concept", label=concept["label"], phrase=concept["phrase"], owner=hero.id))

    hero.memes["pride"] = 1
    hero.memes["desire"] = 1
    plan.meters["risk"] = 1
    mug.meters["fragile"] = 1

    w.say(f"{hero.id} was a {rng_word(hero.type, ['careful', 'curious', 'proud'])} young builder who loved big ideas.")
    w.say(f"One day, {hero.id} found {plan.phrase} and imagined a house with {concept['shape']} walls.")
    w.say(f"{hero.id} also liked {mug.phrase}, because it could {vessel['use']}.")

    w.para()
    w.say(f"At {w.setting.place}, {hero.id} wanted to turn the {mug.label} into an {concept['label']} for the new room.")
    w.say(f"But {concept['danger']}. That made the design {concept['risk']}, and the little {mug.label} was never meant for so much weight.")

    hero.memes["warning"] = 1
    mentor.memes["concern"] = 1
    w.say(f'"That is a sweet picture," {mentor.label}, said, "but a mug is for holding tea, not holding up a roof."')
    w.say(f"{hero.id} paused and looked at the sketch again.")

    w.para()
    hero.memes["humility"] = 1
    hero.memes["pride"] = 0
    w.say(f"Then {hero.id} drew a steadier plan with strong beams under the pretty curve.")
    w.say(f"The new room kept the {mug.label} only as a cup on the table, where it belonged.")
    w.say(f"In the end, the house stood firm, the tea stayed in the mug, and {hero.id} learned that a clever idea must also be a safe one.")

    w.facts.update(hero=hero, mentor=mentor, plan=plan, mug=mug, concept=concept, vessel=vessel, params=params)
    return w

def rng_word(seed_word: str, choices: list[str]) -> str:
    return choices[0] if choices else seed_word

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for children about a {f["concept"]["label"]} and a {f["vessel"]["label"]}.',
        f'Tell a cautionary story where {f["hero"].id} must learn why a {f["vessel"]["label"]} is not a building block.',
        f'Write a gentle architectural fable about a child who learns that a pretty concept still needs safety.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    concept = f["concept"]
    vessel = f["vessel"]
    return [
        QAItem(
            question=f"What idea did {hero.id} want to turn into a house?",
            answer=f"{hero.id} wanted to turn the {concept['label']} into a house, because the idea looked clever and pretty."
        ),
        QAItem(
            question=f"Why did {mentor.label} warn {hero.id} about the {vessel['label']}?",
            answer=f"{mentor.label} warned {hero.id} because a {vessel['label']} is for holding tea, and it cannot safely hold up a roof."
        ),
        QAItem(
            question=f"What changed after {hero.id} listened?",
            answer=f"{hero.id} chose a steadier design with strong beams, and the {vessel['label']} stayed a cup on the table instead of becoming part of the building."
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a concept?", answer="A concept is an idea in your mind about how something could work or look."),
        QAItem(question="What is a mug for?", answer="A mug is used for holding drinks like tea or cocoa."),
        QAItem(question="What does architectural mean?", answer="Architectural means related to the design and building of houses, rooms, and other structures."),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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

CURATED = [StoryParams(place="workshop", concept="mughouse", vessel="mug", hero="Mina", hero_type="girl", mentor="the mason")]

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid_combos()
        print(f"{len(vals)} compatible combos:\n")
        for item in vals:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(args.n, 1)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
