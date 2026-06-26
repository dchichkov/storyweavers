#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/clover_moral_value_bad_ending_transformation_slice.py
==============================================================================================================

A small slice-of-life story world about a child, a clover patch, a simple
moral choice, and a transformation that can end badly.

The seed image:
- A child finds a clover in an ordinary place.
- Someone wants to keep it private, pick it, trade it, or show kindness.
- The choice changes the clover patch and the child's feelings.
- Some stories end with a missed chance or a ruined clover.

This world is intentionally compact: fewer variants, stronger causal shape.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    caretakers: list[str] = field(default_factory=list)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    mood: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    desire: str
    touch: str
    turn: str
    consequence: str
    moral: str
    transform: str
    bad: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class CloverPatch:
    id: str
    label: str
    phrase: str
    intact: bool = True
    picked: bool = False
    watered: bool = False
    trampled: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.patch: Optional[CloverPatch] = None
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
    "yard": Place("yard", "the yard", "quiet", {"look", "pick", "water", "share"}),
    "sidewalk": Place("sidewalk", "the sidewalk", "ordinary", {"look", "share"}),
    "garden": Place("garden", "the garden", "soft", {"look", "pick", "water", "share"}),
}

ACTIONS = {
    "share": Action(
        id="share",
        verb="share",
        desire="wanted to share the clover",
        touch="gently held out the clover for a friend",
        turn="chose kindness instead of keeping the surprise",
        consequence="the clover stayed in the patch",
        moral="sharing can make a small thing feel bigger",
        transform="the patch grew a little brighter",
        bad=False,
        tags={"clover", "kindness", "share"},
    ),
    "pick": Action(
        id="pick",
        verb="pick",
        desire="wanted to pick the clover",
        touch="pulled the clover from the stem",
        turn="chose a quick prize instead of patience",
        consequence="the clover bent and wilted",
        moral="wanting something now can break it later",
        transform="the patch looked sparse afterward",
        bad=True,
        tags={"clover", "taking", "pick"},
    ),
    "hide": Action(
        id="hide",
        verb="hide",
        desire="wanted to hide the clover",
        touch="covered the clover with a shoe",
        turn="kept the clover secret from everyone",
        consequence="the clover lost its sunlight",
        moral="keeping a nice thing hidden can make it suffer",
        transform="the clover drooped under the shoe",
        bad=True,
        tags={"clover", "secret", "hide"},
    ),
    "water": Action(
        id="water",
        verb="water",
        desire="wanted to water the clover",
        touch="poured a little water near the roots",
        turn="helped the clover instead of plucking it",
        consequence="the clover stood up straighter",
        moral="gentle care can change something small for the better",
        transform="the clover patch looked fresh and alive",
        bad=False,
        tags={"clover", "care", "water"},
    ),
}

NAMES = ["Maya", "Nora", "Eli", "Luca", "Mina", "Theo", "Rose", "Sam"]
GENDERS = ["girl", "boy"]
PARENTS = ["mother", "father"]
TRAITS = ["quiet", "curious", "careful", "stubborn", "gentle", "cheerful"]


@dataclass
class StoryParams:
    place: str
    action: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life clover story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, p in SETTINGS.items():
        for action, a in ACTIONS.items():
            if "clover" in a.tags and action in p.affordances:
                combos.append((place, action))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.action:
        combos = [c for c in combos if c[1] == args.action]
    if not combos:
        raise StoryError("(No valid clover story matches the given options.)")
    place, action = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, action=action, name=name, gender=gender, parent=parent, trait=trait)


def _make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    clover = CloverPatch(id="clover", label="clover", phrase="a tiny green clover patch")
    world.patch = clover
    world.facts.update(hero=hero, parent=parent, clover=clover, action=ACTIONS[params.action], place=world.place, params=params)
    return world


def _intro(world: World, params: StoryParams) -> None:
    hero = world.facts["hero"]
    world.say(f"{hero.id} was a {params.trait} {params.gender} who liked ordinary days at {world.place.label}.")
    world.say(f"Near a path in {world.place.label}, {hero.id} noticed {world.patch.phrase}.")


def _setup(world: World, params: StoryParams) -> None:
    hero = world.facts["hero"]
    action = world.facts["action"]
    world.say(f"{hero.id} {action.desire}, because {hero.pronoun('possessive')} eyes kept returning to the little green clover.")
    world.say(f"It felt like one of those small moments that could become a memory all by itself.")


