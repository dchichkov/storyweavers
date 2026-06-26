#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/contestant_curiosity_happy_ending_kindness_adventure.py
===============================================================================================================================

A small adventure storyworld about a curious contestant, a kind helper, and a
problem that turns into a happy ending.

The premise is simple: a child enters a gentle contest in a bright setting and
gets a task that seems hard. Curiosity leads to a better method, kindness brings
help, and the story ends with a clear reward and an image of the changed world.

This file follows the Storyweavers storyworld contract:
- standalone stdlib script
- shared result containers imported eagerly
- inline ASP rules with a Python reasonableness gate
- world state with meters and memes
- state-driven prose and grounded Q&A
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
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    danger_meter: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "hands"
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "forest": Setting(place="the forest trail", affords={"bridge", "riddle"}),
    "cove": Setting(place="the bright cove", affords={"bridge"}),
    "fair": Setting(place="the little fairground", affords={"riddle", "bridge"}),
}

CHALLENGES = {
    "bridge": Challenge(
        id="bridge",
        verb="cross the wobbly bridge",
        gerund="crossing the wobbly bridge",
        rush="dash over the bridge",
        risk="the bridge could wobble and scare the path out of shape",
        danger_meter="wobble",
        tags={"adventure", "bridge", "wobble"},
    ),
    "riddle": Challenge(
        id="riddle",
        verb="solve the lantern riddle",
        gerund="solving the lantern riddle",
        rush="blurting out the first guess",
        risk="the wrong guess could leave the lantern dark",
        danger_meter="confusion",
        tags={"adventure", "riddle", "curiosity"},
    ),
}

PRIZES = {
    "ribbon": Prize(
        label="ribbon",
        phrase="a bright ribbon prize",
        type="ribbon",
        region="hands",
        tags={"winner", "happy"},
    ),
    "badge": Prize(
        label="badge",
        phrase="a shiny adventure badge",
        type="badge",
        region="hands",
        tags={"winner", "happy"},
    ),
}

