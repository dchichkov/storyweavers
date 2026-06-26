#!/usr/bin/env python3
"""
storyworlds/worlds/symmetry_curiosity_suspense_moral_value_mystery.py
=====================================================================

A standalone story world about a small mystery built from symmetry, curiosity,
suspense, and moral value.

Premise:
A child notices a strange symmetrical pattern in a quiet place, follows the
clues, worries about what they mean, and discovers that being careful and
honest matters more than making a quick guess.

The simulated world tracks:
- physical meters: distance, hiddenness, matchedness, disorder, brightness
- emotional memes: curiosity, suspense, worry, relief, moral_value, trust

The story is intentionally compact and child-facing, with a clear beginning,
middle turn, and resolution image proving what changed.
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
    pair: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        if self.type in {"girl", "woman", "mother"}:
            return "she"
        if self.type in {"boy", "man", "father"}:
            return "he"
        return "it"

    def possessive(self) -> str:
        if self.type in {"girl", "woman", "mother"}:
            return "her"
        if self.type in {"boy", "man", "father"}:
            return "his"
        return "its"


@dataclass
class Place:
    id: str
    label: str
    hush: str
    symmetry_kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    pair: str
    reveal: str
    risk: str
    moral: str


@dataclass
class StoryParams:
    place: str
    clue: str
    hero_name: str
    hero_gender: str
    companion_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.observed_pattern = False
        self.suspicious_gap = False
        self.truth_found = False

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


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.entities.values() if e.kind == "character"), None)
    if hero is None:
        return out
    if hero.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    sig = ("curiosity", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.observed_pattern = True
    _add_meter(hero, "attention", 1.0)
    out.append(f"{hero.label} leaned closer, because the pattern looked too neat to ignore.")
    return out


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.entities.values() if e.kind == "character"), None)
    clue = world.entities.get("clue")
    if hero is None or clue is None:
        return out
    if not world.observed_pattern:
        return out
    if world.suspicious_gap:
        return out
    sig = ("suspense", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.suspicious_gap = True
    _add_meme(hero, "suspense", 1.0)
    _add_meme(hero, "worry", 1.0)
    out.append("But one side of the clue did not match the other, and that made the room feel quiet and tense.")
    return out


def _r_truth(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.entities.values() if e.kind == "character"), None)
    clue = world.entities.get("clue")
    if hero is None or clue is None:
        return out
    if not world.suspicious_gap:
        return out
    sig = ("truth", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.truth_found = True
    _add_meter(clue, "matchedness", 1.0)
    _add_meme(hero, "relief", 1.0)
    _add_meme(hero, "moral_value", 1.0)
    out.append("When the missing piece was found, the whole clue made sense at last.")
    return out


CAUSAL_RULES = [_r_curiosity, _r_suspense, _r_truth]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    spoken: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                spoken.extend(sents)
    if narrate:
        for s in spoken:
            world.say(s)


PLACES = {
    "hallway": Place(
        id="hallway",
        label="the hallway",
        hush="quiet",
        symmetry_kind="mirror",
        affords={"look", "search"},
    ),
    "garden": Place(
        id="garden",
        label="the garden path",
        hush="still",
        symmetry_kind="stone",
        affords={"look", "search"},
    ),
    "attic": Place(
        id="attic",
        label="the attic",
        hush="dusty",
        symmetry_kind="window",
        affords={"look", "search"},
    ),
}

CLUES = {
    "mirror_token": Clue(
        id="mirror_token",
        label="a mirror token",
        phrase="a small silver token with two matching sides",
        pair="left and right halves",
        reveal="it belonged with the other half of the token",
        risk="someone had dropped it and left the story unfinished",
        moral="it was better to look carefully than to jump to a mean guess",
    ),
    "shell_stone": Clue(
        id="shell_stone",
        label="a shell stone",
        phrase="a smooth stone with a shell mark on each side",
        pair="two shell marks",
        reveal="the marks lined up with the old box lock",
        risk="the stone had been moved and its partner was missing",
        moral="a fair guess needs both clues, not just one",
    ),
    "ribbon_key": Clue(
        id="ribbon_key",
        label="a ribbon key",
        phrase="a brass key tied with a blue ribbon and a twin notch",
        pair="two notches",
        reveal="the twin notch fit a tiny lock on the drawer",
        risk="the ribbon had been cut off one side",
        moral="honest hands put things back where they belong",
    ),
}

NAMES_GIRL = ["Mia", "Nora", "Lina", "Ruby", "Ivy", "Tessa"]
NAMES_BOY = ["Eli", "Noah", "Owen", "Ben", "Theo", "Arlo"]
COMPANIONS = ["grandma", "dad", "teacher", "older sister", "neighbor"]
TRAITS = ["careful", "curious", "gentle", "brave", "thoughtful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery about symmetry, curiosity, suspense, and moral value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
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


def _hero_pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "girl":
        return "she", "her", "her"
    return "he", "him", "his"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gender and args.name is None:
        pass

    choices = []
    for place in (args.place,) if args.place else PLACES:
        for clue in (args.clue,) if args.clue else CLUES:
            choices.append((place, clue))
    if not choices:
        raise StoryError("No valid story choices.")
    place, clue = rng.choice(choices)

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(place=place, clue=clue, hero_name=name, hero_gender=gender, companion_name=companion)


def tell(place: Place, clue: Clue, hero_name: str, hero_gender: str, companion_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name))
    companion = world.add(Entity(id="companion", kind="character", type="adult", label=companion_name))
    token = world.add(Entity(id="clue", type="object", label=clue.label, phrase=clue.phrase))

    _add_meme(hero, "curiosity", 1.0)
    _add_meme(hero, "moral_value", 0.5)

    world.say(f"{hero.label} was {TRAITS[hash(hero_name) % len(TRAITS)]} and noticed that {place.label} felt especially quiet.")
    world.say(f"On a shelf, {hero.label} saw {clue.phrase}, and the two sides looked almost the same.")
    world.para()

    world.say(f"{hero.label} asked {companion.label if companion_name else 'someone nearby'} about it, because {hero.pronoun()} liked to solve small puzzles.")
    world.say(f"But the clue had a gap, and that made the room feel like it was holding its breath.")
    propagate(world)
    world.para()

    if world.truth_found:
        world.say(f"After a careful search, {hero.label} found the missing piece beside a dusty book.")
        world.say(f"It fit the other side at once, and {clue.reveal}.")
        world.say(f"{hero.label} chose to put it back instead of claiming it, because {clue.moral}.")
        world.say(f"At the end, the clue was whole again, and {hero.label} smiled with quiet relief.")
    else:
        world.say(f"{hero.label} kept looking until the pattern made sense, and the answer came gently.")
    world.facts.update(
        hero=hero,
        companion=companion,
        clue=token,
        clue_def=clue,
        place=place,
        observed=world.observed_pattern,
        suspense=world.suspicious_gap,
        resolved=world.truth_found,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue_def"]
    return [
        f'Write a short mystery for a young child about {hero.label} noticing symmetry in {f["place"].label}.',
        f'Tell a gentle story where curiosity leads {hero.label} to a clue and suspense grows before the missing piece is found.',
        f'Write a simple story about doing the honest thing when a neat, symmetrical clue turns out to belong somewhere else.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue_def"]
    place = f["place"]
    pron, obj, pos = _hero_pronouns(hero.type)
    return [
        QAItem(
            question=f"What did {hero.label} notice in {place.label}?",
            answer=f"{hero.label} noticed {clue.phrase}, and the matching sides made the clue look like a little symmetry puzzle.",
        ),
        QAItem(
            question=f"Why did the story feel suspenseful after {hero.label} looked closer?",
            answer=f"It felt suspenseful because one side did not match the other, so the clue seemed unfinished and the answer was still hidden.",
        ),
        QAItem(
            question=f"What was the moral value in {hero.label}'s choice at the end?",
            answer=f"The moral value was honesty and care: {hero.label} put the found piece back where it belonged instead of taking it.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is symmetry?",
            answer="Symmetry means two sides match in a balanced way, like a mirror image or a neat pair of shapes.",
        ),
        QAItem(
            question="What does curiosity do in a mystery?",
            answer="Curiosity makes someone keep looking and asking questions until the clues make sense.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the tense feeling that happens when the answer is not known yet.",
        ),
    ]


ASP_RULES = r"""
symmetry(Obj) :- clue(Obj), matching_sides(Obj).
curious(H) :- hero(H), wants_to_know(H).
suspenseful(H) :- curious(H), not solved.
moral(H) :- hero(H), returned_missing_piece(H).
valid_story(P, C) :- place(P), clue(C), symmetry(C), curious(hero), suspenseful(hero), moral(hero).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
        lines.append(asp.fact("matching_sides", c))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("wants_to_know", "hero"))
    lines.append(asp.fact("returned_missing_piece", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    atoms = set(asp.atoms(model, "valid_story"))
    expected = {(p, c) for p in PLACES for c in CLUES}
    if atoms == expected:
        print(f"OK: ASP matches Python registry ({len(atoms)} stories).")
        return 0
    print("MISMATCH between ASP and Python registries.")
    print("only in ASP:", sorted(atoms - expected))
    print("only in Python:", sorted(expected - atoms))
    return 1


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    world = tell(place, clue, params.hero_name, params.hero_gender, params.companion_name)
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
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"{e.id}: {e.label} {', '.join(bits)}")
    if qa:
        print("\n== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(place="hallway", clue="mirror_token", hero_name="Mia", hero_gender="girl", companion_name="grandma"),
    StoryParams(place="attic", clue="ribbon_key", hero_name="Eli", hero_gender="boy", companion_name="dad"),
    StoryParams(place="garden", clue="shell_stone", hero_name="Nora", hero_gender="girl", companion_name="teacher"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < max(1, args.n) and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            p = sample.params
            print(f"### variant {idx + 1}: {p.hero_name} in {p.place} with {p.clue}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
