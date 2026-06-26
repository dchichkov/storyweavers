#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/armadillo_transformation_bad_ending_suspense_animal_story.py
===============================================================================================

A small animal story world about an armadillo, a strange transformation, and a
suspenseful bad ending.

Premise:
- A small animal protagonist wants to explore.
- A transformation changes its body in a way that seems useful at first.
- Suspense rises because the change helps in one moment but creates danger in the next.
- The ending is bad in a child-safe way: the animal cannot undo the change in time
  and ends the story stuck, lonely, or unable to reach home.

This script models the story as a tiny simulation with physical meters and
emotional memes, then renders a complete, state-driven story and QA sets.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    transformed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"size": 0.0, "safety": 0.0, "distance": 0.0, "stuck": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "fear": 0.0, "hope": 0.0, "sadness": 0.0, "panic": 0.0}


@dataclass
class Place:
    id: str
    label: str
    dangers: set[str] = field(default_factory=set)
    paths_home: bool = True
    dim: bool = False


@dataclass
class Form:
    id: str
    label: str
    body_change: str
    help_text: str
    risk_text: str
    safe_against: set[str] = field(default_factory=set)
    blocks: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    form: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


PLACES = {
    "burrow": Place(id="burrow", label="the burrow", dangers={"darkness", "tight_tunnel"}, paths_home=True, dim=True),
    "canyon": Place(id="canyon", label="the canyon path", dangers={"wind", "falling_rocks"}, paths_home=False, dim=False),
    "grass": Place(id="grass", label="the tall grass", dangers={"quiet", "getting_lost"}, paths_home=True, dim=False),
    "pond": Place(id="pond", label="the muddy pond", dangers={"water", "mud"}, paths_home=True, dim=False),
}

FORMS = {
    "shell": Form(
        id="shell",
        label="a hard shell",
        body_change="grew a hard shell over its back",
        help_text="the shell could bump through sharp grass and tiny rocks",
        risk_text="the shell made it hard to squeeze back through small spaces",
        safe_against={"falling_rocks", "sharp_grass"},
        blocks={"tight_tunnel"},
    ),
    "spikes": Form(
        id="spikes",
        label="pointy spikes",
        body_change="sprouted pointy spikes all along its sides",
        help_text="the spikes could scare away a hungry fox",
        risk_text="the spikes made it hard to hide under bushes or in narrow roots",
        safe_against={"fox", "predator"},
        blocks={"tight_tunnel"},
    ),
    "big": Form(
        id="big",
        label="a much bigger body",
        body_change="grew bigger and heavier all at once",
        help_text="the bigger body could push through wind on the open path",
        risk_text="the bigger body made quiet hiding places feel too small",
        safe_against={"wind"},
        blocks={"tight_tunnel", "bushes"},
    ),
    "slow": Form(
        id="slow",
        label="a slow, heavy shape",
        body_change="became slow and heavy like a stone",
        help_text="the heavy shape could not be blown over easily",
        risk_text="the slow shape could not hurry when danger came close",
        safe_against={"wind"},
        blocks={"running"},
    ),
}

NAMES = ["Pip", "Milo", "Nina", "Toby", "Luna", "Poppy", "Moss", "Bento"]
WORLD_ORDER = ["burrow", "canyon", "grass", "pond"]


def reasonableness_gate(place: Place, form: Form) -> bool:
    if place.id == "burrow" and "tight_tunnel" in form.blocks:
        return False
    if place.id == "canyon" and form.id == "slow":
        return False
    return True


