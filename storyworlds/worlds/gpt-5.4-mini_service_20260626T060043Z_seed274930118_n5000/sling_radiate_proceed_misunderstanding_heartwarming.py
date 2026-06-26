#!/usr/bin/env python3
"""
storyworlds/worlds/sling_radiate_proceed_misunderstanding_heartwarming.py
=========================================================================

A small heartwarming story world about a child in a sling, a misunderstanding,
and a gentle resolution. The seed words are folded into the domain as real
world-state causes: a bright message can radiate hope, a mistaken guess can
create misunderstanding, and the story can proceed toward kindness.

Premise:
- A child has an arm in a sling.
- A parent/friend plans a small outing or task.
- A misunderstanding makes the child think they will be left out.

Turn:
- The misunderstanding is revealed to be caused by concern, not rejection.

Resolution:
- The adults and child proceed together, with a small accommodation that keeps
  the child included and comforted.

The story is built from simulated meters (physical state) and memes (emotional
state), then rendered into prose and Q&A.
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

SETTING_NAME = "home-and-garden"


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    setting: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Content registry
# ---------------------------------------------------------------------------
CHILD_NAMES = ["Ava", "Milo", "Lina", "Noah", "June", "Theo", "Maya", "Eli"]
PARENT_TYPES = ["mother", "father"]
SETTINGS = {
    "garden": "the garden",
    "kitchen": "the kitchen",
    "porch": "the porch",
    "library": "the library",
    "clinic": "the clinic",
}

# Seed words integrated into realistic domain vocabulary.
STORY_VERBS = {
    "sling": "wear a sling",
    "radiate": "radiate warmth",
    "proceed": "proceed together",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world: sling, misunderstanding, and comfort.")
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--setting", choices=SETTINGS)
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


def _pronoun(gender: str, case: str = "subject") -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(CHILD_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(PARENT_TYPES)
    setting = args.setting or rng.choice(list(SETTINGS))
    return StoryParams(name=name, gender=gender, parent=parent, setting=setting)


def _setup_world(params: StoryParams) -> World:
    world = World(setting=SETTINGS[params.setting])
    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"arm_pain": 1.0, "energy": 0.8},
        memes={"worry": 0.2, "hope": 0.3, "belonging": 0.4},
        props={"sling": "true"},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={"care": 1.0},
        memes={"care": 1.0, "certainty": 0.5},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type="friend",
        label="a friend",
        meters={"energy": 1.0},
        memes={"kindness": 0.8, "patience": 0.7},
    ))
    lunch = world.add(Entity(
        id="lunch",
        type="thing",
        label="a small lunch basket",
        phrase="a small lunch basket with two cups",
    ))
    world.facts.update(child=child, parent=parent, friend=friend, lunch=lunch)
    return world


def _proceed_with_plan(world: World, child: Entity, parent: Entity, friend: Entity) -> None:
    child.memes["worry"] += 0.2
    world.say(
        f"{child.label} was in a sling and wanted to help at {world.setting}."
    )
    world.say(
        f"{child.pronoun().capitalize()} could still smile, but {child.pronoun('possessive')} arm hurt whenever {child.pronoun()} reached too far."
    )
    world.para()

    world.say(
        f"That morning, {parent.label} said they would {STORY_VERBS['proceed']} and take the little lunch basket outside."
    )
    world.say(
        f"{friend.label} was there too, and {friend.pronoun().capitalize()} seemed ready to help."
    )
    child.memes["hope"] += 0.1
    world.para()

    # Misunderstanding: the child thinks the parent means "stay back."
    child.memes["misunderstanding"] = 1.0
    child.memes["worry"] += 0.6
    parent.memes["care"] += 0.2
    world.say(
        f"When {parent.label} quietly moved the basket away from the busy path, {child.label} made the wrong guess."
    )
    world.say(
        f"{child.label} thought, 'Maybe I am not needed because of my sling.'"
    )
    world.say(
        f"The thought made the room feel small for a moment, even though nothing unkind had been said."
    )
    world.para()

    # Clarification / radiate warmth.
    parent.memes["clarity"] = 1.0
    child.memes["misunderstanding"] = 0.0
    child.memes["worry"] -= 0.2
    child.memes["hope"] += 0.5
    friend.memes["kindness"] += 0.2
    world.say(
        f"{parent.label} knelt down and explained that the basket had only been moved so no one would bump the sore arm."
    )
    world.say(
        f"'{child.label}, we want you with us,' {parent.label} said. 'Your kindness still {STORY_VERBS['radiate']}.'"
    )
    world.say(
        f"Then {friend.label} held up a strap on the basket and said they could carry the lunch together."
    )
    world.para()

    # Resolution.
    child.memes["belonging"] += 0.8
    child.memes["hope"] += 0.4
    child.meters["arm_pain"] = 0.7
    world.say(
        f"So they {STORY_VERBS['proceed']} slowly across {world.setting}, with {friend.label} carrying the basket and {child.label} pointing out the flowers."
    )
    world.say(
        f"{child.label} did not have to lift anything heavy, but {child.pronoun()} still helped by choosing the path and watching the door."
    )
    world.say(
        f"By the end, the sling was still there, yet the worry was gone, and the little group felt warm and close."
    )


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    child: Entity = world.get("child")
    parent: Entity = world.get("parent")
    friend: Entity = world.get("friend")

    intro = (
        f"{child.label} wore a sling after hurting {child.pronoun('possessive')} arm."
    )
    middle = (
        f"{parent.label} planned a gentle trip to {world.setting} with a small lunch basket."
    )
    ending = (
        f"By the end, {child.label} knew {parent.label} had only been careful, not distant."
    )
    world.say(intro)
    world.say(
        f"{child.label} liked being helpful, so the sling felt frustrating even when the day was bright."
    )
    world.para()
    world.say(middle)
    _proceed_with_plan(world, child, parent, friend)
    world.para()
    world.say(ending)

    prompts = [
        f"Write a heartwarming story about a child who has to wear a sling and thinks they are being left out.",
        f"Tell a gentle story where a misunderstanding is corrected and everyone proceeds together.",
        f"Write a child-friendly story that uses the words sling, radiate, and proceed.",
    ]

    story_qa = [
        QAItem(
            question=f"Why did {child.label} feel worried at first?",
            answer=(
                f"{child.label} felt worried because {child.pronoun()} thought the sling meant {parent.label} wanted {child.pronoun('object')} to stay out of the way. "
                f"It was a misunderstanding, not a real rejection."
            ),
        ),
        QAItem(
            question=f"What did {parent.label} do to fix the misunderstanding?",
            answer=(
                f"{parent.label} explained that the basket was moved only to protect the sore arm, then said they wanted {child.label} with them. "
                f"That clear explanation helped the worry fade."
            ),
        ),
        QAItem(
            question=f"How did the group proceed in the end?",
            answer=(
                f"They proceeded slowly together to {world.setting}, with {friend.label} carrying the basket and {child.label} helping in a lighter way. "
                f"The sling stayed on, but the child felt included and cared for."
            ),
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a sling?",
            answer="A sling is a soft support that holds an injured arm still so it can rest and heal.",
        ),
        QAItem(
            question="What does it mean to radiate warmth?",
            answer="To radiate warmth means to spread a feeling of kindness or comfort so other people can feel it too.",
        ),
        QAItem(
            question="What does it mean to proceed?",
            answer="To proceed means to move forward or continue with a plan.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.props:
            bits.append(f"props={e.props}")
        lines.append(f"  {e.id:6} ({e.kind:9}) {e.label:20} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child(C) :- child_name(C).
parent(P) :- parent_type(P).
setting(S) :- setting_name(S).

misunderstanding(C) :- confusion(C), not clarified(C).
heartwarming(C) :- comforted(C), understood(C).

proceed_together(C,P,F) :- child(C), parent(P), friend(F), comforted(C), helped(F), clarified(P).

#show valid_story/4.
valid_story(Name,Parent,Setting,Outcome) :- child_name(Name), parent_type(Parent), setting_name(Setting), outcome(Outcome).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for n in CHILD_NAMES:
        lines.append(asp.fact("child_name", n))
    for p in PARENT_TYPES:
        lines.append(asp.fact("parent_type", p))
    for s in SETTINGS:
        lines.append(asp.fact("setting_name", s))
    for o in ["misunderstanding", "heartwarming"]:
        lines.append(asp.fact("outcome", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {(n, p, s, o) for n in CHILD_NAMES for p in PARENT_TYPES for s in SETTINGS for o in ["misunderstanding", "heartwarming"]}
    if atoms == py:
        print(f"OK: clingo gate matches Python registry facts ({len(atoms)} combos).")
        return 0
    print("MISMATCH between clingo and Python facts.")
    return 1


def resolve_story_choices(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


CURATED = [
    StoryParams(name="Ava", gender="girl", parent="mother", setting="garden"),
    StoryParams(name="Milo", gender="boy", parent="father", setting="porch"),
    StoryParams(name="June", gender="girl", parent="mother", setting="kitchen"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        for atom in atoms:
            print(atom)
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
            params = resolve_story_choices(args, random.Random(seed))
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
