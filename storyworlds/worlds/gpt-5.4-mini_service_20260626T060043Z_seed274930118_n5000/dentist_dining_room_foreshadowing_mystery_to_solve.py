#!/usr/bin/env python3
"""
storyworlds/worlds/dentist_dining_room_foreshadowing_mystery_to_solve.py
=========================================================================

A standalone storyworld about a dentist, a dining room, and a small mystery to
solve. The tale is written in a superhero-story style: the child notices clues,
the dentist follows foreshadowing, and together they uncover what caused the
trouble and fix it.

This world models a small home visit where a child with a bright hero-spirited
personality needs help after dinner. The dining room holds the clues; the
dentist reads them; the mystery is solved by a gentle, concrete action.

The core premise:
- A child feels a tooth problem after dinner.
- Foreshadowing clues in the dining room hint at the cause.
- The dentist solves the mystery and helps the child feel brave again.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "dentist"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dining room"
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    symptom: str
    clue: str
    culprit: str
    solution: str
    foreshadow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    use: str
    fixes: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.clues: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "dining_room": Setting(place="the dining room", affords={"after_dinner"}),
}

CASES = {
    "stuck_fruit": Case(
        id="stuck_fruit",
        symptom="a toothache",
        clue="a red strawberry seed hiding near a plate",
        culprit="a sticky fruit piece",
        solution="careful flossing and water",
        foreshadow="tiny red crumbs on the table",
        tags={"fruit", "sticky", "dinner"},
    ),
    "sugar_crust": Case(
        id="sugar_crust",
        symptom="a sore tooth",
        clue="a shiny sugar crust on the edge of a spoon",
        culprit="a sweet crust left after dessert",
        solution="gentle brushing and a glass of water",
        foreshadow="a sparkly spoon and a half-finished cup",
        tags={"sugar", "sweet", "dessert"},
    ),
    "popcorn_shell": Case(
        id="popcorn_shell",
        symptom="a sharp little poke",
        clue="a popcorn shell tucked under a napkin",
        culprit="a tiny shell stuck between teeth",
        solution="careful flossing",
        foreshadow="crumbs that pointed like arrows",
        tags={"popcorn", "crunchy", "snack"},
    ),
}

TOOLS = {
    "floss": Tool(id="floss", label="floss", use="slide between the teeth", fixes={"sticky", "popcorn"}),
    "brush": Tool(id="brush", label="toothbrush", use="gently brush the teeth", fixes={"sugar"}),
    "water": Tool(id="water", label="water", use="rinse away the bits", fixes={"sticky", "sugar"}),
}

HERO_NAMES = ["Mina", "Theo", "Luna", "Arlo", "Zia", "Kai"]
DENTIST_NAMES = ["Dr. Pearl", "Dr. Mica", "Dr. Willow"]
TRAITS = ["brave", "curious", "sparkly-eyed", "bold", "cheerful"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    case: str
    hero_name: str
    hero_trait: str
    dentist_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A case is reasonable only if the symptom matches the culprit family and there
% is at least one tool that can fix it.
reasonable_case(C) :- case(C), symptom_family(C, F), culprit_family(C, F), has_tool(F).
valid_story(S, C) :- setting(S), reasonable_case(C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CASES.items():
        lines.append(asp.fact("case", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("tag", cid, t))
        if "sticky" in c.tags or "popcorn" in c.tags:
            lines.append(asp.fact("symptom_family", cid, "sticky"))
        if "sugar" in c.tags:
            lines.append(asp.fact("symptom_family", cid, "sugar"))
        if "fruit" in c.tags:
            lines.append(asp.fact("symptom_family", cid, "sticky"))
        if "popcorn" in c.tags:
            lines.append(asp.fact("culprit_family", cid, "sticky"))
        if "sticky" in c.tags:
            lines.append(asp.fact("culprit_family", cid, "sticky"))
        if "sugar" in c.tags:
            lines.append(asp.fact("culprit_family", cid, "sugar"))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for f in sorted(t.fixes):
            lines.append(asp.fact("fixes", tid, f))
            lines.append(asp.fact("has_tool", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    if set(asp_valid_stories()) == set(valid_stories()):
        print(f"OK: clingo gate matches valid_stories() ({len(valid_stories())} stories).")
        return 0
    print("MISMATCH between clingo and Python story gate.")
    print("Python:", sorted(valid_stories()))
    print("ASP   :", sorted(asp_valid_stories()))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_stories() -> list[tuple[str, str]]:
    out = []
    for s in SETTINGS:
        if s != "dining_room":
            continue
        for c_id, c in CASES.items():
            if any(t in c.tags for t in {"sticky", "sugar", "popcorn"}):
                out.append((s, c_id))
    return out


def explain_rejection(setting: str, case: str) -> str:
    return f"(No story: the case {case} does not fit the dining-room mystery setup.)"


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, dentist: Entity, case: Case) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', 'brave')} little hero who liked to solve problems before they grew big."
    )
    world.say(
        f"That evening, {hero.id} sat in {world.setting.place} with {hero.pronoun('possessive')} plate and noticed a tiny trouble."
    )
    world.say(
        f"{hero.id} said {hero.pronoun('subject').capitalize()}, \"My tooth feels strange.\""
    )
    world.say(
        f"Then {dentist.id} came like a calm captain in a cape of kindness, ready to solve the mystery."
    )
    world.clues.append(case.foreshadow)


def foreshadow(world: World, hero: Entity, dentist: Entity, case: Case) -> None:
    world.say(
        f"On the table, there were {case.foreshadow}, and {dentist.id} slowed down to look carefully."
    )
    world.say(
        f"{hero.id} had not noticed them before, but now the clues shone like little warning lights."
    )
    world.clues.append(case.clue)


def investigate(world: World, hero: Entity, dentist: Entity, case: Case) -> None:
    world.say(
        f"{dentist.id} looked at the clues, then checked {hero.pronoun('possessive')} smile very gently."
    )
    world.say(
        f"\"This is a mystery to solve,\" {dentist.id} said. \"The clues point to {case.culprit}.\""
    )


def solve(world: World, hero: Entity, dentist: Entity, case: Case) -> None:
    tool = next((t for t in TOOLS.values() if case.id.startswith("popcorn") and "popcorn" in t.fixes), None)
    if tool is None:
        if "sugar" in case.tags:
            tool = TOOLS["brush"]
        else:
            tool = TOOLS["floss"]
    world.say(
        f"{dentist.id} used {tool.label} to {tool.use}, and the little trouble came loose."
    )
    world.say(
        f"The mystery was solved: the problem had been {case.culprit}, hiding where it could make {hero.id}'s tooth hurt."
    )
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    world.facts["tool"] = tool
    world.facts["case"] = case


def ending(world: World, hero: Entity, dentist: Entity, case: Case) -> None:
    world.para()
    world.say(
        f"{hero.id} smiled again, and {world.setting.place} felt warm and safe."
    )
    world.say(
        f"The clues were gone, the toothache was gone, and {hero.id} stood a little taller, like a hero after a victory."
    )


def tell(setting: Setting, case: Case, hero_name: str, hero_trait: str, dentist_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", traits=[hero_trait]))
    hero.memes["trait"] = hero_trait
    dentist = world.add(Entity(id=dentist_name, kind="character", type="dentist"))
    world.facts.update(hero=hero, dentist=dentist, case=case, setting=setting)

    intro(world, hero, dentist, case)
    world.para()
    foreshadow(world, hero, dentist, case)
    investigate(world, hero, dentist, case)
    solve(world, hero, dentist, case)
    ending(world, hero, dentist, case)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    case = f["case"]
    dentist = f["dentist"]
    return [
        f"Write a superhero-style story about {hero.id} in the dining room, where a dentist helps solve a small mystery.",
        f"Tell a child-friendly mystery in {world.setting.place} where {dentist.id} notices clues and figures out why {hero.id}'s tooth hurts.",
        f"Write a short story with foreshadowing, a clue, and a gentle solution involving {case.culprit}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    dentist = f["dentist"]
    case = f["case"]
    tool: Tool = f["tool"]

    return [
        QAItem(
            question=f"Where did the mystery happen?",
            answer=f"The mystery happened in {world.setting.place}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the mystery?",
            answer=f"{dentist.id} helped {hero.id} solve the mystery.",
        ),
        QAItem(
            question=f"What clue foreshadowed the problem?",
            answer=f"The clue was {case.foreshadow}, which hinted that something small and tricky was causing the trouble.",
        ),
        QAItem(
            question=f"What caused {hero.id}'s tooth trouble?",
            answer=f"The trouble was caused by {case.culprit}.",
        ),
        QAItem(
            question=f"What did {dentist.id} use to fix it?",
            answer=f"{dentist.id} used {tool.label} to {tool.use}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a dentist do?",
            answer="A dentist helps keep teeth clean and healthy and checks for problems that can cause pain.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a clue that hints something important will happen later.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a problem where you look for clues to figure out what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"clues={world.clues}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Dentist dining-room mystery storyworld.")
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--case", choices=list(CASES))
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--dentist", choices=DENTIST_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.setting and args.setting != "dining_room":
        raise StoryError(explain_rejection(args.setting, args.case or "any"))
    case = args.case or rng.choice(list(CASES))
    if args.case and args.case not in CASES:
        raise StoryError("Unknown case.")
    if args.setting and (args.setting, case) not in valid_stories():
        raise StoryError(explain_rejection(args.setting, case))

    return StoryParams(
        setting="dining_room",
        case=case,
        hero_name=args.name or rng.choice(HERO_NAMES),
        hero_trait=args.trait or rng.choice(TRAITS),
        dentist_name=args.dentist or rng.choice(DENTIST_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CASES[params.case],
        params.hero_name,
        params.hero_trait,
        params.dentist_name,
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
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid stories:")
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(setting="dining_room", case=cid, hero_name=HERO_NAMES[i % len(HERO_NAMES)], hero_trait=TRAITS[i % len(TRAITS)], dentist_name=DENTIST_NAMES[i % len(DENTIST_NAMES)])) for i, cid in enumerate(CASES)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
