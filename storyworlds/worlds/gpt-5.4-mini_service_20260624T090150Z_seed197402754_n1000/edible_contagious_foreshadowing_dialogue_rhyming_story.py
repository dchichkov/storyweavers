#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/edible_contagious_foreshadowing_dialogue_rhyming_story.py
====================================================================================================

A small, self-contained story world for an edible, contagious, foreshadowed,
dialogue-rich rhyming tale.

Premise:
- A child has a special edible treat.
- The treat is sweet, but its funny magic is contagious.
- Foreshadowing hints that the first bite will start a chain of giggles.
- Dialogue carries the story from worry to shared delight.

The world is intentionally tiny and classical:
- one setting
- a few typed entities
- one causal turn
- one warm ending image

The prose aims to feel like a short rhyming story for young children, while the
state model drives what happens and why.
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
# Core world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    edible: bool = False
    contagious: bool = False
    eaten: bool = False
    shared: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_character(self) -> bool:
        return self.kind == "character"


@dataclass
class Setting:
    place: str = "the picnic blanket"
    detail: str = "the grass was soft and green"


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    flavor: str
    rhyme_word: str
    contagious_meme: str = "giggle"
    edible: bool = True


@dataclass
class StoryParams:
    place: str
    treat: str
    name: str
    child_type: str
    parent_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.is_character()]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: Entity(**vars(v)) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "blanket": Setting(place="the picnic blanket", detail="the grass was soft and green"),
    "kitchen": Setting(place="the kitchen table", detail="the window winked with warm sun"),
    "porch": Setting(place="the porch step", detail="the breezes blew by, brisk and neat"),
}

TREATS = {
    "berry_tart": Treat(
        id="berry_tart",
        label="berry tart",
        phrase="a tiny berry tart",
        flavor="sweet and bright",
        rhyme_word="heart",
        contagious_meme="giggle",
    ),
    "honey_muffin": Treat(
        id="honey_muffin",
        label="honey muffin",
        phrase="a warm honey muffin",
        flavor="golden and sweet",
        rhyme_word="sunny",
        contagious_meme="giggle",
    ),
    "apple_turnover": Treat(
        id="apple_turnover",
        label="apple turnover",
        phrase="a flaky apple turnover",
        flavor="cinnamon-sweet",
        rhyme_word="glow",
        contagious_meme="giggle",
    ),
}

CHILD_NAMES = ["Mia", "Nora", "Luca", "Owen", "Zoe", "Penny", "Theo", "Lily"]
CHILD_TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the chosen treat is edible and can become contagious,
% and the setting supports a shared snack moment.
valid_story(P, T) :- place(P), treat(T), edible(T), contagious(T), suitable(P).

% The turn is only reasonable if someone can notice the foreshadowing:
% sweet smell + wobbling plate + a warning from the parent.
foreshadowing(P, T) :- valid_story(P, T), sweet(T), hint(P), warning(T).

