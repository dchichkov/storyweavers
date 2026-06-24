#!/usr/bin/env python3
"""
storyworlds/worlds/conference_transformation_bravery_heartwarming.py
====================================================================

A small heartwarming storyworld about a child at a conference who finds the
bravery to transform something shy into something shared.

Premise:
- A child comes to a conference with a small handmade display or invention.
- They feel nervous speaking in front of a crowd.
- A gentle helper encourages them to transform their fear into a brave action.
- The child changes the display, the talk, or the way they present it.
- The ending proves the transformation through a warm, concrete image.

The world is intentionally tiny and state-driven:
- physical meters track objects, stage setup, and wearables
- emotional memes track nerves, bravery, pride, and relief
- the prose is assembled from simulated state, not from a frozen template

This file is standalone and uses only stdlib plus the shared Storyweavers result
containers. ASP support is inline via ASP_RULES and imported lazily.
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

CONFERENCE_TOPICS = ["science", "art", "books", "music", "bugs", "gardening"]
TRANSFORMATIONS = ["decorate", "practice", "turn", "rearrange", "brighten"]
BRAVE_ACTIONS = ["speak to the crowd", "show the project", "answer a question", "walk to the stage"]

NAMES = ["Mina", "Noah", "Ava", "Leo", "Luna", "Maya", "Theo", "Ivy"]
HELPER_NAMES = ["Grandpa", "Aunt Rosa", "Ms. Kim", "Dad", "Mom", "Big Sister"]

TRAITS = ["quiet", "curious", "gentle", "careful", "shy", "thoughtful"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Venue:
    place: str = "the conference hall"
    crowd_size: str = "small"


@dataclass
class Display:
    topic: str
    label: str
    fragile: bool = True
    transformable: bool = True


@dataclass
class StoryParams:
    venue: str
    topic: str
    transformation: str
    brave_action: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


@dataclass
class World:
    venue: Venue
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
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

    def copy(self) -> "World":
        import copy
        return World(
            venue=copy.deepcopy(self.venue),
            entities=copy.deepcopy(self.entities),
            facts=copy.deepcopy(self.facts),
            paragraphs=[[]],
        )


def world_state(world: World, key: str, default=0.0):
    return world.facts.get(key, default)


def can_transform(topic: str, transformation: str) -> bool:
    return topic in CONFERENCE_TOPICS and transformation in TRANSFORMATIONS


def is_brave_action(brave_action: str) -> bool:
    return brave_action in BRAVE_ACTIONS


def assert_reasonable(params: StoryParams) -> None:
    if not can_transform(params.topic, params.transformation):
        raise StoryError("That transformation does not fit the conference project.")
    if not is_brave_action(params.brave_action):
        raise StoryError("That brave action is not part of this small conference world.")


def select_venue(name: str) -> Venue:
    if name == "conference":
        return Venue(place="the conference hall", crowd_size="small")
    raise StoryError("Unknown venue.")


def setting_line(venue: Venue) -> str:
    return f"{venue.place.capitalize()} was bright, with a small crowd waiting kindly."


def introduce(world: World, child: Entity, helper: Entity, display: Entity) -> None:
    world.say(
        f"{child.id} was a {child.label} child who came to the conference with {child.pronoun('possessive')} {display.label}."
    )
    world.say(
        f"{helper.id} stayed nearby and smiled whenever {child.id} looked nervous."
    )


def nervous_before_talk(world: World, child: Entity, display: Entity) -> None:
    child.memes["nervous"] = 1.0
    world.say(
        f"{child.id} felt a flutter in {child.pronoun('possessive')} stomach because the room was full of listening faces."
    )
    world.say(
        f"{child.id} looked at {display.label} and wished it felt easier to share."
    )


def transform_display(world: World, child: Entity, display: Entity, transformation: str) -> None:
    child.memes["bravery"] += 1.0
    display.meters["beauty"] = display.meters.get("beauty", 0.0) + 1.0
    display.meters["order"] = display.meters.get("order", 0.0) + 1.0
    world.facts["transformed"] = transformation
    world.say(
        f"{child.id} took a careful breath and chose to {transformation} {display.label} instead of hiding it."
    )


def helper_encourages(world: World, helper: Entity, child: Entity) -> None:
    child.memes["nervous"] = max(0.0, child.memes.get("nervous", 0.0) - 1.0)
    world.say(
        f"{helper.id} told {child.id}, \"You do not have to be loud to be brave. Just take one honest step.\""
    )


def brave_moment(world: World, child: Entity, brave_action: str, display: Entity) -> None:
    child.memes["bravery"] = child.memes.get("bravery", 0.0) + 1.0
    child.memes["pride"] = child.memes.get("pride", 0.0) + 1.0
    world.facts["brave_action"] = brave_action
    world.say(
        f"Then {child.id} did it: {child.pronoun()} went to the front and chose to {brave_action}."
    )
    world.say(
        f"The {display.label} looked brighter than before, as if it had learned how to smile back."
    )


def warm_resolution(world: World, child: Entity, helper: Entity, display: Entity) -> None:
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
    child.memes["nervous"] = 0.0
    world.say(
        f"When the applause came, {child.id} smiled so wide that even the {display.label} seemed to glow."
    )
    world.say(
        f"{helper.id} gave {child.id} a proud hug, and the two of them stood together beside the finished display."
    )


def tell(params: StoryParams) -> World:
    world = World(venue=select_venue(params.venue))
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.trait,
        phrase=f"a {params.trait} child",
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="helper",
        label="helper",
        phrase=f"a kind helper",
    ))
    display = world.add(Entity(
        id="display",
        type="project",
        label=f"{params.topic} project",
        phrase=f"a {params.topic} project",
    ))

    world.say(setting_line(world.venue))
    introduce(world, child, helper, display)
    world.para()
    nervous_before_talk(world, child, display)
    helper_encourages(world, helper, child)
    transform_display(world, child, display, params.transformation)
    world.para()
    brave_moment(world, child, params.brave_action, display)
    warm_resolution(world, child, helper, display)

    world.facts.update(
        child=child,
        helper=helper,
        display=display,
        venue=world.venue,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a heartwarming story about a child at a conference who learns bravery.",
        f"Tell a gentle story where {p.name} must {p.brave_action} while helping a {p.topic} project become more {p.transformation}.",
        f"Create a small conference tale with a shy child, a kind helper, and a warm transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    display: Entity = world.facts["display"]
    return [
        QAItem(
            question=f"Where did {child.id} go with the {display.label}?",
            answer=f"{child.id} went to {world.venue.place} with {child.pronoun('possessive')} {display.label}.",
        ),
        QAItem(
            question=f"Why did {child.id} feel nervous before speaking?",
            answer=f"{child.id} felt nervous because the conference room was full of listening faces.",
        ),
        QAItem(
            question=f"What did {helper.id} help {child.id} do?",
            answer=f"{helper.id} helped {child.id} breathe, be brave, and show the {display.label}.",
        ),
        QAItem(
            question=f"How did the {display.label} change?",
            answer=f"The {display.label} became more {p.transformation} and looked brighter when {child.id} shared it.",
        ),
        QAItem(
            question=f"What brave thing did {child.id} do at the end?",
            answer=f"{child.id} chose to {p.brave_action} in front of the crowd.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a conference?",
            answer="A conference is a meeting where people gather to share ideas, listen, and learn from one another.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary or hard while still moving forward with a steady heart.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state to another, like a plain idea becoming a shining project.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    venue = args.venue or "conference"
    topic = args.topic or rng.choice(CONFERENCE_TOPICS)
    transformation = args.transformation or rng.choice(TRANSFORMATIONS)
    brave_action = args.brave_action or rng.choice(BRAVE_ACTIONS)
    if not can_transform(topic, transformation):
        raise StoryError("The requested topic and transformation do not fit together.")
    if not is_brave_action(brave_action):
        raise StoryError("The requested brave action is not supported.")
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        venue=venue,
        topic=topic,
        transformation=transformation,
        brave_action=brave_action,
        name=name,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    assert_reasonable(params)
    world = tell(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming conference storyworld.")
    ap.add_argument("--venue", choices=["conference"])
    ap.add_argument("--topic", choices=CONFERENCE_TOPICS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--brave-action", choices=BRAVE_ACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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


ASP_RULES = r"""
% A story is valid when the conference has a topic, a transformation, and a brave action.
valid_story(V,T,Tr,B) :- venue(V), topic(T), transformation(Tr), brave_action(B),
                         can_transform(T,Tr), is_brave_action(B).

% The child's inner state should move from nervousness to bravery.
transformed(T) :- topic(T), can_transform(T,_).
brave(V) :- venue(V), brave_action(_).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("venue", "conference")]
    for t in CONFERENCE_TOPICS:
        lines.append(asp.fact("topic", t))
        for tr in TRANSFORMATIONS:
            if can_transform(t, tr):
                lines.append(asp.fact("can_transform", t, tr))
    for tr in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tr))
    for b in BRAVE_ACTIONS:
        lines.append(asp.fact("brave_action", b))
        lines.append(asp.fact("is_brave_action", b))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {
        ("conference", t, tr, b)
        for t in CONFERENCE_TOPICS
        for tr in TRANSFORMATIONS
        for b in BRAVE_ACTIONS
        if can_transform(t, tr) and is_brave_action(b)
    }
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams("conference", "science", "decorate", "show the project", "Mina", "Grandpa", "shy"),
    StoryParams("conference", "art", "brighten", "speak to the crowd", "Ava", "Aunt Rosa", "gentle"),
    StoryParams("conference", "books", "rearrange", "answer a question", "Theo", "Ms. Kim", "careful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        for item in vals:
            print(item)
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
            header = f"### {p.name}: {p.topic} / {p.transformation} / {p.brave_action}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
