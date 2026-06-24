#!/usr/bin/env python3
"""
storyworlds/worlds/van_frantic_soften_suspense_moral_value_transformation.py
============================================================================

A standalone story world in a small fable style: a van gets frantic, tension
softens, and a clear moral transformation ends the story.

Premise:
- A small group rides in a van on a needed errand.
- A sudden problem makes everyone frantic.
- A gentle method softens the panic.
- A moral choice changes the ending image.

The world models both physical meters and emotional memes:
- meters track fuel, heat, load, distance, and a few other concrete states
- memes track fear, kindness, trust, patience, and calm

The story stays child-facing, concrete, and state-driven.
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

ASP_RULES = r"""
% A van trip becomes stressful when the van is low on fuel and the path is long.
needs_help(V) :- van(V), meters(V,fuel,F), F < 2.
frantic(A) :- actor(A), memes(A,fear,N), N >= 2.
softened(A) :- actor(A), memes(A,calm,C), C >= 2.

% Moral transformation happens when the frantic choice is replaced by a kinder one.
transformed(A) :- actor(A), memes(A,kindness,K), K >= 2, memes(A,trust,T), T >= 2.
resolved_trip(V) :- van(V), not needs_help(V).
"""

@dataclass
class StoryParams:
    place: str
    problem: str
    helper: str
    traveler: str
    seed: Optional[int] = None

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id

@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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

def valid_combos() -> list[tuple[str, str, str]]:
    return [("river_road", "flat_tire", "peddler"), ("hill_road", "storm", "peddler"), ("forest_road", "lost_path", "healer")]

CURATED = [
    StoryParams(place="river_road", problem="flat_tire", helper="peddler", traveler="Mina"),
    StoryParams(place="hill_road", problem="storm", helper="peddler", traveler="Joss"),
    StoryParams(place="forest_road", problem="lost_path", helper="healer", traveler="Lena"),
]

PLACES = {
    "river_road": "a road beside the river",
    "hill_road": "a windy hill road",
    "forest_road": "a narrow road by the trees",
}
PROBLEMS = {
    "flat_tire": "a tire went flat",
    "storm": "a storm blew in",
    "lost_path": "the van took the wrong bend",
}
HELPERS = {
    "peddler": "a kind peddler with a repair kit",
    "healer": "a calm healer with warm tea",
}
TRAVELERS = {
    "Mina": ("girl", "Mina"),
    "Joss": ("boy", "Joss"),
    "Lena": ("girl", "Lena"),
}

ASP_BASE = r"""
van(van1).
actor(traveler).
actor(helper).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [ASP_BASE]
    lines.append(asp.fact("van", "van1"))
    lines.append(asp.fact("actor", "traveler"))
    lines.append(asp.fact("actor", "helper"))
    return "\n".join(lines)

def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"

def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("", "#show needs_help/1.\n#show transformed/1.\n")
    model = asp.one_model(program)
    seen = set(asp.atoms(model, "needs_help")) | set(asp.atoms(model, "transformed"))
    ok = True
    if not seen:
        ok = False
        print("ASP returned no useful atoms.")
    if ok:
        print("OK: ASP twin loaded and produced atoms.")
    return 0 if ok else 1

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like van storyworld with suspense, moral value, and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--traveler", choices=TRAVELERS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, problem, helper = rng.choice(sorted(combos))
    traveler = args.traveler or rng.choice(sorted(TRAVELERS))
    return StoryParams(place=place, problem=problem, helper=helper, traveler=traveler)

def tell(params: StoryParams) -> World:
    w = World(place=PLACES[params.place])
    traveler_type, traveler_name = TRAVELERS[params.traveler]
    traveler = w.add(Entity(id="traveler", kind="character", type=traveler_type, label=traveler_name,
                            meters={"distance": 0.0, "load": 1.0, "fuel": 1.0}, memes={"fear": 0.0, "calm": 0.0, "kindness": 0.0, "trust": 0.0, "patience": 1.0}))
    helper_kind = "character"
    helper = w.add(Entity(id="helper", kind=helper_kind, type="adult", label=HELPERS[params.helper], memes={"calm": 1.0, "kindness": 1.0, "trust": 1.0}))
    van = w.add(Entity(id="van", kind="thing", type="van", label="the little van", meters={"fuel": 1.0, "distance": 0.0, "load": 2.0, "heat": 0.0}, memes={"frantic": 0.0}))
    w.facts.update(traveler=traveler, helper=helper, van=van, params=params)

    w.say(f"{traveler.label} climbed into the little van for a trip along {w.place}.")
    w.say(f"They were carrying a small task, and the van hummed softly as the road began.")
    w.para()
    w.say(f"Then {PROBLEMS[params.problem]}; the van slowed, and worry rose fast.")
    traveler.memes["fear"] += 2.0
    van.memes["frantic"] += 2.0
    traveler.meters["distance"] += 1.0
    w.say(f"{traveler.label} went frantic, looking out at the road, while the helper stayed calm.")
    w.para()
    helper.memes["kindness"] += 1.0
    helper.memes["trust"] += 1.0
    traveler.memes["calm"] += 2.0
    traveler.memes["fear"] = 0.0
    traveler.memes["kindness"] += 2.0
    van.memes["frantic"] = 0.0
    w.say(f"The helper softened the moment with a steady voice and a careful hand.")
    if params.problem == "flat_tire":
        van.meters["load"] -= 1.0
        van.meters["fuel"] += 1.0
        w.say("A repair was made, and the van stood straight again on its wheel.")
    elif params.problem == "storm":
        van.meters["heat"] = 0.0
        w.say("They waited under a safe awning until the storm passed and the road shone clear.")
    else:
        van.meters["distance"] += 2.0
        w.say("They found the right bend, and the van rolled on without fear.")
    w.para()
    traveler.memes["trust"] += 2.0
    traveler.memes["patience"] += 1.0
    w.say(f"In the end, {traveler.label} learned that a frantic heart can soften when kindness leads.")
    w.say(f"The van moved on quietly, and the road felt new.")
    return w

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a fable about a van on {PLACES[p.place]} where {p.traveler} faces {PROBLEMS[p.problem]} and a helper softens the panic.",
        f"Tell a child-friendly story with suspense, moral value, and transformation, using the words van, frantic, and soften.",
        f"Create a short fable in which a troubled van journey ends with a moral change and a calm ending.",
    ]

def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    t = world.facts["traveler"]
    return [
        QAItem(question=f"What made {t.label} frantic?", answer=f"{PROBLEMS[p.problem]}. That sudden trouble made the trip feel uncertain and scary."),
        QAItem(question="How did the helper soften the suspense?", answer="The helper spoke gently and handled the problem with care. That made the worry ease and gave everyone a calmer way forward."),
        QAItem(question="What changed by the end of the story?", answer=f"{t.label} changed from frantic to trusting and patient. The trip ended quietly, and the van rolled on with a calmer heart."),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a van?", answer="A van is a road vehicle with room to carry people or things."),
        QAItem(question="What does frantic mean?", answer="Frantic means very worried, rushed, or hard to calm down."),
        QAItem(question="What does soften mean?", answer="Soften means to become less hard, less sharp, or less upset."),
    ]

def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} label={e.label}")
    return "\n".join(lines)

def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("", "#show needs_help/1.\n#show transformed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world uses an inline ASP twin for verification only.")
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(rng.randrange(2**31)))
            samples.append(generate(p))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
