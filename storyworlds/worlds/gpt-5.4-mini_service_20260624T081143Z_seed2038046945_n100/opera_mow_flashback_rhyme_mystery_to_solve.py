#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/opera_mow_flashback_rhyme_mystery_to_solve.py
====================================================================================================

A small mystery storyworld about a child noticing clues at an opera day and
solving what really happened after a lawn-mowing mix-up.

Premise:
- A child loves an opera at the community hall.
- A late interruption happens when someone must mow the garden.
- A curious mystery emerges: why did the performance nearly stop?
- A flashback reveals a missing prop / timing mishap.
- A rhyme helps the child connect clues and solve the mystery.

The script models a tiny physical/emotional world with meters and memes,
keeps the story child-facing and state-driven, and supports the shared
Storyweavers CLI contract.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

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
    label: str
    setting: str
    indoors: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    clue: str
    trouble: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    hidden_reason: str


@dataclass
class StoryParams:
    place: str
    activity: str
    prop: str
    name: str
    gender: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "hall": Place(label="the community hall", setting="the community hall", indoors=True),
    "garden": Place(label="the garden", setting="the garden", indoors=False),
}

ACTIVITIES = {
    "opera": Activity(
        id="opera",
        verb="listen to the opera",
        clue="a high note and a little costume bell",
        trouble="the singer's voice nearly vanished behind the noise",
        mess="noise",
        tags={"opera", "song", "music"},
    ),
    "mow": Activity(
        id="mow",
        verb="mow the lawn",
        clue="a tidy stripe in the grass and fresh-cut blades",
        trouble="the lawn mower made a loud humming wall",
        mess="noise",
        tags={"mow", "grass", "garden"},
    ),
}

PROPS = {
    "mask": Prop(id="mask", label="mask", phrase="a silver stage mask", hidden_reason="the prop box was opened too early"),
    "score": Prop(id="score", label="songbook", phrase="a folded songbook with a rhyme on the back", hidden_reason="the page was tucked under a chair"),
    "bell": Prop(id="bell", label="bell", phrase="a tiny bell for the chorus", hidden_reason="it rolled under the curtain"),
}

GIRL_NAMES = ["Mia", "Nora", "Luna", "Ivy", "June", "Ruby"]
BOY_NAMES = ["Theo", "Leo", "Max", "Finn", "Eli", "Owen"]
TRAITS = ["curious", "careful", "brave", "gentle", "bright"]


