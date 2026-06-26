#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tortilla_sharing_problem_solving_suspense_superhero_story.py
================================================================================================

A small standalone story world for a superhero-style tale about sharing a tortilla,
solving a problem, and building suspense before a kind ending.

The seed idea:
- A young hero wants to eat or share a tortilla.
- A teammate or friend needs it too.
- Something suspenseful happens: the tortilla can fall, get cold, or be taken.
- The heroes solve the problem by sharing carefully, splitting, or passing it along.
- The ending proves the change in state: everyone is fed, calm, and the tortilla is shared.

This file follows the Storyweavers world contract:
- one standalone stdlib script
- eager import of shared results containers
- lazy ASP import inside ASP helpers
- typed entities with meters and memes
- state-driven prose
- inline ASP twin and Python reasonableness gate
- CLI support for default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0
FILLINGS = ["beans", "cheese", "rice", "corn", "salsa"]
SHARING_ACTIONS = ["split", "share", "pass"]
SUSPENSE_EVENTS = ["wind", "goblin", "alarm", "drip", "crowd"]
PLACES = {
    "rooftop": {"outside": True, "windy": True},
    "kitchen": {"outside": False, "windy": False},
    "alley": {"outside": True, "windy": True},
    "classroom": {"outside": False, "windy": False},
}
HERO_TYPES = ["girl", "boy"]
HERO_NAMES = {
    "girl": ["Maya", "Zoe", "Lina", "Ruby", "Nina", "Pia"],
    "boy": ["Leo", "Ben", "Tariq", "Milo", "Owen", "Eli"],
}
ALLY_NAMES = ["Kai", "Pip", "Nova", "Juno", "Tess", "Ari"]
TRAITS = ["brave", "quick", "kind", "curious", "steady", "clever"]