AIDS = {
    "map": Aid(
        id="map",
        label="a hand-drawn map",
        prep="follow a hand-drawn map",
        tail="followed the hand-drawn map",
        helps={"bridge"},
        tags={"curiosity", "adventure"},
    ),
    "lantern": Aid(
        id="lantern",
        label="a small lantern",
        prep="carry a small lantern together",
        tail="carried the small lantern together",
        helps={"riddle"},
        tags={"kindness", "adventure"},
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Ava", "Finn", "Ben", "Zoe", "Maya"]
TRAITS = ["curious", "brave", "kind", "cheerful", "gentle"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def challenge_reaches_prize(challenge: Challenge, prize: Prize) -> bool:
    return True


def select_aid(challenge: Challenge, prize: Prize) -> Optional[Aid]:
    if challenge.id == "bridge":
        return AIDS["map"]
    if challenge.id == "riddle":
        return AIDS["lantern"]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for ch_id in setting.affords:
            ch = CHALLENGES[ch_id]
            for pr_id, pr in PRIZES.items():
                if challenge_reaches_prize(ch, pr) and select_aid(ch, pr):
                    out.append((place, ch_id, pr_id))
    return out


# ---------------------------------------------------------------------------
# Story verbs and world dynamics
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved adventure.")


def wants(world: World, hero: Entity, challenge: Challenge) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(f"{hero.id} wanted to {challenge.verb}, because curiosity kept tugging at {hero.pronoun('possessive')} thoughts.")


def set_out(world: World, hero: Entity, helper: Entity, setting: Setting, challenge: Challenge) -> None:
    world.say(f"One day, {hero.id} and {helper.id} went to {setting.place}.")
    world.say(f"The task there was to {challenge.verb}, and {challenge.risk}.")


def forward_mess(world: World, hero: Entity, challenge: Challenge) -> None:
    if challenge.id == "bridge":
        hero.meters["wobble"] = hero.meters.get("wobble", 0.0) + 1
    else:
        hero.meters["confusion"] = hero.meters.get("confusion", 0.0) + 1


def predict_failure(world: World, hero: Entity, challenge: Challenge) -> bool:
    sim = world.copy()
    forward_mess(sim, sim.get(hero.id), challenge)
    if challenge.id == "bridge":
        return sim.get(hero.id).meters.get("wobble", 0.0) >= THRESHOLD
    return sim.get(hero.id).meters.get("confusion", 0.0) >= THRESHOLD


def warn(world: World, helper: Entity, hero: Entity, prize: Entity, challenge: Challenge) -> None:
    if predict_failure(world, hero, challenge):
        world.say(f"{helper.id} looked at {prize.label} and warned that a rushed try might spoil the happy ending.")


def decide_kindly(world: World, hero: Entity, helper: Entity, challenge: Challenge) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    world.say(f"{hero.id} listened kindly and decided to slow down instead of rushing ahead.")


def receive_aid(world: World, hero: Entity, helper: Entity, aid: Aid) -> None:
    world.say(f"{helper.id} offered {aid.label}, and {hero.id} happily accepted.")
    hero.memes["helped"] = hero.memes.get("helped", 0.0) + 1


def succeed(world: World, hero: Entity, helper: Entity, challenge: Challenge, prize: Entity, aid: Aid) -> None:
    hero.memes["happy"] = hero.memes.get("happy", 0.0) + 1
    hero.meters["wobble"] = 0.0
    hero.meters["confusion"] = 0.0
    world.say(f"They {aid.tail}, and {hero.id} made it through by being curious, careful, and kind.")
    world.say(f"At the end, {hero.id} won {prize.phrase}, and the whole place felt bright and safe.")


def tell(setting: Setting, challenge: Challenge, prize_cfg: Prize, name: str, gender: str, trait: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait, "curious"]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, traits=["kind", "steady"]))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))

    introduce(world, hero)
    wants(world, hero, challenge)
    world.para()
    set_out(world, hero, helper, setting, challenge)
    warn(world, helper, hero, prize, challenge)
    decide_kindly(world, hero, helper, challenge)
    receive_aid(world, hero, helper, select_aid(challenge, prize))
    succeed(world, hero, helper, challenge, prize, select_aid(challenge, prize))

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        challenge=challenge,
        setting=setting,
        aid=select_aid(challenge, prize),
        happy_ending=True,
        curiosity=True,
        kindness=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    challenge: Challenge = f["challenge"]  # type: ignore[assignment]
    prize: Entity = f["prize"]  # type: ignore[assignment]
    return [
        f'Write a short adventure story for a child named {hero.id} who is curious and kind.',
        f"Tell a story where {hero.id} wants to {challenge.verb} and wins {prize.label} with help.",
        f'Write a happy-ending adventure featuring curiosity, kindness, and a simple contest.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    challenge: Challenge = f["challenge"]  # type: ignore[assignment]
    prize: Entity = f["prize"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    aid: Aid = f["aid"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who is the contestant in this adventure story?",
            answer=f"The contestant is {hero.id}, a little {next(t for t in hero.traits if t != 'little')} {hero.type}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {setting.place}?",
            answer=f"{hero.id} wanted to {challenge.verb}.",
        ),
        QAItem(
            question=f"How did {helper.id} help {hero.id} in the story?",
            answer=f"{helper.id} helped by bringing {aid.label} and staying calm and kind.",
        ),
        QAItem(
            question=f"What did {hero.id} win at the end?",
            answer=f"{hero.id} won {prize.phrase}, which made the ending happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone want to look, ask, and learn new things.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle and helpful to someone else.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets solved and things turn out well.",
        ),
        QAItem(
            question="What is an adventure?",
            answer="An adventure is an exciting trip or task where something important has to be done.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
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
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_story(Place, Challenge, Prize) :- setting(Place), affords(Place, Challenge), prize(Prize), challenge(Challenge), has_fix(Challenge, Prize).
has_fix(bridge, ribbon) :- aid(map).
has_fix(bridge, badge) :- aid(map).
has_fix(riddle, ribbon) :- aid(lantern).
has_fix(riddle, badge) :- aid(lantern).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for ch in sorted(s.affords):
            lines.append(asp.fact("affords", sid, ch))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny adventure storyworld about curiosity, kindness, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "sister", "brother"])
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
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(["mother", "father", "sister", "brother"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CHALLENGES[params.challenge], PRIZES[params.prize], params.name, params.gender, params.trait, params.helper)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="forest", challenge="bridge", prize="badge", name="Mia", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="fair", challenge="riddle", prize="ribbon", name="Leo", gender="boy", helper="sister", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
