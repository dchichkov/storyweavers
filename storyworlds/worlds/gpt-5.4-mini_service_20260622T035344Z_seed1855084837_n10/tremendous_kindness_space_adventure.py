#!/usr/bin/env python3
"""
storyworlds/worlds/tremendous_kindness_space_adventure.py
=========================================================

A small storyworld about a space adventure where kindness changes the mission.
A child astronaut faces a problem among stars, chooses a gentle action, and the
world state proves the change in the ending image.

Seed idea:
---
A young space explorer travels with a robot and a small crew. A ship problem or
lost tool makes the mission tense, but kindness helps them share, repair, and
return home with a tremendous new feeling of trust.

This script keeps the domain compact:
- typed entities with physical meters and emotional memes
- a forward-chaining rule or two
- a reasonableness gate
- a Python/ASP twin
- three QA sets grounded in the simulated world
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
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id


@dataclass
class Ship:
    id: str
    name: str
    setting: str
    station: str
    sky: str
    travel: str
    mission: str
    problem: str
    hazard: str
    rescue: str
    ending: str


@dataclass
class Mission:
    id: str
    clue: str
    event: str
    risk: str
    fix: str
    result: str
    noun: str
    tool: str
    location: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, ...]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.ship)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.history = copy.deepcopy(self.history)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    ship: str
    mission: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    adult: str
    adult_type: str
    seed: Optional[int] = None


SHIPS = {
    "lullaby": Ship("lullaby", "the Lullaby", "a silver ship", "Moon Station", "the starry sky", "floated", "a supply run", "a broken hatch latch", "a missing bolt", "a bright repair light", "home safe"),
    "comet": Ship("comet", "the Comet", "a blue ship", "Orbit Station", "the deep sky", "glided", "a map delivery", "a stuck drawer", "a tiny key", "a lantern lamp", "home happy"),
}

MISSIONS = {
    "hatch": Mission("hatch", "the hatch latch had slipped loose", "a tremble rattled the airlock", "air could leak out", "find the tiny bolt and share the work", "the hatch held tight again", "bolt", "bolt kit", "airlock"),
    "drawer": Mission("drawer", "the storage drawer had jammed shut", "a tool slid under a bench", "the crew might miss a needed piece", "ask everyone to help search gently", "the missing tool came back", "tool", "search light", "cargo bay"),
}

HERO_NAMES = ["Mia", "Noah", "Lina", "Toby", "Zuri", "Eli", "Nora", "Ari"]
HELPER_NAMES = ["Pip", "Robo", "Kai", "Nell", "Juno", "Bex"]
ADULT_NAMES = ["Captain Sol", "Commander Vale", "Engineer Remy", "Pilot Sera"]

TYPES = {
    "girl": {"boy", "girl"},
    "boy": {"boy", "girl"},
}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for ship in SHIPS:
        for mission in MISSIONS:
            combos.append((ship, mission))
    return combos


def _hero_pool(hero_type: str) -> list[str]:
    return HERO_NAMES if hero_type == "girl" else HERO_NAMES + ["Leo", "Finn", "Owen", "Max"]


def _helper_pool() -> list[str]:
    return HELPER_NAMES


def _adult_pool() -> list[str]:
    return ADULT_NAMES


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld about kindness.")
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy", "robot"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("-n", "--n", type=int, default=1)
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
              if (args.ship is None or c[0] == args.ship)
              and (args.mission is None or c[1] == args.mission)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    ship, mission = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy", "robot"])
    adult_type = args.adult_type or rng.choice(["woman", "man"])
    hero = args.hero or rng.choice(_hero_pool(hero_type))
    helper = args.helper or rng.choice(_helper_pool())
    adult = args.adult or rng.choice(_adult_pool())
    return StoryParams(ship=ship, mission=mission, hero=hero, hero_type=hero_type,
                       helper=helper, helper_type=helper_type, adult=adult,
                       adult_type=adult_type)


def build_world(params: StoryParams) -> World:
    if params.ship not in SHIPS:
        raise StoryError("Unknown ship.")
    if params.mission not in MISSIONS:
        raise StoryError("Unknown mission.")
    ship = SHIPS[params.ship]
    mission = MISSIONS[params.mission]
    world = World(ship)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper))
    adult = world.add(Entity(id="adult", kind="character", type=params.adult_type, label=params.adult))
    tool = world.add(Entity(id="tool", type="thing", label=mission.noun, phrase=mission.tool, caretaker="adult", owner="ship"))
    place = world.add(Entity(id="place", type="place", label=mission.location))
    helper.memes["kindness"] += 1
    hero.memes["wonder"] += 1
    adult.memes["care"] += 1
    world.facts.update(hero=hero, helper=helper, adult=adult, tool=tool, place=place, ship=ship, mission=mission)
    return world


def _predict_mishap(world: World, params: StoryParams) -> bool:
    sim = world.copy()
    mission = sim.facts["mission"]
    if params.mission == "hatch":
        sim.get("place").meters["danger"] += 1
        sim.get("tool").meters["lost"] += 1
    else:
        sim.get("tool").meters["lost"] += 1
    return sim.get("place").meters["danger"] >= THRESHOLD or sim.get("tool").meters["lost"] >= THRESHOLD


def tell(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    adult = world.facts["adult"]
    tool = world.facts["tool"]
    place = world.facts["place"]
    ship = world.ship
    mission = world.facts["mission"]

    hero.memes["hope"] += 1
    helper.memes["kindness"] += 1
    adult.memes["calm"] += 1

    world.say(f"On {ship.setting}, {hero.label} and {helper.label} floated through the ship with {ship.name} shining above them.")
    world.say(f"They were on {ship.mission}, and {mission.event} made the mission feel {ship.problem}.")

    world.para()
    world.say(f"{hero.label} wanted to fix it fast, but {helper.label} noticed the trouble first.")
    if _predict_mishap(world, StoryParams(ship=ship.id, mission=mission.id, hero=hero.label, hero_type=hero.type, helper=helper.label, helper_type=helper.type, adult=adult.label, adult_type=adult.type)):
        hero.memes["worry"] += 1
        world.say(f'"That could get worse," {helper.label} said softly. "{mission.fix.capitalize()}."')

    mission_fix = False
    if mission.id == "hatch":
        world.get("place").meters["danger"] += 1
        hero.memes["responsibility"] += 1
        helper.memes["kindness"] += 1
        world.say(f"{hero.label} passed the tiny bolt to {adult.label}, and {adult.label} held the hatch steady while {helper.label} lined it up.")
        world.say(f"That gentle teamwork was {mission.result}, and the ship felt solid again.")
        mission_fix = True
    else:
        world.say(f"{helper.label} used a search light, and {hero.label} looked under the bench with careful hands.")
        world.say(f"{adult.label} smiled at how they shared the job, and {mission.result} after the lost piece came back.")
        mission_fix = True

    world.para()
    if mission_fix:
        hero.memes["joy"] += 1
        helper.memes["joy"] += 1
        adult.memes["pride"] += 1
        world.say(f"In the final glow, {ship.name} drifted on toward {ship.ending}, and {hero.label} felt a tremendous kind of courage that came from being kind.")
    world.event("story", ship=ship.id, mission=mission.id, fixed=mission_fix)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    ship = f["ship"]
    mission = f["mission"]
    return [
        f'Write a short space adventure for a 3-to-5-year-old that includes the word "tremendous" and shows kindness helping {hero.label} on {ship.name}.',
        f"Tell a gentle space story where {helper.label} helps {hero.label} fix a ship problem on {ship.name} with kindness.",
        f'Write a child-friendly space adventure about teamwork, a little danger, and a tremendous ending on {ship.setting}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    adult = f["adult"]
    ship = f["ship"]
    mission = f["mission"]
    place = f["place"]
    qa = [
        QAItem(
            question=f"Who was the story about on {ship.name}?",
            answer=f"It was about {hero.label}, who worked with {helper.label} and {adult.label} on {ship.mission}. They were all inside {ship.setting} when the problem came up.",
        ),
        QAItem(
            question=f"What problem made the mission tense at {place.label}?",
            answer=f"{mission.clue.capitalize()}. That was risky because {mission.risk}, so the crew had to slow down and help each other.",
        ),
        QAItem(
            question=f"How did {helper.label} help {hero.label}?",
            answer=f"{helper.label} helped with kindness by staying calm, sharing the job, and pointing to the right fix. That made it easier for {hero.label} to do the brave thing without panicking.",
        ),
    ]
    if world.get("place").meters.get("danger", 0) >= THRESHOLD:
        qa.append(QAItem(
            question=f"Why did the adult step in during the {mission.noun} problem?",
            answer=f"{adult.label} stepped in because the mission could become unsafe if nobody acted carefully. The adult's help kept the ship steady and protected the crew.",
        ))
    qa.append(QAItem(
        question=f"What changed at the end of the adventure?",
        answer=f"The trouble was solved, the ship felt safe again, and {hero.label} finished the day feeling tremendous courage. Kindness turned the scary part into a happy ending image.",
    ))
    return qa


WORLD_KNOWLEDGE = {
    "tremendous": QAItem(
        question="What does tremendous mean?",
        answer="Tremendous means very, very big or very strong. People often use it to show that something feels amazing.",
    ),
    "space": QAItem(
        question="What is space?",
        answer="Space is the huge area beyond Earth where stars, planets, and ships can float. It is quiet and very wide.",
    ),
    "kindness": QAItem(
        question="What is kindness?",
        answer="Kindness means helping, sharing, or speaking gently so someone feels cared for. It can make a hard moment feel safer.",
    ),
    "robot": QAItem(
        question="What can a robot do in a story?",
        answer="A robot can help with simple jobs, carry tools, or watch for trouble. In stories, robots often work with people as helpful partners.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["mission"].id, "space", "kindness", "tremendous"}
    out = []
    for key, item in WORLD_KNOWLEDGE.items():
        if key in tags:
            out.append(item)
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
mission_ok(S, M) :- ship(S), mission(M).
kindness_help(H, K) :- hero(H), helper(K).
tremendous_end(M) :- mission(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SHIPS:
        lines.append(asp.fact("ship", s))
    for m in MISSIONS:
        lines.append(asp.fact("mission", m))
    lines.append(asp.fact("word", "tremendous"))
    lines.append(asp.fact("feature", "kindness"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show mission_ok/2."))
    return sorted(set(asp.atoms(model, "mission_ok")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between Python and ASP:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        return 1
    print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    return 0


CURATED = [
    StoryParams(ship="lullaby", mission="hatch", hero="Mia", hero_type="girl", helper="Pip", helper_type="robot", adult="Captain Sol", adult_type="woman"),
    StoryParams(ship="comet", mission="drawer", hero="Noah", hero_type="boy", helper="Kai", helper_type="boy", adult="Commander Vale", adult_type="man"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.ship is None or c[0] == args.ship)
              and (args.mission is None or c[1] == args.mission)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    ship, mission = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy", "robot"])
    adult_type = args.adult_type or rng.choice(["woman", "man"])
    hero = args.hero or rng.choice(_hero_pool(hero_type))
    helper = args.helper or rng.choice(_helper_pool())
    adult = args.adult or rng.choice(_adult_pool())
    return StoryParams(ship=ship, mission=mission, hero=hero, hero_type=hero_type,
                       helper=helper, helper_type=helper_type, adult=adult,
                       adult_type=adult_type)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print(asp_program("#show mission_ok/2."))
        return
    if args.verify:
        try:
            sample = generate(CURATED[0])
            if not sample.story:
                print("Smoke test failed: empty story.")
                sys.exit(1)
        except Exception as exc:
            print(f"Smoke test failed: {exc}")
            sys.exit(1)
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (ship, mission) combos:\n")
        for ship, mission in combos:
            print(f"  {ship:10} {mission}")
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
            header = f"### {p.hero} on {p.ship} ({p.mission})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
