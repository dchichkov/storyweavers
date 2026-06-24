#!/usr/bin/env python3
"""
storyworlds/worlds/avatar_romantic_bias_misunderstanding_lesson_learned_rhyming.py
===================================================================================

A tiny rhyme-first story world about an avatar, a romantic misunderstanding,
and a lesson learned about bias.

The seed tale idea:
---
A child made an avatar for a little game and loved to show it off.
When a friendly note with a heart appeared, the child guessed it meant something
romantic. Then the child worried that the game judge had a bias toward shiny,
sweet avatars. After a gentle talk, the child learned the note was only praise,
not romance, and that the judge had simply scored the pictures by clear shapes,
not favorites.
---

This script turns that premise into a small state-driven simulation:
- the avatar gets attention, confidence, and confusion
- the child misreads a heart note
- a worried bias belief rises
- a helper explains the ordinary reason
- the child learns not to assume romance or bias from one small sign

The prose is intentionally rhyming and child-facing, but the story facts are
driven by the world state rather than by a frozen template.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    light: str
    mood: str


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    sparkle: str
    owner: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    avatar_style: str
    note: str
    judge_style: str
    helper: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


PLACES = {
    "game_room": Place("the game room", "bright", "cheery"),
    "library_corner": Place("the library corner", "soft", "quiet"),
    "sunroom": Place("the sunroom", "golden", "gentle"),
}

AVATAR_STYLES = {
    "sparkly": Item("sparkly", "sparkly avatar", "a sparkly avatar with bright eyes", "glimmer"),
    "sporty": Item("sporty", "sporty avatar", "a sporty avatar with fast shoes", "zoom"),
    "cozy": Item("cozy", "cozy avatar", "a cozy avatar with a warm scarf", "snug"),
}

NOTES = {
    "heart_note": "a little note with a heart",
    "star_note": "a little note with a star",
    "smile_note": "a little note with a smile",
}

JUDGE_STYLES = {
    "clear": "clear lines and easy-to-see shapes",
    "kind": "kind smiles and neat colors",
    "bright": "bright colors and tidy details",
}

HELPERS = {
    "friend": "friend",
    "parent": "parent",
    "teacher": "teacher",
}


def rhyme(a: str, b: str) -> str:
    return f"{a} {b}"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world about avatar, romantic bias, and misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--avatar-style", choices=AVATAR_STYLES)
    ap.add_argument("--note", choices=NOTES)
    ap.add_argument("--judge-style", choices=JUDGE_STYLES)
    ap.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(list(PLACES))
    avatar_style = args.avatar_style or rng.choice(list(AVATAR_STYLES))
    note = args.note or rng.choice(list(NOTES))
    judge_style = args.judge_style or rng.choice(list(JUDGE_STYLES))
    helper = args.helper or rng.choice(list(HELPERS))
    name = args.name or rng.choice(["Mira", "Noah", "Lena", "Owen", "Zia", "Theo"])
    return StoryParams(place=place, avatar_style=avatar_style, note=note, judge_style=judge_style, helper=helper, name=name)


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    child = world.add(Entity(id="child", kind="character", type="child", label=params.name, traits=["curious", "sweet"]))
    avatar = world.add(Entity(id="avatar", kind="thing", type="avatar", label="avatar", phrase=AVATAR_STYLES[params.avatar_style].phrase, owner=child.id))
    note = world.add(Entity(id="note", kind="thing", type="note", label=NOTES[params.note], phrase=NOTES[params.note], owner=None))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))
    judge = world.add(Entity(id="judge", kind="character", type="judge", label="judge"))

    child.meters["hope"] = 1.0
    child.memes["joy"] = 1.0
    avatar.meters["shine"] = 1.0 if params.avatar_style == "sparkly" else 0.5
    avatar.memes["pride"] = 1.0
    helper.memes["kindness"] = 1.0
    judge.memes["fairness"] = 1.0
    world.facts.update(params=params, child=child, avatar=avatar, note=note, helper=helper, judge=judge)

    # Scene 1: setup
    world.say(
        f"In {world.place.name}, {params.name} made an {avatar.phrase}, neat as could be, "
        f"with a smile that shone in a rhyme and a ring."
    )
    world.say(
        f"{params.name} showed that avatar off with a hop and a cheer, "
        f"for the little bright picture felt clever and dear."
    )

    # Scene 2: misunderstanding and bias fear
    world.para()
    child.memes["confusion"] = 1.0
    child.memes["romantic_thought"] = 1.0
    child.memes["bias_worry"] = 1.0
    world.say(
        f"Then came {note.phrase}, with a heart that could glow, "
        f"and {params.name} thought, “Oh dear, is this romantic show?”"
    )
    world.say(
        f"The child also worried, “Does the judge have a bias, a tilt in the game, "
        f"for shiny sweet avatars that look just the same?”"
    )

    # Scene 3: helper explains, lesson learned
    world.para()
    helper.memes["helpfulness"] = 1.0
    child.memes["confusion"] = 0.0
    child.memes["bias_worry"] = 0.0
    child.memes["lesson_learned"] = 1.0
    world.say(
        f"{params.helper.capitalize()} came close with a soft, simple grin, "
        f"and said, “That heart means praise, not romance within.”"
    )
    world.say(
        f"“And the judge looks at shapes, not favorites, see? "
        f"No bias is needed; the score keeps things free.”"
    )

    # Resolution image
    child.memes["relief"] = 1.0
    child.memes["trust"] = 1.0
    world.say(
        f"So {params.name} took a deep breath, felt lighter than foam, "
        f"and learned not to guess too fast from one tiny home."
    )
    world.say(
        f"{params.name} kept the avatar smiling, both tidy and bright, "
        f"with a lesson learned true: ask first, then see right."
    )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    return [
        f'Write a rhyming story for a young child about an avatar and a misunderstanding with the word "{params.avatar_style}".',
        f"Tell a gentle rhyme where {params.name} thinks a heart note is romantic, then learns what it really means.",
        f"Write a simple story about bias, a helper, and a lesson learned, ending with a happy avatar image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    qa = [
        QAItem(
            question=f"What did {params.name} make in {world.place.name}?",
            answer=f"{params.name} made an avatar, and it was {AVATAR_STYLES[params.avatar_style].phrase}.",
        ),
        QAItem(
            question=f"What did {params.name} first think the heart note meant?",
            answer=f"{params.name} first thought it meant something romantic, but that was a misunderstanding.",
        ),
        QAItem(
            question=f"What worried {params.name} about the judge?",
            answer=f"{params.name} worried that the judge might have a bias toward shiny, sweet avatars.",
        ),
        QAItem(
            question=f"Who helped {params.name} understand the truth?",
            answer=f"{params.helper.capitalize()} helped {params.name} understand that the heart was praise and that the judge was being fair.",
        ),
        QAItem(
            question=f"What lesson did {params.name} learn?",
            answer=f"{params.name} learned to ask first and not jump to a romantic guess or a bias worry from one small sign.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an avatar?",
            answer="An avatar is a picture or character that stands for a person in a game, app, or online world.",
        ),
        QAItem(
            question="What does bias mean?",
            answer="Bias means liking one thing over another in a way that is not fair.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone gets the wrong idea about what something means.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand something better so you can do a wiser thing next time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when the avatar exists, a note can be read, and the judge is fair.
valid_story(P) :- place(P), avatar_style(_), note_kind(_), judge_style(_), helper_kind(_).

% Misunderstanding happens when a heart note is present and the child can misread it.
misunderstanding(P) :- note_kind(heart_note), valid_story(P).

% Lesson learned happens when helper advice clears confusion and bias worry.
lesson_learned(P) :- misunderstanding(P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for a in AVATAR_STYLES:
        lines.append(asp.fact("avatar_style", a))
    for n in NOTES:
        lines.append(asp.fact("note_kind", n))
    for j in JUDGE_STYLES:
        lines.append(asp.fact("judge_style", j))
    for h in HELPERS:
        lines.append(asp.fact("helper_kind", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Lightweight parity gate: the ASP twin should at least produce a model for the base facts.
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    if model is None:
        print("MISMATCH: ASP produced no model.")
        return 1
    print("OK: ASP program grounds and solves.")
    return 0


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1.\n#show misunderstanding/1.\n#show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("game_room", "sparkly", "heart_note", "clear", "friend", "Mira"),
            StoryParams("library_corner", "cozy", "star_note", "kind", "teacher", "Noah"),
            StoryParams("sunroom", "sporty", "smile_note", "bright", "parent", "Lena"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