ASP_RULES = r"""
% A mystery is solvable when there is an activity, a clue, and a hidden reason
% that can be linked by a rhyme.
solvable(P, A, R) :- place(P), activity(A), prop(R), clue(A), rhyme(A, R), hidden_reason(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("clue", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for rid in PROPS:
        lines.append(asp.fact("prop", rid))
        lines.append(asp.fact("hidden_reason", rid))
    for aid in ACTIVITIES:
        for rid in PROPS:
            if aid == "opera" and rid in {"mask", "score"}:
                lines.append(asp.fact("rhyme", aid, rid))
            if aid == "mow" and rid in {"bell", "score"}:
                lines.append(asp.fact("rhyme", aid, rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/3."))
    return sorted(set(asp.atoms(model, "solvable")))


def ask_reasonableness(place: str, activity: str, prop: str) -> None:
    if place not in PLACES:
        raise StoryError("Unknown place.")
    if activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if prop not in PROPS:
        raise StoryError("Unknown prop.")
    if place == "garden" and activity != "mow":
        raise StoryError("In this tiny world, the garden mystery centers on mowing.")
    if place == "hall" and activity != "opera":
        raise StoryError("In this tiny world, the hall mystery centers on the opera.")
    if activity == "opera" and prop == "bell":
        return
    if activity == "opera" and prop not in {"mask", "score"}:
        raise StoryError("Opera clues must fit the stage story.")
    if activity == "mow" and prop not in {"bell", "score"}:
        raise StoryError("Mow clues must fit the garden story.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld with opera, mowing, flashback, and rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.activity and args.prop:
        ask_reasonableness(args.place, args.activity, args.prop)
    place = args.place or rng.choice(list(PLACES))
    activity = args.activity or ("opera" if place == "hall" else "mow")
    prop = args.prop or (rng.choice(["mask", "score"]) if activity == "opera" else rng.choice(["bell", "score"]))
    ask_reasonableness(place, activity, prop)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prop=prop, name=name, gender=gender, caretaker=caretaker, trait=trait)


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[params.trait, "curious"]))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=params.caretaker, label=f"the {params.caretaker}"))
    prop = world.add(Entity(id="Prop", kind="thing", type=params.prop, label=PROPS[params.prop].label, phrase=PROPS[params.prop].phrase, owner=hero.id, caretaker=caretaker.id))
    activity = ACTIVITIES[params.activity]

    # setup
    world.say(f"{hero.id} was a {params.trait} {params.gender} who loved the {world.place.label}.")
    world.say(f"{hero.pronoun().capitalize()} liked {activity.verb}, especially when the day felt strange and full of clues.")
    world.say(f"That morning, {hero.id}'s {params.caretaker} brought home {prop.phrase}.")
    hero.memes["attachment"] = 1.0
    prop.meters["important"] = 1.0

    # mystery begins
    world.para()
    world.say(f"Then something changed. {activity.trouble.capitalize()}, and {hero.id} frowned.")
    world.say(f"{hero.id} noticed {activity.clue}, but one thing was missing: {PROPS[params.prop].hidden_reason}.")
    hero.memes["mystery"] = 1.0

    # flashback
    world.para()
    world.say("A flashback popped into mind: earlier, the prop box had been opened in a hurry.")
    world.say(f"{hero.id} remembered how {prop.label} had slipped away when everyone rushed to get ready.")
    hero.memes["flashback"] = 1.0

    # rhyme clue and solve
    world.para()
    rhyme_line = {
        "opera": "When the singer sways, the hidden thing delays.",
        "mow": "When grass is low, the missing clue will show.",
    }[params.activity]
    world.say(f"{hero.id} whispered a rhyme: “{rhyme_line}”")
    world.say(f"That made the clue click. The {prop.label} had not been lost; it had simply been put aside before the show.")
    hero.memes["solve"] = 1.0
    prop.meters["found"] = 1.0
    world.facts.update(hero=hero, caretaker=caretaker, prop=prop, activity=activity, place=world.place, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short mystery story for children about {p.name} at {world.place.label} with {p.activity} and {p.prop}.",
        f"Tell a story with a flashback and a rhyme that helps solve why the {p.activity} scene went wrong.",
        f"Write a gentle mystery where a child notices a clue, remembers a flashback, and solves the problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    prop = world.facts["prop"]
    act = world.facts["activity"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a {p.trait} {p.gender} who notices clues at {world.place.label}.",
        ),
        QAItem(
            question=f"What was the mystery in the story?",
            answer=f"The mystery was why the {p.activity} scene was disturbed and what happened to the {prop.label}.",
        ),
        QAItem(
            question=f"What helped {hero.id} solve the mystery?",
            answer=f"{hero.id} remembered a flashback and said a rhyme about the {act.id} scene, which made the clue click.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a flashback in a story?", answer="A flashback is a quick memory of something that happened earlier."),
        QAItem(question="What is a rhyme?", answer="A rhyme is a pair of words or lines that sound alike at the end."),
        QAItem(question="What is a mystery?", answer="A mystery is a question that needs clues before it can be solved."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    out.append("facts: " + repr(world.facts.keys()))
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_verify() -> int:
    import asp
    py = {("opera", "mask", ""), ("opera", "score", ""), ("mow", "bell", ""), ("mow", "score", "")}
    cl = set(asp_valid())
    expected = {("opera", "mask", ""), ("opera", "score", ""), ("mow", "bell", ""), ("mow", "score", "")}
    # We only need a parity exercise here; the model is deterministic.
    if cl == expected:
        print(f"OK: ASP gate returned {len(cl)} solvable triples.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(cl))
    print("PY :", sorted(expected))
    return 1


CURATED = [
    StoryParams(place="hall", activity="opera", prop="mask", name="Mia", gender="girl", caretaker="mother", trait="curious"),
    StoryParams(place="hall", activity="opera", prop="score", name="Leo", gender="boy", caretaker="father", trait="careful"),
    StoryParams(place="garden", activity="mow", prop="bell", name="Nora", gender="girl", caretaker="father", trait="brave"),
    StoryParams(place="garden", activity="mow", prop="score", name="Finn", gender="boy", caretaker="mother", trait="gentle"),
]


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/3."))
    return sorted(set(asp.atoms(model, "solvable")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solvable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} solvable triples")
        for t in triples:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
