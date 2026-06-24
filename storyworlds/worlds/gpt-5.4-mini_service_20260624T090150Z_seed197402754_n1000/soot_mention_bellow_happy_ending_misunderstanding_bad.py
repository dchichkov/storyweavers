#!/usr/bin/env python3
"""
A small bedtime-story world about soot, a loud bellow, and a misunderstanding
that can end happily or badly depending on what the child does.

Initial seed tale:
---
A little child saw black soot on the hearth and wanted to help clean it away.
A grown-up mentioned that the soft brush was for the shelf, not the wall.
The child misunderstood and picked the wrong cloth anyway.
The grown-up bellowed a warning, but then showed a gentler way.
In the happy ending, they cleaned the soot together and the room looked warm
and tidy. In a bad ending variant, the soot was smeared everywhere and nobody
felt good at bedtime.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the kitchen hearth"
    bedtime: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    clears: set[str] = field(default_factory=set)
    safe_for: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    ending: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


THRESHOLD = 1.0

TOOLS = {
    "soft_brush": Tool(
        id="soft_brush",
        label="a soft brush",
        phrase="a soft brush",
        clears={"soot"},
        safe_for={"hearth"},
    ),
    "damp_cloth": Tool(
        id="damp_cloth",
        label="a damp cloth",
        phrase="a damp cloth",
        clears={"soot"},
        safe_for={"table"},
    ),
    "small_pail": Tool(
        id="small_pail",
        label="a small pail",
        phrase="a small pail of warm water",
        clears={"soot"},
        safe_for={"hearth", "wall"},
    ),
}

SETTINGS = {
    "hearth": Setting(place="the kitchen hearth", bedtime=True),
    "wall": Setting(place="the nursery wall by the lamp", bedtime=True),
    "table": Setting(place="the little tea table", bedtime=True),
}

NAMES = {
    "girl": ["Mila", "Nora", "Luna", "Ella", "Mia"],
    "boy": ["Theo", "Finn", "Leo", "Owen", "Max"],
}

TRAITS = ["curious", "gentle", "sleepy", "helpful", "quiet"]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for k in sorted(t.clears):
            lines.append(asp.fact("clears", tid, k))
        for k in sorted(t.safe_for):
            lines.append(asp.fact("safe_for", tid, k))
    lines.append(asp.fact("mess", "soot"))
    return "\n".join(lines)


ASP_RULES = r"""
needs_cleaning(P) :- soot_on(P).
can_use(T,P) :- tool(T), needs_cleaning(P), clears(T,soot), safe_for(T,P).
happy_ending(P,T) :- can_use(T,P).
bad_ending(P) :- needs_cleaning(P), not happy_ending(P,_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _py_supports(setting_id: str, tool_id: str) -> bool:
    return "soot" in TOOLS[tool_id].clears and setting_id in TOOLS[tool_id].safe_for


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for tool in TOOLS:
            if _py_supports(place, tool):
                out.append((place, "soot", tool))
    return out


def _says(world: World, line: str) -> None:
    world.say(line)


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    adult = world.add(Entity(id="Adult", kind="character", type=params.adult, label="the grown-up", meters={}, memes={}))
    soot = world.add(Entity(id="Soot", type="soot", label="soot", phrase="black soot", meters={"mess": 1.0}))
    tool = world.add(Entity(id="Tool", type="tool", label=TOOLS["soft_brush"].label, phrase=TOOLS["soft_brush"].phrase))

    world.facts.update(child=child, adult=adult, soot=soot, tool=tool, ending=params.ending, place=params.place)

    _says(world, f"{child.id} was a little {params.trait} {params.gender} who lived near {setting.place}.")
    _says(world, f"At bedtime, {child.pronoun('subject')} noticed black soot by the warm hearth and wanted to help.")
    _says(world, f"{adult.pronoun().capitalize()} mentioned, \"Use the soft brush for the shelf, not the wall.\"")
    _says(world, f"But {child.id} misunderstood the kind words and picked up the wrong cloth anyway.")
    world.para()
    child.memes["misunderstanding"] = 1.0
    _says(world, f"Then {adult.pronoun().capitalize()} had to bellow, \"No, little one, not that way!\"")
    child.memes["startled"] = 1.0

    if params.ending == "happy":
        world.para()
        _says(world, f"{child.id} froze, listened, and nodded. The grown-up showed a gentle way to brush the soot away.")
        _says(world, f"Together they cleaned the hearth, and the black soot lifted from the stones like a dark cloud.")
        _says(world, f"At the end, the room looked warm and tidy, and {child.id} smiled at the sleepy glow.")
        soot.meters["mess"] = 0.0
        world.facts["happy"] = True
    else:
        world.para()
        _says(world, f"{child.id} kept scraping with the wrong cloth, and the soot smeared over the corner instead.")
        _says(world, f"The grown-up sighed, and the little room felt sad and messy at bedtime.")
        _says(world, f"That was a bad ending, because the soot stayed on the wall and nobody felt like singing.")
        soot.meters["mess"] = 2.0
        world.facts["happy"] = False

    world.facts["soot_on"] = {"hearth": True}
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    return [
        f"Write a bedtime story about {child.id}, soot, and a misunderstanding that gets fixed kindly.",
        f"Tell a gentle story where {adult.label} bellowed a warning, but the child still learned what to do with soot.",
        "Write a short story for children that includes soot, mention, and bellow, and ends with either a happy ending or a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    happy = f["happy"]
    place = f["place"]
    ans = []
    ans.append(QAItem(
        question=f"Who was the story about at {place}?",
        answer=f"It was about {child.id}, a little {child.type}, and {adult.label}, the grown-up nearby."
    ))
    ans.append(QAItem(
        question="What did the child notice by the hearth?",
        answer="The child noticed black soot and wanted to help clean it away."
    ))
    ans.append(QAItem(
        question="What mistake happened in the middle of the story?",
        answer="The child misunderstood the grown-up's mention about the brush and picked the wrong cloth."
    ))
    if happy:
        ans.append(QAItem(
            question="How did the story end?",
            answer="It ended happily, with the soot cleaned away and the room looking warm and tidy."
        ))
    else:
        ans.append(QAItem(
            question="How did the story end?",
            answer="It ended badly, with soot smeared around and the room still messy."
        ))
    return ans


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is soot?",
            answer="Soot is a black powdery mark left by fire or smoke."
        ),
        QAItem(
            question="What does it mean to bellow?",
            answer="To bellow means to speak very loudly, like a strong warning."
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone does not understand a message the right way."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.extend(world.trace)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about soot and misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--ending", choices=["happy", "bad"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS.keys()))
    ending = args.ending or rng.choice(["happy", "bad"])
    gender = args.gender or rng.choice(["girl", "boy"])
    adult = args.adult or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice(NAMES[gender])
    if ending not in {"happy", "bad"}:
        raise StoryError("Invalid ending.")
    return StoryParams(place=place, ending=ending, name=name, gender=gender, adult=adult, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
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


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - asp_set))
    print("only in clingo:", sorted(asp_set - py))
    return 1


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
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="hearth", ending="happy", name="Mila", gender="girl", adult="mother", trait="gentle"),
            StoryParams(place="wall", ending="happy", name="Theo", gender="boy", adult="father", trait="curious"),
            StoryParams(place="table", ending="bad", name="Nora", gender="girl", adult="mother", trait="sleepy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