def _conflict(world: World, params: StoryParams) -> None:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    action = world.facts["action"]
    world.para()
    world.say(f"Then {hero.id} reached toward it and {action.touch}.")
    if action.bad:
        world.say(f"{parent.label.capitalize()} frowned, because {action.moral}.")
        world.say(f"{parent.label.capitalize()} warned {hero.id} to be careful, but the wish to act fast was already tugging hard.")
    else:
        world.say(f"{parent.label.capitalize()} nodded, because {action.moral}.")
        world.say(f"It was a small, gentle choice that fit the quiet afternoon.")


def _transform(world: World, params: StoryParams) -> None:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    action = world.facts["action"]
    patch = world.facts["clover"]
    world.para()
    if action.bad:
        patch.intact = False
        patch.picked = action.id == "pick"
        patch.trampled = action.id == "hide"
        hero.memes["guilt"] = hero.memes.get("guilt", 0.0) + 1.0
        world.say(f"By the time {hero.id} looked down again, {action.consequence}.")
        world.say(f"The little patch had changed: {action.transform}.")
        world.say(f"{hero.id} felt the mistake in a quiet way, and {parent.label} stayed close without making it bigger.")
        world.say(f"That was the bad ending: the moment could not be put back the way it was.")
    else:
        patch.watered = action.id == "water"
        patch.meters["health"] = patch.meters.get("health", 0.0) + 1.0
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
        world.say(f"Then {action.consequence}.")
        world.say(f"{action.transform}, and {hero.id} smiled at how such a small kindness could change the whole patch.")
        world.say(f"At the end, the clover was still there, only brighter than before.")


def tell(params: StoryParams) -> World:
    world = _make_world(params)
    _intro(world, params)
    _setup(world, params)
    _conflict(world, params)
    _transform(world, params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    a = world.facts["action"]
    return [
        f'Write a slice-of-life story about a child named {p.name} and a clover in {world.place.label}.',
        f"Tell a gentle story where {p.name} {a.desire} and something small changes by the end.",
        "Write a simple story with a clover, an everyday choice, and a clear ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    a = world.facts["action"]
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    patch = world.facts["clover"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a {p.trait} {p.gender} who notices a clover in {world.place.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the clover?",
            answer=f"{hero.id} wanted to {a.verb} it.",
        ),
        QAItem(
            question=f"Why did {parent.label} react the way they did?",
            answer=f"{parent.label.capitalize()} reacted that way because {a.moral}.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"The clover patch changed from a small ordinary patch into one that was {'hurt' if a.bad else 'healthier and brighter'}.",
        ),
    ]
    if a.bad:
        qa.append(QAItem(
            question=f"Why is this a bad ending?",
            answer="It is a bad ending because the clover was damaged, and the nice moment could not be undone.",
        ))
    else:
        qa.append(QAItem(
            question=f"How did the choice transform the clover patch?",
            answer="The choice helped the clover patch become healthier and brighter.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clover?",
            answer="A clover is a small plant with round leaves, often found in grass.",
        ),
        QAItem(
            question="Why should some small plants be handled gently?",
            answer="Some small plants can be easily broken or crushed, so gentle hands help them stay healthy.",
        ),
        QAItem(
            question="What does a choice change in a story?",
            answer="A choice can change what happens next, including how characters feel and what the ending looks like.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    if world.patch:
        lines.append(f"clover_patch: intact={world.patch.intact} picked={world.patch.picked} watered={world.patch.watered} trampled={world.patch.trampled}")
    return "\n".join(lines)


ASP_RULES = r"""
place_affords(Place, Action) :- affords(Place, Action).
valid(Place, Action) :- place_affords(Place, Action).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affordances):
            lines.append(asp.fact("affords", pid, a))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("bad", aid)) if action.bad else None
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


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


CURATED = [
    StoryParams(place="yard", action="share", name="Maya", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="garden", action="water", name="Eli", gender="boy", parent="father", trait="curious"),
    StoryParams(place="yard", action="pick", name="Nora", gender="girl", parent="mother", trait="stubborn"),
    StoryParams(place="garden", action="hide", name="Theo", gender="boy", parent="father", trait="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.asp:
        print(asp_program("#show valid/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