% The ending is only interesting if the contagion spreads by sharing.
shared_resolution(P, T) :- foreshadowing(P, T), shared(T), laugh_spreads(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("suitable", pid))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("edible", tid))
        lines.append(asp.fact("contagious", tid))
        lines.append(asp.fact("sweet", tid))
        lines.append(asp.fact("warning", tid))
        lines.append(asp.fact("shared", tid))
        lines.append(asp.fact("laugh_spreads", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    pairs = {(p, t) for p, t in asp_valid_pairs()}
    python_pairs = {(p, t) for p in valid_pairs()}
    if pairs == python_pairs:
        print(f"OK: clingo gate matches valid_pairs() ({len(pairs)} combos).")
        return 0
    print("MISMATCH between clingo and python reasonableness gates:")
    if pairs - python_pairs:
        print("  only in clingo:", sorted(pairs - python_pairs))
    if python_pairs - pairs:
        print("  only in python:", sorted(python_pairs - pairs))
    return 1


def valid_pairs() -> list[tuple[str, str]]:
    return [(p, t) for p in SETTINGS for t in TREATS]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def foreshadow_line(treat: Treat) -> str:
    return f"The {treat.label} smelled sweet, and the spoon gave a little wobble, like it knew a joke was near."


def initial_scene(world: World, child: Entity, parent: Entity, treat: Treat) -> None:
    world.say(
        f"{child.id} was a little {child.type} who loved a treat with a soft, bright start."
    )
    world.say(
        f"Today {parent.pronoun('subject')} brought {child.pronoun('object')} {treat.phrase}; "
        f"it was edible, and the taste was {treat.flavor}."
    )


def setup_dialogue(world: World, child: Entity, parent: Entity, treat: Treat) -> None:
    world.say(
        f'"Can I have a bite?" asked {child.id}. "Yes," said {parent.pronoun("subject")}, '
        f'"but slow and light, and keep your eyes in sight."'
    )
    world.say(foreshadow_line(treat))


def first_bite(world: World, child: Entity, parent: Entity, treat: Treat) -> None:
    child.eaten = True
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.memes["anticipation"] = child.memes.get("anticipation", 0) + 1
    world.say(
        f"{child.id} took a small first bite, and the room felt cozy and right."
    )
    world.say(
        f'Then {child.id} blinked and grinned. "Oh! That is funny!" {child.pronoun("subject")} cried.'
    )
    world.say(
        f'The parent laughed, "I knew it would bloom; the giggle was waiting in the spoon."'
    )


def contagion_turn(world: World, child: Entity, parent: Entity, treat: Treat) -> None:
    child.memes[treat.contagious_meme] = child.memes.get(treat.contagious_meme, 0) + 1
    parent.memes[treat.contagious_meme] = parent.memes.get(treat.contagious_meme, 0) + 1
    child.contagious = True
    world.say(
        f"The giggle was contagious, quick as a tune; it skipped from mouth to mouth by noon."
    )
    world.say(
        f'"It is catching!" said {parent.id}. "Then catch this too," said {child.id}, and they both said "boo!"'
    )


def shared_resolution(world: World, child: Entity, parent: Entity, treat: Treat) -> None:
    child.shared = True
    parent.shared = True
    child.memes["love"] = child.memes.get("love", 0) + 1
    parent.memes["love"] = parent.memes.get("love", 0) + 1
    world.say(
        f"They split the last sweet bit in two, and the little laughs came dancing through."
    )
    world.say(
        f"By the end of the snack, {child.id} sat snug and bright, with crumbs on {child.pronoun('possessive')} chin and joy in {child.pronoun('possessive')} sight."
    )


def tell(setting: Setting, treat: Treat, child_name: str, child_type: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    snack = world.add(Entity(
        id=treat.id,
        kind="thing",
        type="snack",
        label=treat.label,
        phrase=treat.phrase,
        owner=child.id,
        edible=treat.edible,
        contagious=True,
    ))

    initial_scene(world, child, parent, treat)
    world.para()
    world.say(f"They sat at {setting.place}, where {setting.detail}.")
    setup_dialogue(world, child, parent, treat)
    world.para()
    world.say(f"{parent.pronoun('subject').capitalize()} tapped the plate and said, \"Watch the tray, and hear the way.\"")
    first_bite(world, child, parent, treat)
    contagion_turn(world, child, parent, treat)
    world.para()
    world.say(
        f"{parent.id} passed another crumb, and the laughing went round like a drum."
    )
    shared_resolution(world, child, parent, treat)

    world.facts.update(
        child=child,
        parent=parent,
        snack=snack,
        setting=setting,
        treat=treat,
        edible=snack.edible,
        contagious=snack.contagious,
        shared=snack.shared,
        foreshadowed=True,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, parent, treat = f["child"], f["parent"], f["treat"]
    return [
        f'Write a short rhyming story for a young child about {child.id} and a {treat.label}.',
        f'Write a gentle story with dialogue, foreshadowing, and a contagious giggle from a sweet snack.',
        f'Write a child-friendly rhyme where a parent warns about a treat and the ending is warm and shared.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, treat = f["child"], f["parent"], f["treat"]
    return [
        QAItem(
            question=f"What did {child.id} want to do with the {treat.label}?",
            answer=f"{child.id} wanted a bite of the {treat.label}, because it looked sweet and inviting.",
        ),
        QAItem(
            question=f"Why did the story hint that something would happen before the first bite?",
            answer=f"The story foreshadowed the joke in the snack by saying the {treat.label} smelled sweet and the spoon wobbled like it knew a joke was near.",
        ),
        QAItem(
            question=f"What happened after {child.id} took the first bite?",
            answer=f"{child.id} smiled, then the giggles spread to {parent.id} too, because the laughter was contagious.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with them sharing the last sweet bit and sitting together in a happy, crumbly glow.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    treat = world.facts["treat"]
    qa = [
        QAItem(
            question="What does edible mean?",
            answer="Edible means safe to eat.",
        ),
        QAItem(
            question="What does contagious mean in a funny story?",
            answer="Contagious means something can spread from one person to another, like a laugh or a yawn.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints that something important may happen later in the story.",
        ),
        QAItem(
            question="Why do stories use dialogue?",
            answer="Dialogue lets characters speak to each other, so the story feels lively and real.",
        ),
    ]
    if treat.id == "berry_tart":
        qa.append(
            QAItem(
                question="What is a tart?",
                answer="A tart is a small baked treat with a crust and a sweet filling.",
            )
        )
    return qa


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.edible:
            bits.append("edible=True")
        if e.contagious:
            bits.append("contagious=True")
        if e.eaten:
            bits.append("eaten=True")
        if e.shared:
            bits.append("shared=True")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An edible, contagious, foreshadowed rhyming story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(SETTINGS))
    treat = args.treat or rng.choice(list(TREATS))
    gender = args.gender or rng.choice(CHILD_TYPES)
    if args.name:
        name = args.name
    else:
        name = rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(place=place, treat=treat, name=name, child_type=gender, parent_type=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TREATS[params.treat], params.name, params.child_type, params.parent_type)
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
    StoryParams(place="blanket", treat="berry_tart", name="Mia", child_type="girl", parent_type="mother"),
    StoryParams(place="kitchen", treat="honey_muffin", name="Theo", child_type="boy", parent_type="father"),
    StoryParams(place="porch", treat="apple_turnover", name="Zoe", child_type="girl", parent_type="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_pairs())} valid story pairs")
        for place, treat in asp_valid_pairs():
            print(place, treat)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        if len(samples) > 1 and not args.all:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
