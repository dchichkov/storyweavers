#!/usr/bin/env python3
"""
storyworlds/worlds/envelope_error_repetition_ghost_story.py
===========================================================

A tiny story world about a repeated mistake with an envelope, and the gentle
ghostly surprise that follows.

The premise:
- A child finds an old envelope with the wrong address.
- Each attempt to fix the error repeats the same eerie pattern.
- The repetition becomes a clue: the envelope is trying to be seen.
- In the end, the child learns the truth and sets the letter free.

This world keeps the story close to a ghost story: quiet rooms, soft knocks,
whispered messages, and a repeated phrase that changes meaning as the state
changes.

The seed words are included in the world:
- envelope
- error

The key feature is repetition: a mistaken action can happen more than once,
and each repeat increases unease until the child finally notices the pattern.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    quiet: bool = True
    rainy: bool = False


@dataclass
class PromptCard:
    action: str
    clue: str
    repeatable: bool
    kind: str  # "mistake" | "fix" | "haunt"


@dataclass
class StoryParams:
    place: str
    action: str
    name: str
    gender: str
    caretaker: str
    clue: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


def story_error(msg: str) -> StoryError:
    return StoryError(msg)


SETTINGS = {
    "hall": Place(name="the hall", quiet=True, rainy=False),
    "attic": Place(name="the attic", quiet=True, rainy=False),
    "porch": Place(name="the porch", quiet=True, rainy=True),
    "study": Place(name="the study", quiet=True, rainy=False),
}

ACTIONS = {
    "open": PromptCard(action="open the envelope", clue="the seal", repeatable=True, kind="mistake"),
    "shake": PromptCard(action="shake the envelope", clue="the soft paper", repeatable=True, kind="mistake"),
    "read": PromptCard(action="read the note", clue="the fading ink", repeatable=False, kind="fix"),
    "return": PromptCard(action="return the envelope to the mailbox", clue="the address", repeatable=False, kind="fix"),
}

CLUES = {
    "address": "address",
    "seal": "seal",
    "ink": "ink",
    "mailbox": "mailbox",
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Ivy", "Zoe"]
BOY_NAMES = ["Leo", "Noah", "Eli", "Finn", "Theo", "Max"]


def ghostly_phrase(times: int, clue: str) -> str:
    if times == 1:
        return f"Once, very softly, the envelope seemed to whisper about the {clue}."
    if times == 2:
        return f"Again, the same soft whisper came back about the {clue}."
    return f"Again and again, the whisper returned, always about the {clue}."


def build_tension(world: World, child: Entity, envelope: Entity, action: PromptCard) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    envelope.meters["noticed"] = envelope.meters.get("noticed", 0.0) + 1
    world.say(
        f"{child.id} found an old envelope on a quiet table. "
        f"It looked ordinary, but {child.pronoun('possessive')} fingers paused at the edge as if the paper remembered something."
    )
    world.say(
        f"{child.id} wanted to {action.action}, even though the little mistake in the message felt strange."
    )


def repeat_error(world: World, child: Entity, envelope: Entity, action: PromptCard, max_repeats: int = 3) -> None:
    repeats = 0
    while repeats < max_repeats:
        repeats += 1
        tag = ("repeat", action.kind, repeats)
        if tag in world.fired:
            continue
        world.fired.add(tag)
        child.memes["unease"] = child.memes.get("unease", 0.0) + 1
        envelope.meters["touched"] = envelope.meters.get("touched", 0.0) + 1
        world.say(
            f"{child.id} {action.action}."
        )
        world.say(
            ghostly_phrase(repeats, action.clue)
        )
        if repeats < max_repeats:
            world.say(
                f"But the same error was still there, as if the envelope had been waiting for someone brave enough to notice."
            )


def reveal(world: World, child: Entity, caretaker: Entity, envelope: Entity) -> None:
    child.memes["fear"] = max(0.0, child.memes.get("fear", 0.0) - 1)
    child.memes["understanding"] = child.memes.get("understanding", 0.0) + 1
    envelope.meters["opened"] = 1.0
    world.say(
        f"At last, {child.id} saw the error clearly: the envelope was addressed wrong, and the message inside had never reached the right home."
    )
    world.say(
        f"{caretaker.id} listened by the doorway and said the softest thing: the letter could be sent again, the right way, so it would not wander anymore."
    )


def ending(world: World, child: Entity, envelope: Entity) -> None:
    child.memes["peace"] = child.memes.get("peace", 0.0) + 1
    world.say(
        f"{child.id} placed the envelope carefully in a safe place, and the room felt quieter after the repetition stopped."
    )
    world.say(
        f"In the last dim light, the envelope no longer felt haunted; it felt waited for, as if it had finally been heard."
    )


def tell(place: Place, action: PromptCard, name: str, gender: str, caretaker: str, clue: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=gender))
    adult = world.add(Entity(id="Caretaker", kind="character", type=caretaker))
    envelope = world.add(Entity(
        id="Envelope",
        type="envelope",
        label="old envelope",
        phrase="an old envelope with a wrong address",
        owner=child.id,
        caretaker=adult.id,
    ))

    world.say(
        f"{child.id} was a small {gender} who liked quiet places and tiny mysteries."
    )
    world.say(
        f"One evening, {child.id} found {envelope.phrase} on a table in {place.name}."
    )
    world.para()

    build_tension(world, child, envelope, action)
    repeat_error(world, child, envelope, action)
    world.para()
    reveal(world, child, adult, envelope)
    ending(world, child, envelope)

    world.facts.update(
        child=child,
        adult=adult,
        envelope=envelope,
        action=action,
        clue=clue,
        place=place,
    )
    return world


def pick_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    action = f["action"]
    place = f["place"].name
    clue = f["clue"]
    return [
        f"Write a short ghost story for a young child about an envelope and a repeated error in {place}.",
        f"Tell a quiet, spooky-but-gentle story where {child.id} keeps trying to {action.action} and notices the same {clue} again and again.",
        f"Write a story with repetition, a wrong address, and a soft ending where a child helps an envelope find its way home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    action = f["action"]
    envelope = f["envelope"]
    place = f["place"].name
    return [
        QAItem(
            question=f"What did {child.id} find in {place}?",
            answer=f"{child.id} found an old envelope with a wrong address on it.",
        ),
        QAItem(
            question=f"What kept happening when {child.id} tried to {action.action}?",
            answer=f"The same error seemed to come back again and again, making the envelope feel a little ghostly.",
        ),
        QAItem(
            question=f"How did the story end for the envelope?",
            answer=f"{child.id} and {adult.id} decided to send the envelope again the right way, so it could reach the correct home.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an envelope used for?",
            answer="An envelope is a paper cover used to hold a letter or card so it can be sent to someone.",
        ),
        QAItem(
            question="What is an error?",
            answer="An error is a mistake, which means something was not done the right way.",
        ),
        QAItem(
            question="Why can repetition feel spooky in a ghost story?",
            answer="Repetition can feel spooky because the same thing happening again and again can seem like a sign that something wants attention.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
repeatable(action) :- action(open).
repeatable(action) :- action(shake).

mistake(action) :- action(open).
mistake(action) :- action(shake).

spooky(X) :- envelope(X), mistake(A), repeatable(A).
resolved(X) :- envelope(X), fixed(X).

fixed(X) :- returned(X).
fixed(X) :- read(X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
        if ACTIONS[aid].repeatable:
            lines.append(asp.fact("repeatable_action", aid))
    lines.append(asp.fact("envelope", "Envelope"))
    lines.append(asp.fact("error", "Envelope"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show spooky/1."))
    spooky = set(asp.atoms(model, "spooky"))
    python_spooky = {("Envelope",)}
    if spooky == python_spooky:
        print("OK: ASP parity matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  ASP:", sorted(spooky))
    print("  Python:", sorted(python_spooky))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A quiet ghost-story world about an envelope, an error, and repetition."
    )
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--action", choices=ACTIONS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--clue", choices=CLUES.keys())
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    action = args.action or rng.choice(list(ACTIONS.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    clue = args.clue or rng.choice(list(CLUES.keys()))
    name = args.name or pick_name(gender, rng)
    return StoryParams(place=place, action=action, name=name, gender=gender, caretaker=caretaker, clue=clue)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIONS[params.action],
        params.name,
        params.gender,
        params.caretaker,
        params.clue,
    )
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


def asp_validities() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show spooky/1."))
    return sorted(set(asp.atoms(model, "spooky")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show spooky/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"spooky models: {asp_validities()}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="hall", action="open", name="Mia", gender="girl", caretaker="mother", clue="address"),
            StoryParams(place="attic", action="shake", name="Leo", gender="boy", caretaker="father", clue="seal"),
            StoryParams(place="study", action="read", name="Nora", gender="girl", caretaker="mother", clue="ink"),
            StoryParams(place="porch", action="return", name="Finn", gender="boy", caretaker="father", clue="mailbox"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.name}: {p.action} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
