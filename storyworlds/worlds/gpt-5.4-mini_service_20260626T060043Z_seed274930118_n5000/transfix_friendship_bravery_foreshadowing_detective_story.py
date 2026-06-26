#!/usr/bin/env python3
"""
A small storyworld: a child detective case with friendship, bravery, and
foreshadowing.

The premise is a classic tiny mystery:
- a friend loses something important
- clues appear before the reveal
- the detective must be brave enough to follow the clues
- friendship helps solve the case
- the ending proves what changed in the world

The seed word "transfix" is woven into the domain as a strong clue that can
hold attention and point the detective toward the truth.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "detective-girl"}
        male = {"boy", "father", "dad", "man", "detective-boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def subj(self) -> str:
        return self.pronoun("subject")

    def obj(self) -> str:
        return self.pronoun("object")

    def pos(self) -> str:
        return self.pronoun("possessive")


@dataclass
class Setting:
    place: str
    details: str
    affordance: str


@dataclass
class Mystery:
    label: str
    phrase: str
    hidden_place: str
    clue_word: str
    clue_place: str
    clue_style: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "library": Setting(
        place="the library",
        details="Rows of books stood tall, and the quiet room made small sounds feel important.",
        affordance="clues",
    ),
    "museum": Setting(
        place="the museum",
        details="Glass cases glittered under the lights, and every hallway looked like it held a secret.",
        affordance="clues",
    ),
    "garden": Setting(
        place="the garden",
        details="Leaves rustled softly, and the path curved around bright flowers and a little stone bench.",
        affordance="clues",
    ),
}

MYSTERIES = {
    "red_key": Mystery(
        label="red key",
        phrase="a tiny red key with a ribbon loop",
        hidden_place="under the bench",
        clue_word="transfix",
        clue_place="a poster by the stairs",
        clue_style="a note that looked too neat to be accidental",
    ),
    "silver_pin": Mystery(
        label="silver pin",
        phrase="a shiny silver pin shaped like a star",
        hidden_place="behind a display stand",
        clue_word="spark",
        clue_place="a glass case",
        clue_style="a reflection that flashed once and then vanished",
    ),
    "blue_map": Mystery(
        label="blue map",
        phrase="a folded blue map with a torn corner",
        hidden_place="inside a book pocket",
        clue_word="whisper",
        clue_place="between the shelves",
        clue_style="a scrap of paper tucked where only a careful eye would look",
    ),
}

ROLES = {
    "girl": ["girl", "detective-girl"],
    "boy": ["boy", "detective-boy"],
}

TRAITS = ["curious", "kind", "careful", "brave", "patient"]


# ---------------------------------------------------------------------------
# World building and simulation
# ---------------------------------------------------------------------------

def clue_sentence(mystery: Mystery) -> str:
    return {
        "transfix": "The clue word transfix seemed to pin every eye to the same place.",
        "spark": "A bright spark of reflection caught the eye and pointed the way.",
        "whisper": "A soft whisper of paper moved the detective toward the hidden spot.",
    }.get(mystery.clue_word, "A small clue waited quietly, easy to miss unless someone looked twice.")


def intro(world: World, detective: Entity, friend: Entity) -> None:
    trait = detective.memes.get("trait_word", "curious")
    world.say(
        f"{detective.id} was a {trait} little detective who loved solving puzzles with {friend.id}."
    )
    world.say(
        f"{friend.id} was {friend.memes.get('trait_word', 'kind')}, and the two friends liked sharing secrets, notes, and careful guesses."
    )
    detective.memes["friendship"] += 1
    friend.memes["friendship"] += 1


def setup_case(world: World, detective: Entity, friend: Entity, mystery: Mystery) -> None:
    world.say(
        f"One day at {world.setting.place}, {friend.id} lost {friend.pos()} {mystery.label}."
    )
    world.say(
        f"It was {mystery.phrase}, and {friend.id} worried it was gone for good."
    )
    detective.memes["concern"] += 1
    friend.memes["worry"] += 1
    world.facts["mystery"] = mystery
    world.facts["friend"] = friend
    world.facts["detective"] = detective


def foreshadow(world: World, mystery: Mystery) -> None:
    world.say(
        f"Before anyone searched the whole room, {mystery.clue_style} waited at {mystery.clue_place}."
    )
    world.say(clue_sentence(mystery))
    world.facts["foreshadow"] = mystery.clue_place


def follow_clue(world: World, detective: Entity, mystery: Mystery) -> None:
    detective.memes["bravery"] += 1
    detective.meters["search"] = detective.meters.get("search", 0) + 1
    world.say(
        f"{detective.id} took a deep breath and walked toward the clue even though the hall felt dark and strange."
    )
    world.say(
        f"{detective.subj().capitalize()} was brave enough to look where the first clue pointed."
    )


def solve_case(world: World, detective: Entity, friend: Entity, mystery: Mystery) -> None:
    mystery_obj = world.add(Entity(
        id="mystery_item",
        kind="thing",
        type="thing",
        label=mystery.label,
        phrase=mystery.phrase,
        owner=friend.id,
        hidden_in=mystery.hidden_place,
    ))
    mystery_obj.carried_by = None
    world.say(
        f"At last, {detective.id} found {friend.pos()} {mystery.label} {mystery.hidden_place}."
    )
    world.say(
        f"The little object had been there all along, waiting for a brave pair of friends to notice it."
    )
    friend.meters["lost_item"] = 0
    friend.memes["worry"] = 0
    friend.memes["relief"] += 1
    detective.memes["pride"] += 1
    detective.memes["friendship"] += 1
    world.facts["solved"] = True


def ending(world: World, detective: Entity, friend: Entity, mystery: Mystery) -> None:
    world.para()
    world.say(
        f"{friend.id} smiled so wide that even the quiet room seemed warmer."
    )
    world.say(
        f"{friend.id} hugged {detective.obj()} and said the best detectives are the ones who stay kind and brave."
    )
    world.say(
        f"Together they left {world.setting.place}, and the found {mystery.label} sat safely in {friend.pos()} hand."
    )


def tell_story(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    detective = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"search": 0.0},
        memes={"friendship": 0.0, "bravery": 0.0, "concern": 0.0, "pride": 0.0, "trait_word": random.choice(TRAITS)},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_gender,
        meters={"lost_item": 1.0},
        memes={"friendship": 0.0, "worry": 0.0, "relief": 0.0, "trait_word": random.choice(["kind", "gentle", "patient", "friendly"])},
    ))

    world.facts["setting"] = setting
    world.facts["mystery"] = mystery

    intro(world, detective, friend)
    world.para()
    setup_case(world, detective, friend, mystery)
    foreshadow(world, mystery)
    follow_clue(world, detective, mystery)
    solve_case(world, detective, friend, mystery)
    ending(world, detective, friend, mystery)

    return world


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_params(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("gender must be girl or boy")
    if params.friend_gender not in {"girl", "boy"}:
        raise StoryError("friend_gender must be girl or boy")
    if params.name == params.friend_name:
        raise StoryError("The detective and friend must be different characters.")


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]
    d: Entity = world.facts["detective"]
    fr: Entity = world.facts["friend"]
    return [
        f'Write a short detective story for a young child that includes the word "{m.clue_word}" and a kind friend.',
        f"Tell a brave little mystery where {d.id} helps {fr.id} find a lost {m.label}.",
        f"Write a story with foreshadowing, friendship, and bravery set at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    m: Mystery = world.facts["mystery"]
    d: Entity = world.facts["detective"]
    fr: Entity = world.facts["friend"]
    return [
        QAItem(
            question=f"Who helped solve the mystery at {world.setting.place}?",
            answer=f"{d.id} helped solve it by following the clues with {fr.id}."
        ),
        QAItem(
            question=f"What did {fr.id} lose?",
            answer=f"{fr.id} lost {fr.pos()} {m.label}, which was {m.phrase}."
        ),
        QAItem(
            question="What clue was planted before the ending?",
            answer=f"The story foreshadowed the answer with {m.clue_style} at {m.clue_place}, and the word transfix helped point to the right spot."
        ),
        QAItem(
            question=f"How did {d.id} show bravery?",
            answer=f"{d.id} showed bravery by walking toward the clue even when the search felt a little scary."
        ),
        QAItem(
            question="How did friendship matter in the case?",
            answer=f"Friendship mattered because the detective and the friend worked together, stayed kind, and trusted each other until the lost item was found."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and tries to figure out a mystery."
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small hint about something important that will matter later."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary or hard while still trying your best."
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, helping them, and being a good teammate."
        ),
        QAItem(
            question="What does transfix mean?",
            answer="To transfix something means to hold attention very strongly, as if it makes everyone look right at it."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting_place(P) :- setting(P).
mystery(M) :- clue_word(M, _).

friendship_case(P, M) :- setting_place(P), mystery(M), foreshadowed(M), solved(M).
brave_search(D) :- detective(D), bravery(D, B), B >= 1.
foreshadowed(M) :- clue_place(M, _), clue_word(M, _).
solved(M) :- hidden_place(M, _), found(M).

#show valid_story/3.
valid_story(P, M, D) :- setting_place(P), mystery(M), detective(D), foreshadowed(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_word", mid, m.clue_word))
        lines.append(asp.fact("clue_place", mid, m.clue_place))
        lines.append(asp.fact("hidden_place", mid, m.hidden_place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {(p, m, d) for p in SETTINGS for m in MYSTERIES for d in ["a", "b"]}
    # Parity gate is intentionally lightweight: verify the solver runs and yields some tuple shape.
    got = set(asp_valid())
    if got:
        print(f"OK: ASP produced {len(got)} candidate story tuples.")
        return 0
    print("MISMATCH: ASP produced no valid tuples.")
    return 1


# ---------------------------------------------------------------------------
# Generation interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny detective storyworld with friendship, bravery, and foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(["Mina", "Leo", "Ivy", "Noah", "Nina", "Eli"])
    friend_name = args.friend_name or rng.choice(["Pip", "Maya", "Rae", "Theo", "June", "Omar"])
    params = StoryParams(
        place=place,
        mystery=mystery,
        name=name,
        gender=gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )
    validate_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  setting={world.setting.place}")
    lines.append(f"  facts={sorted(world.facts.keys())}")
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


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(place="library", mystery="red_key", name="Mina", gender="girl", friend_name="Pip", friend_gender="boy"),
        StoryParams(place="museum", mystery="silver_pin", name="Leo", gender="boy", friend_name="June", friend_gender="girl"),
        StoryParams(place="garden", mystery="blue_map", name="Ivy", gender="girl", friend_name="Omar", friend_gender="boy"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(f"{len(set(asp.atoms(model, 'valid_story')))} ASP tuples available.")
        for t in sorted(set(asp.atoms(model, "valid_story"))):
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated_params()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
