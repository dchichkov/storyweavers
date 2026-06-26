#!/usr/bin/env python3
"""
A tiny adventure storyworld about a mower contest in a tropic garden,
driven by inner monologue and a misunderstanding that gets resolved.

The source seed suggests:
- mower
- contest
- tropic
- inner monologue
- misunderstanding
- Adventure style

This script builds a small simulated domain where a child hero joins a
tropical yard contest, misreads a judge's signal, worries in an inner monologue,
and then learns the judge actually meant something friendly and helpful.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    tropical: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "tropic_garden": Setting(place="the tropic garden", tropical=True, affords={"contest", "mow"}),
    "palm_courtyard": Setting(place="the palm courtyard", tropical=True, affords={"contest"}),
}

ACTIVITIES = {
    "contest": Activity(
        id="contest",
        verb="join the contest",
        gerund="competing in the contest",
        rush="run to the contest rope",
        mess="nervous",
        soil="shaky and loud",
        keyword="contest",
        tags={"contest", "adventure"},
    ),
    "mow": Activity(
        id="mow",
        verb="mow the grass",
        gerund="mowing the grass",
        rush="dash toward the mower",
        mess="grass",
        soil="full of clippings",
        keyword="mower",
        tags={"mower", "grass", "adventure"},
    ),
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a bright contest shirt", type="shirt", region="torso"),
    "hat": Prize(label="hat", phrase="a sun hat with a green ribbon", type="hat", region="head"),
}

GEAR = {
    "gloves": Gear(
        id="gloves",
        label="garden gloves",
        guards={"grass"},
        prep="put on garden gloves first",
        tail="slipped on the garden gloves",
    ),
    "band": Gear(
        id="wristband",
        label="a bright wristband",
        guards={"nervous"},
        prep="take a deep breath and wear a bright wristband",
        tail="wore the bright wristband",
    ),
}

NAMES_GIRL = ["Mina", "Lina", "Tara", "Nora"]
NAMES_BOY = ["Pico", "Jules", "Ben", "Theo"]
TRAITS = ["curious", "brave", "quick", "spirited"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    judge = world.get("judge")
    if hero.memes.get("misread", 0) >= THRESHOLD and not world.facts.get("clarified"):
        world.facts["clarified"] = True
        out.append(
            f"{judge.label.capitalize()} waved the little flag to point at the mower path, not to send {hero.id} away."
        )
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes.get("calm", 0) >= THRESHOLD and hero.memes.get("fear", 0) >= THRESHOLD:
        if not world.facts.get("calm_seen"):
            world.facts["calm_seen"] = True
            out.append(f"{hero.id} noticed the plan and stood a little straighter.")
    return out


RULES = [Rule("misunderstanding", _r_misunderstanding), Rule("calm", _r_calm)]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                produced.extend(sents)
                changed = True
    for s in produced:
        world.say(s)
    return produced


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: mower contest in a tropic garden.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["judge", "friend"])
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                out.append((place, act, prize))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid story matches those options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(["judge", "friend"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def predict(world: World, hero: Entity, activity: Activity) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**vars(v)) for k, v in world.entities.items()}
    sim.get("hero").memes["fear"] = sim.get("hero").memes.get("fear", 0) + 1
    sim.get("hero").memes["misread"] = sim.get("hero").memes.get("misread", 0) + 1
    if activity.id == "mow":
        sim.get("hero").meters["grass"] = sim.get("hero").meters.get("grass", 0) + 1
    return {"tension": sim.get("hero").memes.get("fear", 0), "misread": sim.get("hero").memes.get("misread", 0)}


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name, traits=[params.trait]))
    helper = world.add(Entity(id="judge", kind="character", type="man", label=params.helper))
    prize = world.add(Entity(id="prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase))
    prize.worn_by = hero.id
    world.facts.update(hero=hero, helper=helper, prize=prize, activity=ACTIVITIES[params.activity], params=params)
    return world


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    hero = world.get("hero")
    helper = world.get("judge")
    prize = world.get("prize")
    activity = world.facts["activity"]

    world.say(f"{hero.label} was a {params.trait} little {params.gender} who loved adventure in {world.setting.place}.")
    world.say(f"{hero.label} wore {prize.phrase} and dreamed of the day {hero.pronoun()} could {activity.verb}.")
    world.para()
    world.say(f"One bright day, the tropic garden buzzed with a contest near the mower path.")
    world.say(f"{hero.label} wanted to go fast, but {helper.label} lifted a hand and pointed toward the mower.")
    hero.memes["fear"] = 1
    hero.memes["misread"] = 1
    world.say(f"In {hero.label}'s head, that looked serious. {hero.label} thought, 'Maybe the contest is over, and I did something wrong.'")
    world.say(f"{hero.label} felt a knot of worry and almost turned back.")
    propagate(world)
    world.para()
    if activity.id == "mow":
        world.say(f"Then {helper.label} smiled and showed {hero.label} the safe lane beside the mower.")
        world.say(f"{helper.label} said the contest was to mow a neat line, not to chase the machine.")
        gear = GEAR["gloves"]
        world.say(f"{helper.label} asked {hero.label} to {gear.prep} before starting.")
        hero.memes["calm"] = 1
        hero.meters["grass"] = 1
        world.say(f"{hero.label} took the gloves, breathed in the warm green air, and began {activity.gerund}.")
        world.say(f"At the end, the grass looked tidy, {prize.label} stayed clean, and the contest ribbon shone in the tropic light.")
    else:
        world.say(f"Then {helper.label} laughed softly and explained the flag was only marking the contest start.")
        world.say(f"{hero.label} smiled, because the warning was really an invitation.")
        hero.memes["calm"] = 1
        world.say(f"Soon {hero.label} was {activity.gerund}, and the sunny contest felt like a treasure hunt through the palms.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    a = world.facts["activity"]
    return [
        f"Write an adventure story about a {p.gender} named {p.name} in a tropic garden contest with a mower.",
        f"Tell a child-friendly adventure where {p.name} misunderstands {p.helper}'s signal and then learns the real plan.",
        f"Write a short story about {a.keyword} and a contest in the tropic garden with a happy correction.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    prize = world.facts["prize"]
    activity = world.facts["activity"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, a {p.trait} little {p.gender} who goes to a tropic garden contest."
        ),
        QAItem(
            question=f"What did {hero.label} misunderstand about {helper.label}'s signal?",
            answer=f"{hero.label} thought {helper.label} was sending {hero.label} away, but the signal was really pointing to the mower path and the contest start."
        ),
        QAItem(
            question=f"What happened to {prize.label} at the end?",
            answer=f"{prize.label.capitalize()} stayed clean while {hero.label} took part in {activity.gerund} and finished the contest happily."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a contest?", answer="A contest is a game or event where people try their best and someone can win or earn praise."),
        QAItem(question="What is a mower?", answer="A mower is a machine used to cut grass short and neat."),
        QAItem(question="What does tropic mean?", answer="Tropic means warm and sunny, with plants that like hot weather."),
        QAItem(question="What is a misunderstanding?", answer="A misunderstanding happens when someone thinks something means one thing, but it really means something else."),
        QAItem(question="What is an inner monologue?", answer="An inner monologue is the private voice in a character's head, where they think about what is happening."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts.keys()}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
% A story is valid when it takes place in a setting that affords the activity.
valid(Place, Activity, Prize) :- affords(Place, Activity), activity(Activity), prize(Prize).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.tropical:
            lines.append(asp.fact("tropical", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    try:
        asp_set = set(asp_valid_combos())
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    if asp_set == py:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only in ASP:", sorted(asp_set - py))
    print("only in Python:", sorted(py - asp_set))
    return 1


CURATED = [
    StoryParams(place="tropic_garden", activity="mow", prize="shirt", name="Mina", gender="girl", helper="judge", trait="curious"),
    StoryParams(place="palm_courtyard", activity="contest", prize="hat", name="Pico", gender="boy", helper="friend", trait="brave"),
]


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(["judge", "friend"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
