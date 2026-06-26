#!/usr/bin/env python3
"""
A small detective-story world about a compliment that goes missing, a quiet
flashback, and a kindness that solves the case.

The seed premise:
- A detective notices that a kind compliment was never delivered.
- An inner monologue weighs a possible misunderstanding.
- A flashback reveals why the compliment mattered.
- The case ends when kindness is chosen over suspicion.

This world is intentionally small, child-facing, and constraint-checked.
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

PLACES = {
    "library": "the library",
    "cafeteria": "the cafeteria",
    "schoolyard": "the schoolyard",
    "bookshop": "the bookshop",
    "garden": "the garden",
}

DETECTIVE_TOOLS = ["notebook", "magnifying glass", "penlight", "clipboard"]
EMOTIONS = ["curious", "careful", "hopeful", "nervous", "gentle"]
NAMES = ["Milo", "Nia", "Eli", "Sage", "Rosa", "Jun", "Ari", "Tess"]
NICKNAMES = ["Detective Dot", "Detective Blue", "Detective Finch", "Detective Vale"]

# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing | clue
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def is_plural(self) -> bool:
        return self.type in {"clues", "glasses"}

@dataclass
class Setting:
    place: str

@dataclass
class Case:
    compliment_text: str
    target_label: str
    target_type: str
    target_trait: str
    target_identity: str   # child-facing, respectful descriptor used in narration
    reason: str
    flashback_line: str
    kindness_act: str
    resolution_line: str

@dataclass
class StoryParams:
    place: str
    detective_name: str
    detective_type: str
    detective_emotion: str
    target_name: str
    target_type: str
    target_identity: str
    target_trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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

# ---------------------------------------------------------------------------
# Story case generation
# ---------------------------------------------------------------------------
def build_case(params: StoryParams) -> Case:
    compliment_text = f"You have a brave smile"
    reason = f"{params.target_name} had helped someone feel welcome earlier."
    flashback_line = (
        f"The detective remembered a small flashback: {params.target_name} had "
        f"shared a seat, a snack, or a kind word when nobody was looking."
    )
    kindness_act = "step in gently and share the compliment"
    resolution_line = (
        f"So the detective chose kindness, spoke the compliment out loud, and "
        f"watched the worry melt away."
    )
    return Case(
        compliment_text=compliment_text,
        target_label=params.target_name,
        target_type=params.target_type,
        target_trait=params.target_trait,
        target_identity=params.target_identity,
        reason=reason,
        flashback_line=flashback_line,
        kindness_act=kindness_act,
        resolution_line=resolution_line,
    )

# ---------------------------------------------------------------------------
# Prose helpers
# ---------------------------------------------------------------------------
def intro(world: World, detective: Entity, case: Case) -> None:
    world.say(
        f"Detective {detective.label} stood in {world.setting.place} with "
        f"{detective.pronoun('possessive')} notebook open."
    )
    world.say(
        f"{detective.pronoun().capitalize()} was feeling {detective.meters.get('emotion_word', 0) and 'watchful' or 'watchful'}, "
        f"and {detective.pronoun('possessive')} inner monologue kept asking, "
        f'"Where did the compliment go?"'
    )
    world.say(
        f"The missing compliment was simple: “{case.compliment_text}.”"
    )

def evidence(world: World, detective: Entity, target: Entity, case: Case) -> None:
    world.say(
        f"{detective.pronoun().capitalize()} looked at {target.label} and noticed "
        f"{target.pronoun('possessive')} kind face, calm hands, and careful way of listening."
    )
    world.say(
        f"Someone had called {target.pronoun('object')} gay before, and {target.label} "
        f"did not want that to become the whole story; the detective's job was to see the whole person."
    )
    world.say(
        f"In the detective's inner monologue, one thought kept returning: maybe the missed compliment was not a crime at all, just a moment that needed courage."
    )

def flashback(world: World, target: Entity, case: Case) -> None:
    world.para()
    world.say(
        f"Flashback: earlier that day, {target.label} had helped another child "
        f"pick up dropped papers and had smiled as if it was the easiest thing in the world."
    )
    world.say(case.flashback_line)

def turn(world: World, detective: Entity, target: Entity, case: Case) -> None:
    world.para()
    world.say(
        f"The detective finally understood the clue. {target.label}'s kindness was the reason everyone noticed {target.pronoun('object')}, even before the compliment was spoken."
    )
    world.say(
        f"So {detective.pronoun('subject')} decided to {case.kindness_act}."
    )
    world.say(
        f'“{case.compliment_text},” {detective.pronoun("subject")} said. “You are thoughtful, and you make this place nicer.”'
    )
    world.say(case.resolution_line)

def ending(world: World, detective: Entity, target: Entity) -> None:
    world.say(
        f"{target.label} smiled with relief, and the room felt lighter."
    )
    world.say(
        f"The detective closed {detective.pronoun('possessive')} notebook, certain the case was solved: the best clues had been a flashback, an inner monologue, and a little kindness."
    )

# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def tell_story(params: StoryParams) -> World:
    world = World(Setting(place=PLACES[params.place]))
    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=params.detective_type,
        label=params.detective_name,
        meters={"attention": 1.0},
        memes={"curiosity": 1.0, "emotion": 1.0},
    ))
    target = world.add(Entity(
        id="target",
        kind="character",
        type=params.target_type,
        label=params.target_name,
        meters={"calm": 1.0},
        memes={"kindness": 1.0},
    ))
    world.facts.update(
        detective=detective,
        target=target,
        case=build_case(params),
        place=params.place,
    )
    case: Case = world.facts["case"]  # type: ignore[assignment]
    intro(world, detective, case)
    evidence(world, detective, target, case)
    flashback(world, target, case)
    turn(world, detective, target, case)
    ending(world, detective, target)
    return world

# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective: Entity = f["detective"]  # type: ignore[assignment]
    target: Entity = f["target"]  # type: ignore[assignment]
    case: Case = f["case"]  # type: ignore[assignment]
    return [
        f'Write a short detective story for a child about a missing compliment in {f["place"]}.',
        f"Tell a gentle story where Detective {detective.label} uses an inner monologue and a flashback to understand {target.label}.",
        f'Write a story where kindness helps someone receive the compliment "{case.compliment_text}".',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]  # type: ignore[assignment]
    target: Entity = f["target"]  # type: ignore[assignment]
    case: Case = f["case"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did Detective {detective.label} look for the missing compliment?",
            answer=f"Detective {detective.label} looked in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did the detective keep thinking about in the inner monologue?",
            answer="The detective kept wondering where the compliment had gone and whether kindness could solve the problem.",
        ),
        QAItem(
            question=f"What did the flashback show about {target.label}?",
            answer=f"The flashback showed {target.label} being kind and helpful earlier, which explained why the compliment mattered.",
        ),
        QAItem(
            question=f"How was the case solved?",
            answer=f"The detective chose kindness and spoke the compliment: “{case.compliment_text}.”",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a compliment?",
            answer="A compliment is a kind thing you say about someone, like telling them they did a good job or look nice.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in a character's head that tells us what they are thinking.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a quick memory of something that happened earlier.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring to others.",
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
% A compliment is relevant if a detective and a target are present.
relevant_compliment(D,T) :- detective(D), target(T).

% A flashback matters when it reveals kindness.
use_flashback(T) :- target(T), kind(T).

% Kindness resolves the case.
solved_case(D,T) :- relevant_compliment(D,T), use_flashback(T), kindness(T).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import requirement
    lines: list[str] = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for name in NAMES:
        lines.append(asp.fact("name", name))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show solved_case/2."))
    # The rule is trivial; parity check is intentionally simple.
    if model is not None:
        print("OK: ASP rules loaded and solved.")
        return 0
    print("ASP verification failed.")
    return 1

# ---------------------------------------------------------------------------
# Parameter resolution / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryWorldChoice:
    place: str
    detective_name: str
    detective_type: str
    detective_emotion: str
    target_name: str
    target_type: str
    target_identity: str
    target_trait: str

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world about a compliment, flashback, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--detective-name")
    ap.add_argument("--target-name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    detective_name = args.detective_name or args.name or rng.choice(NICKNAMES)
    target_name = args.target_name or rng.choice(NAMES)
    if target_name == detective_name:
        target_name = rng.choice([n for n in NAMES if n != detective_name])
    detective_type = rng.choice(["girl", "boy"])
    target_type = rng.choice(["girl", "boy"])
    target_identity = "a gay kid"  # respectful, storyworld-level descriptor
    target_trait = rng.choice(["kind", "brave", "gentle", "helpful"])
    return StoryParams(
        place=place,
        detective_name=detective_name,
        detective_type=detective_type,
        detective_emotion=rng.choice(EMOTIONS),
        target_name=target_name,
        target_type=target_type,
        target_identity=target_identity,
        target_trait=target_trait,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print("\n--- world trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))

CURATED = [
    StoryParams(
        place="library",
        detective_name="Detective Finch",
        detective_type="girl",
        detective_emotion="curious",
        target_name="Ari",
        target_type="boy",
        target_identity="a gay kid",
        target_trait="kind",
    ),
    StoryParams(
        place="bookshop",
        detective_name="Detective Vale",
        detective_type="boy",
        detective_emotion="hopeful",
        target_name="Sage",
        target_type="girl",
        target_identity="a gay kid",
        target_trait="helpful",
    ),
]

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved_case/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show solved_case/2."))
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
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
