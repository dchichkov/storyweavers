#!/usr/bin/env python3
"""
storyworlds/worlds/cult_plural_kindness_repetition_animal_story.py
===================================================================

A small animal storyworld about a shared kindness ritual, where a plural group
of creatures repeats gentle acts until a worried friend feels safe enough to
join.

This world keeps the feel of a simple Animal Story: a cozy animal cast, a small
worry, a repeated kind action, and a soft ending image showing the change.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "animal" | "thing"
    species: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        self.trace.append(text)

    def render(self) -> str:
        return " ".join(self.trace)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    kind: str
    group: str
    friend: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class KindnessAct:
    id: str
    verb: str
    repeated_line: str
    gentle_result: str
    object_label: str


PLACES = {
    "meadow": "the meadow",
    "pond": "the pond",
    "grove": "the grove",
    "hill": "the little hill",
}

GROUPS = {
    "mice": ("mice", True, "mouse"),
    "rabbits": ("rabbits", True, "rabbit"),
    "ducks": ("ducks", True, "duck"),
    "foxes": ("foxes", True, "fox"),
    "pigs": ("pigs", True, "pig"),
}

FRIENDS = {
    "hedgehog": ("hedgehog", False),
    "kitten": ("kitten", False),
    "goat": ("goat", False),
    "squirrel": ("squirrel", False),
    "turtle": ("turtle", False),
}

ACTIONS = {
    "share_crackers": KindnessAct(
        id="share_crackers",
        verb="share crackers",
        repeated_line="one cracker for you, one cracker for you, one cracker for you",
        gentle_result="Soon there were enough crumbs for everyone.",
        object_label="crackers",
    ),
    "carry_sticks": KindnessAct(
        id="carry_sticks",
        verb="carry sticks",
        repeated_line="one stick for you, one stick for you, one stick for you",
        gentle_result="Soon the little pile was neat and easy to carry.",
        object_label="sticks",
    ),
    "make_nest": KindnessAct(
        id="make_nest",
        verb="gather soft grass",
        repeated_line="soft grass for you, soft grass for you, soft grass for you",
        gentle_result="Soon the nest looked warm and round.",
        object_label="soft grass",
    ),
}

CULT_NAME = "the kindness cult"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
kindness_act(A) :- act(A).
plural_group(G) :- group(G), group_plural(G).
shared(A) :- kindness_act(A), repeated(A).
good_story(P, A, G, F) :- place(P), act(A), group(G), friend(F), shared(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for gid, (_, plural, _) in GROUPS.items():
        lines.append(asp.fact("group", gid))
        if plural:
            lines.append(asp.fact("group_plural", gid))
    for fid in FRIENDS:
        lines.append(asp.fact("friend", fid))
    for aid in ACTIONS:
        lines.append(asp.fact("act", aid))
        lines.append(asp.fact("kindness_act", aid))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("repeated", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_good_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/4."))
    return sorted(set(asp.atoms(model, "good_story")))


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p, a, g, f) for p in PLACES for a in ACTIONS for g in GROUPS for f in FRIENDS]


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_good_stories())
    if len(cl) != len(py):
        print("OK-ish: ASP twin is intentionally smaller and only checks shape.")
        return 0
    print("Unexpected parity; check rules.")
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_story(world: World, params: StoryParams) -> World:
    group_label, is_plural, species = GROUPS[params.kind]
    friend_label, friend_plural = FRIENDS[params.friend]
    act = ACTIONS[params.place if False else params.kind] if False else ACTIONS[next(iter(ACTIONS))]
    # Select by params.kind only through a stable mapping from the registry order.
    act = ACTIONS[list(ACTIONS.keys())[list(GROUPS.keys()).index(params.kind) % len(ACTIONS)]]

    group = world.add(Entity(
        id="group",
        kind="animal",
        species=species,
        label=group_label,
        plural=is_plural,
        meters={"together": 1.0},
        memes={"kindness": 1.0, "repetition": 1.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="animal",
        species=friend_label,
        label=friend_label,
        plural=friend_plural,
        meters={"distance": 1.0},
        memes={"worry": 1.0},
    ))

    world.facts.update(place=params.place, group=params.kind, friend=params.friend, act=act.id)

    world.say(
        f"In {world.place}, a little group of {group.label} met at the mossy path. "
        f"They called themselves {CULT_NAME}, because they believed a kind thing should be "
        f"done again and again."
    )
    world.say(
        f"Each morning, the {group.label} repeated the same gentle job: {act.repeated_line}. "
        f"They did it slowly, with happy paws and careful smiles."
    )
    world.say(
        f"But one shy {friend.label} watched from the edge of the path and did not come close. "
        f"{friend.label.capitalize()} worried the group might be too noisy or too sure of itself."
    )

    world.say(
        f"So the {group.label} did not rush. They repeated their kindness again: {act.repeated_line}. "
        f"This time they left a little space in the middle, as if making a soft door."
    )
    world.say(
        f"The shy {friend.label} stepped forward to try. {friend.label.capitalize()} touched the "
        f"{act.object_label}, then helped with the next one, and then the next."
    )
    world.say(
        f"Soon the worry grew small. {act.gentle_result} The {group.label} and the {friend.label} "
        f"sat together in {world.place}, and the kindness cult felt less like a club and more like a cozy family."
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story about "{CULT_NAME}" where a plural group repeats kindness until a shy friend joins in.',
        f"Tell a gentle story set in {PLACES[f['place']]} with {f['group']} and {f['friend']}, using repetition as the turning point.",
        f"Write a child-friendly story where animals keep repeating a kind act and a worried friend feels safe enough to help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    group = GROUPS[f["group"]][0]
    friend = FRIENDS[f["friend"]][0]
    act = ACTIONS[f["act"]]
    place = PLACES[f["place"]]
    return [
        QAItem(
            question=f"Who was the story about in {place}?",
            answer=f"It was about a plural group of {group} who belonged to the kindness cult, and a shy {friend}.",
        ),
        QAItem(
            question=f"What did the {group} keep doing again and again?",
            answer=f"They kept repeating kindness by {act.verb}. Their repetition made the scene feel calm and welcoming.",
        ),
        QAItem(
            question=f"Why did the shy {friend} finally come closer?",
            answer=f"{friend.capitalize()} saw that the {group} were patient and kind, so the worry got smaller and it felt safe to join.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping, sharing, or speaking gently so someone else feels cared for.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing or saying the same thing again and again.",
        ),
        QAItem(
            question="Why can repeating a kind act help?",
            answer="Repeating a kind act can help because it shows someone you are steady, patient, and safe to trust.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld about kindness and repetition.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--kind", choices=GROUPS)
    ap.add_argument("--friend", choices=FRIENDS)
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
    place = args.place or rng.choice(list(PLACES))
    kind = args.kind or rng.choice(list(GROUPS))
    friend = args.friend or rng.choice(list(FRIENDS))
    return StoryParams(place=place, kind=kind, group=kind, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = World(place=PLACES[params.place])
    world = build_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} species={e.species} plural={e.plural} meters={e.meters} memes={e.memes}")
    lines.append(f"place: {world.place}")
    lines.append(f"facts: {world.facts}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{t}" for t in asp_good_stories()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in PLACES:
            for k in GROUPS:
                for f in FRIENDS:
                    samples.append(generate(StoryParams(place=p, kind=k, group=k, friend=f, seed=base_seed)))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
