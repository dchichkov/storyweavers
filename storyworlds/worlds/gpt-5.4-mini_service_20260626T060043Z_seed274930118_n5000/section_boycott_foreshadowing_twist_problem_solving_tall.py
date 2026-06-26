#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/section_boycott_foreshadowing_twist_problem_solving_tall.py
================================================================================

A standalone story world for a tall-tale-style miniature domain about a town
section, a boycott, foreshadowing, a twist, and problem solving.

Premise:
- In a booming frontier town, one section of the annual market is being boycotted.
- The hero notices small signs that something is off before the trouble fully blooms.
- The boycotted section turns out to be tied to a misunderstanding, not malice.
- The hero solves the problem with a practical, town-sized compromise.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- state-driven story generation
- story QA, world QA, trace, JSON, ASP twin, verify mode
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
# Domain registries
# ---------------------------------------------------------------------------

TOWNS = {
    "dusty_mill": "Dusty Mill",
    "pine_cross": "Pine Cross",
    "red_fork": "Red Fork",
    "sage_landing": "Sage Landing",
}

SECTIONS = {
    "north_section": {
        "label": "the north section",
        "detail": "the stalls by the big water tower",
        "floor": "planks",
    },
    "river_section": {
        "label": "the river section",
        "detail": "the booths near the ferry ropes",
        "floor": "boards",
    },
    "square_section": {
        "label": "the square section",
        "detail": "the tables around the clock tower",
        "floor": "stone",
    },
    "rail_section": {
        "label": "the rail section",
        "detail": "the sheds beside the rail line",
        "floor": "grit",
    },
}

GRIEVANCES = {
    "price": {
        "label": "high prices",
        "cause": "the prices were too high for ordinary families",
        "fix": "post fair prices and share a smaller cup for a dime",
    },
    "noise": {
        "label": "too much noise",
        "cause": "the music and shouting were rattling the shop windows",
        "fix": "move the fiddle band to the open square and keep the drums soft",
    },
    "smoke": {
        "label": "smoky air",
        "cause": "the cook fires were sending smoke into every nose",
        "fix": "lift the cook fires to the windy lane and open the vents wide",
    },
    "mud": {
        "label": "muddy floors",
        "cause": "mud from the wagons kept getting tracked through the section",
        "fix": "lay down straw mats and park the wagons outside the fence",
    },
}

TOOLS = {
    "ledger": "a crooked little ledger",
    "lantern": "a bright brass lantern",
    "megaphone": "a tin megaphone",
    "map": "a folded town map",
}

HELPERS = {
    "baker": "the baker",
    "marshal": "the marshal",
    "fiddler": "the fiddler",
    "teacher": "the teacher",
    "carpenter": "the carpenter",
}

NAMES = [
    "Mabel", "Hank", "Tilly", "Jed", "Nora", "Silas", "Ruby", "Cal", "Mina", "Otis"
]

TRAITS = [
    "stubborn", "quick-witted", "loud-hearted", "steady", "curious", "long-legged"
]


# ---------------------------------------------------------------------------
# Shared world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    town: str
    section: str
    grievance: str
    hero_name: str
    hero_type: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


@dataclass
class StoryState:
    town: str
    section: str
    grievance: str
    hero: Entity
    helper: Entity
    sign: Entity
    bell: Entity
    ledger: Entity
    people: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(section: str, grievance: str) -> bool:
    # Every listed section can host a boycott, but each grievance needs a specific
    # practical fix. We keep the space tight and controlled.
    return section in SECTIONS and grievance in GRIEVANCES


def explain_rejection(section: str, grievance: str) -> str:
    return f"(No story: the {section} and the {grievance} grievance do not make a workable town problem.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A town situation is valid when a section and a grievance are both present.
valid(S, G) :- section(S), grievance(G).

% A workable story needs a practical fix.
workable(S, G) :- valid(S, G), has_fix(G).

