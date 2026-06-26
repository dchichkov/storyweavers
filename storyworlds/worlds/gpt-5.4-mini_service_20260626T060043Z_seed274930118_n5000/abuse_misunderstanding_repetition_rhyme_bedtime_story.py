#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/abuse_misunderstanding_repetition_rhyme_bedtime_story.py
==============================================================================================================

A small bedtime-story world about a misunderstanding, a repeated comfort,
and a gentle rhyme that helps a child understand the word "abuse".

The premise is intentionally soft and child-facing: a child hears the word
"abuse" in a bedtime conversation and first misunderstands it as something
like "using a toy too hard." The caregiver explains that abuse means hurting
someone or treating them badly, then restores calm with a repeated lullaby
and a rhyme. The simulated state drives the prose, questions, and outcomes.

This world keeps the scope small on purpose:
- one child
- one caregiver
- one beloved bedtime toy
- one misunderstood word
- one resolution through explanation, repetition, and rhyme
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class Setting:
    place: str = "the little bedroom"


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    comfort: str
    rhyme_word: str


@dataclass
class StoryParams:
    place: str
    toy: str
    name: str
    gender: str
    caregiver: str
    seed: Optional[int] = None


SETTINGS = {
    "bedroom": Setting(place="the little bedroom"),
}

TOYS = {
    "bunny": Toy(
        id="bunny",
        label="stuffed bunny",
        phrase="a soft stuffed bunny with floppy ears",
        comfort="soft and calm",
        rhyme_word="honey",
    ),
    "bear": Toy(
        id="bear",
        label="teddy bear",
        phrase="a round teddy bear with a stitched smile",
        comfort="warm and snug",
        rhyme_word="dear",
    ),
    "blanket": Toy(
        id="blanket",
        label="blanket",
        phrase="a blue blanket with little stars",
        comfort="warm and tucked",
        rhyme_word="night",
    ),
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Ben", "Lily", "Owen", "Zoe", "Eli"]
CAREGIVERS = {"mother": "mother", "father": "father"}

TRAITS = ["sleepy", "curious", "gentle", "wobbly", "small"]


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"worry": 0.0, "sleepiness": 0.0, "understanding": 0.0, "comfort": 0.0},
        memes={"sadness": 0.0, "trust": 0.0},
    ))
    caregiver = world.add(Entity(
        id="Caregiver",
        kind="character",
        type=params.caregiver,
        label=f"the {params.caregiver}",
        meters={"worry": 0.0, "care": 0.0},
        memes={"love": 1.0},
    ))
    toy = TOYS[params.toy]
    world.add(Entity(
        id=toy.id,
        type="toy",
        label=toy.label,
        phrase=toy.phrase,
        owner=child.id,
        caretaker=caregiver.id,
        meters={"clean": 1.0},
        memes={"comfort": 1.0},
    ))
    world.facts.update(params=params, child=child, caregiver=caregiver, toy=toy, setting=SETTINGS[params.place])
    return world


def explain_abuse() -> str:
    return (
        "Abuse means hurting someone or treating them in a mean and harmful way. "
        "It is not a game, and it is not a silly mistake."
    )


def rhyme_line(toy: Toy) -> str:
    return {
        "bunny": "Hush, little honey, stay soft and sunny.",
        "bear": "Hush, little dear, the dark is kind and near.",
        "blanket": "Hush, little night, all is warm and right.",
    }[toy.id]


def lullaby_repeat(toy: Toy) -> list[str]:
    line = f"Soft and slow, soft and slow, {toy.label} keeps the sleepy glow."
    return [line, line]


def gentle_resolve(world: World) -> None:
    child = world.facts["child"]
    caregiver = world.facts["caregiver"]
    toy = world.facts["toy"]

    if child.meters["worry"] >= 1.0:
        world.say(
            f"The {caregiver.type} sat beside {child.id} and said, "
            f'"{explain_abuse()}"'
        )
        child.meters["understanding"] += 1.0
        child.meters["worry"] = 0.0
        child.meters["comfort"] += 1.0
        child.memes["trust"] += 1.0
        caregiver.meters["care"] += 1.0
        world.say(
            f"{child.id} listened and nodded. The word was not about a toy at all; "
            f"it was about being unkind in a hurtful way."
        )
        world.say(
            f"Then the {caregiver.type} tucked {toy.label} close and sang the same soft line twice:"
        )
        for line in lullaby_repeat(toy):
            world.say(line)
        world.say(
            f"{rhyme_line(toy)} Soon {child.id} felt safe, and the little bedroom felt "
            f"quiet, warm, and ready for sleep."
        )


