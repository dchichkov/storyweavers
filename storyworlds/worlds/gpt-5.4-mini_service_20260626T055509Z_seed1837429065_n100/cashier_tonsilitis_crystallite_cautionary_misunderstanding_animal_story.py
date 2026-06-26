#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/cashier_tonsilitis_crystallite_cautionary_misunderstanding_animal_story.py
============================================================================================================

A tiny animal-story world about a careful cashier, a sore throat, and a
sparkly crystallite that causes a misunderstanding.

Premise:
- A young animal wants a shiny crystallite from the shop.
- The cashier notices the child has tonsilitis and gives a cautionary warning.
- The child misunderstands the warning at first and thinks the crystallite is
  being refused for no reason.
- A patient explanation turns the moment into a gentle, careful lesson.

World model:
- Animals have meters for health, throat soreness, and safety.
- Careful words reduce danger; misunderstanding raises it.
- A reassuring explanation lowers worry and resolves the scene.

The prose is intentionally small, concrete, and child-facing, with an ending
that proves the child learned something and the shiny thing stayed safe.
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
# Core model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "animal" | "person" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "rabbit", "bunny", "cat", "deer", "squirrel", "mouse"}
        male = {"boy", "fox", "bear", "dog", "wolf", "rat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    setting: str = "the little market"
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


@dataclass
class StoryParams:
    cashier_type: str
    child_type: str
    child_name: str
    cashier_name: str
    setting: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

CASHIER_TYPES = {
    "cat": {"label": "cashier-cat", "gender": "female"},
    "dog": {"label": "cashier-dog", "gender": "male"},
    "rabbit": {"label": "cashier-rabbit", "gender": "female"},
}

CHILD_TYPES = {
    "fox": {"label": "young fox", "gender": "male"},
    "bunny": {"label": "little bunny", "gender": "female"},
    "mouse": {"label": "small mouse", "gender": "female"},
    "bear": {"label": "cub", "gender": "male"},
}

SETTINGS = {
    "market": "the little market",
    "corner_shop": "the corner shop",
    "station_kiosk": "the station kiosk",
}

NAMES = {
    "fox": ["Finn", "Toby", "Remy"],
    "bunny": ["Mina", "Lulu", "Poppy"],
    "mouse": ["Nina", "Tia", "Mimi"],
    "bear": ["Ollie", "Bram", "Hugo"],
}

CASHIER_NAMES = ["Mara", "Pip", "Nell", "Juno", "Iris"]

ITEMS = {
    "crystallite": {
        "label": "crystallite",
        "phrase": "a tiny crystallite in a paper cup",
        "shine": "sparkled like a bead of ice",
    }
}

ILLNESSES = {
    "tonsilitis": {
        "label": "tonsilitis",
        "symptoms": "a sore throat and trouble swallowing",
        "warning": "sweet, hard, or scratchy treats could hurt",
    }
}

TRAITS = ["careful", "kind", "patient", "gentle"]


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    w = World(setting=SETTINGS[params.setting])
    child_gender = CHILD_TYPES[params.child_type]["gender"]
    cashier_gender = CASHIER_TYPES[params.cashier_type]["gender"]

    child = w.add(Entity(
        id=params.child_name,
        kind="animal",
        type=params.child_type,
        label=CHILD_TYPES[params.child_type]["label"],
        meters={"health": 1.0, "throat_sore": 0.0, "worry": 0.0},
        memes={"hope": 0.0, "misunderstanding": 0.0, "relief": 0.0},
    ))
    cashier = w.add(Entity(
        id=params.cashier_name,
        kind="animal",
        type=params.cashier_type,
        label=CASHIER_TYPES[params.cashier_type]["label"],
        meters={"health": 1.0, "care": 1.0},
        memes={"caution": 0.0, "kindness": 1.0},
    ))
    crystallite = w.add(Entity(
        id="crystallite",
        kind="thing",
        type="crystallite",
        label="crystallite",
        phrase=ITEMS["crystallite"]["phrase"],
        owner=params.cashier_name,
        meters={"shine": 1.0},
    ))
    illness = w.add(Entity(
        id="tonsilitis",
        kind="thing",
        type="tonsilitis",
        label="tonsilitis",
        phrase=ILLNESSES["tonsilitis"]["label"],
        meters={"risk": 1.0},
    ))

    w.facts.update(
        child=child,
        cashier=cashier,
        crystallite=crystallite,
        illness=illness,
        child_gender=child_gender,
        cashier_gender=cashier_gender,
        child_type=params.child_type,
        cashier_type=params.cashier_type,
        setting=params.setting,
        setting_name=w.setting,
    )

    # Story beats.
    intro(w, child, cashier, crystallite)
    w.para()
    cautionary_warning(w, child, cashier, crystallite, illness)
    misunderstanding(w, child, cashier)
    w.para()
    explanation_and_resolution(w, child, cashier, crystallite, illness)
    return w


def intro(w: World, child: Entity, cashier: Entity, crystallite: Entity) -> None:
    w.say(
        f"In {w.setting}, {child.id} was a {child.label} who loved shiny things."
    )
    w.say(
        f"One bright morning, {child.id} spotted {crystallite.phrase}, and its little glow {ITEMS['crystallite']['shine']}."
    )
    w.say(
        f"Behind the counter, {cashier.id} was a {cashier.label} who watched over the treats with a careful eye."
    )
    child.memes["hope"] += 1.0


def cautionary_warning(w: World, child: Entity, cashier: Entity, crystallite: Entity, illness: Entity) -> None:
    child.meters["throat_sore"] = 1.0
    child.memes["worry"] += 1.0
    cashier.memes["caution"] += 1.0
    w.say(
        f"{cashier.id} leaned down and said, '{cashier.pronoun('subject').capitalize()} wanted to warn {child.id} kindly: with {illness.label}, {ILLNESSES['tonsilitis']['warning']}.'"
    )
    w.say(
        f"{cashier.id} said {child.id} could look at the {crystallite.label} now, but should wait before tasting anything sharp or hard."
    )


def misunderstanding(w: World, child: Entity, cashier: Entity) -> None:
    child.memes["misunderstanding"] += 1.0
    child.meters["worry"] += 1.0
    w.say(
        f"{child.id} blinked and looked sad. {child.pronoun('subject').capitalize()} thought {cashier.id} was saying no to the {crystallite.label} forever."
    )
    w.say(
        f"'{child.id} was not trying to be naughty,' {cashier.id} said softly, 'just mistaken.'"
    )


def explanation_and_resolution(w: World, child: Entity, cashier: Entity, crystallite: Entity, illness: Entity) -> None:
    child.memes["misunderstanding"] = 0.0
    child.meters["worry"] = 0.0
    child.meters["throat_sore"] = 0.5
    child.memes["relief"] += 1.0
    w.say(
        f"{cashier.id} pointed to the {crystallite.label} and explained that it was only too hard for a sore throat right then."
    )
    w.say(
        f"Then {cashier.id} set the {crystallite.label} aside in a safe little box and offered warm tea instead."
    )
    w.say(
        f"{child.id}'s ears perked up. {child.id} nodded, sipped the tea, and smiled when {cashier.id} promised the {crystallite.label} would wait for a better day."
    )
    w.say(
        f"By the end, {child.id} felt less worried, and the shiny {crystallite.label} stayed safe on the counter, waiting like a tiny star."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story in a gentle cautionary tone about a cashier and a child who wants a crystallite but has tonsilitis.',
        f"Tell a small story where {f['cashier'].id} warns {f['child'].id} about {f['illness'].label}, and a misunderstanding gets kindly fixed.",
        f"Write a story for young children about a shiny crystallite, a sore throat, and a patient cashier in {world.setting}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    cashier = f["cashier"]
    crystallite = f["crystallite"]
    illness = f["illness"]
    return [
        QAItem(
            question=f"What did {child.id} want from {cashier.id}?",
            answer=f"{child.id} wanted the {crystallite.label}, which looked tiny and shiny on the counter.",
        ),
        QAItem(
            question=f"Why did {cashier.id} give a cautionary warning?",
            answer=f"{cashier.id} gave a warning because {child.id} had {illness.label}, and the sore throat could make hard or scratchy treats hurt.",
        ),
        QAItem(
            question=f"What misunderstanding happened at first?",
            answer=f"{child.id} thought {cashier.id} was saying the {crystallite.label} was forbidden forever, instead of just unsafe for a sore throat right then.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{cashier.id} explained the reason kindly, the {crystallite.label} was put safely aside, and {child.id} drank warm tea and felt better.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "cashier": [
        QAItem(
            question="What does a cashier do?",
            answer="A cashier takes care of buying and paying at a shop, and often helps customers with what they are choosing.",
        )
    ],
    "tonsilitis": [
        QAItem(
            question="What is tonsilitis?",
            answer="Tonsilitis is when the throat gets sore and swollen, so swallowing can hurt.",
        )
    ],
    "crystallite": [
        QAItem(
            question="What is a crystallite?",
            answer="A crystallite is a very small crystal-like piece that can look shiny or sparkly.",
        )
    ],
    "cautionary": [
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means careful and warning about possible trouble before it happens.",
        )
    ],
    "misunderstanding": [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea and needs a clearer explanation.",
        )
    ],
    "animal": [
        QAItem(
            question="Why do animal stories feel friendly to children?",
            answer="Animal stories often feel friendly because animals can act like people in simple, warm, easy-to-follow ways.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [qa for key in ["cashier", "tonsilitis", "crystallite", "cautionary", "misunderstanding", "animal"] for qa in WORLD_KNOWLEDGE[key]]


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
# Trace and verification helpers
# ---------------------------------------------------------------------------

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
        lines.append(f"  {e.id:12} ({e.type:11}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A child wants the crystallite if it is shiny and the child has hope.
wants(C, crystallite) :- child(C), shine(crystallite), hope(C).

% A cashier gives a cautionary warning when tonsilitis is present.
warns(Cashier, Child) :- cashier(Cashier), child(Child), tonsilitis(Child).

% A misunderstanding happens if the child is worried after the warning.
misunderstanding(Child) :- warns(_, Child), worry(Child).

% The gentle resolution is valid if warning, misunderstanding, and explanation all occur.
resolved(Child) :- misunderstanding(Child), explained(Child), comforted(Child).

#show wants/2.
#show warns/2.
#show misunderstanding/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t in CASHIER_TYPES:
        lines.append(asp.fact("cashier_type", t))
    for t in CHILD_TYPES:
        lines.append(asp.fact("child_type", t))
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for item in ITEMS:
        lines.append(asp.fact("shine", item))
    lines.append(asp.fact("crystallite", "crystallite"))
    lines.append(asp.fact("tonsilitis", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show wants/2.\n#show warns/2.\n#show misunderstanding/1.\n#show resolved/1."))
    atoms = set()
    for sym in model:
        atoms.add((sym.name, tuple(a.name if a.type != a.type.String and a.type != a.type.Number else (a.string if a.type == a.type.String else a.number) for a in sym.arguments)))
    expected = {
        ("wants", ("child", "crystallite")),
        ("warns", ("cashier", "child")),
        ("misunderstanding", ("child",)),
    }
    if atoms == expected:
        print("OK: ASP twin matches the simple reasonableness gate.")
        return 0
    print("MISMATCH between ASP and expectation:")
    print("  got:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Sampling / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: cashier, tonsilitis, and a crystallite.")
    ap.add_argument("--cashier-type", choices=sorted(CASHIER_TYPES))
    ap.add_argument("--child-type", choices=sorted(CHILD_TYPES))
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--cashier-name")
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
    cashier_type = args.cashier_type or rng.choice(sorted(CASHIER_TYPES))
    child_type = args.child_type or rng.choice(sorted(CHILD_TYPES))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    child_name = args.name or rng.choice(NAMES[child_type])
    cashier_name = args.cashier_name or rng.choice(CASHIER_NAMES)
    return StoryParams(
        cashier_type=cashier_type,
        child_type=child_type,
        child_name=child_name,
        cashier_name=cashier_name,
        setting=setting,
    )


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


CURATED = [
    StoryParams(cashier_type="cat", child_type="bunny", child_name="Mina", cashier_name="Mara", setting="market"),
    StoryParams(cashier_type="dog", child_type="fox", child_name="Finn", cashier_name="Pip", setting="corner_shop"),
    StoryParams(cashier_type="rabbit", child_type="mouse", child_name="Tia", cashier_name="Nell", setting="station_kiosk"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show wants/2.\n#show warns/2.\n#show misunderstanding/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world's ASP twin is intentionally tiny; use --show-asp to inspect it.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.child_name}: {p.child_type} with {p.cashier_type} cashier at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