#show valid/2.
#show workable/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SECTIONS:
        lines.append(asp.fact("section", sid))
    for gid in GRIEVANCES:
        lines.append(asp.fact("grievance", gid))
        lines.append(asp.fact("has_fix", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2. #show workable/2."))
    clingo_valid = set(asp.atoms(model, "valid"))
    clingo_workable = set(asp.atoms(model, "workable"))
    py_valid = {(s, g) for s in SECTIONS for g in GRIEVANCES if valid_combo(s, g)}
    py_workable = set(py_valid)
    ok = (clingo_valid == py_valid) and (clingo_workable == py_workable)
    if ok:
        print(f"OK: ASP and Python agree on {len(py_valid)} valid/workable combos.")
        return 0
    print("MISMATCH between ASP and Python.")
    if clingo_valid - py_valid:
        print(" only in ASP valid:", sorted(clingo_valid - py_valid))
    if py_valid - clingo_valid:
        print(" only in Python valid:", sorted(py_valid - clingo_valid))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> StoryState:
    town_label = TOWNS[params.town]
    section = SECTIONS[params.section]
    grievance = GRIEVANCES[params.grievance]

    hero = Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"courage": 0.0, "miles_walked": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0},
    )
    helper = Entity(
        id="Helper",
        kind="character",
        type=params.helper_type,
        label=HELPERS[params.helper_type],
        meters={"patience": 1.0, "work": 0.0},
        memes={"doubt": 0.0, "hope": 0.0},
    )
    sign = Entity(
        id="Sign",
        kind="thing",
        type="sign",
        label="boycott sign",
        phrase="a hand-painted boycott sign",
        meters={"wobble": 0.0},
        memes={"warning": 1.0},
    )
    bell = Entity(
        id="Bell",
        kind="thing",
        type="bell",
        label="courthouse bell",
        phrase="the courthouse bell",
        meters={"ring": 0.0},
        memes={"notice": 1.0},
    )
    ledger = Entity(
        id="Ledger",
        kind="thing",
        type="ledger",
        label="ledger",
        phrase=TOOLS["ledger"],
        meters={"pages": 12.0},
    )
    return StoryState(
        town=town_label,
        section=section["label"],
        grievance=grievance["label"],
        hero=hero,
        helper=helper,
        sign=sign,
        bell=bell,
        ledger=ledger,
        people={hero.id: hero, helper.id: helper},
    )


def foreshadow(world: StoryState) -> None:
    world.hero.meters["miles_walked"] += 2
    world.hero.memes["curiosity"] += 1
    world.sign.meters["wobble"] += 1
    world.bell.meters["ring"] += 1
    world.say(
        f"In {world.town}, {world.hero.id} had a habit of noticing small things before they turned into big ones. "
        f"That morning, {world.hero.pronoun('subject')} saw a boycott sign leaning crooked near {world.section}, "
        f"and the courthouse bell gave one lonely ring like a warning from an old friend."
    )
    world.say(
        f"Even the lanterns seemed to hold their breath around the stalls, as if the whole town knew a ruckus was gathering its boots."
    )


def setup(world: StoryState) -> None:
    world.hero.meters["courage"] += 1
    world.helper.memes["hope"] += 1
    world.say(
        f"{world.hero.id}, a {world.hero.type} with a {world.hero.memes['curiosity']:.0f}-spark curiosity and a long memory, "
        f"walked straight toward {world.section}. {world.hero.pronoun('subject').capitalize()} wanted to know why a whole stretch of town had stopped buying, selling, and smiling in the usual way."
    )


def twist(world: StoryState) -> None:
    grievance = GRIEVANCES[world.params.grievance]
    world.helper.memes["doubt"] += 1
    world.say(
        f"At first, {world.hero.id} thought the boycott was aimed at the merchants themselves. "
        f"But then {world.hero.pronoun('subject')} heard the real grumble: {grievance['cause']}."
    )
    world.say(
        f"That was the twist of it. The townsfolk were not trying to ruin the {world.section}; they were trying to push it toward fairness."
    )


def problem_solving(world: StoryState) -> None:
    grievance = GRIEVANCES[world.params.grievance]
    world.ledger.meters["pages"] -= 1
    world.helper.memes["hope"] += 1
    world.helper.meters["work"] += 1
    world.hero.meters["courage"] += 1

    world.say(
        f"{world.hero.id} and {world.helper.label} spread {world.ledger.phrase} on a barrel-top table and counted the trouble out loud, one piece at a time."
    )
    world.say(
        f"Then they made a plain little plan: {grievance['fix']}."
    )
    world.say(
        f"The boycott stayed in place until the promise was posted, and after that the section opened again with fairer prices, calmer faces, and enough laughter to shake dust off the rafters."
    )


def ending(world: StoryState) -> None:
    world.hero.memes["worry"] = 0.0
    world.helper.memes["doubt"] = 0.0
    world.say(
        f"By sundown, {world.section} was bustling so hard it sounded like a herd of friendly horses. "
        f"{world.hero.id} went home with dusty boots, a proud grin, and the fine feeling that even a big boycott can be steered straight when somebody tells the truth and brings a good plan."
    )


