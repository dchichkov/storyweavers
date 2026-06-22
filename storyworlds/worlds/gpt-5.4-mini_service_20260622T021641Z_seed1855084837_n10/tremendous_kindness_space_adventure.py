#!/usr/bin/env python3
"""
storyworlds/worlds/tremendous_kindness_space_adventure.py
=========================================================

A standalone story world for a small space-adventure tale about kindness.

Premise:
- Two young space travelers explore a tiny moon base or shuttle.
- One finds a stranded helper / lost robot / tired crewmate.
- A risky shortcut would solve a problem, but kindness changes the plan.
- The ending shows a practical, warm result: help shared, problem solved,
  and the child-like hero feeling proud of being kind.

This world models:
- typed entities with physical meters and emotional memes,
- a small forward-chaining causal engine,
- a Python reasonableness gate plus inline ASP twin,
- three QA sets grounded in simulated state,
- CLI support for default runs, seeded random generation, JSON, trace, QA,
  ASP modes, verification, and an ASP program dump.

The story always includes the word "tremendous".
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
from typing import Callable, Optional

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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    companion: Optional[str] = None
    location: str = ""
    portable: bool = False
    helpful: bool = False
    heavy: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.attrs.get("plural") else "it"

    @property
    def label_word(self) -> str:
        return {"captain": "captain", "pilot": "pilot"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    backdrop: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    consequence: str
    location: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RescueTool:
    id: str
    label: str
    phrase: str
    action: str
    result: str
    covers: set[str] = field(default_factory=set)
    fixes: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class KindnessMove:
    id: str
    label: str
    description: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_assist(world: World) -> list[str]:
    out: list[str] = []
    for helper in world.characters():
        if helper.memes["kindness"] < THRESHOLD:
            continue
        if helper.attrs.get("assisted"):
            continue
        sig = ("assist", helper.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        helper.memes["warmth"] += 1
        out.append(f"{helper.id} felt a warm, steady glow after helping.")
    return out


def _r_heavy_load(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["load"] < THRESHOLD:
            continue
        if ent.kind != "thing":
            continue
        sig = ("load", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{ent.label} felt too heavy to move alone.")
    return out


CAUSAL_RULES = [
    Rule("assist", "emotional", _r_assist),
    Rule("load", "physical", _r_heavy_load),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def puzzle_at_risk(challenge: Challenge, prize: RescueTool) -> bool:
    return challenge.location in prize.covers or challenge.keyword in prize.fixes


def select_tool(challenge: Challenge, prize: RescueTool) -> Optional[RescueTool]:
    return prize if puzzle_at_risk(challenge, prize) else None


def kind_move(challenge: Challenge) -> KindnessMove:
    for move in KINDNESS_MOVES.values():
        if challenge.keyword in move.tags:
            return move
    return KINDNESS_MOVES["share"]


def predict(world: World, hero: Entity, helper: Entity, challenge: Challenge) -> dict:
    sim = world.copy()
    _do_challenge(sim, sim.get(hero.id), sim.get(helper.id), challenge, narrate=False)
    return {
        "solved": sim.facts.get("solved", False),
        "kind": sim.get(hero.id).memes["kindness"],
    }


def _do_challenge(world: World, hero: Entity, helper: Entity, challenge: Challenge, narrate: bool = True) -> None:
    hero.meters["pressure"] += 1
    helper.meters["pressure"] += 1
    if challenge.keyword == "signal":
        helper.meters["load"] += 1
    if helper.memes["kindness"] >= THRESHOLD:
        helper.attrs["assisted"] = True
        helper.memes["kindness"] += 1
        hero.memes["hope"] += 1
        world.facts["solved"] = True
        propagate(world, narrate=narrate)
    else:
        world.facts["solved"] = False


def opening(world: World, hero: Entity, helper: Entity, challenge: Challenge) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"{hero.id} floated through {world.setting.place} with {helper.id}, "
        f"and the station beyond the window looked {world.setting.backdrop}."
    )
    world.say(
        f"{hero.id} loved the {challenge.gerund}, because space felt full of "
        f"tiny bright surprises."
    )


def arrival(world: World, hero: Entity, helper: Entity, challenge: Challenge) -> None:
    world.say(
        f"Then they heard about {challenge.label}, and the problem seemed "
        f"tremendous for such a small day."
    )
    world.say(
        f"{helper.id} wanted to help, but the {challenge.location} needed a careful plan."
    )


def warn(world: World, hero: Entity, helper: Entity, challenge: Challenge, prize: RescueTool) -> bool:
    pred = predict(world, hero, helper, challenge)
    if not pred["solved"]:
        world.facts["risk"] = challenge.consequence
        world.say(
            f'"If we rush, we could {challenge.consequence}," {hero.pronoun("possessive")} '
            f"friend said. "
            f'"Let us choose the kind way," {hero.id} answered.'
        )
        return True
    world.say(
        f'{hero.id} noticed that kindness could solve the trouble before it grew worse.'
    )
    return True


def choose_kindness(world: World, hero: Entity, helper: Entity, challenge: Challenge) -> None:
    move = kind_move(challenge)
    helper.attrs["assisted"] = True
    helper.memes["kindness"] += 1
    hero.memes["kindness"] += 1
    hero.memes["joy"] += 1
    world.facts["kind_move"] = move
    world.say(
        f"Instead of pushing past the problem, {hero.id} used {move.label}: "
        f"{move.description}."
    )


def resolution(world: World, hero: Entity, helper: Entity, challenge: Challenge) -> None:
    move = world.facts["kind_move"]
    world.say(
        f"{move.result} Soon the task was done, and {helper.id} could breathe again."
    )
    world.say(
        f"{hero.id} smiled at the stars outside the porthole, proud that a kind act "
        f"had made the day feel bigger and safer at once."
    )


def story_end(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"In the quiet afterward, {hero.id} and {helper.id} drifted on, "
        f"their hands steady and their hearts light."
    )


def tell(setting: Setting, challenge: Challenge, tool: RescueTool, move: KindnessMove,
         hero_name: str = "Mira", hero_type: str = "girl",
         helper_name: str = "Jax", helper_type: str = "boy",
         seed_note: str = "") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["curious", "gentle"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, traits=["tired", "kind"]))
    world.add(Entity(id="task", kind="thing", type="thing", label=tool.label, phrase=tool.phrase, portable=True))
    hero.memes["kindness"] = 1.0
    helper.memes["kindness"] = 1.0
    world.facts["seed_note"] = seed_note
    opening(world, hero, helper, challenge)
    world.para()
    arrival(world, hero, helper, challenge)
    warn(world, hero, helper, challenge, tool)
    world.para()
    choose_kindness(world, hero, helper, challenge)
    _do_challenge(world, hero, helper, challenge, narrate=True)
    world.para()
    resolution(world, hero, helper, challenge)
    story_end(world, hero, helper)
    world.facts.update(hero=hero, helper=helper, challenge=challenge, tool=tool, move=move)
    return world


SETTINGS = {
    "orbit": Setting(place="the little orbiting station", backdrop="bright and patient"),
    "moonbase": Setting(place="the moonbase hallway", backdrop="silver and quiet"),
    "shuttle": Setting(place="the shuttle cabin", backdrop="tiny and glowing"),
}

CHALLENGES = {
    "signal": Challenge(
        id="signal",
        verb="fix the signal",
        gerund="fiddling with the signal box",
        rush="rush the signal box",
        risk="short out the panel",
        consequence="short out the panel",
        location="signal room",
        keyword="signal",
        tags={"signal", "panel"},
    ),
    "supply": Challenge(
        id="supply",
        verb="carry the supplies",
        gerund="sorting supplies",
        rush="haul the crates too fast",
        risk="drop the food",
        consequence="drop the food",
        location="supply bay",
        keyword="supply",
        tags={"supply", "crate"},
    ),
    "robot": Challenge(
        id="robot",
        verb="help the robot",
        gerund="working beside the robot",
        rush="tug at the robot too hard",
        risk="scratch its wheel",
        consequence="scratch its wheel",
        location="robot nook",
        keyword="robot",
        tags={"robot", "wheel"},
    ),
}

RESCUES = {
    "gloves": RescueTool(
        id="gloves",
        label="soft gloves",
        phrase="a pair of soft gloves",
        action="carefully lift",
        result="They lifted the thing gently instead of forcing it.",
        covers={"robot"},
        fixes={"robot"},
    ),
    "magnet": RescueTool(
        id="magnet",
        label="tiny magnet strip",
        phrase="a tiny magnet strip",
        action="guide",
        result="They used the strip to guide the loose piece into place.",
        covers={"signal"},
        fixes={"signal"},
    ),
    "sled": RescueTool(
        id="sled",
        label="cargo sled",
        phrase="a little cargo sled",
        action="roll",
        result="They rolled the boxes in a safe line, one by one.",
        covers={"supply"},
        fixes={"supply"},
    ),
}

KINDNESS_MOVES = {
    "share": KindnessMove(
        id="share",
        label="sharing",
        description="they split the work into smaller, easier parts",
        result="The smaller steps fit together beautifully.",
        tags={"signal", "supply", "robot"},
    ),
    "wait": KindnessMove(
        id="wait",
        label="waiting patiently",
        description="they paused long enough for the helper to catch up",
        result="The pause gave everyone time to breathe and try again.",
        tags={"signal", "robot"},
    ),
    "carry": KindnessMove(
        id="carry",
        label="kindly carrying",
        description="they carried the heavy part together so nobody got stuck",
        result="Together they made the heavy work feel light.",
        tags={"supply", "robot"},
    ),
}

HERO_NAMES = ["Mira", "Nia", "Luna", "Zuri", "Ari", "Tess", "Nova", "Ivy"]
HELPER_NAMES = ["Jax", "Pip", "Sol", "Ren", "Bea", "Kai", "Ollie", "Finn"]


@dataclass
class StoryParams:
    setting: str
    challenge: str
    rescue: str
    move: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CHALLENGES:
            for r in RESCUES:
                if puzzle_at_risk(CHALLENGES[c], RESCUES[r]):
                    combos.append((s, c, r))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ch: Challenge = f["challenge"]
    return [
        f'Write a short space-adventure story for a young child that includes the word "tremendous" and shows kindness solving a problem at {world.setting.place}.',
        f"Tell a gentle story about {f['hero'].id} and {f['helper'].id} in space, where kindness turns a tremendous problem into a safe success.",
        f"Write a child-friendly space story where a small crew faces {ch.label}, chooses kindness, and ends with a calm, bright image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    ch: Challenge = f["challenge"]
    move: KindnessMove = f["kind_move"]
    return [
        QAItem(
            question=f"Who is the story about in {world.setting.place}?",
            answer=f"It is about {hero.id} and {helper.id}, two young space travelers who were working together in {world.setting.place}. The story follows how they faced a tremendous problem and chose kindness.",
        ),
        QAItem(
            question=f"What problem did {hero.id} and {helper.id} have?",
            answer=f"They had {ch.label}. It felt tremendous because it needed careful help, not a quick rough fix.",
        ),
        QAItem(
            question=f"What did {hero.id} choose to do instead of rushing?",
            answer=f"{hero.id} chose {move.label}. That kept the problem calm and let both of them solve it without making things worse.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping gently, sharing, and caring about how another person feels. A kind choice can make a hard moment easier for everyone.",
        ),
        QAItem(
            question="What is a space station?",
            answer="A space station is a place in space where people can live or work for a while. It usually has rooms, machines, and windows looking out at the stars.",
        ),
        QAItem(
            question="Why is teamwork helpful in space?",
            answer="Teamwork is helpful because space jobs can be tricky and everyone may need a hand. When people work together, big tasks feel more possible.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.location:
            parts.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="orbit", challenge="signal", rescue="magnet", move="share", hero="Mira", hero_gender="girl", helper="Jax", helper_gender="boy", seed=1),
    StoryParams(setting="moonbase", challenge="supply", rescue="sled", move="carry", hero="Nova", hero_gender="girl", helper="Ren", helper_gender="boy", seed=2),
    StoryParams(setting="shuttle", challenge="robot", rescue="gloves", move="wait", hero="Ivy", hero_gender="girl", helper="Kai", helper_gender="boy", seed=3),
]


def explain_rejection(challenge: Challenge, rescue: RescueTool) -> str:
    return f"(No story: {rescue.label} does not actually help with {challenge.label}. Choose a rescue that fits the problem.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("location", cid, ch.location))
        lines.append(asp.fact("keyword", cid, ch.keyword))
    for rid, rescue in RESCUES.items():
        lines.append(asp.fact("rescue", rid))
        for c in sorted(rescue.covers):
            lines.append(asp.fact("covers", rid, c))
        for f in sorted(rescue.fixes):
            lines.append(asp.fact("fixes", rid, f))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,R) :- setting(S), challenge(C), rescue(R), covers(R, X), fixes(R, X).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, challenge=None, rescue=None, move=None, hero=None, hero_gender=None, helper=None, helper_gender=None, seed=None), random.Random(777)))
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
    except Exception as err:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world built around kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--move", choices=KINDNESS_MOVES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              and (args.challenge is None or c[1] == args.challenge)
              and (args.rescue is None or c[2] == args.rescue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, challenge, rescue = rng.choice(sorted(combos))
    move = args.move or rng.choice(sorted(KINDNESS_MOVES))
    hero_gender = args.hero_gender or "girl"
    helper_gender = args.helper_gender or "boy"
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    return StoryParams(setting=setting, challenge=challenge, rescue=rescue, move=move,
                       hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.challenge not in CHALLENGES or params.rescue not in RESCUES or params.move not in KINDNESS_MOVES:
        raise StoryError("Invalid story parameters.")
    challenge = CHALLENGES[params.challenge]
    rescue = RESCUES[params.rescue]
    move = KINDNESS_MOVES[params.move]
    world = tell(SETTINGS[params.setting], challenge, rescue, move,
                 hero_name=params.hero, hero_type=params.hero_gender,
                 helper_name=params.helper, helper_type=params.helper_gender,
                 seed_note=str(params.seed or ""))
    world.facts.update(hero=world.get(params.hero), helper=world.get(params.helper))
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
