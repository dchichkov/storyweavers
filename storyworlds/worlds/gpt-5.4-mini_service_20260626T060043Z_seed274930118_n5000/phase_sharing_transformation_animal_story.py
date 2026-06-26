#!/usr/bin/env python3
"""
A small animal-story world about a phase of sharing and transformation.

A tiny source-tale premise:
A little squirrel has a shiny red acorn and does not want to share it. A hungry
rabbit asks for a bite, then offers to split a carrot in return. The squirrel
tries sharing, discovers it feels warm to help, and changes from stingy to kind.
By the end, the two animals share a snack together, and the squirrel's heart has
softened into a sharing phase.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
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
    plural: bool = False
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        animalish = {"squirrel", "rabbit", "fox", "bear", "deer", "owl", "mouse", "chipmunk"}
        if self.type in animalish:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    animal_a: str
    animal_b: str
    prize: str
    setting: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    shared_space: bool
    phase: str


@dataclass
class Prize:
    label: str
    phrase: str
    kind: str
    shareable: bool = True


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


SETTINGS = {
    "meadow": Setting(place="the meadow", shared_space=True, phase="sharing"),
    "pond": Setting(place="the pond", shared_space=True, phase="sharing"),
    "burrow": Setting(place="the burrow", shared_space=False, phase="transformation"),
}

PRIZES = {
    "acorn": Prize(label="acorn", phrase="a shiny red acorn", kind="food"),
    "carrot": Prize(label="carrot", phrase="a crunchy orange carrot", kind="food"),
    "berry": Prize(label="berry", phrase="a bowl of sweet berries", kind="food"),
    "cookie": Prize(label="cookie", phrase="one big honey cookie", kind="food"),
}

ANIMALS = ["squirrel", "rabbit", "fox", "bear", "deer", "owl", "mouse", "chipmunk"]

ASP_RULES = r"""
#show valid/3.
shareable_prize(P) :- prize(P).
social_setting(S) :- setting(S).
valid(S,A,B) :- social_setting(S), animal(A), animal(B), A != B, prize(P), shareable_prize(P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.shared_space:
            lines.append(asp.fact("shared_space", sid))
        lines.append(asp.fact("phase", sid, s.phase))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for a in ANIMALS:
            for b in ANIMALS:
                if a != b:
                    for p in PRIZES:
                        if s.shared_space:
                            combos.append((sid, a, p))
    return combos

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about sharing and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal-a", choices=ANIMALS)
    ap.add_argument("--animal-b", choices=ANIMALS)
    ap.add_argument("--prize", choices=PRIZES)
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

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = []
    for sid, a, p in valid_combos():
        s = SETTINGS[sid]
        if args.setting and sid != args.setting:
            continue
        if args.animal_a and a != args.animal_a:
            continue
        if args.prize and p != args.prize:
            continue
        combos.append((sid, a, p))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, a, p = rng.choice(sorted(combos))
    b_choices = [x for x in ANIMALS if x != a]
    b = args.animal_b or rng.choice(b_choices)
    return StoryParams(animal_a=a, animal_b=b, prize=p, setting=sid)

def _name(animal: str) -> str:
    return animal.capitalize()

def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    a = world.add(Entity(id=params.animal_a, kind="character", type=params.animal_a, label=params.animal_a))
    b = world.add(Entity(id=params.animal_b, kind="character", type=params.animal_b, label=params.animal_b))
    prize = world.add(Entity(id=params.prize, kind="thing", type=params.prize, label=params.prize, phrase=PRIZES[params.prize].phrase, owner=a.id, holder=a.id))
    a.memes["stingy"] = 1.0
    a.memes["curious"] = 1.0
    b.memes["hungry"] = 1.0

    world.say(f"One day in {world.setting.place}, {_name(a.type)} had {prize.phrase} and did not want to share.")
    world.say(f"Then {_name(b.type)} came along and asked, \"May I have a little bit, please?\"")
    world.para()
    world.say(f"{_name(a.type)} hugged the snack close and felt a prickly, stingy phase settle in.")
    world.say(f"But {_name(b.type)} smiled and offered to split a {PRIZES['carrot'].phrase if params.prize != 'carrot' else 'fresh berry pile'} in return.")
    a.memes["stingy"] = 0.0
    a.memes["kind"] = 1.0
    a.memes["sharing"] = 1.0
    world.para()
    world.say(f"{_name(a.type)} tried it and found that sharing made the air feel lighter.")
    world.say(f"The two animals sat together, traded bites, and turned the day into a sharing phase.")
    world.say(f"By the end, {_name(a.type)} was no longer guarding the snack; {prize.phrase} was part of both of them's happy little meal.")
    world.facts.update(a=a, b=b, prize=prize, setting=world.setting)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, prize, setting = f["a"], f["b"], f["prize"], f["setting"]
    return [
        f'Write a short animal story about a {a.type} and a {b.type} in {setting.place} that moves from stingy to sharing.',
        f"Tell a gentle story where {_name(a.type)} starts with {prize.phrase}, feels grumpy for a moment, and then changes.",
        f'Write a child-friendly story using the word "phase" about animals learning to share food.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, prize, setting = f["a"], f["b"], f["prize"], f["setting"]
    return [
        QAItem(
            question=f"Who had {prize.phrase} at first?",
            answer=f"{_name(a.type)} had {prize.phrase} at first."
        ),
        QAItem(
            question=f"What did {_name(b.type)} ask for?",
            answer=f"{_name(b.type)} asked if it could have a little bit of the {prize.label}."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with both animals sharing together in {setting.place}, and {_name(a.type)} changed into a kinder, sharing phase."
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does sharing mean?", answer="Sharing means letting someone else use or enjoy some of what you have."),
        QAItem(question="What is a phase?", answer="A phase is a period of time when something is happening or changing in a certain way."),
        QAItem(question="How can animals show kindness?", answer="Animals can show kindness by taking turns, sharing food, and helping one another."),
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)

CURATED = [
    StoryParams(animal_a="squirrel", animal_b="rabbit", prize="acorn", setting="meadow"),
    StoryParams(animal_a="fox", animal_b="mouse", prize="berry", setting="pond"),
    StoryParams(animal_a="bear", animal_b="deer", prize="cookie", setting="burrow"),
]

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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.animal_a}, {p.animal_b} in {p.setting} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
