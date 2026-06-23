#!/usr/bin/env python3
"""
storyworlds/worlds/air_misunderstanding_teamwork_sharing_space_adventure.py
============================================================================

A tiny space-adventure storyworld about a team in a small habitat, a mistaken
fear about the air supply, and a shared fix that proves teamwork.

Premise:
- Two young explorers are inside a little moon habitat.
- One sees the air gauge dipping and misunderstands what it means.
- The team must share tools, space, and calm thinking to solve the problem.
- The ending shows the habitat safe, the air steady, and the friends working
  together.

This is a self-contained stdlib storyworld script. It models physical state
(meters) and emotional state (memes), generates a story plus QA, and includes a
Python reasonableness gate mirrored by inline ASP rules.
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
    role: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

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
class Place:
    id: str
    label: str
    inside: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class AirDevice:
    id: str
    label: str
    phrase: str
    action: str
    helps: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    kind: str
    role: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_air_drop(world: World) -> list[str]:
    out: list[str] = []
    tank = world.get("tank")
    gauge = tank.meters["air"]
    if gauge < THRESHOLD and ("drop",) not in world.fired:
        world.fired.add(("drop",))
        world.get("hab").meters["air_risk"] += 1
        out.append("__air_risk__")
    return out


def _r_hush(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.characters():
        if kid.memes["worry"] < THRESHOLD:
            continue
        sig = ("hush", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["calm"] += 1
        out.append("__calm__")
    return out


CAUSAL_RULES = [_r_air_drop, _r_hush]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule(world)
            if produced:
                changed = True
                lines.extend(x for x in produced if not x.startswith("__"))
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def _simulate_air_use(world: World) -> None:
    tank = world.get("tank")
    tank.meters["air"] -= 1
    if tank.meters["air"] < 0:
        tank.meters["air"] = 0
    propagate(world, narrate=False)


def predict_issue(world: World, use_device: bool) -> dict[str, float]:
    sim = world.copy()
    if use_device:
        _simulate_air_use(sim)
    return {
        "air": sim.get("tank").meters["air"],
        "risk": sim.get("hab").meters["air_risk"],
    }


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES:
        for misunderstanding in MISUNDERSTANDINGS:
            for teamwork in TEAMWORKS:
                if misunderstanding.air_risk and teamwork.fixes_air and place.affords >= {"airlock", "sharing"}:
                    combos.append((place.id, misunderstanding.id, teamwork.id))
    return combos


@dataclass
class StoryParams:
    place: str = ""
    misunderstanding: str = ""
    teamwork: str = ""
    hero: str = ""
    helper: str = ""
    seed: Optional[int] = None


@dataclass
class MisunderstandingCfg:
    id: str
    label: str
    mistaken_reading: str
    truth: str
    concern: str
    air_risk: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class TeamworkCfg:
    id: str
    label: str
    action1: str
    action2: str
    ending: str
    fixes_air: bool = True
    tags: set[str] = field(default_factory=set)


PLACES = [
    Place("hab", "the moon habitat", inside=True, affords={"airlock", "sharing"}),
    Place("rover", "the rover bay", inside=True, affords={"sharing"}),
]

MISUNDERSTANDINGS = [
    MisunderstandingCfg(
        id="low_gauge",
        label="the low air gauge",
        mistaken_reading="the air is almost gone",
        truth="the gauge is only showing that the scrubber needs a reset",
        concern="the habitat might run out of air",
        tags={"air"},
    ),
    MisunderstandingCfg(
        id="hissing_panel",
        label="the hissing panel",
        mistaken_reading="the wall is leaking air",
        truth="a loose cover is making a tiny hiss, not a dangerous leak",
        concern="the habitat could lose its air",
        tags={"air"},
    ),
]

TEAMWORKS = [
    TeamworkCfg(
        id="share_map",
        label="share the job",
        action1="one child checks the gauge",
        action2="the other resets the scrubber",
        ending="their teamwork brings the air back to steady",
        tags={"sharing"},
    ),
    TeamworkCfg(
        id="share_mask",
        label="share the space",
        action1="one child holds the flashlight",
        action2="the other fits the cover back on",
        ending="they work shoulder to shoulder until everything is calm",
        tags={"sharing"},
    ),
]

GIRL_NAMES = ["Ava", "Mia", "Nora", "Luna", "Zoe", "Ivy"]
BOY_NAMES = ["Leo", "Finn", "Max", "Theo", "Noah", "Kai"]


def story_place(place: Place) -> str:
    return place.label


def build_world(params: StoryParams) -> World:
    try:
        place = next(p for p in PLACES if p.id == params.place)
        misunderstanding = next(m for m in MISUNDERSTANDINGS if m.id == params.misunderstanding)
        teamwork = next(t for t in TEAMWORKS if t.id == params.teamwork)
    except StopIteration as exc:
        raise StoryError("invalid parameters for this space adventure") from exc

    world = World(place)
    hero = world.add(Entity(id=params.hero, kind="character", type="girl" if params.hero in GIRL_NAMES else "boy", role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type="girl" if params.helper in GIRL_NAMES else "boy", role="helper"))
    hab = world.add(Entity(id="hab", kind="thing", type="habitat", label="habitat"))
    tank = world.add(Entity(id="tank", kind="thing", type="tank", label="air tank"))
    scrubber = world.add(Entity(id="scrubber", kind="thing", type="tool", label="scrubber"))
    panel = world.add(Entity(id="panel", kind="thing", type="tool", label="panel"))

    tank.meters["air"] = 2.0
    hab.meters["air_risk"] = 0.0
    hero.memes["worry"] = 0.0
    helper.memes["worry"] = 0.0
    hero.memes["team"] = 0.0
    helper.memes["team"] = 0.0

    world.facts.update(place=place, misunderstanding=misunderstanding, teamwork=teamwork,
                       hero=hero, helper=helper, hab=hab, tank=tank, scrubber=scrubber, panel=panel)

    world.say(f"Inside {place.label}, {hero.id} and {helper.id} floated past the control board.")
    world.say(f"The little habitat hummed softly, and the air smelled clean and cool.")

    world.para()
    hero.memes["worry"] += 1
    helper.memes["team"] += 1
    world.say(f"{hero.id} stared at the gauge and thought {misunderstanding.mistaken_reading}.")
    world.say(f"{helper.id} looked too and saw the same number, so for a moment both of them felt unsure.")

    if misunderstanding.id == "low_gauge":
        world.say(f"They worried the {misunderstanding.concern}.")
    else:
        world.say(f"They worried that {misunderstanding.concern}.")

    world.para()
    world.say(f"Then {helper.id} remembered to look closer.")
    world.say(f"It was a misunderstanding: {misunderstanding.truth}.")
    world.say(f"{helper.id} said they should {teamwork.label}, because two calm minds are better than one worried one.")

    hero.memes["team"] += 1
    helper.memes["team"] += 1
    world.say(f"{teamwork.action1.capitalize()}, while {teamwork.action2}.")
    _simulate_air_use(world)
    tank.meters["air"] += 1
    world.get("hab").meters["air_risk"] = 0.0
    propagate(world, narrate=False)

    world.para()
    world.say(f"Soon the gauge settled down again.")
    world.say(f"{teamwork.ending.capitalize()}.")
    world.say(f"By the end, they were sharing the small space, the tools, and the work with easy smiles.")
    world.say(f"The moon habitat stayed bright and safe, with enough air for one more adventure.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure for a young child that includes the word "air" and a misunderstanding in a moon habitat.',
        f"Tell a gentle story where {f['hero'].id} and {f['helper'].id} think something is wrong with the air, then fix it by teamwork.",
        f'Write a child-friendly space story about sharing space and sharing work in {f["place"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    ms: MisunderstandingCfg = f["misunderstanding"]
    tw: TeamworkCfg = f["teamwork"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"What did {hero.id} first think about the air in {place.label}?",
            answer=f"{hero.id} first thought the air was almost gone. That was a misunderstanding, because the gauge was only giving a confusing reading.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} fix the problem together?",
            answer=f"They shared the work instead of panicking. {tw.action1.capitalize()}, and {tw.action2}, which helped the habitat settle back down.",
        ),
        QAItem(
            question=f"Why was the ending happy even though the story started with worry?",
            answer=f"They looked again, learned the truth, and worked as a team. Because they shared the job, the air stayed safe and the adventure could continue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is air?",
            answer="Air is the invisible stuff all around us that we breathe. People and animals need air to stay alive.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together. It can make a hard job easier and safer.",
        ),
        QAItem(
            question="Why is sharing useful in a small space?",
            answer="Sharing helps everyone take turns and use what they need without arguing. In a small place, sharing can keep things calm and fair.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
air_risk(H) :- tank(H), air(H,A), A < 2.
misunderstanding(M) :- misread(M).
teamwork(T) :- shares_work(T).
valid(P, M, T) :- place(P), misunderstanding(M), teamwork(T), allows(P, sharing).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p.id))
        if p.inside:
            lines.append(asp.fact("inside", p.id))
        for a in sorted(p.affords):
            lines.append(asp.fact("allows", p.id, a))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misread", m.id))
    for t in TEAMWORKS:
        lines.append(asp.fact("shares_work", t.id))
    lines.append(asp.fact("tank", "hab"))
    lines.append(asp.fact("air", "hab", 2))
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
    ok = py == cl
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, misunderstanding=None, teamwork=None, hero=None, helper=None, seed=None), random.Random(777)))
        smoke = bool(sample.story.strip())
    except Exception as exc:
        print(f"SMOKE FAIL: {exc}")
        return 1
    if not smoke:
        print("SMOKE FAIL: empty story")
        return 1
    if ok:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        print("OK: generate smoke test passed.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld about air, misunderstanding, teamwork, and sharing.")
    ap.add_argument("--place", choices=[p.id for p in PLACES])
    ap.add_argument("--misunderstanding", choices=[m.id for m in MISUNDERSTANDINGS])
    ap.add_argument("--teamwork", choices=[t.id for t in TEAMWORKS])
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.misunderstanding is None or c[1] == args.misunderstanding)
              and (args.teamwork is None or c[2] == args.teamwork)]
    if not combos:
        raise StoryError("no valid story matches the requested filters")
    place, misunderstanding, teamwork = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    return StoryParams(place=place, misunderstanding=misunderstanding, teamwork=teamwork, hero=hero, helper=helper, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    if not params.place or not params.misunderstanding or not params.teamwork:
        raise StoryError("missing parameters")
    world = build_world(params)
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


CURATED = [
    StoryParams(place="hab", misunderstanding="low_gauge", teamwork="share_map", hero="Ava", helper="Leo", seed=1),
    StoryParams(place="rover", misunderstanding="hissing_panel", teamwork="share_mask", hero="Kai", helper="Mia", seed=2),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
