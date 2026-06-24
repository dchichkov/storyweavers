#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T073042Z_seed779406221_n50/haggis_status_suspense_lesson_learned_animal_story.py
===============================================================================================================================

A small standalone animal-story world about a status-fuss, a missing haggis,
suspense, and a lesson learned.

Premise:
- A little animal wants a high status prize for the supper table.
- The prize turns out to be missing.
- The search creates suspense.
- The ending proves what changed: the prize is found, shared, or replaced, and
  the animal learns a kinder lesson about status.

This script follows the Storyweavers world contract:
- stdlib-only single file
- typed entities with meters and memes
- state-driven prose
- Python reasonableness gate and inline ASP twin
- resolve_params / generate / emit / main
- QA sets and trace support
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
    location: str = ""
    plural: bool = False
    edible: bool = False
    prized: bool = False
    hidden: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("status", "suspense", "hunger", "relief", "kindness", "worry"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "cow", "sheep"}
        male = {"boy", "father", "dad", "man", "ram", "rooster", "he"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Animal:
    id: str
    type: str
    name: str
    title: str
    home: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    hidden: bool = False

    def __post_init__(self) -> None:
        for key in ("status", "suspense", "hunger", "relief", "kindness", "worry"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "cow", "sheep"}
        male = {"boy", "father", "dad", "man", "ram", "rooster", "he"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False
    supports: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    location: str
    status_value: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    location: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        import copy

        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def gate_ok(prize: Prize, clue: Clue) -> bool:
    return prize.location == clue.location


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for prize_id, prize in PRIZES.items():
        for clue_id, clue in CLUES.items():
            if gate_ok(prize, clue):
                combos.append((prize_id, clue_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    animal: str
    prize: str
    clue: str
    status_name: str
    seed: Optional[int] = None


SETTINGS = {
    "barn": Setting(place="the barn", indoor=True, supports={"search", "share"}),
    "hill": Setting(place="the windy hill", indoor=False, supports={"search", "share"}),
    "pond": Setting(place="the pond bank", indoor=False, supports={"search", "share"}),
}

ANIMALS = {
    "fox": Animal(id="fox", type="fox", name="Fenn", title="a clever fox", home="the burrow", traits=["quick", "proud"]),
    "rabbit": Animal(id="rabbit", type="rabbit", name="Pip", title="a small rabbit", home="the meadow", traits=["gentle", "curious"]),
    "bear": Animal(id="bear", type="bear", name="Moss", title="a patient bear", home="the den", traits=["steady", "kind"]),
}

PRIZES = {
    "haggis": Prize(
        id="haggis",
        label="haggis",
        phrase="a warm haggis for the supper table",
        location="the pantry",
        status_value=3,
        tags={"haggis", "food", "status"},
    ),
    "pie": Prize(
        id="pie",
        label="pie",
        phrase="a berry pie for the supper table",
        location="the pantry",
        status_value=2,
        tags={"pie", "food"},
    ),
    "cheese": Prize(
        id="cheese",
        label="cheese",
        phrase="a round wheel of cheese for the supper table",
        location="the pantry",
        status_value=1,
        tags={"cheese", "food"},
    ),
}

CLUES = {
    "pantry_note": Clue(
        id="pantry_note",
        label="note",
        phrase="a note by the pantry door",
        location="the pantry",
        tags={"note", "search"},
    ),
    "table_track": Clue(
        id="table_track",
        label="track",
        phrase="muddy tracks near the table",
        location="the pantry",
        tags={"track", "search"},
    ),
    "root_cellar": Clue(
        id="root_cellar",
        label="cellar note",
        phrase="a hint from the root cellar",
        location="the cellar",
        tags={"note", "search"},
    ),
}

STATUS_WORDS = {
    "status": "status",
    "lesson": "lesson learned",
    "share": "sharing",
    "kindness": "kindness",
}


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for sup in sorted(SETTINGS[sid].supports):
            lines.append(asp.fact("supports", sid, sup))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_loc", pid, prize.location))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_loc", cid, clue.location))
    return "\n".join(lines)


ASP_RULES = r"""
match(P,C) :- prize_loc(P,L), clue_loc(C,L).
valid(P,C) :- match(P,C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" python-only:", sorted(py - cl))
    print(" asp-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: haggis, status, suspense, lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--status-name", choices=list(STATUS_WORDS))
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
    combos = [c for c in valid_combos()
              if (args.prize is None or c[0] == args.prize)
              and (args.clue is None or c[1] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    prize, clue = rng.choice(sorted(combos))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    animal = args.animal or rng.choice(sorted(ANIMALS))
    status_name = args.status_name or "status"
    return StoryParams(setting=setting, animal=animal, prize=prize, clue=clue, status_name=status_name)


def introduce(world: World, animal: Animal, prize: Prize) -> None:
    animal.memes["status"] += 1
    world.say(f"{animal.name} was {animal.title}, and everyone in {world.setting.place} knew it.")
    world.say(f"{animal.name} loved {prize.label} because {prize.phrase} made a big feast feel important.")


def suspense(world: World, animal: Animal, clue: Clue, prize: Prize) -> None:
    animal.memes["worry"] += 1
    world.say(f"One quiet morning, {animal.name} found {clue.phrase}.")
    world.say(f"That meant the {prize.label} was missing, and the pantry felt very still.")
    world.say(f"{animal.name} looked under baskets, behind jars, and even near the door.")
    world.say(f"The longer the search went on, the more the tiny room filled with suspense.")


def reveal(world: World, animal: Animal, prize: Prize) -> None:
    prize.found = True
    prize.hidden = False
    animal.memes["relief"] += 1
    world.say(f"At last, {animal.name} found the {prize.label} tucked safely in a soft hay basket.")
    world.say(f"It had been hidden there to keep it warm, not lost forever.")


def lesson(world: World, animal: Animal, prize: Prize) -> None:
    animal.memes["kindness"] += 1
    animal.memes["status"] = 0
    world.say(f"{animal.name} smiled and shared the {prize.label} with the others instead of bragging.")
    world.say(f"That day, {animal.name} learned that true status came from being helpful, not from being bossy.")
    world.say(f"The little feast ended with warm bites, gentle laughs, and a calmer heart.")


def tell(setting: Setting, animal: Animal, prize: Prize, clue: Clue) -> World:
    world = World(setting)
    hero = world.add(Animal(**animal.__dict__))
    prize_ent = world.add(Entity(
        id=prize.id, kind="object", type="food", label=prize.label, phrase=prize.phrase,
        location=prize.location, prized=True, hidden=True, found=False,
        meters={"status": prize.status_value, "suspense": 0.0, "hunger": 0.0, "relief": 0.0},
        memes={"status": 0.0, "suspense": 0.0, "hunger": 0.0, "relief": 0.0, "kindness": 0.0, "worry": 0.0},
    ))
    clue_ent = world.add(Entity(
        id=clue.id, kind="thing", type="clue", label=clue.label, phrase=clue.phrase,
        location=clue.location, hidden=False, found=True,
    ))
    world.facts.update(hero=hero, prize=prize_ent, clue=clue_ent, setting=setting)

    introduce(world, hero, prize_ent)
    world.para()
    suspense(world, hero, clue_ent, prize_ent)
    world.para()
    reveal(world, hero, prize_ent)
    lesson(world, hero, prize_ent)
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero, prize, clue = f["hero"], f["prize"], f["clue"]
    return [
        f'Write a short animal story for a small child about {hero.name}, {prize.label}, and a missing surprise.',
        f"Tell a suspenseful but gentle story where {hero.name} searches for the {prize.label} after finding {clue.phrase}.",
        f'Write an animal story with the words "{prize.label}" and "{STATUS_WORDS["status"]}" that ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, prize, clue = f["hero"], f["prize"], f["clue"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.name}, {hero.title}, who cared a lot about the {prize.label}.",
        ),
        QAItem(
            question=f"What made the story suspenseful?",
            answer=f"The suspense came when {hero.name} found {clue.phrase} and the {prize.label} was missing for a little while.",
        ),
        QAItem(
            question=f"Where was the {prize.label} found?",
            answer=f"The {prize.label} was found tucked safely in a hay basket near the end of the search.",
        ),
        QAItem(
            question=f"What lesson did {hero.name} learn?",
            answer=f"{hero.name} learned that being kind and helpful matters more than acting high-status or showing off.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a haggis?",
            answer="A haggis is a warm, hearty food that can be served at supper, especially in a story about a special meal.",
        ),
        QAItem(
            question="What does status mean?",
            answer="Status means how important or respected someone seems in a group. In a good story, kindness matters more than status.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} {e.kind:8} meters={dict(e.meters)} memes={dict(e.memes)} hidden={getattr(e, 'hidden', False)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    if params.prize not in PRIZES or params.clue not in CLUES:
        raise StoryError("Invalid params.")
    if not gate_ok(PRIZES[params.prize], CLUES[params.clue]):
        raise StoryError("The clue does not fit the prize location.")
    world = tell(SETTINGS[params.setting], ANIMALS[params.animal], PRIZES[params.prize], CLUES[params.clue])
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
    StoryParams(setting="barn", animal="fox", prize="haggis", clue="pantry_note", status_name="status"),
    StoryParams(setting="hill", animal="rabbit", prize="haggis", clue="table_track", status_name="status"),
    StoryParams(setting="pond", animal="bear", prize="haggis", clue="pantry_note", status_name="status"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid prize/clue combos:")
        for p, c in combos:
            print(f"  {p:8} {c}")
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.animal} in {p.setting} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
