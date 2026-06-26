#!/usr/bin/env python3
"""
A small Storyweavers world: an animal learns why insurance matters after a
geology mistake breaks something valuable.

Seed words: geology-ist, insurance
Style: Animal Story
Feature: Lesson Learned

Premise:
A young animal wants to explore a rocky place and handle a shiny stone.
A careful geology-ist warns that the stone can crack, and the family has an
insurance plan for exactly this kind of accident. The animal ignores the
warning, a small accident happens, and then learns why rules and insurance
exist.
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
# Basic model
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "kitten", "lion", "tiger", "fox"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"mother", "father", "parent"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    animal: str
    parent: str
    geologyist: str
    place: str
    valuable: str
    seed: Optional[int] = None


@dataclass
class World:
    animal: Entity
    parent: Entity
    geologyist: Entity
    valuable: Entity
    insurance_card: Entity
    place: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
ANIMALS = {
    "rabbit": ("rabbit", "little rabbit"),
    "fox": ("fox", "curious fox"),
    "bear": ("bear", "small bear"),
    "otter": ("otter", "playful otter"),
    "mouse": ("mouse", "tiny mouse"),
}

PARENTS = {
    "mother": "mother",
    "father": "father",
    "parent": "parent",
}

GEOLOGISTS = {
    "badger": ("badger", "careful geology-ist badger"),
    "owl": ("owl", "wise geology-ist owl"),
    "turtle": ("turtle", "patient geology-ist turtle"),
    "beaver": ("beaver", "practical geology-ist beaver"),
}

PLACES = {
    "cave": "the cave",
    "cliff": "the cliff path",
    "riverbank": "the riverbank",
    "hill": "the old hill",
    "quarry": "the little quarry",
}

VALUABLES = {
    "geode": ("geode", "sparkly geode"),
    "crystal": ("crystal", "glass crystal"),
    "fossil": ("fossil", "fossil in a rock"),
    "stone": ("stone", "smooth river stone"),
}

NAMES = {
    "rabbit": ["Bun", "Pip", "Milo", "Nia"],
    "fox": ["Fenn", "Ruby", "Tavi", "Mira"],
    "bear": ["Bruno", "Moss", "Otis", "Nori"],
    "otter": ["Luna", "Toby", "Suri", "Juno"],
    "mouse": ["Dot", "Peep", "Wren", "Tilly"],
}

# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    animal_kind, animal_label = ANIMALS[params.animal]
    geology_kind, geology_label = GEOLOGISTS[params.geologyist]
    valuable_kind, valuable_phrase = VALUABLES[params.valuable]

    animal = Entity(id="animal", kind="character", type=animal_kind, label=animal_label)
    parent = Entity(id="parent", kind="character", type=params.parent, label=params.parent)
    geologyist = Entity(id="geologyist", kind="character", type=geology_kind, label=geology_label)
    valuable = Entity(
        id="valuable",
        kind="thing",
        type=valuable_kind,
        label=valuable_kind,
        phrase=valuable_phrase,
        caretaker="parent",
        meters={"fragile": 1.0},
    )
    insurance_card = Entity(
        id="insurance_card",
        kind="thing",
        type="card",
        label="insurance card",
        phrase="an insurance card",
        owner="parent",
        protective=True,
    )
    return World(
        animal=animal,
        parent=parent,
        geologyist=geologyist,
        valuable=valuable,
        insurance_card=insurance_card,
        place=PLACES[params.place],
    )


def tell(world: World) -> None:
    a = world.animal
    p = world.parent
    g = world.geologyist
    v = world.valuable

    world.say(
        f"{a.label.capitalize()} lived near {world.place} and loved shiny rocks."
    )
    world.say(
        f"One day, {g.label} visited and explained that a {v.phrase} could crack "
        f"if someone tapped it too hard."
    )
    world.say(
        f"{a.label.capitalize()} wanted to look brave, but {p.label} kept "
        f"{world.insurance_card.label if hasattr(world, 'insurance_card') else 'an insurance card'} "
        f"in the bag for safe days."
    )

    world.para()
    world.say(
        f"At {world.place}, {a.label} reached for the {v.label} before anyone could stop {a.pronoun('object')}."
    )
    world.say(
        f"{a.label.capitalize()} bumped the rock shelf, and the {v.label} made a sharp little crack."
    )
    v.meters["cracked"] = 1.0
    a.memes["shame"] = 1.0
    p.memes["worry"] = 1.0

    world.para()
    world.say(
        f"{g.label} did not scold {a.label}; instead, {g.pronoun().capitalize()} helped "
        f"show the broken piece and said, '{world.insurance_card.label} is for moments like this.'"
    )
    world.say(
        f"{p.label.capitalize()} used the insurance card, and the family got help to fix the damage."
    )
    a.memes["relief"] = 1.0
    a.memes["lesson_learned"] = 1.0
    p.memes["worry"] = 0.0
    v.meters["repaired"] = 1.0

    world.para()
    world.say(
        f"{a.label.capitalize()} sat very still and listened."
    )
    world.say(
        f"After that, {a.label} asked before touching any rock, and {g.label} said that was a very smart habit."
    )
    world.say(
        f"By sunset, the family walked home with the insurance card back in the bag, and {a.label} remembered the lesson."
    )

    world.facts.update(
        animal=a,
        parent=p,
        geologyist=g,
        valuable=v,
        place=world.place,
        insurance_card=world.insurance_card,
        cracked=True,
        repaired=True,
        lesson_learned=True,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short animal story about {f['animal'].label} learning why insurance matters after a rock breaks.",
        f"Tell a gentle story where {f['geologyist'].label} warns about a valuable rock and the family uses insurance.",
        f"Write a child-friendly lesson learned story at {f['place']} with a curious animal and a cracked stone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["animal"]
    p = world.facts["parent"]
    g = world.facts["geologyist"]
    v = world.facts["valuable"]
    return [
        QAItem(
            question=f"Who wanted to touch the {v.label} first?",
            answer=f"{a.label.capitalize()} wanted to touch the {v.label} first."
        ),
        QAItem(
            question=f"Who explained why the rock could crack?",
            answer=f"{g.label.capitalize()} explained why the {v.label} could crack."
        ),
        QAItem(
            question="What did the family use after the accident?",
            answer="The family used the insurance card to get help fixing the damage."
        ),
        QAItem(
            question="What lesson did the animal learn?",
            answer=f"{a.label.capitalize()} learned to ask first and be careful with valuable rocks."
        ),
        QAItem(
            question=f"Did {p.label} stay worried at the end?",
            answer=f"No. {p.label.capitalize()} was relieved after the insurance helped."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is insurance?",
            answer="Insurance is a plan that helps pay for damage or loss when something goes wrong."
        ),
        QAItem(
            question="What does a geology-ist study?",
            answer="A geology-ist studies rocks, stones, and the ground."
        ),
        QAItem(
            question="Why should you ask before touching something fragile?",
            answer="You should ask first because fragile things can break if they are handled carelessly."
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
    for e in [world.animal, world.parent, world.geologyist, world.valuable, world.insurance_card]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:13} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------
@dataclass
class StorySeed:
    animal: str
    parent: str
    geologyist: str
    place: str
    valuable: str


CURATED = [
    StoryParams(animal="rabbit", parent="mother", geologyist="owl", place="cave", valuable="geode"),
    StoryParams(animal="otter", parent="father", geologyist="beaver", place="riverbank", valuable="stone"),
    StoryParams(animal="mouse", parent="parent", geologyist="turtle", place="quarry", valuable="fossil"),
]

ASP_RULES = r"""
animal(A) :- animal_fact(A).
geologyist(G) :- geologyist_fact(G).
place(P) :- place_fact(P).
valuable(V) :- valuable_fact(V).

