#!/usr/bin/env python3
"""
storyworlds/worlds/augmentin_kindness_rhyming_story.py
======================================================

A small storyworld for a gentle, rhyming-kindness tale about taking augmentin.

Premise:
- A child or parent notices someone is feeling unwell.
- A doctor says augmentin will help.
- The medicine tastes a bit yucky, so the patient hesitates.
- Kindness and a calm helper turn the moment into a brave, cozy ending.

This world keeps the narrative close to a rhyming-story feel:
- short, musical sentences
- concrete daily actions
- a clear emotional turn from worry to comfort
- an ending image that proves what changed

The script exposes the standard storyworld interface:
- StoryParams
- build_parser
- resolve_params
- generate
- emit
- main

It also includes:
- a Python reasonableness gate
- inline ASP_RULES
- asp_facts() and ASP parity verification
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
    wore_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Situation:
    id: str
    ailment: str
    symptom: str
    need: str
    sound: str
    kind_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Medicine:
    id: str
    label: str
    phrase: str
    purpose: str
    taste: str
    prep: str
    tags: set[str] = field(default_factory=set)


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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "home": Setting(place="the cozy home", indoor=True, affords={"medicine"}),
    "clinic": Setting(place="the little clinic", indoor=True, affords={"medicine"}),
    "kitchen": Setting(place="the sunny kitchen", indoor=True, affords={"medicine"}),
}

SITUATIONS = {
    "sore_throat": Situation(
        id="sore_throat",
        ailment="a sore throat",
        symptom="a scratchy throat",
        need="helped the throat heal",
        sound="cough",
        kind_word="kindness",
        tags={"illness", "medicine", "kindness"},
    ),
    "earache": Situation(
        id="earache",
        ailment="an earache",
        symptom="a sore ear",
        need="helped the ear feel better",
        sound="whimper",
        kind_word="kindness",
        tags={"illness", "medicine", "kindness"},
    ),
    "tummy_bug": Situation(
        id="tummy_bug",
        ailment="a tummy bug",
        symptom="a twisty tummy",
        need="helped the tummy settle",
        sound="groan",
        kind_word="kindness",
        tags={"illness", "medicine", "kindness"},
    ),
}

MEDICINES = {
    "augmentin": Medicine(
        id="augmentin",
        label="augmentin",
        phrase="a little pink dose of augmentin",
        purpose="helped fight the germs",
        taste="bitter",
        prep="sip it with water",
        tags={"medicine", "augmentin", "kindness"},
    ),
    "honey_sip": Medicine(
        id="honey_sip",
        label="honey water",
        phrase="a warm spoon of honey water",
        purpose="soothed the throat",
        taste="sweet",
        prep="sip it slowly",
        tags={"medicine", "kindness"},
    ),
}

CHILD_NAMES = ["Mia", "Noah", "Luna", "Eli", "Zoe", "Owen", "Ava", "Theo"]
ADULT_NAMES = ["Mom", "Dad", "Nurse Jo", "Dr. Lee"]
TRAITS = ["brave", "gentle", "little", "sweet", "curious", "shy"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    situation: str
    medicine: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Python reasonableness gate
# ---------------------------------------------------------------------------
def reasonableness_check(place: str, situation: Situation, medicine: Medicine) -> bool:
    if place not in SETTINGS:
        return False
    if situation.id not in SITUATIONS:
        return False
    if medicine.id not in MEDICINES:
        return False
    if situation.id == "tummy_bug" and medicine.id == "augmentin":
        return False
    return True


def explain_rejection(place: str, situation: Situation, medicine: Medicine) -> str:
    if situation.id == "tummy_bug" and medicine.id == "augmentin":
        return (
            "(No story: augmentin is a better fit for throat or ear troubles here, "
            "not a tummy bug. The kindness tale should use a medicine that feels honest.)"
        )
    return "(No story: that combination does not make a gentle, believable story.)"


# ---------------------------------------------------------------------------
# Tiny world simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    situation = SITUATIONS[params.situation]
    medicine = MEDICINES[params.medicine]
    world = World(setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Mia", "Luna", "Zoe", "Ava"} else "boy",
        meters={"comfort": 0.0},
        memes={"worry": 0.0, "kindness": 0.0, "brave": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="mother" if params.helper == "Mom" else "father" if params.helper == "Dad" else "doctor",
        meters={"comfort": 0.0},
        memes={"kindness": 0.0, "patience": 0.0},
    ))
    med = world.add(Entity(
        id=medicine.id,
        type="medicine",
        label=medicine.label,
        phrase=medicine.phrase,
        owner=child.id,
        caretaker=helper.id,
    ))
    world.facts.update(child=child, helper=helper, medicine=med, situation=situation, setting=setting)

    # Act 1: setup
    world.say(
        f"{child.id} had {situation.symptom}, oh dear, oh dear; "
        f"the little ache felt close and near."
    )
    world.say(
        f"{helper.id} came close with a careful cheer, "
        f"and said that kindness could calm the fear."
    )
    world.say(
        f"At {setting.place}, where the warm lights gleam, "
        f"the day felt soft like a sleepy dream."
    )

    # Act 2: tension
    world.para()
    child.memes["worry"] += 1
    world.say(
        f"{child.id} saw {medicine.label} and frowned a bit, "
        f"for {medicine.label} can taste quite bitter-ish."
    )
    world.say(
        f"{child.id} said, \"I do not want a yucky sip!\" "
        f"and hugged the cup with a trembling lip."
    )
    helper.memes["patience"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.id} smiled and said, \"We can go slow; "
        f"a tiny brave step can help you grow.\""
    )

    # Act 3: turn and resolution
    world.para()
    child.memes["brave"] += 1
    child.memes["kindness"] += 1
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    child.meters["comfort"] += 1.0
    helper.meters["comfort"] += 1.0
    world.say(
        f"{child.id} took {medicine.label} with a little sip, "
        f"then chased it down with a grateful grip."
    )
    world.say(
        f"The dose went in; the fear let go. "
        f"Kindness made the whole room glow."
    )
    world.say(
        f"By bedtime, {child.id} felt softer and steady, "
        f"and the night was calm and story-ready."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Story text helpers
# ---------------------------------------------------------------------------
def opening_line(params: StoryParams) -> str:
    return (
        f"{params.name} had a tiny trouble, a sniffly little trial, "
        f"and kindness came to meet it with a gentle, hopeful smile."
    )


def setting_line(world: World) -> str:
    return f"The story sat in {world.setting.place}, bright and snug and mild."


def ending_line(world: World) -> str:
    child = world.facts["child"]
    medicine = world.facts["medicine"]
    return (
        f"At the end, {child.id} was tucked in deep and green, "
        f"with {medicine.label} taken, and the worry scarcely seen."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    situation = f["situation"]
    medicine = f["medicine"]
    return [
        "Write a short rhyming story for a young child about kindness and a medicine named augmentin.",
        f"Tell a gentle story where {child.id} feels unwell, {medicine.label} helps, and the mood changes from worry to courage.",
        f"Write a cozy rhyme about {situation.ailment}, a patient helper, and a brave sip at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    situation = f["situation"]
    medicine = f["medicine"]
    return [
        QAItem(
            question=f"What was {child.id} feeling in the story?",
            answer=f"{child.id} had {situation.ailment}, which felt like {situation.symptom}.",
        ),
        QAItem(
            question=f"Who helped {child.id} with kindness?",
            answer=f"{helper.id} helped {child.id} with patience, soft words, and a calm smile.",
        ),
        QAItem(
            question=f"What medicine did {child.id} take?",
            answer=f"{child.id} took {medicine.label}, a little dose that was meant to help the germs go away.",
        ),
        QAItem(
            question=f"Why did {child.id} hesitate at first?",
            answer=f"{medicine.label} tasted bitter, so {child.id} felt worried about the sip.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {child.id} felt braver and calmer, and the room felt warm with kindness.",
        ),
    ]


KNOWLEDGE = {
    "augmentin": [
        (
            "What is augmentin?",
            "Augmentin is a medicine that doctors may use to help fight certain infections.",
        ),
    ],
    "kindness": [
        (
            "What does kindness mean?",
            "Kindness means choosing gentle words and helpful actions so someone else feels cared for.",
        ),
    ],
    "medicine": [
        (
            "Why do people take medicine?",
            "People take medicine to help their bodies get better or to ease symptoms when they are sick.",
        ),
    ],
    "illness": [
        (
            "What is an illness?",
            "An illness is when a person's body is not feeling well and needs care or rest.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["situation"].tags)
    tags.add(world.facts["medicine"].id)
    out: list[QAItem] = []
    for tag in ["augmentin", "kindness", "medicine", "illness"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is reasonable when the setting, situation, and medicine are known.
reasonable(P, S, M) :- setting(P), situation(S), medicine(M).

% Augmentin is a valid medicine for throat and ear troubles in this tiny world.
compatible(augmentin, sore_throat).
compatible(augmentin, earache).

% A valid story needs a reasonable match.
valid_story(P, S, M) :- reasonable(P, S, M), compatible(M, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for sid in SITUATIONS:
        lines.append(asp.fact("situation", sid))
    for mid in MEDICINES:
        lines.append(asp.fact("medicine", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid_combos() -> list[tuple]:
    combos = []
    for place in SETTINGS:
        for sid, situation in SITUATIONS.items():
            for mid, medicine in MEDICINES.items():
                if reasonableness_check(place, situation, medicine):
                    if medicine.id == "augmentin" and situation.id in {"sore_throat", "earache"}:
                        combos.append((place, sid, mid))
    return combos


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(python_valid_combos())
    if a == p:
        print(f"OK: clingo gate matches python gate ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A rhyming kindness storyworld about augmentin."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--situation", choices=SITUATIONS)
    ap.add_argument("--medicine", choices=MEDICINES)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--helper", choices=ADULT_NAMES)
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
    place = args.place or rng.choice(list(SETTINGS))
    situation = args.situation or rng.choice(["sore_throat", "earache"])
    medicine = args.medicine or "augmentin"
    if not reasonableness_check(place, SITUATIONS[situation], MEDICINES[medicine]):
        raise StoryError(explain_rejection(place, SITUATIONS[situation], MEDICINES[medicine]))
    name = args.name or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice(ADULT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, situation=situation, medicine=medicine, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = "\n\n".join(
        [
            opening_line(params),
            setting_line(world),
            world.render(),
            ending_line(world),
        ]
    )
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="home", situation="sore_throat", medicine="augmentin", name="Mia", helper="Mom", trait="gentle"),
    StoryParams(place="clinic", situation="earache", medicine="augmentin", name="Noah", helper="Dr. Lee", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
