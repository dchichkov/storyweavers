#!/usr/bin/env python3
"""
A small story world for a detective-style tale about a recyclable item,
guided by inner monologue and a simple, state-driven mystery.

Premise:
- A child detective notices a recyclable item that should be in the blue bin.
- The item goes missing, making a small mystery.
- The detective thinks through clues silently, then acts.
- The ending proves the item was sorted correctly and the worry is gone.

This world stays tiny on purpose: fewer choices, stronger causality.
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
# Model
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
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outdoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    seen_in: str
    points_to: str
    helpful: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    location: str
    recyclable: bool = True


@dataclass
class StoryParams:
    setting: str
    clue: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", outdoors=False, affords={"sorting", "search"}),
    "alley": Setting(place="the alley behind the café", outdoors=True, affords={"search"}),
    "garage": Setting(place="the garage", outdoors=False, affords={"sorting", "search"}),
    "yard": Setting(place="the yard", outdoors=True, affords={"search", "sorting"}),
}

CLUES = {
    "cap": Clue(
        id="cap",
        label="a bottle cap",
        seen_in="near the sink",
        points_to="the blue bin",
        helpful="It matched the bottle and showed the item should be sorted with recyclables.",
    ),
    "label": Clue(
        id="label",
        label="a paper label",
        seen_in="by the trash can",
        points_to="the pantry shelf",
        helpful="It showed the object had once held juice, which made it a recyclable container.",
    ),
    "scrape": Clue(
        id="scrape",
        label="a small scrape of shiny paint",
        seen_in="on the counter",
        points_to="the back porch",
        helpful="It suggested the missing thing had been moved in a hurry and left a shiny trail.",
    ),
}

PRIZES = {
    "can": Prize(
        id="can",
        label="aluminum can",
        phrase="a clean recyclable aluminum can",
        location="the blue bin",
        recyclable=True,
    ),
    "bottle": Prize(
        id="bottle",
        label="plastic bottle",
        phrase="a clear recyclable bottle",
        location="the blue bin",
        recyclable=True,
    ),
    "box": Prize(
        id="box",
        label="cardboard box",
        phrase="a folded recyclable cardboard box",
        location="the recycling stack",
        recyclable=True,
    ),
}

GIRL_NAMES = ["Mina", "Tara", "Lila", "Noa", "June", "Ivy", "Sara"]
BOY_NAMES = ["Eli", "Owen", "Milo", "Finn", "Theo", "Arlo", "Ben"]
TRAITS = ["curious", "careful", "quiet", "sharp-eyed", "patient"]

parents = {"mother": "mom", "father": "dad"}


# ---------------------------------------------------------------------------
# Reasonableness and ASP twin
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_name, setting in SETTINGS.items():
        for c_name, clue in CLUES.items():
            for p_name, prize in PRIZES.items():
                if setting.affords & {"search", "sorting"} and prize.recyclable and clue.points_to:
                    combos.append((s_name, c_name, p_name))
    return combos


def explain_rejection(setting: str, clue: str, prize: str) -> str:
    return (
        f"(No story: that combination does not support a believable detective turn. "
        f"Try a different setting, clue, or recyclable item.)"
    )


ASP_RULES = r"""
setting(kitchen). setting(alley). setting(garage). setting(yard).
affords(kitchen,search). affords(kitchen,sorting).
affords(alley,search).
affords(garage,search). affords(garage,sorting).
affords(yard,search). affords(yard,sorting).

clue(cap). clue(label). clue(scrape).
points_to(cap,blue_bin).
points_to(label,pantry_shelf).
points_to(scrape,back_porch).

prize(can). prize(bottle). prize(box).
recyclable(can). recyclable(bottle). recyclable(box).

valid(S,C,P) :- setting(S), clue(C), prize(P), affords(S,search), recyclable(P), points_to(C,_).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s_name, setting in SETTINGS.items():
        lines.append(asp.fact("setting", s_name))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", s_name, a))
    for c_name, clue in CLUES.items():
        lines.append(asp.fact("clue", c_name))
        lines.append(asp.fact("points_to", c_name, clue.points_to))
    for p_name, prize in PRIZES.items():
        lines.append(asp.fact("prize", p_name))
        if prize.recyclable:
            lines.append(asp.fact("recyclable", p_name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def investigate(world: World, hero: Entity, clue: Clue, prize: Entity) -> None:
    hero.memes["focus"] = hero.memes.get("focus", 0) + 1
    hero.memes["uncertainty"] = hero.memes.get("uncertainty", 0) + 1
    world.say(
        f"{hero.id} found {clue.label} {clue.seen_in} and looked at it like a small detective."
    )
    world.say(
        f"Inside {hero.pronoun('possessive')} head, {hero.pronoun('subject')} thought, "
        f"“If I follow this clue, I can find the missing {prize.label}.”"
    )


def search_scene(world: World, hero: Entity, parent: Entity, clue: Clue, prize: Entity) -> None:
    world.say(
        f"At {world.setting.place}, {hero.id} and {hero.pronoun('possessive')} {parent.type} "
        f"searched carefully."
    )
    world.say(
        f"{hero.pronoun().capitalize()} checked low shelves, the bin, and the floor, listening to "
        f"the tiny clink of anything metallic."
    )
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    if prize.location == clue.points_to:
        world.say(
            f"Then {hero.id} saw the {prize.label} where the clue had pointed: {prize.location}."
        )
    else:
        world.say(
            f"Then {hero.id} noticed something else useful, but the real answer still felt close."
        )


def inner_monologue(world: World, hero: Entity, clue: Clue, prize: Entity) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} thought, “A {clue.label} near the sink, a recyclable {prize.label}, "
        f"and a blue bin nearby. That is no accident.”"
    )
    world.say(
        f"“Someone meant to sort it,” {hero.pronoun('subject')} thought, “so the missing thing must be hiding "
        f"where it belongs.”"
    )


