#!/usr/bin/env python3
"""
Bedtime story world: a small, soft tale about a child who stammers, a merry
evening, and a lesson learned.

The model keeps one grounded premise:
- a child wants to say something kind or important,
- the words get stuck in a stammer,
- a helper waits patiently,
- the child learns that slow, calm speech can still reach the listener,
- the ending proves the lesson with a warmer mood.

The prose is driven by state:
- meters track physical events like breath, page, light, and bedtime readiness,
- memes track feelings like worry, bravery, joy, and relief.

The world is intentionally small and classical, so the generated stories feel
like short bedtime stories rather than event logs.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the bedroom"
    light: str = "lamplight"
    bedtime: bool = True


@dataclass
class Lesson:
    title: str
    learned_line: str
    comfort_line: str


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    setting: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mia", "Luna", "Ivy", "Nora", "Ruby", "Ella", "Zoe"]
BOY_NAMES = ["Noah", "Theo", "Eli", "Finn", "Leo", "Ari", "Max"]
TRAITS = ["gentle", "curious", "shy", "brave", "soft-hearted", "careful"]

SETTINGS = {
    "bedroom": Setting(place="the bedroom", light="lamplight", bedtime=True),
    "nursery": Setting(place="the nursery", light="night-light", bedtime=True),
    "cottage": Setting(place="the cottage room", light="warm lamplight", bedtime=True),
}

LESSONS = {
    "stammer": Lesson(
        title="Lesson Learned",
        learned_line="Slow words can still be kind words.",
        comfort_line="A patient listener can make room for every word.",
    )
}

ASP_RULES = r"""
% A child is ready for the lesson when worry drops and joy rises.
ready_for_lesson(C) :- child(C), worry(C, W), joy(C, J), W < 1, J >= 1.

% If a child stammers, the story should contain patience and a calmer ending.
needs_patience(C) :- stammers(C).
learns_lesson(C) :- stammers(C), ready_for_lesson(C), heard_kind_response(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.bedtime:
            lines.append(asp.fact("bedtime", sid))
    for lid in LESSONS:
        lines.append(asp.fact("lesson", lid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a child stammers, learns a lesson, and ends merry."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    setting = args.setting or rng.choice(list(SETTINGS))
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait, setting=setting)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[params.trait, "little"]))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    book = world.add(Entity(id="book", type="thing", label="storybook", phrase="a shiny bedtime storybook", owner=child.id))
    blanket = world.add(Entity(id="blanket", type="thing", label="blanket", phrase="a soft blanket", owner=child.id))

    child.memes.update(worry=1.0, joy=0.0, bravery=0.0, relief=0.0)
    child.meters.update(breath=0.2, bedtime_ready=0.0)
    parent.memes.update(patience=1.0, love=1.0)
    world.facts.update(child=child, parent=parent, book=book, blanket=blanket)

    world.say(f"{child.id} was a {params.trait} little {params.gender} who liked the warm quiet of {world.setting.place}.")
    world.say(f"At bedtime, {child.id} held {child.pronoun('possessive')} storybook close while the {world.setting.light} glowed softly.")

    world.para()
    world.say(f"{child.id} had something important to say, but the first words came out in a stammer.")
    child.memes["worry"] += 1.0
    child.meters["breath"] += 0.6
    world.say(f"The stammer made {child.id} feel small for a moment, and the room seemed very still.")

    world.para()
    world.say(f"{parent.id.capitalize()} sat down beside {child.id} and waited with a gentle smile.")
    world.say(f'"Take your time," {parent.pronoun()} said. "I am listening."')
    parent.memes["patience"] += 1.0
    child.memes["bravery"] += 1.0
    child.meters["breath"] += 0.8
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    world.say(f"That made {child.id}'s heart feel a little steadier.")

    world.para()
    world.say(f"{child.id} tried again, this time slowly, and the words came out clear and true.")
    world.say(f"{child.id} told {child.pronoun('possessive')} {params.parent} about the merry thing {child.pronoun()} had noticed: the room felt safe, the blanket felt soft, and love felt near.")
    child.memes["joy"] += 1.5
    child.memes["relief"] += 1.5
    child.meters["bedtime_ready"] += 1.0
    world.say(f"{params.parent.capitalize()} laughed a warm little laugh and gave {child.id} a hug.")

    world.para()
    world.say(f"In the end, {child.id} tucked {child.pronoun('possessive')} blanket around the book and smiled at the lamp.")
    world.say("Lesson Learned: slow words can still be kind words, and patient listening makes a merry room at bedtime.")

    world.facts["lesson"] = LESSONS["stammer"]
    world.facts["merry"] = True
    world.facts["resolved"] = True
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
    child = f["child"]
    return [
        'Write a short bedtime story for a small child about a stammer, a kind listener, and a lesson learned.',
        f"Tell a gentle story where {child.id} wants to speak at bedtime but stammers, and {child.pronoun('possessive')} parent helps.",
        "Write a cozy, child-friendly story that ends with a lesson learned and a merry feeling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    setting = world.setting.place
    return [
        QAItem(
            question=f"Why did {child.id} feel stuck when trying to speak in {setting}?",
            answer=f"{child.id} felt stuck because the words came out in a stammer, and that made {child.pronoun('object')} worry for a moment.",
        ),
        QAItem(
            question=f"What did {parent.id} do when {child.id} stammered?",
            answer=f"{parent.id.capitalize()} sat beside {child.id}, waited patiently, and told {child.pronoun('object')} to take {child.pronoun('possessive')} time.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn by the end of the bedtime story?",
            answer="The lesson learned was that slow words can still be kind words, and patient listening can help them come out.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt relieved, brave, and merry after the words finally came out clearly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bedtime?",
            answer="Bedtime is the time when children get ready to rest, listen to a story, and go to sleep.",
        ),
        QAItem(
            question="What does patient mean?",
            answer="Patient means calm and willing to wait without getting upset.",
        ),
        QAItem(
            question="What is a stammer?",
            answer="A stammer is when words come out in a bumpy or repeated way while someone is speaking.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show ready_for_lesson/1. #show learns_lesson/1."))
    atoms = set((s.name, tuple(a.name if a.type == a.type.SymbolType.Function else a.number for a in s.arguments)) for s in model)
    if atoms:
        print("OK: ASP program solved.")
        return 0
    print("ASP produced no model.")
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


def valid_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show ready_for_lesson/1. #show learns_lesson/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show ready_for_lesson/1. #show learns_lesson/1."))
        print(f"ASP model atoms: {len(model)}")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mia", gender="girl", parent="mother", trait="gentle", setting="bedroom"),
            StoryParams(name="Noah", gender="boy", parent="father", trait="shy", setting="nursery"),
            StoryParams(name="Luna", gender="girl", parent="mother", trait="brave", setting="cottage"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = valid_params(args, random.Random(seed))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