fragile(V) :- valuable_fact(V).
at_risk(P, V) :- place_fact(P), valuable_fact(V), fragile(V).
lesson_story(A, G, P, V) :- animal_fact(A), geologyist_fact(G), place_fact(P), valuable_fact(V), at_risk(P, V).
#show lesson_story/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for a in ANIMALS:
        lines.append(asp.fact("animal_fact", a))
    for g in GEOLOGISTS:
        lines.append(asp.fact("geologyist_fact", g))
    for p in PLACES:
        lines.append(asp.fact("place_fact", p))
    for v in VALUABLES:
        lines.append(asp.fact("valuable_fact", v))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show lesson_story/4."))
    asp_set = set(asp.atoms(model, "lesson_story"))
    py_set = {(p.animal, p.geologyist, p.place, p.valuable) for p in CURATED}
    if asp_set == py_set:
        print(f"OK: ASP matches curated lesson-story set ({len(py_set)} stories).")
        return 0
    print("MISMATCH between ASP and curated set:")
    print("  only in ASP:", sorted(asp_set - py_set))
    print("  only in Python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about geology and insurance.")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--geologyist", choices=GEOLOGISTS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--valuable", choices=VALUABLES)
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
    animal = args.animal or rng.choice(list(ANIMALS))
    parent = args.parent or rng.choice(list(PARENTS))
    geologyist = args.geologyist or rng.choice(list(GEOLOGISTS))
    place = args.place or rng.choice(list(PLACES))
    valuable = args.valuable or rng.choice(list(VALUABLES))
    return StoryParams(animal=animal, parent=parent, geologyist=geologyist, place=place, valuable=valuable)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print(asp_program("#show lesson_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show lesson_story/4."))
        combos = sorted(set(asp.atoms(model, "lesson_story")))
        print(f"{len(combos)} lesson-story combinations:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
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