def reveal(world: World, hero: Entity, parent: Entity, prize: Entity) -> None:
    hero.memes["clarity"] = hero.memes.get("clarity", 0) + 1
    prize.location = "the blue bin"
    world.say(
        f"{hero.id} lifted the lid, and there it was: {prize.phrase} waiting in the blue bin."
    )
    world.say(
        f"{hero.id}'s {parent.type} smiled and said the little detective had solved the case."
    )


def resolve(world: World, hero: Entity, parent: Entity, prize: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"In the end, the room looked neat again, the recyclable {prize.label} was in its proper place, "
        f"and {hero.id} felt proud and calm."
    )
    world.say(
        f"{hero.id} stood still for a moment, enjoying the quiet feeling that comes after a mystery is solved."
    )


def tell(setting: Setting, clue: Clue, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(
        id=prize_cfg.id,
        type=prize_cfg.id,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        location="missing",
    ))

    world.say(
        f"{hero.id} was a little {trait} {hero.type} who liked to solve small mysteries."
    )
    world.say(
        f"{hero.id} especially liked things that were neat, sorted, and recyclable."
    )
    world.para()

    investigate(world, hero, clue, prize)
    inner_monologue(world, hero, clue, prize)
    world.para()

    search_scene(world, hero, parent, clue, prize)
    world.para()

    reveal(world, hero, parent, prize)
    world.para()

    resolve(world, hero, parent, prize)

    world.facts = {
        "hero": hero,
        "parent": parent,
        "prize": prize,
        "clue": clue,
        "setting": setting,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    clue = f["clue"]
    return [
        f'Write a short detective story for a child about a recyclable {prize.label} and a small clue.',
        f"Tell a gentle mystery where {hero.id} thinks carefully about {clue.label} and finds the missing {prize.label}.",
        f'Write a story with inner monologue where a child detective solves a recyclable-object mystery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    clue = f["clue"]
    qa = [
        QAItem(
            question=f"What kind of story is this about {hero.id}?",
            answer=f"It is a small detective story about {hero.id}, who uses clues and careful thinking to find a recyclable {prize.label}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} think about where the {prize.label} belonged?",
            answer=f"{clue.label} helped {hero.id} think about the missing {prize.label}. It pointed toward {clue.points_to}, which made the answer feel clear.",
        ),
        QAItem(
            question=f"What did {hero.id} think inside {hero.pronoun('possessive')} head before the answer was found?",
            answer=f"{hero.id} thought that the clue and the recyclable {prize.label} were connected, and that the missing item must be hiding where it belonged.",
        ),
        QAItem(
            question=f"Where was the recyclable {prize.label} at the end?",
            answer=f"At the end, the recyclable {prize.label} was in the blue bin, and {hero.id} had solved the little mystery.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    prize = f["prize"]
    clue = f["clue"]
    return [
        QAItem(
            question="What does recyclable mean?",
            answer="Recyclable means something can be collected and made into new things instead of being thrown away forever.",
        ),
        QAItem(
            question="Why do people sort recyclables?",
            answer="People sort recyclables so paper, metal, and plastic can go into the right place and be reused properly.",
        ),
        QAItem(
            question="What is a clue in a detective story?",
            answer="A clue is a small piece of information that helps a detective figure out what happened.",
        ),
        QAItem(
            question=f"What kind of thing is a {prize.label} in this world?",
            answer=f"In this world, a {prize.label} is a recyclable item that belongs in the blue bin or recycling area.",
        ),
        QAItem(
            question="Why is inner monologue useful in a mystery?",
            answer="Inner monologue is useful because it lets the detective think through the clues quietly before deciding what to do.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} location={e.location} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style story world with inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        clue=clue,
        prize=prize,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CLUES[params.clue],
        PRIZES[params.prize],
        params.name,
        "girl" if params.gender == "girl" else "boy",
        params.parent,
        params.trait,
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


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="kitchen", clue="cap", prize="can", name="Mina", gender="girl", parent="mother", trait="sharp-eyed"),
    StoryParams(setting="garage", clue="label", prize="bottle", name="Eli", gender="boy", parent="father", trait="careful"),
    StoryParams(setting="yard", clue="scrape", prize="box", name="Tara", gender="girl", parent="mother", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible (setting, clue, prize) combos:")
        for t in triples:
            print(" ", t)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
