#!/usr/bin/env python3
"""
A standalone story world for a tiny Space Adventure domain.

Premise seed:
- tremor
- wander
- Cautionary
- Teamwork

The story world models a small crew aboard a space vessel where a cautionary
tremor warns of danger, one character wanders into the wrong module, and the
teamworks together to fix the problem before anything drifts into space.
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
class CrewMember:
    id: str
    role: str
    label: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"drift": 0.0, "alert": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"caution": 0.0, "teamwork": 0.0, "worry": 0.0})
    location: str = "bridge"

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class Module:
    id: str
    label: str
    safe: bool = True
    sealed: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"tremor": 0.0, "damage": 0.0})


@dataclass
class StoryParams:
    setting: str = "space station"
    hero: str = "Mina"
    partner: str = "Jace"
    ship: str = "Aurora"
    seed: Optional[int] = None


@dataclass
class World:
    crew: dict[str, CrewMember] = field(default_factory=dict)
    modules: dict[str, Module] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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

HEROES = [
    ("Mina", "pilot"),
    ("Juno", "engineer"),
    ("Tari", "scanner"),
    ("Lio", "navigator"),
    ("Nova", "cadet"),
]

PARTNERS = [
    ("Jace", "engineer"),
    ("Pip", "mechanic"),
    ("Rin", "navigator"),
    ("Sol", "medic"),
    ("Vera", "pilot"),
]

SHIPS = [
    "Aurora",
    "Comet Star",
    "Skyline",
    "Lantern",
]

SETTINGS = {
    "space station": "space station",
    "research ship": "research ship",
    "moon base": "moon base",
}

MODULES = {
    "bridge": Module(id="bridge", label="bridge", safe=True),
    "corridor": Module(id="corridor", label="corridor", safe=True),
    "lab": Module(id="lab", label="science lab", safe=True),
    "hull": Module(id="hull", label="outer hull", safe=False),
    "airlock": Module(id="airlock", label="airlock", safe=False),
}


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/1.
#show warning/1.

valid(Story) :- story(Story), tremor(Story), wander(Story), teamwork(Story), cautionary(Story).

warning(Story) :- valid(Story), risk(Story).

% A story is reasonable only when the tremor creates a real risk,
% the wandering creates a problem, and teamwork resolves it.
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("story", "space_adventure"),
        asp.fact("tremor", "space_adventure"),
        asp.fact("wander", "space_adventure"),
        asp.fact("teamwork", "space_adventure"),
        asp.fact("cautionary", "space_adventure"),
        asp.fact("risk", "space_adventure"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    ok = any(sym.name == "valid" and sym.arguments[0].string == "space_adventure" for sym in model)
    if ok:
        print("OK: ASP gate accepts the space adventure story shape.")
        return 0
    print("MISMATCH: ASP gate rejected the story shape.")
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def reasonableness_check(params: StoryParams) -> None:
    if not params.hero or not params.partner:
        raise StoryError("A story needs both a hero and a teammate.")
    if params.hero == params.partner:
        raise StoryError("The hero and partner must be different characters.")
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.ship not in SHIPS:
        raise StoryError("Unknown ship name.")


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World()
    hero_name, hero_role = next((n, r) for n, r in HEROES if n == params.hero)
    partner_name, partner_role = next((n, r) for n, r in PARTNERS if n == params.partner)

    world.crew["hero"] = CrewMember(id="hero", role=hero_role, label=hero_name, traits=["curious", "cautious"], location="bridge")
    world.crew["partner"] = CrewMember(id="partner", role=partner_role, label=partner_name, traits=["steady", "helpful"], location="bridge")

    for mid, mod in MODULES.items():
        world.modules[mid] = Module(id=mod.id, label=mod.label, safe=mod.safe, sealed=mod.sealed)

    world.facts["setting"] = params.setting
    world.facts["ship"] = params.ship
    world.facts["hero_name"] = hero_name
    world.facts["partner_name"] = partner_name
    return world


def raise_tremor(world: World) -> None:
    for module in world.modules.values():
        if module.id in {"hull", "airlock"}:
            module.meters["tremor"] += 1.0
    world.crew["hero"].memes["caution"] += 1.0
    world.crew["partner"].memes["worry"] += 1.0
    world.say(
        f"On the {world.facts['ship']}, a soft tremor shivered through the walls. "
        f"{world.crew['hero'].label} felt it first and looked up from the console."
    )


def wander_into_risk(world: World) -> None:
    hero = world.crew["hero"]
    hero.location = "airlock"
    hero.meters["drift"] += 1.0
    hero.memes["caution"] += 0.5
    world.say(
        f"{hero.label} wandered toward the airlock, curious about a blinking light. "
        f"That was the wrong place to wander when the ship was already trembling."
    )


def team_up(world: World) -> None:
    hero = world.crew["hero"]
    partner = world.crew["partner"]
    hero.memes["teamwork"] += 1.0
    partner.memes["teamwork"] += 1.0
    partner.location = "airlock"
    world.modules["airlock"].sealed = True
    world.modules["airlock"].meters["damage"] = 0.0
    hero.location = "bridge"
    hero.meters["drift"] = 0.0
    world.say(
        f"{partner.label} rushed over, and the two of them worked side by side. "
        f"They sealed the airlock, steadied the loose panel, and guided {hero.label} safely back to the bridge."
    )


def finish(world: World) -> None:
    hero = world.crew["hero"]
    partner = world.crew["partner"]
    world.para()
    world.say(
        f"When the tremor faded, the ship was quiet again. "
        f"{hero.label} promised to pause and check first next time, and {partner.label} smiled because teamwork had kept everyone safe."
    )
    world.say(
        f"From then on, the {world.facts['ship']} felt less scary and more like a place where careful friends could solve trouble together."
    )
    world.facts["resolved"] = True
    world.facts["hero"] = hero
    world.facts["partner"] = partner


def generate_story(params: StoryParams) -> World:
    reasonableness_check(params)
    world = build_world(params)
    world.say(
        f"{params.hero} and {params.partner} lived and worked on the {params.ship}, a {params.setting} with bright screens and humming lights."
    )
    world.say(
        f"{params.hero} was a cautious little {world.crew['hero'].role}, and {params.partner} was a steady {world.crew['partner'].role} who liked helping."
    )
    world.para()
    raise_tremor(world)
    wander_into_risk(world)
    world.para()
    team_up(world)
    finish(world)
    world.facts["risk"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short cautionary space adventure about a trembling ship and a team that solves the problem together.",
        f"Tell a child-friendly story about {world.facts['hero_name']} and {world.facts['partner_name']} on the {world.facts['ship']}.",
        "Make the story include a tremor, a wandering mistake, and a teamwork ending that feels safe and hopeful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero_name"]
    partner = world.facts["partner_name"]
    ship = world.facts["ship"]
    return [
        QAItem(
            question=f"Where did {hero} and {partner} work together?",
            answer=f"They worked together on the {ship}, a space setting with a bridge and a tricky airlock.",
        ),
        QAItem(
            question=f"What problem first made {hero} pay attention?",
            answer=f"A soft tremor shook the ship, which was a cautionary sign that something might go wrong.",
        ),
        QAItem(
            question=f"What did {hero} do that was risky?",
            answer=f"{hero} wandered toward the airlock when the ship was already trembling.",
        ),
        QAItem(
            question=f"How did the crew solve the problem?",
            answer=f"{partner} and {hero} used teamwork to seal the airlock, steady the loose panel, and get back to safety.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tremor?",
            answer="A tremor is a small shake or vibration that can be a warning that something is not stable.",
        ),
        QAItem(
            question="Why should someone be careful near an airlock?",
            answer="An airlock opens to the outside of a ship, so it needs to stay sealed and safe before anyone uses it.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together to solve a problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny cautionary teamwork space adventure storyworld.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--hero", choices=[n for n, _ in HEROES])
    ap.add_argument("--partner", choices=[n for n, _ in PARTNERS])
    ap.add_argument("--ship", choices=SHIPS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice([n for n, _ in HEROES])
    partner = args.partner or rng.choice([n for n, _ in PARTNERS if n != hero])
    ship = args.ship or rng.choice(SHIPS)
    params = StoryParams(setting=setting, hero=hero, partner=partner, ship=ship, seed=args.seed)
    reasonableness_check(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = generate_story(params)
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
        print()
        print("--- world trace ---")
        for cm in sample.world.crew.values():
            print(cm.id, cm.label, cm.role, cm.location, cm.meters, cm.memes)
        for mod in sample.world.modules.values():
            print(mod.id, mod.label, mod.sealed, mod.meters)
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_check() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    ok = any(sym.name == "valid" and sym.arguments[0].name == "space_adventure" for sym in model)
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="space station", hero="Mina", partner="Jace", ship="Aurora"),
    StoryParams(setting="research ship", hero="Juno", partner="Pip", ship="Comet Star"),
    StoryParams(setting="moon base", hero="Nova", partner="Rin", ship="Lantern"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/1.\n#show warning/1."))
        return
    if args.verify:
        sys.exit(asp_check())
    if args.asp:
        print(asp_program("#show valid/1."))
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### story {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