def build_story(params: StoryParams) -> StoryState:
    world = make_world(params)
    foreshadow(world)
    world.para()
    setup(world)
    world.para()
    twist(world)
    world.para()
    problem_solving(world)
    world.para()
    ending(world)

    world.facts = {
        "town": params.town,
        "section": params.section,
        "grievance": params.grievance,
        "hero_name": params.hero_name,
        "hero_type": params.hero_type,
        "helper_type": params.helper_type,
        "trait": params.trait,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a child about {f["hero_name"]} noticing a boycott in {world.town}.',
        f"Tell a story with foreshadowing, a twist, and problem solving in {world.section}.",
        f'Write a short frontier story about a boycott, a town section, and a fair fix.',
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    hero = world.hero
    grievance = GRIEVANCES[f["grievance"]]
    return [
        QAItem(
            question=f"Where did {f['hero_name']} first notice that something was wrong?",
            answer=f"{f['hero_name']} first noticed trouble in {world.section} in {world.town}, where a boycott sign was leaning crooked and the town felt unusually quiet.",
        ),
        QAItem(
            question=f"What was the boycott about?",
            answer=f"It was about {grievance['label']}. The townsfolk were refusing business there until the problem was handled in a fairer way.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the boycott was not simple anger. The townsfolk were trying to fix a real problem, so the story turned from suspicion to understanding.",
        ),
        QAItem(
            question=f"How did {f['hero_name']} help solve the problem?",
            answer=f"{f['hero_name']} helped by making a practical plan with {world.helper.label}: {grievance['fix']}. That gave the town a way to reopen the section fairly.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, {world.section} was open again, the boycott ended, and the town had a better agreement than before.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "boycott": (
        "What is a boycott?",
        "A boycott is when people agree not to buy, use, or visit something for a while so they can ask for change.",
    ),
    "section": (
        "What is a section?",
        "A section is one part of a bigger place, like one part of a town, a book, or a market.",
    ),
    "lantern": (
        "What does a lantern do?",
        "A lantern gives light, which helps people see at night or in dim places.",
    ),
    "ledger": (
        "What is a ledger?",
        "A ledger is a book for keeping track of numbers, names, or goods.",
    ),
}


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for _, (q, a) in WORLD_KNOWLEDGE.items()]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation and emit
# ---------------------------------------------------------------------------

def valid_params(params: StoryParams) -> None:
    if params.town not in TOWNS:
        raise StoryError(f"Unknown town: {params.town}")
    if params.section not in SECTIONS:
        raise StoryError(f"Unknown section: {params.section}")
    if params.grievance not in GRIEVANCES:
        raise StoryError(f"Unknown grievance: {params.grievance}")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    town = args.town or rng.choice(list(TOWNS))
    section = args.section or rng.choice(list(SECTIONS))
    grievance = args.grievance or rng.choice(list(GRIEVANCES))
    if not valid_combo(section, grievance):
        raise StoryError(explain_rejection(section, grievance))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    helper_type = args.helper_type or rng.choice(["man", "woman"])
    hero_name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        town=town,
        section=section,
        grievance=grievance,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    valid_params(params)
    world = build_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.helper, world.sign, world.bell, world.ledger]:
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(
        town="dusty_mill",
        section="north_section",
        grievance="price",
        hero_name="Mabel",
        hero_type="girl",
        helper_type="woman",
        trait="quick-witted",
    ),
    StoryParams(
        town="pine_cross",
        section="square_section",
        grievance="noise",
        hero_name="Hank",
        hero_type="boy",
        helper_type="man",
        trait="steady",
    ),
    StoryParams(
        town="red_fork",
        section="river_section",
        grievance="mud",
        hero_name="Ruby",
        hero_type="girl",
        helper_type="man",
        trait="curious",
    ),
    StoryParams(
        town="sage_landing",
        section="rail_section",
        grievance="smoke",
        hero_name="Silas",
        hero_type="boy",
        helper_type="woman",
        trait="loud-hearted",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall tale storyworld about a town section, a boycott, and a clever fix."
    )
    ap.add_argument("--town", choices=list(TOWNS))
    ap.add_argument("--section", choices=list(SECTIONS))
    ap.add_argument("--grievance", choices=list(GRIEVANCES))
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--helper-type", choices=["man", "woman"])
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2. #show workable/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_workable_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2. #show workable/2."))
    return sorted(set(asp.atoms(model, "workable")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2. #show workable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        vals = asp_valid_combos()
        print(f"{len(vals)} valid combos:")
        for s, g in vals:
            print(f"  {s} {g}")
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
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.section} boycott in {p.town} ({p.grievance})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
