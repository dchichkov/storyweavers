#!/usr/bin/env python3
"""
storyworlds/worlds/french_mystery_to_solve_adventure.py
=======================================================

A small adventure storyworld about a child who follows clues, asks gentle
questions, and solves a little mystery in a French-flavored place.

Seed tale idea:
---
A curious child arrives at a lively place with a missing item to find.
The first clue seems small, but it leads to a second clue and then a turn.
A helper shares one last detail, and the child solves the mystery and
returns home proud.

This world models:
- a hero with a need to solve a mystery
- a place with clues, a keeper, and a missing thing
- an adventure path of looking, asking, comparing, and discovering
- emotional change from worry to excitement to relief
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    france_hint: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing: str
    label: str
    phrase: str
    clue1: str
    clue2: str
    final_place: str
    keeper_hint: str
    reason: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "bakery": Setting(place="the little bakery", france_hint="a warm French bakery", affords={"find"}),
    "garden": Setting(place="the quiet garden", france_hint="a French garden with stone paths", affords={"find"}),
    "museum": Setting(place="the small museum", france_hint="a French museum with tall windows", affords={"find"}),
    "market": Setting(place="the busy market", france_hint="a French market with bright stalls", affords={"find"}),
}

MYSTERIES = {
    "missing_baguette": Mystery(
        id="missing_baguette",
        missing="baguette",
        label="the baguette",
        phrase="a long crusty baguette",
        clue1="a trail of flour near the door",
        clue2="a tiny basket by the window",
        final_place="the oven shelf",
        keeper_hint="the baker",
        reason="it had been moved to keep it warm",
        tags={"bread", "french", "bakery"},
    ),
    "missing_postcard": Mystery(
        id="missing_postcard",
        missing="postcard",
        label="the postcard",
        phrase="a picture postcard with a blue boat",
        clue1="a stamp on the floor near the desk",
        clue2="a map with a corner folded over",
        final_place="the front pocket of a coat",
        keeper_hint="the museum guide",
        reason="someone tucked it away to keep it safe",
        tags={"museum", "map", "french"},
    ),
    "missing_key": Mystery(
        id="missing_key",
        missing="key",
        label="the little key",
        phrase="a tiny brass key",
        clue1="a jingling sound by the bench",
        clue2="a ribbon tied near a chair",
        final_place="a tray behind the counter",
        keeper_hint="the shop helper",
        reason="it had rolled into a tray during the morning rush",
        tags={"key", "market", "french"},
    ),
}

GENDERS = {"girl", "boy"}
NAMES = {
    "girl": ["Lina", "Mila", "Nora", "Clara", "Zoe"],
    "boy": ["Leo", "Noah", "Theo", "Max", "Eli"],
}
HELPERS = ["mother", "father", "aunt", "uncle"]


def reasonableness_gate(setting: Setting, mystery: Mystery) -> bool:
    return "find" in setting.affords and "french" in mystery.tags


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTINGS:
        for mid in MYSTERIES:
            if reasonableness_gate(SETTINGS[place], MYSTERIES[mid]):
                out.append((place, mid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle French-flavored mystery adventure.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.place and args.mystery:
        if not reasonableness_gate(SETTINGS[args.place], MYSTERIES[args.mystery]):
            raise StoryError("No story: this place cannot honestly host that mystery.")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("No valid mystery matches the given options.")

    place, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(GENDERS))
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, helper=helper)


def introduce(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} arrived at {world.setting.place}, a {world.setting.france_hint}, "
        f"with a little mystery to solve."
    )
    world.say(
        f"{hero.pronoun().capitalize()} was looking for {mystery.phrase}, and {hero.pronoun('possessive')} "
        f"{helper.id} stayed close with a calm smile."
    )


def look_for_clue(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    hero.meters["search"] = hero.meters.get("search", 0) + 1
    world.say(
        f"{hero.id} looked carefully and found {mystery.clue1}."
    )


def ask_for_help(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    hero.memes["brave"] = hero.memes.get("brave", 0) + 1
    world.say(
        f"{hero.id} asked, \"Bonjour, have you seen {mystery.label}?\""
    )
    world.say(
        f"{helper.id} pointed to {mystery.clue2} and said it was a good next clue."
    )


def follow_clues(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.meters["clues"] = hero.meters.get("clues", 0) + 1
    world.say(
        f"{hero.id} followed the clue trail past the tables and into the quiet back corner."
    )
    world.say(
        f"There, {mystery.final_place} made the mystery feel nearly solved."
    )


def solve(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    hero.memes["worry"] = 0
    world.say(
        f"At last, {hero.id} found {mystery.label} where it belonged."
    )
    world.say(
        f"It had been there because {mystery.reason}. {helper.id} laughed softly and said, "
        f"\"Bien joué!\""
    )
    world.say(
        f"{hero.id} held up {mystery.label} proudly, and the whole place felt bright again."
    )


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_type.capitalize(), kind="character", type=helper_type))
    obj = world.add(Entity(id=mystery.missing, type=mystery.missing, label=mystery.label, phrase=mystery.phrase))
    world.facts.update(hero=hero, helper=helper, mystery=mystery, object=obj, setting=setting)

    introduce(world, hero, helper, mystery)
    world.para()
    look_for_clue(world, hero, mystery)
    ask_for_help(world, hero, helper, mystery)
    world.para()
    follow_clues(world, hero, mystery)
    solve(world, hero, helper, mystery)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mystery = f["hero"], f["mystery"]
    return [
        f'Write a short adventure story for a young child about a French mystery with the word "french".',
        f"Tell a gentle mystery story where {hero.id} searches for {mystery.label} and solves it with help.",
        f"Write a simple adventure story set at {world.setting.place} with clues, a helper, and a happy solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, mystery = f["hero"], f["helper"], f["mystery"]
    return [
        QAItem(
            question=f"Who went to {world.setting.place} to solve the mystery?",
            answer=f"It was {hero.id}, with {helper.id} nearby to help.",
        ),
        QAItem(
            question=f"What was {hero.id} looking for?",
            answer=f"{hero.id} was looking for {mystery.phrase}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} keep going?",
            answer=f"{mystery.clue1} was the first clue, and {mystery.clue2} helped point to the answer.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"{hero.id} found {mystery.label} in {mystery.final_place}, and the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bonjour mean?",
            answer="Bonjour is a French word people often use to say hello.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure something out.",
        ),
        QAItem(
            question="What is an adventure story?",
            answer="An adventure story is a story about going somewhere, trying something brave, and discovering what happens.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_mystery(M) :- mystery(M), french_tag(M).
valid_story(P,M) :- afford_find(P), valid_mystery(M).
#show valid_story/2.
#show valid_place/1.
#show valid_mystery/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        if "find" in SETTINGS[p].affords:
            lines.append(asp.fact("afford_find", p))
    for m in MYSTERIES.values():
        lines.append(asp.fact("mystery", m.id))
        if "french" in m.tags:
            lines.append(asp.fact("french_tag", m.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set((p, m) for p, m in valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in asp:", sorted(asp_set - py_set))
    print("only in py:", sorted(py_set - asp_set))
    return 1


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} ({e.kind:8}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bakery", mystery="missing_baguette", name="Lina", gender="girl", helper="mother"),
    StoryParams(place="museum", mystery="missing_postcard", name="Theo", gender="boy", helper="aunt"),
    StoryParams(place="market", mystery="missing_key", name="Mila", gender="girl", helper="father"),
]


def explain_rejection(place: str, mystery: str) -> str:
    return f"(No story: {place} cannot honestly host {mystery} as a French mystery adventure.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], params.name, params.gender, params.helper)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, mystery in combos:
            print(f"  {place:8} {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
