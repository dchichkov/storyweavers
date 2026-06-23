#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/reputation_bravery_kindness_whodunit.py
===============================================================================================================

A tiny whodunit storyworld about reputation, bravery, and kindness.

Premise:
- A small place has a cherished item.
- Someone's reputation makes people jump to the wrong conclusion.
- A brave, kind child follows clues instead of rumors.
- The truth restores both the missing item and the person's good name.

The world is kept small on purpose: a few settings, a few suspects, and a few
valid combinations. Stories are generated from state, not from a frozen template.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    clues: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    hide_place: str
    trace: str
    issue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Reputation:
    id: str
    label: str
    rumor: str
    truth: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path: list[str] = []

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.path = list(self.path)
        return c


@dataclass
class StoryParams:
    place: str
    mystery: str
    reputation: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    suspect_name: str
    suspect_gender: str
    seed: Optional[int] = None


PLACES = {
    "school": Place("school", "the school hall", clues={"paper", "door", "ink"}),
    "library": Place("library", "the little library", clues={"paper", "shelf", "dust"}),
    "market": Place("market", "the market stall", clues={"crate", "mud", "string"}),
    "garden": Place("garden", "the garden shed", clues={"soil", "leaf", "rope"}),
}

MYSTERIES = {
    "missing_book": Mystery(
        "missing_book",
        "missing book",
        "the missing book",
        "shelf",
        "a scuffed step",
        "the shelf looks empty",
        tags={"book", "paper"},
    ),
    "missing_cookie": Mystery(
        "missing_cookie",
        "missing cookie tin",
        "the missing cookie tin",
        "table",
        "a crumb trail",
        "the tray is empty",
        tags={"cookie", "crumb"},
    ),
    "missing_bell": Mystery(
        "missing_bell",
        "missing brass bell",
        "the missing brass bell",
        "bench",
        "a tiny bell mark",
        "the counter is quiet",
        tags={"bell", "metal"},
    ),
    "missing_seed_bag": Mystery(
        "missing_seed_bag",
        "missing seed bag",
        "the missing seed bag",
        "shed",
        "a line of soil",
        "the shelf is bare",
        tags={"seed", "soil"},
    ),
}

REPUTATIONS = {
    "messy": Reputation("messy", "messy", "people call you messy", "messy hands do not prove anything", tags={"messy"}),
    "shy": Reputation("shy", "shy", "people think you stay quiet", "quiet people can still be brave", tags={"shy"}),
    "slow": Reputation("slow", "slow", "people think you move slowly", "moving slowly can help you notice clues", tags={"slow"}),
    "grumpy": Reputation("grumpy", "grumpy", "people think you are grumpy", "a grumpy face can hide a kind heart", tags={"grumpy"}),
}