def do_story(world: World) -> None:
    child = world.facts["child"]
    caregiver = world.facts["caregiver"]
    toy = world.facts["toy"]
    setting = world.facts["setting"]

    world.say(
        f"At {setting.place}, {child.id} hugged {toy.label} and got ready for bed."
    )
    world.say(
        f"{child.id} loved {toy.label} because it was {toy.comfort} and always waited by the pillow."
    )
    world.para()
    world.say(
        f"Then {child.id} heard the {caregiver.type} say the word 'abuse' in a serious voice."
    )
    child.meters["worry"] += 1.0
    child.memes["sadness"] += 1.0
    world.say(
        f"{child.id} blinked and thought the word might mean to squeeze {toy.label} too hard, "
        f"or to use it the wrong way."
    )
    world.say(
        f"So {child.id} asked again and again, 'Abuse? Abuse? What does abuse mean?'"
    )
    world.para()
    gentle_resolve(world)
    world.facts["resolved"] = child.meters["understanding"] >= 1.0


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    toy = f["toy"]
    return [
        f'Write a bedtime story for a young child named {child.id} about a misunderstood word, a soft toy, and a gentle explanation.',
        f'Create a soothing bedtime story that uses repetition and rhyme and helps a child understand the word "abuse" safely.',
        f'Write a short bedtime tale where {child.id} hears the word "abuse", worries about {toy.label}, and calms down after a kind explanation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    toy = f["toy"]
    return [
        QAItem(
            question=f"What did {child.id} first think the word 'abuse' might mean?",
            answer=f"{child.id} first thought it might mean squeezing {toy.label} too hard or using it the wrong way.",
        ),
        QAItem(
            question=f"How did the {caregiver.type} explain the word 'abuse'?",
            answer="The caregiver explained that abuse means hurting someone or treating them in a mean and harmful way.",
        ),
        QAItem(
            question=f"What helped {child.id} feel safe again at bedtime?",
            answer=f"The repeated lullaby, the rhyme, and the caregiver's gentle explanation helped {child.id} feel safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    toy = world.facts["toy"]
    return [
        QAItem(
            question="What is a lullaby?",
            answer="A lullaby is a soft song sung to help someone relax and fall asleep.",
        ),
        QAItem(
            question="Why do repeated words feel comforting at bedtime?",
            answer="Repeated words can feel comforting because they are predictable and make the room feel calm and safe.",
        ),
        QAItem(
            question=f"Why is {toy.label} nice to hug at bedtime?",
            answer=f"{toy.label.capitalize()} is nice to hug because it is soft and can make a child feel cozy and brave.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A child is worried if they hear the word abuse and do not yet understand it.
worried(C) :- hears_abuse(C), not understands_abuse(C).

% A misunderstanding is present when worry is caused by the wrong meaning.
misunderstanding(C) :- worried(C), guesses_wrong(C).

% Repetition is a comfort if a calm line is said twice.
repetition_help(R) :- repeated_line(R), repeated_line(R).

% A rhyme helps when it is spoken after the explanation.
rhyme_help(T) :- rhyme_line(T), explained_abuse.

% The story resolves when the child understands and feels safe.
resolved(C) :- understands_abuse(C), comforted(C).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hears_abuse", "child"),
        asp.fact("guesses_wrong", "child"),
        asp.fact("repeated_line", "lullaby"),
        asp.fact("rhyme_line", "toy"),
        asp.fact("explained_abuse"),
        asp.fact("comforted", "child"),
        asp.fact("understands_abuse", "child"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1.\n#show misunderstanding/1.\n#show repetition_help/1.\n#show rhyme_help/1."))
    atoms = {(sym.name, tuple(arg.name if arg.type != 2 else arg.string for arg in sym.arguments)) for sym in model}
    expected = {
        ("misunderstanding", ("child",)),
        ("repetition_help", ("lullaby",)),
        ("rhyme_help", ("toy",)),
        ("resolved", ("child",)),
    }
    if atoms == expected:
        print(f"OK: ASP gate matches expected story logic ({len(expected)} atoms).")
        return 0
    print("MISMATCH between ASP and expected logic:")
    print("  got:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    return [("bedroom", toy_id, "child") for toy_id in TOYS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Invalid place.")
    if args.toy and args.toy not in TOYS:
        raise StoryError("Invalid toy.")
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("Invalid gender.")
    place = args.place or "bedroom"
    toy = args.toy or rng.choice(list(TOYS))
    gender = args.gender or rng.choice(["girl", "boy"])
    caregiver = args.caregiver or rng.choice(["mother", "father"])
    name = args.name or rng.choice(CHILD_NAMES)
    return StoryParams(place=place, toy=toy, name=name, gender=gender, caregiver=caregiver)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    do_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime story world about misunderstanding, repetition, and rhyme."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1.\n#show misunderstanding/1.\n#show repetition_help/1.\n#show rhyme_help/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = []
        for place, toy, _ in valid_combos():
            params = StoryParams(
                place=place,
                toy=toy,
                name=CHILD_NAMES[0],
                gender="girl",
                caregiver="mother",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        samples = []
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
