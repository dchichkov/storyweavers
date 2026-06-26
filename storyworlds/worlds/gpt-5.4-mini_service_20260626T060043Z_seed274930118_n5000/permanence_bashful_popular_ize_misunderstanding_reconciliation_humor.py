#!/usr/bin/env python3
"""
Story world: a small mystery about a bashful little rumor, a permanence spell,
and a plan to popular-ize a clue without breaking trust.

This world is built around three narrative instruments:
- Misunderstanding
- Reconciliation
- Humor

The style is close to Mystery: there is a puzzling sign, a mistaken guess,
a careful reveal, and a gentle ending where everyone sees what was really true.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    mood: str
    clues: list[str] = field(default_factory=list)
    hides: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    clue: str
    misunderstanding: str
    humor: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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


PLACES = {
    "museum": Place(
        name="the museum",
        mood="quiet",
        clues=["a glass case", "a locked room", "a tiny footprint"],
        hides=["a missing label", "a dusty shelf"],
    ),
    "library": Place(
        name="the library",
        mood="hushed",
        clues=["a book cart", "a note in the margin", "a bookmark"],
        hides=["a folded map", "a whispering corner"],
    ),
    "garden": Place(
        name="the garden",
        mood="soft",
        clues=["a bent flower", "a muddy path", "a small gate"],
        hides=["a chipped pot", "a hidden path"],
    ),
}

MISUNDERSTANDINGS = {
    "missing_label": "the missing label meant someone had stolen the clue",
    "dusty_shelf": "the dusty shelf looked like nobody had touched it for ages",
    "tiny_footprint": "the tiny footprint seemed to prove a secret visitor came by",
    "bookmark": "the bookmark seemed to point to a bad deed",
    "folded_map": "the folded map looked like a secret escape plan",
    "hidden_path": "the hidden path looked like a place to hide trouble",
}

HUMOR = {
    "sneeze": "the old guard sneezed so suddenly that even the clock seemed surprised",
    "hat": "the big hat slipped over one eye and made the serious moment look silly",
    "echo": "the echo answered every whisper like it was trying to join the case",
    "cat": "a cat marched through as if it owned the mystery and the floor",
}

RECONCILIATIONS = {
    "apology": "said sorry and told the truth",
    "shared_laugh": "laughed together at the mistake",
    "admired_courage": "admired how brave the other one had been to ask",
}

PEOPLE = ["girl", "boy"]
NAMES = ["Mina", "Otis", "Lena", "Theo", "Ruby", "Noel", "Ivy", "Pip"]


@dataclass
class StoryState:
    place: Place
    hero: Entity
    companion: Entity
    clue: str
    misunderstanding: str
    humor: str
    solved: bool = False
    reconciled: bool = False
    clue_seen: bool = False


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery story world about misunderstanding and reconciliation.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=PEOPLE)
    ap.add_argument("--companion-name")
    ap.add_argument("--companion-type", choices=PEOPLE)
    ap.add_argument("--clue")
    ap.add_argument("--misunderstanding", choices=sorted(MISUNDERSTANDINGS))
    ap.add_argument("--humor", choices=sorted(HUMOR))
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
    place = args.place or rng.choice(sorted(PLACES))
    mis = args.misunderstanding or rng.choice(sorted(MISUNDERSTANDINGS))
    hum = args.humor or rng.choice(sorted(HUMOR))
    place_obj = PLACES[place]
    clue = args.clue or rng.choice(place_obj.clues + place_obj.hides)
    hero_type = args.hero_type or rng.choice(PEOPLE)
    comp_type = args.companion_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(NAMES)
    companion_name = args.companion_name or rng.choice([n for n in NAMES if n != hero_name])
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        companion_name=companion_name,
        companion_type=comp_type,
        clue=clue,
        misunderstanding=mis,
        humor=hum,
    )


def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name, traits=["bashful"]))
    companion = world.add(Entity(id="companion", kind="character", type=params.companion_type, label=params.companion_name))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=params.clue, phrase=params.clue))
    world.facts.update(
        hero=hero,
        companion=companion,
        clue=clue,
        place=place,
        misunderstanding=params.misunderstanding,
        humor=params.humor,
    )

    hero.memes["bashful"] = 1
    companion.memes["curious"] = 1
    clue.meters["permanence"] = 1

    world.say(f"{hero.label} and {companion.label} went to {place.name}, where the air felt {place.mood}.")
    world.say(f"Near a {params.clue}, {hero.label} noticed a strange sign that seemed to promise a bigger secret.")
    world.say(
        f"{companion.label} thought {MISUNDERSTANDINGS[params.misunderstanding]}, "
        f"and that made the little case feel serious."
    )

    world.para()
    world.say(f"But then {HUMOR[params.humor]}.")
    world.say(f"{hero.label} went quiet at first, because {hero.pronoun()} was bashful and did not want to be wrong.")

    world.para()
    world.say(f"Still, {hero.label} looked again and saw the clue had stayed in place all along.")
    world.say("It had permanence: even when the first guess was wrong, the real mark did not move.")
    world.say(f"{hero.label} whispered the truth, and {companion.label} listened closely.")

    world.para()
    world.say(
        f"{companion.label} smiled, then {RECONCILIATIONS['apology']}. "
        f"{hero.label} laughed too, and the two of them solved the little mystery together."
    )
    world.say(
        f"By the end, they decided to popular-ize the safe answer by telling everyone the clue was not a trick, "
        f"just a sign that needed a second look."
    )
    world.say(f"The old puzzle felt friendly now, and {hero.label} walked home less bashful than before.")

    hero.memes["relief"] = 1
    hero.memes["trust"] = 1
    companion.memes["trust"] = 1
    world.facts["solved"] = True
    world.facts["reconciled"] = True
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    place = f["place"]
    return [
        f"Write a mystery story for children about {hero.label} and a clue in {place.name}.",
        f"Tell a gentle story where a bashful child mistakes {clue.label} for something bigger, then learns the truth.",
        f"Write a short story with a misunderstanding, a funny moment, and a warm reconciliation at {place.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    clue = f["clue"]
    place = f["place"]
    mis = f["misunderstanding"]
    qa = [
        QAItem(
            question=f"Where did {hero.label} and {companion.label} go?",
            answer=f"They went to {place.name}, which felt {place.mood} and full of little clues.",
        ),
        QAItem(
            question=f"What made {companion.label} guess wrong at first?",
            answer=f"{MISUNDERSTANDINGS[mis]}. That was the misunderstanding that made the mystery feel bigger than it was.",
        ),
        QAItem(
            question=f"What helped the story turn from a mistake into a happy ending?",
            answer=f"{hero.label} told the truth, {companion.label} listened, and they reconciled by talking kindly and laughing together.",
        ),
        QAItem(
            question=f"What showed that the clue was still important near the end?",
            answer=f"The clue had permanence: it was still there when they looked again, so they knew the first guess had been wrong.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone guesses the wrong thing because the signs are confusing or incomplete.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make peace again after a disagreement or a mistake.",
        ),
        QAItem(
            question="Why can humor help in a hard moment?",
            answer="Humor can help because a small laugh can loosen worry and make it easier to talk kindly.",
        ),
        QAItem(
            question="What does permanence mean?",
            answer="Permanence means something stays in place for a long time instead of disappearing quickly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = ", ".join(f"{k}={v}" for k, v in ent.meters.items() if v)
        memes = ", ".join(f"{k}={v}" for k, v in ent.memes.items() if v)
        bits = []
        if meters:
            bits.append(meters)
        if memes:
            bits.append(memes)
        lines.append(f"{ent.id}: {ent.label or ent.type} [{' ; '.join(bits)}]")
    lines.append(f"place: {world.place.name}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
clue(C) :- clue_fact(C).
mismatch(M) :- misunderstanding(M).
funny(H) :- humor(H).

solved :- clue(C), permanence(C).
reconciled :- misunderstanding(M), funny(H), clue(C).

#show solved/0.
#show reconciled/0.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for key in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", key))
    for key in HUMOR:
        lines.append(asp.fact("humor", key))
    for place in PLACES.values():
        for clue in place.clues + place.hides:
            lines.append(asp.fact("clue_fact", clue.replace(" ", "_")))
    lines.append(asp.fact("permanence", "permanent_mark"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/0.\n#show reconciled/0."))
    symbols = {str(a) for a in model}
    ok = "solved" in symbols and "reconciled" in symbols
    if ok:
        print("OK: ASP twin produced the expected story-shape facts.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected facts.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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
    StoryParams(
        place="museum",
        hero_name="Mina",
        hero_type="girl",
        companion_name="Otis",
        companion_type="boy",
        clue="a glass case",
        misunderstanding="missing_label",
        humor="hat",
    ),
    StoryParams(
        place="library",
        hero_name="Lena",
        hero_type="girl",
        companion_name="Theo",
        companion_type="boy",
        clue="a bookmark",
        misunderstanding="bookmark",
        humor="echo",
    ),
    StoryParams(
        place="garden",
        hero_name="Ivy",
        hero_type="girl",
        companion_name="Noel",
        companion_type="boy",
        clue="a small gate",
        misunderstanding="hidden_path",
        humor="cat",
    ),
]


def resolve_explicit(args: argparse.Namespace) -> None:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.misunderstanding and args.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Unknown misunderstanding.")
    if args.humor and args.humor not in HUMOR:
        raise StoryError("Unknown humor choice.")


def main() -> None:
    args = build_parser().parse_args()
    resolve_explicit(args)

    if args.show_asp:
        print(asp_program("#show solved/0.\n#show reconciled/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/0.\n#show reconciled/0."))
        print("ASP model:")
        for atom in model:
            print(str(atom))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} at {p.place} with {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