# ---------------------------------------------------------------------------
# Entities
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["intact", "warm", "messy", "fed", "safe"]:
            self.meters.setdefault(key, 0.0)
        for key in ["joy", "fear", "tension", "care", "hunger", "relief", "generosity"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class Setting:
    place: str
    outside: bool
    windy: bool


@dataclass
class HeroConfig:
    name: str
    hero_type: str
    trait: str


@dataclass
class TortillaConfig:
    size: str
    filling: str
    warm: bool = True


@dataclass
class ProblemConfig:
    id: str
    suspense: str
    danger: str
    urgency: str
    source: str


SETTING_REGISTRY = {
    "rooftop": Setting(place="the rooftop", outside=True, windy=True),
    "kitchen": Setting(place="the kitchen", outside=False, windy=False),
    "alley": Setting(place="the narrow alley", outside=True, windy=True),
    "classroom": Setting(place="the classroom", outside=False, windy=False),
}

TORTILLA_REGISTRY = {
    "tiny": TortillaConfig(size="tiny tortilla", filling="beans"),
    "big": TortillaConfig(size="big tortilla", filling="cheese"),
    "rolled": TortillaConfig(size="rolled tortilla", filling="rice"),
    "spicy": TortillaConfig(size="spicy tortilla", filling="salsa"),
}

PROBLEM_REGISTRY = {
    "wind": ProblemConfig(
        id="wind",
        suspense="a sharp wind gust",
        danger="blow the tortilla away",
        urgency="if nobody held on fast, dinner would fly off the roof",
        source="windy air",
    ),
    "hungry_friend": ProblemConfig(
        id="hungry_friend",
        suspense="a hungry friend peeking over the rail",
        danger="leave one hero without food",
        urgency="someone needed a fair share before the tortilla was gone",
        source="sharing",
    ),
    "alarm": ProblemConfig(
        id="alarm",
        suspense="a sudden alarm sound",
        danger="make everyone rush and drop the tortilla",
        urgency="the heroes had to stay calm and keep the food safe",
        source="noise",
    ),
}

SUSPENSE_BEATS = {
    "wind": "The wind tugged at the warm tortilla like it wanted a bite.",
    "hungry_friend": "A hungry friend leaned closer, eyes fixed on the tortilla.",
    "alarm": "An alarm rang out, and the whole place seemed to hold its breath.",
}

SHARING_SOLUTIONS = {
    "split": "split the tortilla in two",
    "share": "share the tortilla fairly",
    "pass": "pass the tortilla from one glove to another",
}


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def hero_name_for(gender: str, rng: random.Random) -> str:
    return rng.choice(HERO_NAMES[gender])


def choose_setting(rng: random.Random, pin: Optional[str] = None) -> str:
    if pin:
        return pin
    return rng.choice(list(SETTING_REGISTRY))


def choose_tortilla(rng: random.Random, pin: Optional[str] = None) -> str:
    if pin:
        return pin
    return rng.choice(list(TORTILLA_REGISTRY))


def choose_problem(rng: random.Random, pin: Optional[str] = None) -> str:
    if pin:
        return pin
    return rng.choice(list(PROBLEM_REGISTRY))


def reasonableness_gate(setting: str, tortilla: str, problem: str) -> bool:
    if setting not in SETTING_REGISTRY or tortilla not in TORTILLA_REGISTRY or problem not in PROBLEM_REGISTRY:
        return False
    # We only tell stories where the tortilla is genuinely at risk or needed for sharing.
    return True


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    tortilla: str
    problem: str
    hero: str
    hero_type: str
    ally: str
    ally_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts define the chosen setting, tortilla, and problem.

at_risk(T, wind) :- tortilla(T), windy_place.
at_risk(T, hungry_friend) :- tortilla(T), hungry_friend_present.
at_risk(T, alarm) :- tortilla(T), alarm_sound.

can_solve(T, wind) :- at_risk(T, wind), share_fix.
can_solve(T, hungry_friend) :- at_risk(T, hungry_friend), share_fix.
can_solve(T, alarm) :- at_risk(T, alarm), calm_fix.

valid_story(S, T, P) :- setting(S), tortilla(T), problem(P), at_risk(T, P), can_solve(T, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTING_REGISTRY.items():
        lines.append(asp.fact("setting", sid))
        if setting.outside:
            lines.append(asp.fact("outside_place", sid))
        if setting.windy:
            lines.append(asp.fact("windy_place", sid))
    for tid, cfg in TORTILLA_REGISTRY.items():
        lines.append(asp.fact("tortilla", tid))
        lines.append(asp.fact("filling", tid, cfg.filling))
        lines.append(asp.fact("share_fix"))
    for pid, cfg in PROBLEM_REGISTRY.items():
        lines.append(asp.fact("problem", pid))
        if pid == "wind":
            lines.append(asp.fact("windy_place"))
        if pid == "hungry_friend":
            lines.append(asp.fact("hungry_friend_present"))
        if pid == "alarm":
            lines.append(asp.fact("alarm_sound"))
            lines.append(asp.fact("calm_fix"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {
        (s, t, p)
        for s in SETTING_REGISTRY
        for t in TORTILLA_REGISTRY
        for p in PROBLEM_REGISTRY
        if reasonableness_gate(s, t, p)
    }
    clingo = set(asp_valid_stories())
    if py == clingo:
        print(f"OK: clingo gate matches python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    setting = SETTING_REGISTRY[params.setting]
    tortilla_cfg = TORTILLA_REGISTRY[params.tortilla]
    problem_cfg = PROBLEM_REGISTRY[params.problem]

    world = World(setting)
    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=params.hero_type,
        memes={"joy": 1.0, "care": 1.0, "hunger": 1.0, "fear": 0.0, "tension": 0.0, "relief": 0.0, "generosity": 0.0},
    ))
    ally = world.add(Entity(
        id=params.ally,
        kind="character",
        type=params.ally_type,
        memes={"joy": 0.5, "care": 1.0, "hunger": 1.0, "fear": 0.0, "tension": 0.0, "relief": 0.0, "generosity": 0.0},
    ))
    tortilla = world.add(Entity(
        id="tortilla",
        kind="thing",
        type="tortilla",
        label=tortilla_cfg.size,
        phrase=f"a warm {tortilla_cfg.size} filled with {tortilla_cfg.filling}",
        owner=hero.id,
        caretaker=hero.id,
        held_by=hero.id,
        plural=False,
        meters={"intact": 1.0, "warm": 1.0, "messy": 0.0, "safe": 1.0},
    ))

    world.facts = {
        "setting": setting,
        "tortilla": tortilla,
        "problem": problem_cfg,
        "hero": hero,
        "ally": ally,
        "params": params,
    }

    # Act 1: setup
    world.say(
        f"{hero.id} was a {params.trait} little {params.hero_type} who wore a cape in {setting.place}."
    )
    world.say(
        f"{hero.id} had a warm {tortilla_cfg.size} stuffed with {tortilla_cfg.filling}, and {ally.id} was hungry too."
    )
    world.para()

    # Act 2: suspense and problem
    if params.problem == "wind":
        world.say(f"{hero.id} balanced on the edge of {setting.place} when {SUSPENSE_BEATS['wind']}")
        hero.memes["fear"] += 1.0
        hero.memes["tension"] += 1.0
        tortilla.meters["warm"] -= 0.2
        tortilla.meters["safe"] -= 0.5
    elif params.problem == "hungry_friend":
        world.say(f"At {setting.place}, {SUSPENSE_BEATS['hungry_friend']}")
        ally.memes["hunger"] += 1.0
        hero.memes["tension"] += 1.0
        tortilla.meters["safe"] -= 0.3
    else:
        world.say(f"Inside {setting.place}, {SUSPENSE_BEATS['alarm']}")
        hero.memes["fear"] += 0.5
        ally.memes["fear"] += 0.5
        hero.memes["tension"] += 1.0
        tortilla.meters["warm"] -= 0.1

    world.say(f"{problem_cfg.urgency}.")
    world.para()

    # Act 3: problem solving through sharing
    if params.problem == "wind":
        world.say(
            f"{hero.id} snapped, '{hero.id} can fix this!' and {SHARING_ACTIONS[0]} the tortilla with {ally.id}."
        )
        tortilla.plural = False
        tortilla.meters["safe"] += 1.0
        hero.memes["generosity"] += 1.0
        ally.memes["relief"] += 1.0
        hero.memes["tension"] = 0.0
        tortilla.held_by = None
    elif params.problem == "hungry_friend":
        world.say(
            f"{hero.id} took a deep breath, then {SHARING_ACTIONS[1]} the tortilla so {ally.id} got the first piece."
        )
        hero.memes["generosity"] += 1.0
        ally.memes["relief"] += 1.0
        hero.memes["tension"] = 0.0
        tortilla.meters["safe"] += 1.0
    else:
        world.say(
            f"{hero.id} kept calm, {SHARING_ACTIONS[2]} the tortilla to {ally.id}, and held it steady until the alarm faded."
        )
        hero.memes["generosity"] += 1.0
        ally.memes["relief"] += 1.0
        hero.memes["tension"] = 0.0
        tortilla.meters["safe"] += 0.8

    # Resolution
    tortilla.meters["intact"] = max(tortilla.meters["intact"], 1.0)
    tortilla.meters["warm"] = max(tortilla.meters["warm"], 0.7)
    hero.memes["joy"] += 1.0
    ally.memes["joy"] += 1.0
    hero.memes["relief"] += 1.0
    world.say(
        f"In the end, {hero.id} and {ally.id} shared the tortilla, and the little cape fluttered like a flag after a win."
    )
    world.say(
        f"Nobody went home hungry, and the last bite stayed safe in {ally.id}'s hands."
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short superhero story for a child about sharing a tortilla at {p.setting}.',
        f"Tell a suspenseful but gentle story where {p.hero} must solve a tortilla problem with {p.ally}.",
        f'Write a story with the word "tortilla" that ends in sharing, problem solving, and relief.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero: Entity = world.facts["hero"]
    ally: Entity = world.facts["ally"]
    tortilla: Entity = world.facts["tortilla"]
    problem: ProblemConfig = world.facts["problem"]

    return [
        QAItem(
            question=f"Who was the story about at {p.setting}?",
            answer=f"It was about {hero.id}, a {p.trait} little {p.hero_type}, and {ally.id}, who helped with the tortilla.",
        ),
        QAItem(
            question=f"What was the important food in the story?",
            answer=f"The important food was {tortilla.phrase}.",
        ),
        QAItem(
            question=f"What problem made the story feel suspenseful?",
            answer=f"The story used {problem.suspense}, which made it feel suspenseful until the heroes solved it.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} solved it by sharing the tortilla with {ally.id} and keeping everyone calm.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the tortilla was still safe, the heroes felt relief, and nobody went home hungry.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "tortilla": [
        QAItem(
            question="What is a tortilla?",
            answer="A tortilla is a soft round flatbread that can hold fillings like beans or cheese.",
        )
    ],
    "share": [
        QAItem(
            question="What does it mean to share food?",
            answer="To share food means to let more than one person have some of it so everyone gets a turn.",
        )
    ],
    "wind": [
        QAItem(
            question="Why can wind be tricky for food outside?",
            answer="Wind can move light things around, so people often hold food carefully when it is breezy.",
        )
    ],
    "calm": [
        QAItem(
            question="Why is staying calm useful in a problem?",
            answer="Staying calm helps you think clearly, choose a good plan, and keep from dropping things.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    out: list[QAItem] = [WORLD_KNOWLEDGE["tortilla"][0], WORLD_KNOWLEDGE["share"][0]]
    if p.problem == "wind":
        out.append(WORLD_KNOWLEDGE["wind"][0])
    if p.problem == "alarm":
        out.append(WORLD_KNOWLEDGE["calm"][0])
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {q}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if n:
            bits.append(f"memes={n}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verification and facts
# ---------------------------------------------------------------------------

def asp_valid_count() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return len(asp.atoms(model, "valid_story"))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero tortilla sharing story world.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--tortilla", choices=TORTILLA_REGISTRY)
    ap.add_argument("--problem", choices=PROBLEM_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--ally")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--ally-gender", choices=["girl", "boy"])
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
    setting = choose_setting(rng, args.setting)
    tortilla = choose_tortilla(rng, args.tortilla)
    problem = choose_problem(rng, args.problem)

    if not reasonableness_gate(setting, tortilla, problem):
        raise StoryError("The chosen setting, tortilla, and problem do not make a valid story.")

    gender = args.gender or rng.choice(HERO_TYPES)
    ally_gender = args.ally_gender or rng.choice(HERO_TYPES)
    hero = args.name or hero_name_for(gender, rng)
    ally = args.ally or rng.choice([n for n in ALLY_NAMES if n != hero])
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        setting=setting,
        tortilla=tortilla,
        problem=problem,
        hero=hero,
        hero_type=gender,
        ally=ally,
        ally_type=ally_gender,
        trait=trait,
    )


def generate_many(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()

    if args.all:
        combos = [
            (s, t, p)
            for s in SETTING_REGISTRY
            for t in TORTILLA_REGISTRY
            for p in PROBLEM_REGISTRY
            if reasonableness_gate(s, t, p)
        ]
        for i, (s, t, p) in enumerate(combos):
            rng = random.Random(base_seed + i)
            params = StoryParams(
                setting=s,
                tortilla=t,
                problem=p,
                hero=hero_name_for("girl" if i % 2 == 0 else "boy", rng),
                hero_type="girl" if i % 2 == 0 else "boy",
                ally=rng.choice(ALLY_NAMES),
                ally_type="boy" if i % 2 == 0 else "girl",
                trait=rng.choice(TRAITS),
                seed=base_seed + i,
            )
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
        return samples

    i = 0
    while len(samples) < args.n and i < max(args.n * 50, 50):
        rng = random.Random(base_seed + i)
        i += 1
        params = resolve_params(args, rng)
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


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
        print(asp_program("#show valid_story/3."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print("  ", t)
        return

    samples = generate_many(args)

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
            header = f"### {p.hero}: tortilla={p.tortilla}, setting={p.setting}, problem={p.problem}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