def explain_rejection(place: Place, form: Form) -> str:
    return (
        f"(No story: the {form.label} change would not make sense in {place.label}. "
        f"The form helps with some dangers, but it also blocks the path the animal needs.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="An armadillo story world with transformation, suspense, and a bad ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--form", choices=FORMS)
    ap.add_argument("--name", choices=NAMES)
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
    combos = [
        (p, f)
        for p in PLACES
        for f in FORMS
        if (args.place is None or args.place == p)
        and (args.form is None or args.form == f)
        and reasonableness_gate(PLACES[p], FORMS[f])
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, form = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, form=form, name=name)


def transform(world: World, hero: Entity, form: Form) -> None:
    hero.transformed = True
    hero.meters["size"] += 1.0 if form.id in {"big", "slow"} else 0.3
    hero.meters["safety"] += 1.0 if form.id in {"shell", "spikes"} else 0.2
    hero.memes["fear"] += 0.2
    hero.memes["hope"] += 0.6
    world.say(f"Then something strange happened: {hero.id} {form.body_change}.")


def suspense_step(world: World, hero: Entity, place: Place, form: Form) -> None:
    world.para()
    world.say(
        f"The path ahead looked quiet, but {place.label} held its own danger."
    )
    if "getting_lost" in place.dangers:
        hero.memes["fear"] += 0.8
        world.say(
            f"{hero.id} kept walking and listening for a home sound, but the grass was so tall that every step felt unsure."
        )
    elif "wind" in place.dangers:
        hero.memes["fear"] += 0.8
        world.say(
            f"A sharp wind worried the little animal, and the new shape felt strange in the open air."
        )
    elif "water" in place.dangers:
        hero.memes["fear"] += 0.8
        world.say(
            f"The mud near the pond made each step slow, and the transformed body felt heavier than before."
        )
    else:
        hero.memes["fear"] += 0.5
        world.say(
            f"The shadows under the burrow walls seemed to grow longer, and the changed body made the tunnel feel tighter."
        )
    world.say(f"{form.risk_text.capitalize()}.")


def bad_ending(world: World, hero: Entity, place: Place, form: Form) -> None:
    world.para()
    hero.memes["panic"] += 1.0
    hero.memes["sadness"] += 1.0
    hero.meters["stuck"] = 1.0
    if not place.paths_home or form.id == "slow":
        world.say(
            f"{hero.id} tried to hurry home, but the new shape would not let {hero.id} do it in time."
        )
    else:
        world.say(
            f"{hero.id} tried to turn back, but the strange new body kept getting caught and the way home grew farther away."
        )
    world.say(
        f"In the end, {hero.id} stopped beside the dark path, alone and still wearing the changed body."
    )


def tell_story(place: Place, form: Form, name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type="armadillo", label="armadillo"))
    parent = world.add(Entity(id="Parent", kind="character", type="adult", label="the burrow parent"))

    hero.meters["distance"] = 0.0
    hero.memes["curiosity"] = 1.0
    world.say(f"{hero.id} was a little armadillo who loved to explore {place.label}.")
    world.say(f"{hero.id} had a quiet heart and a nose that wanted to sniff every leaf and stone.")
    world.say(
        f"One afternoon, {hero.id} saw a strange glow, and {hero.id} touched it before thinking twice."
    )
    transform(world, hero, form)
    world.para()
    world.say(
        f"At first, the change seemed useful, because {form.help_text}."
    )
    hero.meters["distance"] += 1.0
    suspense_step(world, hero, place, form)
    bad_ending(world, hero, place, form)

    world.facts.update(hero=hero, parent=parent, place=place, form=form)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    form = f["form"]
    return [
        f"Write a short animal story about an armadillo named {hero.id} who changes into {form.label} at {place.label}.",
        f"Tell a suspenseful children's story where {hero.id} becomes {form.label} and cannot get home in time.",
        f"Write a simple story with an armadillo, a transformation, and a bad ending set at {place.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    form = f["form"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little armadillo.",
        ),
        QAItem(
            question=f"What strange change happened to {hero.id}?",
            answer=f"{hero.id} {form.body_change}.",
        ),
        QAItem(
            question=f"Why was the middle of the story suspenseful?",
            answer=(
                f"It was suspenseful because {hero.id} had changed in a way that helped at first, "
                f"but also made the trip through {place.label} feel dangerous and uncertain."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended badly, with {hero.id} unable to get home in time and left alone beside the dark path."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an armadillo?",
            answer="An armadillo is a small mammal with a hard body covering that helps protect it.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another form.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling that something important might go wrong or be decided soon.",
        ),
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
        lines.append(
            f"  {e.id:8} ({e.type:10}) transformed={e.transformed} meters={e.meters} memes={e.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
form(F) :- transformation(F).
good_combo(P,F) :- place(P), form(F), not invalid(P,F).

invalid(burrow, F) :- blocks(F, tight_tunnel).
invalid(canyon, slow) :- form(slow).

#show good_combo/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if p.dim:
            lines.append(asp.fact("dim", pid))
        if p.paths_home:
            lines.append(asp.fact("paths_home", pid))
        for d in sorted(p.dangers):
            lines.append(asp.fact("danger", pid, d))
    for fid, f in FORMS.items():
        lines.append(asp.fact("transformation", fid))
        for b in sorted(f.blocks):
            lines.append(asp.fact("blocks", fid, b))
        for s in sorted(f.safe_against):
            lines.append(asp.fact("safe_against", fid, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_combo/2."))
    return sorted(set(asp.atoms(model, "good_combo")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((p, f) for p in PLACES for f in FORMS if reasonableness_gate(PLACES[p], FORMS[f]))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches reasonableness_gate() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def resolve_name(rng: random.Random) -> str:
    return rng.choice(NAMES)


CURATED = [
    StoryParams(place="grass", form="shell", name="Pip"),
    StoryParams(place="pond", form="slow", name="Milo"),
    StoryParams(place="canyon", form="spikes", name="Nina"),
    StoryParams(place="burrow", form="big", name="Toby"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell_story(PLACES[params.place], FORMS[params.form], params.name)
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
        print(asp_program("#show good_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} valid (place, form) combos:\n")
        for p, f in triples:
            print(f"  {p:8} {f}")
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
            header = f"### {p.name}: {p.form} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
