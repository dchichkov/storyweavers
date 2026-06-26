#!/usr/bin/env python3
"""
storyworlds/worlds/vacuum_sneeze_insistent_construction_site_mystery_to.py
=========================================================================

A standalone story world for a small construction-site mystery.

Seed tale sketch:
---
At a busy construction site, a child named Nia keeps hearing a strange sneeze-like puff
near the new rooms. Her big brother says it is only a loose hose, but Nia notices the
dust trail moves when the old vacuum cart turns on by itself. She is insistent that
something at the site is wrong.

Nia and her helper follow the clues: a dusty toolbox, a scraped wheel, and a sneaky
path of plaster crumbs. In the end, they find the vacuum hose was clogged with chalk
dust, which made it cough and puff like a sneeze. Once they clear it, the mystery is
solved and the site feels calm again.

World model:
---
- Physical meters: dust, noise, clutter, repair, airflow
- Emotional memes: curiosity, worry, insistence, relief, trust

Narrative shape:
---
Setup -> a strange sound and a stubborn child
Turn  -> clues accumulate; the wrong explanation fails
Resolution -> the true cause is found and fixed
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
# World data
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
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
class Site:
    place: str = "the construction site"
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue_noun: str
    odd_sound: str
    suspect: str
    true_cause: str
    fix: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    site: str
    mystery: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, site: Site) -> None:
        self.site = site
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

    def copy(self) -> "World":
        import copy
        clone = World(self.site)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SITE = Site(place="the construction site", affords={"vacuum"})

MYSTERIES = {
    "vacuum_sneeze": Mystery(
        id="vacuum_sneeze",
        clue_noun="dust",
        odd_sound="a sneeze-like puff",
        suspect="a worker",
        true_cause="a clogged vacuum hose",
        fix="clear the hose",
        reveal="the vacuum was sneezing dust because its hose was clogged",
        tags={"vacuum", "sneeze", "dust", "mystery"},
    ),
}

GIRL_NAMES = ["Nia", "Mina", "Lina", "Sana", "Tess", "Maya"]
BOY_NAMES = ["Owen", "Jude", "Eli", "Noah", "Finn", "Leo"]
HELPERS = ["big brother", "big sister", "dad", "mom", "uncle", "aunt"]
TRAITS = ["curious", "brave", "careful", "insistent", "sharp-eyed", "patient"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def clue_chain(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"At {world.site.place}, {hero.id} was a {next(t for t in hero.memes if False),}"
    )


def setup_story(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["insistence"] = hero.memes.get("insistence", 0) + 1
    world.say(
        f"At {world.site.place}, {hero.id} was a {hero.label} child with a {hero.traits[0]} mind."
    )
    world.say(
        f"{hero.pronoun().capitalize()} kept hearing {mystery.odd_sound} near the half-built rooms."
    )
    world.say(
        f"{hero.id} thought the sound might be {mystery.suspect}, but {hero.pronoun('possessive')} "
        f"{helper.label} kept saying to wait."
    )


def investigate(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    hero.memes["insistence"] += 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.para()
    world.say(
        f"But {hero.id} was insistent. {hero.pronoun().capitalize()} followed the sound past the stacked boards and buckets."
    )
    world.say(
        f"There, {hero.pronoun().capitalize()} noticed {mystery.clue_noun} on the floor and a vacuum cart humming nearby."
    )
    world.say(
        f"When the vacuum started, it gave another {mystery.odd_sound}, and the dusty trail puffed out again."
    )


def reveal_fix(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    world.para()
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    helper.memes["trust"] = helper.memes.get("trust", 0) + 1
    world.say(
        f"{hero.id} pointed to the hose and said the clues fit: {mystery.true_cause}."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {helper.label} knelt down, {mystery.fix}, and the puffing stopped."
    )
    world.say(
        f"At last, everyone saw that {mystery.reveal}. The construction site grew quiet again, and {hero.id} smiled."
    )


def tell(params: StoryParams) -> World:
    world = World(SITE)
    mystery = MYSTERIES[params.mystery]

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.gender == "girl" else "boy",
        label=params.trait,
        phrasestr := "",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper if params.helper in {"mother", "father"} else "adult",
        label=params.helper,
    ))
    vacuum = world.add(Entity(
        id="vacuum",
        type="vacuum",
        label="vacuum cart",
        phrase="an old vacuum cart",
    ))

    hero.traits = [params.trait]
    hero.memes = {"curiosity": 0.0, "insistence": 0.0, "worry": 0.0, "relief": 0.0, "trust": 0.0}
    helper.memes = {"trust": 0.0}

    setup_story(world, hero, helper, mystery)
    investigate(world, hero, helper, mystery)
    reveal_fix(world, hero, helper, mystery)

    world.facts = {
        "hero": hero,
        "helper": helper,
        "mystery": mystery,
        "vacuum": vacuum,
        "params": params,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f'Write a short mystery story for a child named {hero.id} at a construction site where a vacuum makes {mystery.odd_sound}.',
        f"Tell a simple story in which {hero.id} is insistent about finding out why the vacuum sounds strange.",
        f"Write a child-facing mystery story that begins with clues, includes a vacuum, and ends with the real cause being fixed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"What strange sound kept bothering {hero.id} at the construction site?",
            answer=f"{hero.id} kept hearing {mystery.odd_sound} near the half-built rooms.",
        ),
        QAItem(
            question=f"Why was {hero.id} so insistent about investigating?",
            answer=f"{hero.id} was insistent because the sound felt wrong, and {hero.pronoun('subject')} wanted to solve the mystery instead of walking away.",
        ),
        QAItem(
            question=f"What was the real cause of the mystery?",
            answer=f"The real cause was {mystery.true_cause}.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{hero.id} and the {helper.label} cleared the hose, and the vacuum stopped making the strange puffing sound.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vacuum for?",
            answer="A vacuum is a machine that sucks up dust and little bits from the floor.",
        ),
        QAItem(
            question="What does insistent mean?",
            answer="Insistent means not giving up when you believe something important needs attention.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that seems puzzling at first, so people gather clues to figure it out.",
        ),
        QAItem(
            question="Why can dust make a machine noisy?",
            answer="Dust can block moving parts or airflow, which can make a machine sound strange or work badly.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is worth solving when the hero hears an odd sound and has high insistence.
mystery_worth_solving(M) :- mystery(M), clue(M, _), sound(M, _), insistence(hero, I), I >= 1.

% The true cause is accepted when the hose is clogged and the vacuum makes a sneeze-like puff.
solved(M) :- mystery(M), cause(M, clogged_hose), sound(M, sneeze_puff), fix(M, clear_hose).

#show mystery_worth_solving/1.
#show solved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue_noun))
        lines.append(asp.fact("sound", mid, "sneeze_puff"))
        lines.append(asp.fact("cause", mid, "clogged_hose"))
        lines.append(asp.fact("fix", mid, "clear_hose"))
    lines.append("insistence(hero,1).")
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    shown = set((sym.name, tuple(a.name if hasattr(a, "name") else getattr(a, "number", None) for a in sym.arguments)) for sym in model)
    if ("mystery_worth_solving", ("vacuum_sneeze",)) in shown and ("solved", ("vacuum_sneeze",)) in shown:
        print("OK: ASP gate agrees with the Python story logic.")
        return 0
    print("MISMATCH: ASP gate did not derive the expected mystery result.")
    return 1


# ---------------------------------------------------------------------------
# Parser / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Construction-site mystery story world.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--mystery", choices=MYSTERIES)
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
    mystery = args.mystery or "vacuum_sneeze"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(site="construction_site", mystery=mystery, name=name, gender=gender, helper=helper, trait=trait)


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


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
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


CURATED = [
    StoryParams(site="construction_site", mystery="vacuum_sneeze", name="Nia", gender="girl", helper="big brother", trait="curious"),
    StoryParams(site="construction_site", mystery="vacuum_sneeze", name="Owen", gender="boy", helper="dad", trait="insistent"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        for sym in model:
            print(sym)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.site}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