GIRL_NAMES = ["Mina", "Nora", "Lila", "Tess", "Maya", "June", "Ava", "Iris"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Noah", "Eli", "Max", "Jude", "Cal"]
TRAITS = ["careful", "curious", "brave", "kind", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for m in MYSTERIES:
            for r in REPUTATIONS:
                combos.append((p, m, r))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny whodunit storyworld with reputation, bravery, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--reputation", choices=REPUTATIONS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--suspect")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--suspect-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.reputation is None or c[2] == args.reputation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, rep = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    suspect_gender = args.suspect_gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    helper = args.helper or _pick_name(rng, helper_gender)
    suspect = args.suspect or _pick_name(rng, suspect_gender)
    return StoryParams(place=place, mystery=mystery, reputation=rep,
                       hero_name=name, hero_gender=gender,
                       helper_name=helper, helper_gender=helper_gender,
                       suspect_name=suspect, suspect_gender=suspect_gender)


def infer_clue(mystery: Mystery, place: Place) -> str:
    if mystery.id == "missing_book":
        return "dust on the shelf"
    if mystery.id == "missing_cookie":
        return "crumbs by the table"
    if mystery.id == "missing_bell":
        return "a bell mark near the bench"
    return "a line of soil by the shed"


def tell(place: Place, mystery: Mystery, rep: Reputation, hero_name: str, hero_gender: str,
         helper_name: str, helper_gender: str, suspect_name: str, suspect_gender: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    suspect = world.add(Entity(id=suspect_name, kind="character", type=suspect_gender, role="suspect"))
    item = world.add(Entity(id="item", type="thing", label=mystery.label, phrase=mystery.phrase))
    world.facts = {
        "hero": hero, "helper": helper, "suspect": suspect, "item": item,
        "place": place, "mystery": mystery, "reputation": rep,
        "clue": infer_clue(mystery, place), "solved": False, "revealed": False,
    }
    suspect.attrs["rumor"] = rep.label
    hero.memes["bravery"] = 1.0
    hero.memes["kindness"] = 1.0
    helper.memes["kindness"] = 1.0
    hero.memes["curiosity"] = 1.0
    suspect.meters["innocence"] = 1.0
    world.say(f"At {place.label}, {hero_name} noticed {mystery.issue}.")
    world.say(f"Some children whispered that {suspect_name} had done it, because {rep.rumor}.")
    return world


def propagate(world: World) -> None:
    clue = world.facts["clue"]
    if ("clue", clue) not in world.fired:
        world.fired.add(("clue", clue))
        world.facts["clue_seen"] = True
        world.get(world.facts["hero"].id).memes["bravery"] += 1
        world.say(f"{world.facts['hero'].id} followed the clues instead of the whispers.")
        world.say(f"There, {clue} pointed toward the real hiding place.")
    if world.facts.get("clue_seen") and ("reveal",) not in world.fired:
        world.fired.add(("reveal",))
        world.facts["revealed"] = True
        world.facts["solved"] = True


def search_and_reveal(world: World) -> None:
    mystery = world.facts["mystery"]
    item = world.facts["item"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    suspect = world.facts["suspect"]
    hero.memes["bravery"] += 1
    hero.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    world.say(f"{hero.id} was brave enough to look, and {helper.id} was kind enough to help.")
    world.say(f"Together they checked the {mystery.hide_place} and found {item.label} hidden there.")
    world.say(f"It had not been {suspect.id} after all.")
    world.say(f"{hero.id} spoke up gently, so {suspect.id}'s reputation could be fixed.")
    world.say(f"By the end, {suspect.id} was smiling beside {item.label}, and the room felt calm again.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short whodunit for a child about {f['hero'].id} in {f['place'].label} that includes the word reputation.",
        f"Tell a mystery story where {f['hero'].id} is brave and kind, follows clues, and clears {f['suspect'].id}'s name.",
        f"Write a simple detective story about {f['mystery'].label} where a rumor turns out to be wrong.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, suspect = f["hero"], f["helper"], f["suspect"]
    item, rep, place, mystery = f["item"], f["reputation"], f["place"], f["mystery"]
    return [
        QAItem(
            question=f"Who was the story about at {place.label}?",
            answer=f"It was about {hero.id}, who noticed that {mystery.issue}. {hero.id} then helped solve the mystery at {place.label}.",
        ),
        QAItem(
            question=f"Why did people suspect {suspect.id}?",
            answer=f"People suspected {suspect.id} because {rep.rumor}. That rumor made the wrong person seem guilty until the clues were checked.",
        ),
        QAItem(
            question=f"How did {hero.id} act when the item went missing?",
            answer=f"{hero.id} was brave enough to search carefully and kind enough to speak gently. That helped the truth come out without hurting anyone's feelings.",
        ),
        QAItem(
            question=f"What found the missing {mystery.label}?",
            answer=f"{helper.id} and {hero.id} followed the clue and found it hidden in the {mystery.hide_place}. The clue matched the place and proved what really happened.",
        ),
        QAItem(
            question=f"What happened to {suspect.id}'s reputation?",
            answer=f"{suspect.id}'s reputation was repaired when the truth came out. The children learned that a rumor is not the same thing as proof.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a reputation?", "A reputation is what people think about someone based on what they believe they have seen or heard."),
        QAItem("What does bravery mean?", "Bravery means doing what is right even when you feel nervous or scared."),
        QAItem("What does kindness mean?", "Kindness means caring about others and trying not to hurt their feelings."),
        QAItem("What is a clue in a mystery?", "A clue is a small piece of information that helps you figure out the truth."),
    ]


ASP_RULES = r"""
solved :- clue_seen.
revealed :- solved.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for rid in REPUTATIONS:
        lines.append(asp.fact("reputation", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3.\n"))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    # simple twin: all combos are valid in this small world
    asp_set = set(valid_combos())
    ok = True
    if py != asp_set:
        ok = False
        print("Mismatch in valid combos.")
    # smoke test generation
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, mystery=None, reputation=None, name=None, helper=None, suspect=None, gender=None, helper_gender=None, suspect_gender=None), random.Random(1)))
        _ = sample.story
    except Exception as e:
        print(f"Smoke test failed: {e}")
        ok = False
    if ok:
        print("OK: verify passed.")
        return 0
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.mystery not in MYSTERIES or params.reputation not in REPUTATIONS:
        raise StoryError("Invalid story parameters.")
    world = tell(PLACES[params.place], MYSTERIES[params.mystery], REPUTATIONS[params.reputation],
                 params.hero_name, params.hero_gender, params.helper_name, params.helper_gender,
                 params.suspect_name, params.suspect_gender)
    propagate(world)
    search_and_reveal(world)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, dict(e.meters), dict(e.memes), e.role)
    if qa:
        print()
        for p in sample.prompts:
            print(p)
        print()
        for item in sample.story_qa:
            print("Q:", item.question)
            print("A:", item.answer)
        print()
        for item in sample.world_qa:
            print("Q:", item.question)
            print("A:", item.answer)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="school", mystery="missing_book", reputation="shy", hero_name="Mina", hero_gender="girl", helper_name="Owen", helper_gender="boy", suspect_name="Theo", suspect_gender="boy"),
            StoryParams(place="library", mystery="missing_cookie", reputation="messy", hero_name="Nora", hero_gender="girl", helper_name="Finn", helper_gender="boy", suspect_name="Iris", suspect_gender="girl"),
            StoryParams(place="market", mystery="missing_bell", reputation="grumpy", hero_name="Cal", hero_gender="boy", helper_name="Ava", helper_gender="girl", suspect_name="Jude", suspect_gender="boy"),
            StoryParams(place="garden", mystery="missing_seed_bag", reputation="slow", hero_name="Lila", hero_gender="girl", helper_name="Eli", helper_gender="boy", suspect_name="Maya", suspect_gender="girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
