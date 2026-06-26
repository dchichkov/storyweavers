#!/usr/bin/env python3
"""
A small fable-like storyworld about an anonymous flatter, watchful eyes,
sound effects, friendship, and a twist of truth.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "cat", "rabbit", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Character(Entity):
    kind: str = "character"


@dataclass
class StoryParams:
    name: str
    friend: str
    place: str
    token: str
    seed: Optional[int] = None


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "meadow": "the green meadow",
    "pond": "the quiet pond",
    "hill": "the windy hill",
    "grove": "the shady grove",
}

TOKENS = {
    "berry": {"label": "red berry", "phrase": "a bright red berry"},
    "bell": {"label": "silver bell", "phrase": "a tiny silver bell"},
    "pebble": {"label": "smooth pebble", "phrase": "a smooth gray pebble"},
}

NAMES = ["Milo", "Pippa", "Tansy", "Rook", "Wren", "Hugo", "Nia", "Otis"]
FRIENDS = ["hare", "sparrow", "badger", "mouse", "deer", "otter"]
TRAITS = ["kind", "gentle", "curious", "brave", "patient"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place: str, token: str) -> bool:
    return place in PLACES and token in TOKENS


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in PLACES for t in TOKENS if valid_combo(p, t)]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def onomatopoeia(place: str) -> str:
    return {
        "meadow": "swish",
        "pond": "plink",
        "hill": "whoosh",
        "grove": "rustle",
    }.get(place, "softly")


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.place, params.token):
        raise StoryError("That place and token do not make a fitting fable.")

    w = World()
    hero = w.add(Character(id=params.name, type="fox", label=params.name, phrases=""))
    friend = w.add(Character(id=params.friend, type="hare", label=params.friend, phrases=""))
    token = w.add(Entity(
        id="token",
        type=params.token,
        label=TOKENS[params.token]["label"],
        phrase=TOKENS[params.token]["phrase"],
        owner=hero.id,
    ))
    w.facts.update(hero=hero, friend=friend, token=token, place=params.place)
    return w


def tell(params: StoryParams) -> World:
    w = build_world(params)
    hero: Character = w.facts["hero"]
    friend: Character = w.facts["friend"]
    token: Entity = w.facts["token"]
    place = PLACES[params.place]

    hero.memes["hope"] = 1
    friend.memes["trust"] = 1

    w.say(
        f"Once in {place}, a small fox named {hero.id} found {token.phrase} beside the path."
    )
    w.say(
        f"{hero.id} listened to the gentle {onomatopoeia(params.place)} of the wind and thought the day might be lucky."
    )
    w.say(
        f"Then an anonymous flatter came near, all smiles and soft words: "
        f'"What a splendid finder you are," it said, with bright-eyed praise.'
    )

    w.para()
    hero.memes["pride"] = 1
    w.say(
        f"{hero.id} liked the flattering sound at first. It felt warm like a song, and friendship can be quick to trust."
    )
    w.say(
        f"But {friend.id} watched with careful eyes and heard a small twist in the tale."
    )
    w.say(
        f'"Why praise only you?" asked {friend.id}. "If the bell rings for one, it can still call the whole meadow."'
    )

    w.para()
    hero.memes["doubt"] = 1
    w.say(
        f"That made {hero.id} pause. The anonymous flatter had no name, no reason, and no wish to share."
    )
    w.say(
        f'"Clink," went the token as {hero.id} set it down, and the meadow seemed to breathe easier.'
    )
    w.say(
        f"{hero.id} smiled at {friend.id} and said, 'True friends tell the truth, even when a sweet voice tries to hide it.'"
    )
    w.say(
        f"So the two friends walked on together, and the anonymous flatter faded away like mist after sunrise."
    )

    w.facts["resolved"] = True
    return w


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    token = f["token"]
    place = f["place"]
    return [
        f"Write a short fable about an anonymous flatter near {PLACES[place]} and a {token.type} that tests friendship.",
        f"Tell a child-friendly story where {hero.id} hears a sweet voice, but a friend with careful eyes notices the twist.",
        f"Create a simple fable with sound effects like plink, clink, or rustle, and end with a lesson about truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    token = f["token"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who found the {token.label} in {PLACES[place]}?",
            answer=f"{hero.id} found the {token.label} beside the path in {PLACES[place]}."
        ),
        QAItem(
            question="What did the anonymous flatter try to do?",
            answer="The anonymous flatter tried to make the fox feel special with sweet words, but it did not tell the whole truth."
        ),
        QAItem(
            question=f"How did {friend.id} help?",
            answer=f"{friend.id} used careful eyes and a truthful question to notice the twist and protect the friendship."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flatter?",
            answer="A flatter is someone who gives overly sweet praise, sometimes to hide a trick or get what it wants."
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a word that helps you hear the scene in your head, like plink, clink, swish, or whoosh."
        ),
        QAItem(
            question="What is a twist in a fable?",
            answer="A twist is a surprise turn that changes what the characters think is happening."
        ),
        QAItem(
            question="Why are friends important in a fable?",
            answer="Friends matter because they can warn each other, tell the truth, and help each other make wise choices."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} memes={dict(e.memes)} meters={dict(e.meters)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_combo(P,T) :- place(P), token(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TOKENS:
        lines.append(asp.fact("token", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like world of an anonymous flatter and a truthful friend.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--token", choices=list(TOKENS))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.token:
        combos = [c for c in combos if c[1] == args.token]
    if not combos:
        raise StoryError("No valid combination matches those choices.")
    place, token = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    return StoryParams(name=name, friend=friend, place=place, token=token)


def generate(params: StoryParams) -> StorySample:
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


CURATED = [
    StoryParams(name="Milo", friend="hare", place="meadow", token="berry"),
    StoryParams(name="Pippa", friend="sparrow", place="grove", token="bell"),
    StoryParams(name="Tansy", friend="badger", place="hill", token="pebble"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
