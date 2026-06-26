#!/usr/bin/env python3
"""
storyworlds/worlds/survivor_beverage_tar_lesson_learned_cautionary_inner.py
===========================================================================

A small detective-story world about a survivor, a beverage, and a tar mishap.

Premise:
- A survivor carries a treasured beverage through a smoky dockside street.
- Fresh tar in the path threatens the drink and the survivor's clothes.
- The survivor investigates the danger, makes a cautious choice, and learns a lesson.

Story instruments:
- Detective Story style: clues, observations, careful reasoning.
- Inner Monologue: the survivor thinks through the problem.
- Cautionary tone: the danger is real and named plainly.
- Lesson Learned: the ending states the new habit.

The world is intentionally small and constraint-checked: only one kind of
reasonable danger/fix pair is generated, and invalid explicit choices raise
StoryError.
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
    carried_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "survivor"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Beverage:
    id: str
    label: str
    phrase: str
    container: str
    flavor: str
    hot: bool = False


@dataclass
class Hazard:
    id: str
    label: str
    mess: str
    soil: str
    risk_phrase: str
    zone: set[str]


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    guards: set[str]
    covers: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    beverage: str
    hazard: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "dock": Setting(place="the dockside lane", mood="foggy", affords={"walk"}),
    "alley": Setting(place="the narrow alley", mood="shadowy", affords={"walk"}),
    "harbor": Setting(place="the harbor road", mood="windy", affords={"walk"}),
    "station": Setting(place="the station steps", mood="busy", affords={"walk"}),
}

BEVERAGES = {
    "tea": Beverage(id="tea", label="tea", phrase="a steaming cup of tea", container="cup", flavor="warm and sweet", hot=True),
    "juice": Beverage(id="juice", label="juice", phrase="a bright bottle of juice", container="bottle", flavor="cold and fruity"),
    "milk": Beverage(id="milk", label="milk", phrase="a small carton of milk", container="carton", flavor="cool and plain"),
}

HAZARDS = {
    "tar": Hazard(
        id="tar",
        label="tar",
        mess="sticky",
        soil="stuck with black tar",
        risk_phrase="fresh tar spread across the path",
        zone={"feet", "shoes"},
    ),
}

GEAR = [
    Gear(id="boots", label="rubber boots", phrase="put on rubber boots", guards={"sticky"}, covers={"feet", "shoes"}),
    Gear(id="tray", label="a tray", phrase="carry it on a tray", guards={"sticky"}, covers={"hands"}),
]

NAMES = ["Mira", "Nia", "Lena", "Tess", "Ivy", "Rae", "Mina", "June"]
TRAITS = ["careful", "quiet", "curious", "steady", "sharp", "patient"]


def hazard_at_risk(hazard: Hazard, beverage: Beverage) -> bool:
    return True


def select_gear(hazard: Hazard, beverage: Beverage) -> Optional[Gear]:
    for gear in GEAR:
        if hazard.mess in gear.guards:
            return gear
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective-style story world about a survivor, a beverage, and tar.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--beverage", choices=sorted(BEVERAGES))
    ap.add_argument("--hazard", choices=sorted(HAZARDS))
    ap.add_argument("--gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=sorted(TRAITS))
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
    if args.beverage and args.hazard:
        bev = BEVERAGES[args.beverage]
        haz = HAZARDS[args.hazard]
        if not (hazard_at_risk(haz, bev) and select_gear(haz, bev)):
            raise StoryError("No reasonable story: the hazard does not create a believable caution and fix.")
    combos = [(p, b, h) for p in SETTINGS for b in BEVERAGES for h in HAZARDS]
    combos = [c for c in combos if (args.place is None or c[0] == args.place)
              and (args.beverage is None or c[1] == args.beverage)
              and (args.hazard is None or c[2] == args.hazard)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, beverage, hazard = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["woman", "man", "girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, beverage=beverage, hazard=hazard, name=name, gender=gender, trait=trait)


def _do_walk(world: World, actor: Entity, hazard: Hazard, narrate: bool = True) -> None:
    world.zone = set(hazard.zone)
    actor.meters["alert"] = actor.meters.get("alert", 0.0) + 1
    if narrate:
        world.say(f"{actor.pronoun().capitalize()} kept moving, watching the ground like a detective at a clue board.")


def predict_taint(world: World, actor: Entity, hazard: Hazard, beverage: Beverage) -> bool:
    sim = world.copy()
    _do_walk(sim, sim.get(actor.id), hazard, narrate=False)
    bev = sim.get("beverage")
    return bev.meters.get("dirty", 0.0) >= THRESHOLD or hazard.id == "tar"


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a survivor who noticed every small thing.")
    world.say(f"{hero.pronoun().capitalize()} was {hero.traits[0]} and moved like someone who knew trouble could hide in plain sight.")


def show_beverage(world: World, hero: Entity, beverage: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(f"{hero.id} carried {hero.pronoun('possessive')} {beverage.phrase} carefully.")
    world.say(f"The drink smelled {beverage.meters.get('flavor', 0) if False else world.facts['beverage'].flavor}.")


def warn(world: World, hero: Entity, hazard: Hazard, beverage: Entity) -> bool:
    if not predict_taint(world, hero, hazard, world.facts["beverage"]):
        return False
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1
    world.say(f'"Careful," {hero.pronoun("possessive")} inner monologue said. "Fresh tar is a sticky clue, and it can ruin the whole day."')
    return True


def inner_monologue(world: World, hero: Entity, hazard: Hazard, beverage: Beverage) -> None:
    world.say(
        f'{hero.pronoun().capitalize()} thought, "If I step wrong, the tar will cling to my shoes, '
        f'and this {beverage.label} will no longer be a simple comfort."'
    )


def cautionary_turn(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(f"{hazard.risk_phrase}, and the air felt serious.")
    world.say(f"{hero.id} did not rush. {hero.pronoun().capitalize()} studied the line of dark tar like a detective reading tracks.")


def choose_fix(world: World, hero: Entity, hazard: Hazard, beverage: Beverage) -> Optional[Gear]:
    gear = select_gear(hazard, beverage)
    if gear is None:
        return None
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1
    world.say(f"{hero.id} found a better way: {gear.phrase}.")
    return gear


def lesson_learned(world: World, hero: Entity, beverage: Beverage, gear: Gear) -> None:
    world.say(
        f"Lesson learned: when tar is near, {hero.id} slows down, uses a safe method, and keeps {hero.pronoun('possessive')} drink clean."
    )
    world.say(
        f"With {gear.label} on, {hero.id} crossed without a smear, and the {beverage.label} stayed ready for the next clue."
    )


def tell(setting: Setting, beverage_cfg: Beverage, hazard_cfg: Hazard, name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=[trait, "survivor"]))
    bev = world.add(Entity(id="beverage", type=beverage_cfg.label, label=beverage_cfg.label, phrase=beverage_cfg.phrase, owner=hero.id))
    world.facts["beverage"] = beverage_cfg
    world.facts["hazard"] = hazard_cfg
    world.facts["hero"] = hero

    introduce(world, hero)
    world.say(f"One {setting.mood} morning, {hero.id} entered {setting.place} with {bev.phrase}.")
    world.say(f"Then the clue appeared: {hazard_cfg.risk_phrase}.")
    show_beverage(world, hero, bev)

    world.para()
    inner_monologue(world, hero, hazard_cfg, beverage_cfg)
    warn(world, hero, hazard_cfg, bev)
    cautionary_turn(world, hero, hazard_cfg)

    world.para()
    gear = choose_fix(world, hero, hazard_cfg, beverage_cfg)
    if gear is None:
        raise StoryError("No safe gear exists for this combination.")
    lesson_learned(world, hero, beverage_cfg, gear)

    world.facts["gear"] = gear
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    bev = world.facts["beverage"]
    haz = world.facts["hazard"]
    return [
        f'Write a short detective-style story for a young child about {hero.id}, a survivor, and {bev.label}.',
        f'Tell a cautionary story where {haz.label} threatens {bev.phrase}, and the hero listens to an inner monologue.',
        f'Write a story with a clear lesson learned about how to cross safely when {haz.risk_phrase}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    bev = world.facts["beverage"]
    haz = world.facts["hazard"]
    gear = world.facts["gear"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a survivor who thinks carefully before acting.",
        ),
        QAItem(
            question=f"What risky thing was on the path?",
            answer=f"There was {hazard_name(haz)} on the path, and it could cling to shoes and make trouble.",
        ),
        QAItem(
            question=f"What was {hero.id} carrying?",
            answer=f"{hero.id} was carrying {bev.phrase}, a drink that needed to stay clean.",
        ),
        QAItem(
            question=f"What safe choice helped at the end?",
            answer=f"{hero.id} used {gear.label} and crossed slowly, which kept the beverage safe.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned to slow down, notice the clue, and choose the cautious way when tar is near.",
        ),
    ]


def hazard_name(hazard: Hazard) -> str:
    return hazard.label


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tar?",
            answer="Tar is a sticky black material that can cling to shoes and make a path dangerous.",
        ),
        QAItem(
            question="Why should a drink be carried carefully?",
            answer="A drink can spill or get dirty, so carrying it carefully helps keep it nice to drink.",
        ),
        QAItem(
            question="What does it mean to be a survivor?",
            answer="A survivor is someone who has gone through something hard and is still moving forward.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    StoryParams(place="dock", beverage="tea", hazard="tar", name="Mira", gender="woman", trait="careful"),
    StoryParams(place="alley", beverage="juice", hazard="tar", name="Tess", gender="girl", trait="curious"),
    StoryParams(place="harbor", beverage="milk", hazard="tar", name="Rae", gender="man", trait="steady"),
]


ASP_RULES = r"""
hazard_at_risk(H,B) :- hazard(H), beverage(B).
fix(H,B,G) :- hazard_at_risk(H,B), gear(G), guards(G, sticky).
valid(P,B,H) :- place(P), beverage(B), hazard(H), hazard_at_risk(H,B), fix(H,B,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for b in BEVERAGES:
        lines.append(asp.fact("beverage", b))
    for h in HAZARDS:
        lines.append(asp.fact("hazard", h))
        lines.append(asp.fact("hazard_kind", h, "sticky"))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for k in g.guards:
            lines.append(asp.fact("guards", g.id, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, b, h) for p in SETTINGS for b in BEVERAGES for h in HAZARDS if hazard_at_risk(HAZARDS[h], BEVERAGES[b]) and select_gear(HAZARDS[h], BEVERAGES[b])]


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in asp:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def resolve_params_public(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], BEVERAGES[params.beverage], HAZARDS[params.hazard], params.name, params.gender, params.trait)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.beverage is None or c[1] == args.beverage) and (args.hazard is None or c[2] == args.hazard)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, beverage, hazard = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["woman", "man", "girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, beverage=beverage, hazard=hazard, name=name, gender=gender, trait=trait)


def build_parser_public() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.beverage} at {p.place} (hazard: {p.hazard})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
