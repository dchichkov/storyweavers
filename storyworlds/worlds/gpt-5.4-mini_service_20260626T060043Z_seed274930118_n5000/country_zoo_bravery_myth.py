#!/usr/bin/env python3
"""
storyworlds/worlds/country_zoo_bravery_myth.py
==============================================

A standalone story world for a small zoo myth about country folk, a brave child,
and a gentle turn from fear into courage.

Initial seed tale:
---
A child from the country visits the zoo with a guardian. The child loves old
myths about brave travelers and wants to do one brave thing in the zoo. A small
problem appears near a lion gate or tall animal house, where something precious
is in danger. The guardian warns the child, then offers a safer way forward.
The child finds bravery, helps the creature, and leaves with a bright, mythic
ending.

World model:
---
This world tracks a few concrete meters:
    - physical state of the brave token or helper item
    - emotional state: fear, bravery, relief, pride, care

The story is driven by state transitions, not by swapping nouns in a frozen
paragraph. The child changes from hesitant to brave, and the ending image proves
that change.

Narrative instrument:
---
Myth: the prose leans ceremonial and simple, with a feeling of old stories told
softly for children.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Core knobs
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "zoo"
    child_name: str = "Mina"
    child_role: str = "child"
    guardian_role: str = "grandmother"
    origin: str = "the country"
    creature: str = "lion"
    brave_task: str = "walk past the lion gate to return the keeper's brass key"
    token: str = "brass key"
    token_article: str = "the brass key"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

CHILDREN = ["Mina", "Nori", "Suri", "Ivo", "Lela", "Ari"]
GUARDIANS = ["mother", "father", "grandmother", "grandfather", "aunt", "uncle"]
CREATURES = {
    "lion": {
        "label": "lion gate",
        "danger": "roaring",
        "place": "the lion house",
        "myth": "a lion with a golden mane",
    },
    "elephant": {
        "label": "elephant yard",
        "danger": "trumpeting",
        "place": "the elephant yard",
        "myth": "an elephant as old as hills",
    },
    "giraffe": {
        "label": "giraffe walk",
        "danger": "tall and watchful",
        "place": "the giraffe walk",
        "myth": "a giraffe that seemed to touch the sky",
    },
    "peacock": {
        "label": "peacock court",
        "danger": "sudden and bright",
        "place": "the peacock court",
        "myth": "a peacock with a thousand blue eyes",
    },
}

VALID_CREATURES = set(CREATURES)

# The brave task is kept small and concrete.
TASKS = {
    "lion": "walk past the lion gate to return the keeper's brass key",
    "elephant": "cross the elephant yard to bring back a dropped ribbon",
    "giraffe": "climb the little hill beside the giraffe walk to fetch a fallen kite",
    "peacock": "step into the peacock court to gather a lost silver bell",
}

TOKENS = {
    "brass key": ("the brass key", "key"),
    "ribbon": ("the red ribbon", "ribbon"),
    "kite": ("the small kite", "kite"),
    "silver bell": ("the silver bell", "bell"),
}

# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World()

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        label=params.child_name,
        type="child",
        location=params.place,
        meters={"fear": 1.0, "bravery": 0.0, "relief": 0.0, "pride": 0.0},
        memes={"yearning": 1.0},
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        label=params.guardian_role,
        type=params.guardian_role,
        location=params.place,
        meters={"care": 1.0},
        memes={"worry": 1.0},
    ))
    token = world.add(Entity(
        id="token",
        kind="thing",
        label=TOKENS[params.token][0],
        type=TOKENS[params.token][1],
        owner=params.child_name,
        caretaker="guardian",
        location=params.creature,
        meters={"shine": 1.0, "safe": 0.0},
    ))
    creature = world.add(Entity(
        id="creature",
        kind="thing",
        label=CREATURES[params.creature]["myth"],
        type=params.creature,
        location=CREATURES[params.creature]["place"],
        meters={"restlessness": 1.0, "calm": 0.0},
    ))
    world.facts.update(params=params, child=child, guardian=guardian, token=token, creature=creature)
    return world


def tell_story(world: World) -> None:
    p: StoryParams = world.facts["params"]
    child: Entity = world.facts["child"]
    guardian: Entity = world.facts["guardian"]
    token: Entity = world.facts["token"]
    creature: Entity = world.facts["creature"]

    world.say(
        f"{child.label} came from {p.origin} with {guardian.label}, "
        f"and the zoo seemed like a place from an old story."
    )
    world.say(
        f"{child.label} loved the old myths of brave wanderers, so {child.pronoun('subject')} "
        f"kept looking at the bright {p.place} paths as if they were a road to a kingdom."
    )
    world.say(
        f"At the {CREATURES[p.creature]['label']}, the keeper had lost {token.label}, "
        f"and the little treasure lay where the brave path began."
    )

    world.para()
    child.meters["fear"] += 1.0
    world.say(
        f"{child.label} wanted to {p.brave_task}, but the {p.creature} was near, "
        f"and its {CREATURES[p.creature]['danger']} ways made the path feel huge."
    )
    world.say(
        f'"It is a hard errand," said {guardian.label}, "and a child should not hurry into '
        f"wonder without a plan.""
    )
    world.say(
        f"{creature.label.capitalize()} watched from the tall bars, while the missing {token.label} "
        f"glimmered like a tiny star in the dust."
    )

    world.para()
    child.meters["bravery"] += 1.0
    child.meters["fear"] -= 0.5
    world.say(
        f"{child.label} took one slow breath, remembered the myths, and held {token.pronoun('possessive')} "
        f"shoulders straight."
    )
    world.say(
        f"Then {child.pronoun('subject')} walked with {guardian.label} beside {child.pronoun('object')}, "
        f"not racing, not shouting, but moving like a lantern in the dusk."
    )

    # Causal turn: bravery plus the guardian's help makes the task safe.
    if child.meters["bravery"] >= 1.0:
        token.meters["safe"] = 1.0
        creature.meters["calm"] = 1.0
        creature.meters["restlessness"] = 0.0
        child.meters["relief"] += 1.0
        child.meters["pride"] += 1.0
        guardian.meters["worry"] = 0.0
        world.say(
            f"{child.label} found the {token.label} and gave it back with both hands."
        )
        world.say(
            f"The keeper smiled, the {p.creature} settled, and the whole zoo felt quieter, "
            f"as if a storm had chosen to sleep."
        )

    world.para()
    world.say(
        f"By sunset, {child.label} was no longer only a child from {p.origin}; "
        f"{child.pronoun('subject').capitalize()} was the one who had made the little rescue."
    )
    world.say(
        f"And so the story at the {p.place} ended with a brave heart, a returned {TOKENS[p.token][1]}, "
        f"and a bright animal yard breathing peace."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f'Write a short myth-like story for a child from {p.origin} who visits a {p.place} and learns bravery.',
        f"Tell a gentle zoo myth where {p.child_name} must {p.brave_task}, but a guardian helps keep the danger small.",
        f'Write a child-friendly story set in a {p.place} with the word "{p.origin.split()[-1]}" and a brave ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    child: Entity = world.facts["child"]
    guardian: Entity = world.facts["guardian"]
    token: Entity = world.facts["token"]

    return [
        QAItem(
            question=f"Where did {child.label} go to learn bravery?",
            answer=f"{child.label} went to the {p.place} with {guardian.label}."
        ),
        QAItem(
            question=f"What did {child.label} want to do near the {p.creature}?",
            answer=f"{child.label} wanted to {p.brave_task}."
        ),
        QAItem(
            question=f"What treasure had to be returned in the story?",
            answer=f"The treasure was {token.label}."
        ),
        QAItem(
            question=f"How did the story end for {child.label}?",
            answer=f"{child.label} ended the day proud and relieved after helping return {token.label}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or scary while staying careful and trying to do the right thing."
        ),
        QAItem(
            question="What is a zoo?",
            answer="A zoo is a place where people can visit and learn about animals that live there with keepers."
        ),
        QAItem(
            question="Why can a guardian help a child do a brave thing?",
            answer="A guardian can help by staying close, making a plan, and keeping the child safe while they try."
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(zoo).
origin(country).

creature(lion).
creature(elephant).
creature(giraffe).
creature(peacock).

brave_task(lion, key).
brave_task(elephant, ribbon).
brave_task(giraffe, kite).
brave_task(peacock, bell).

valid(Creature, Token) :- brave_task(Creature, Token).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    lines: list[str] = []
    lines.append(asp.fact("place", "zoo"))
    lines.append(asp.fact("origin", "country"))
    for c in CREATURES:
        lines.append(asp.fact("creature", c))
    for creature, task in TASKS.items():
        token = task.split()[-1].strip("'s").strip(".")
        # normalize by explicit registry instead of parsing prose-like text
        if creature == "lion":
            tok = "key"
        elif creature == "elephant":
            tok = "ribbon"
        elif creature == "giraffe":
            tok = "kite"
        else:
            tok = "bell"
        lines.append(asp.fact("brave_task", creature, tok))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    return sorted((c, "key" if c == "lion" else "ribbon" if c == "elephant" else "kite" if c == "giraffe" else "bell")
                  for c in VALID_CREATURES)


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(python_valid())
    if a == b:
        print(f"OK: clingo gate matches python gate ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic zoo storyworld about bravery and a country child.")
    ap.add_argument("--place", choices=["zoo"], default="zoo")
    ap.add_argument("--child-name", choices=CHILDREN)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--origin", default="the country")
    ap.add_argument("--creature", choices=sorted(CREATURES))
    ap.add_argument("--token", choices=sorted(TOKENS))
    ap.add_argument("--name", dest="child_name_alias")
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
    child_name = args.child_name_alias or args.child_name or rng.choice(CHILDREN)
    guardian = args.guardian or rng.choice(GUARDIANS)
    creature = args.creature or rng.choice(sorted(CREATURES))
    token = args.token or (
        "brass key" if creature == "lion" else
        "ribbon" if creature == "elephant" else
        "kite" if creature == "giraffe" else
        "silver bell"
    )
    if creature == "lion":
        task = TASKS["lion"]
    elif creature == "elephant":
        task = TASKS["elephant"]
    elif creature == "giraffe":
        task = TASKS["giraffe"]
    else:
        task = TASKS["peacock"]
    return StoryParams(
        place="zoo",
        child_name=child_name,
        child_role="child",
        guardian_role=guardian,
        origin=args.origin or "the country",
        creature=creature,
        brave_task=task,
        token=token,
        token_article=TOKENS[token][0],
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
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
    StoryParams(child_name="Mina", guardian_role="grandmother", origin="the country", creature="lion",
                brave_task=TASKS["lion"], token="brass key", token_article=TOKENS["brass key"][0]),
    StoryParams(child_name="Nori", guardian_role="father", origin="the country", creature="elephant",
                brave_task=TASKS["elephant"], token="ribbon", token_article=TOKENS["ribbon"][0]),
    StoryParams(child_name="Suri", guardian_role="aunt", origin="the country", creature="giraffe",
                brave_task=TASKS["giraffe"], token="kite", token_article=TOKENS["kite"][0]),
    StoryParams(child_name="Ivo", guardian_role="uncle", origin="the country", creature="peacock",
                brave_task=TASKS["peacock"], token="silver bell", token_article=TOKENS["silver bell"][0]),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid bravery tasks:")
        for creature, token in vals:
            print(f"  {creature:8} -> {token}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.child_name} at the zoo with {p.guardian_role} and the {p.creature}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
