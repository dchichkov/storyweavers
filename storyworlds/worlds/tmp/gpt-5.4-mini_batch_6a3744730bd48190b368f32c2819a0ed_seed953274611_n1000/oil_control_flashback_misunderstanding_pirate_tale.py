#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/oil_control_flashback_misunderstanding_pirate_tale.py
======================================================================================

A small storyworld in a pirate-tale style: a child on a ship, a slick spill of
oil, a misunderstanding about who is in control, a flashback to a past lesson,
and a safe ending that proves what changed.

The world is intentionally compact:
- a child wants to keep the ship moving,
- oil makes the deck slippery and threatens the helm,
- a misunderstanding creates tension,
- a flashback teaches a better choice,
- the crew regains control with a careful fix.

It supports the standard Storyweavers CLI:
- default run
- -n / --all / --seed
- --trace / --qa / --json
- --asp / --verify / --show-asp
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    can_command: bool = False
    can_fix: bool = False
    slippery: bool = False
    oily: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Ship:
    id: str
    place: str
    deck: str
    helm: str
    cargo: str
    style: str
    flashback: str
    misunderstanding: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    spill: str
    risk: str
    makes_mess: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    verb: str
    text: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    deck = world.get("deck")
    for ent in world.entities.values():
        if ent.meters["oily"] < THRESHOLD:
            continue
        sig = ("slip", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        deck.meters["danger"] += 1
        out.append("__slip__")
    return out


def _r_control_lost(world: World) -> list[str]:
    out: list[str] = []
    helm = world.get("helm")
    deck = world.get("deck")
    if deck.meters["danger"] < THRESHOLD:
        return out
    sig = ("control",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helm.meters["control"] -= 1
    out.append("__control__")
    return out


RULES = [Rule("slip", _r_slip), Rule("control", _r_control_lost)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(hazard: Hazard, ship: Ship) -> bool:
    return hazard.makes_mess and "deck" in ship.tags


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def is_contained(fix: Fix, delay: int) -> bool:
    return fix.power >= 1 + delay


def predict_misunderstanding(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    _spill(sim, sim.get(hazard_id), narrate=False)
    return {
        "danger": sim.get("deck").meters["danger"],
        "control": sim.get("helm").meters["control"],
    }


def _spill(world: World, hazard: Entity, narrate: bool = True) -> None:
    hazard.meters["oily"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, hero: Entity, mate: Entity, ship: Ship, hazard: Hazard) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a bright day at sea, {hero.id} and {mate.id} turned the deck of the "
        f"{ship.place} into a pirate game. {ship.style}"
    )
    world.say(
        f'{hero.id} pointed toward the {ship.helm}. "{ship.ending_image}!"'
    )
    world.say(
        f'But a slick smell drifted from a crate of {hazard.label}, and the '
        f'deck shone in a way that made the boards look tricky.'
    )


def tension(world: World, hero: Entity, mate: Entity, hazard: Hazard, ship: Ship) -> None:
    hero.memes["bravado"] += 1
    world.say(
        f'{hero.id} squinted and said, "{hazard.label.capitalize()} will help us '
        f'control the ship. I know how to handle it."'
    )
    world.say(
        f'{mate.id} frowned. "{ship.misunderstanding} I thought you meant the '
        f'captain had it under control, not that we should pour it out."'
    )
    world.say(
        f'For a moment, the two pirates argued over control instead of listening.'
    )


def flashback(world: World, hero: Entity, mate: Entity, ship: Ship) -> None:
    hero.memes["memory"] += 1
    mate.memes["memory"] += 1
    world.say(
        f"Then {hero.id} remembered something from before. In a small flashback, "
        f"{hero.id} had once watched a deck get slick from oil and saw how a wise "
        f"mate used sand and cloth to keep everyone steady."
    )
    world.say(
        f'"That was the trick," {hero.id} said. "Not more oil. Control the spill."'
    )


def spill(world: World, hazard: Hazard) -> None:
    _spill(world, world.get(hazard.id))
    world.say(
        f"{hazard.label.capitalize()} tipped over. {hazard.spill} The boards grew "
        f"glossy, and the ship began to feel less steady."
    )


def alarm(world: World, mate: Entity, hero: Entity, ship: Ship) -> None:
    world.say(
        f'"Wait!" {mate.id} cried. "That is not control. That is how a ship loses '
        f'its footing!"'
    )
    world.say(
        f'{hero.id} blinked, realizing the misunderstanding. The words had been '
        f'about keeping order, not about making a mess.'
    )


def fix_story(world: World, parent: Entity, fix: Fix, ship: Ship, hazard: Hazard, delay: int) -> None:
    deck = world.get("deck")
    helm = world.get("helm")
    if is_contained(fix, delay):
        deck.meters["danger"] = 0
        world.get(hazard.id).meters["oily"] = 0
        helm.meters["control"] = 1
        world.say(
            f"{parent.id} came running and {fix.text}. Soon the deck was safe "
            f"again, and the wheel answered every careful turn."
        )
        world.say(
            f"The pirates laughed in relief. On that ship, control meant a clean "
            f"deck, a steady helm, and the right person making the right call."
        )
        world.say(
            f"By evening, the boards were dry, and the {ship.cargo} sat still and "
            f"bright, as if the ship had learned to breathe again."
        )
    else:
        world.say(
            f"{parent.id} came running and {fix.text}, but the slick spread had "
            f"already gone too far."
        )
        world.say(
            f"The crew still got everyone safe, but the deck stayed messy, and the "
            f"little ship drifted until help arrived with stronger tools."
        )


def tell(ship: Ship, hazard: Hazard, fix: Fix, hero_name: str, mate_name: str, parent_name: str, delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", role="hero", can_command=False))
    mate = world.add(Entity(id=mate_name, kind="character", type="girl", role="mate", can_command=True))
    parent = world.add(Entity(id=parent_name, kind="character", type="mother", role="parent", can_fix=True))
    world.add(Entity(id="deck", type="deck", label=ship.deck))
    world.add(Entity(id="helm", type="helm", label=ship.helm))
    world.add(Entity(id=hazard.id, type="thing", label=hazard.label, oily=False))
    world.get("helm").meters["control"] = 1
    world.facts["ship"] = ship
    world.facts["hazard"] = hazard
    world.facts["fix"] = fix
    world.facts["delay"] = delay
    opening(world, hero, mate, ship, hazard)
    world.para()
    tension(world, hero, mate, hazard, ship)
    flashback(world, hero, mate, ship)
    world.para()
    spill(world, hazard)
    alarm(world, mate, hero, ship)
    world.para()
    fix_story(world, parent, fix, ship, hazard, delay)
    world.facts.update(hero=hero, mate=mate, parent=parent, outcome="safe")
    return world


SHIP = Ship(
    id="ship",
    place="pirate ship",
    deck="deck",
    helm="helm",
    cargo="sails",
    style="The sofa was a ship's rail, a broom was a mast, and a rope coil sat like treasure.",
    flashback="",
    misunderstanding="",
    ending_image="steady wheel",
    tags={"deck"},
)

HAZARDS = {
    "oil": Hazard(
        id="oil",
        label="oil",
        phrase="a little bottle of oil",
        spill="A shiny ribbon spread across the boards.",
        risk="It can make the deck slippery.",
        makes_mess=True,
        tags={"oil", "slippery"},
    ),
    "lamp_oil": Hazard(
        id="lamp_oil",
        label="lamp oil",
        phrase="a jug of lamp oil",
        spill="A heavy puddle spread and gleamed.",
        risk="It can make people lose their footing.",
        makes_mess=True,
        tags={"oil", "slippery"},
    ),
}

FIXES = {
    "sand_cloth": Fix(
        id="sand_cloth",
        label="sand and cloth",
        verb="spread sand and wrapped the spill in cloth",
        text="spread sand over the oil and pressed cloth down until the shine faded",
        sense=3,
        power=2,
        tags={"sand", "cloth"},
    ),
    "bucket_mop": Fix(
        id="bucket_mop",
        label="bucket and mop",
        verb="brought a bucket and mop",
        text="brought a bucket and mop and cleaned the boards with quick, careful strokes",
        sense=2,
        power=2,
        tags={"mop"},
    ),
    "rush_wipe": Fix(
        id="rush_wipe",
        label="a quick wipe",
        verb="swiped at the spill with a sleeve",
        text="swiped at the spill with a sleeve, but that only spread the shine around",
        sense=1,
        power=0,
        tags={"weak"},
    ),
}

NAMES_BOY = ["Finn", "Tom", "Rory", "Nico", "Eli"]
NAMES_GIRL = ["Lily", "Mina", "Zoe", "Ava", "Nell"]


@dataclass
class StoryParams:
    ship: str
    hazard: str
    fix: str
    hero: str
    mate: str
    parent: str
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in [SHIP.id]:
        for hid, hz in HAZARDS.items():
            for fid, fx in FIXES.items():
                if hazard_at_risk(hz, SHIP) and fx.sense >= SENSE_MIN:
                    combos.append((sid, hid, fid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with oil, control, flashback, and misunderstanding.")
    ap.add_argument("--ship", choices=[SHIP.id], default=SHIP.id)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--mate")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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
    if args.hazard and args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(f"(Refusing fix '{args.fix}': it is too weak and unsafe for this story.)")
    if args.hazard and not HAZARDS[args.hazard].makes_mess:
        raise StoryError("(No story: that hazard would not create the slippery problem.)")
    combos = [c for c in valid_combos()
              if (args.hazard is None or c[1] == args.hazard)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    _, hid, fid = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES_BOY)
    mate = args.mate or rng.choice(NAMES_GIRL)
    if hero == mate:
        mate = rng.choice([n for n in NAMES_GIRL if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(ship=SHIP.id, hazard=hid, fix=fid, hero=hero, mate=mate, parent=parent, delay=args.delay)


def generate(params: StoryParams) -> StorySample:
    if params.hazard not in HAZARDS or params.fix not in FIXES or params.ship != SHIP.id:
        raise StoryError("(Invalid params for this storyworld.)")
    world = tell(SHIP, HAZARDS[params.hazard], FIXES[params.fix], params.hero, params.mate, params.parent, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ship, hz, fx = f["ship"], f["hazard"], f["fix"]
    return [
        f'Write a pirate tale for a young child that includes the words "{hz.label}" and "control".',
        f"Tell a story where {f['hero'].id} and {f['mate'].id} have a misunderstanding about control on a pirate ship, then remember a flashback and fix an oily spill.",
        f"Write a short pirate story with a slippery deck, a misunderstanding, and a safe cleanup using {fx.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, mate, parent, hz, fx = f["hero"], f["mate"], f["parent"], f["hazard"], f["fix"]
    return [
        ("What was the problem on the ship?",
         f"There was a spill of {hz.label} on the deck, and it made the boards slippery. That meant the pirates could lose control if nobody fixed it quickly."),
        ("Why did the two pirates argue?",
         f"They had a misunderstanding about control. {hero.id} thought control meant using the oil, but {mate.id} knew it meant keeping the ship steady and safe."),
        ("What did the flashback help them remember?",
         f"It helped them remember that sand and cloth can calm a slippery spill. The memory turned the argument into a better idea."),
        ("How was the problem solved?",
         f"{parent.id} {fx.text}. After that, the deck was safe again and the wheel could stay steady."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is oil?",
         "Oil is a slippery liquid. If it spills on a floor or deck, it can make people slide and fall."),
        ("What does control mean on a ship?",
         "Control means being able to guide the ship safely. A steady helm and careful hands help the crew stay in control."),
        ("What is a flashback?",
         "A flashback is a short look back to something that happened before. Stories use it to help a character remember an important lesson."),
        ("What is a misunderstanding?",
         "A misunderstanding happens when people think different things are being said. Once they explain themselves, the confusion can go away."),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.can_fix:
            bits.append("can_fix=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(ship=SHIP.id, hazard="oil", fix="sand_cloth", hero="Finn", mate="Lily", parent="mother", delay=0),
    StoryParams(ship=SHIP.id, hazard="lamp_oil", fix="bucket_mop", hero="Tom", mate="Ava", parent="father", delay=1),
]


def explain_rejection(hazard: Hazard) -> str:
    return f"(No story: {hazard.label} would not create a meaningful shipboard hazard.)"


ASP_RULES = r"""
hazard(H) :- hazard(H), spillable(H).
sensible(F) :- fix(F), sense(F,S), sense_min(M), S >= M.
valid(S,H,F) :- ship(S), hazard(H), fix(F), spillable(H), sensible(F).
outcome(safe) :- valid(_,_,_), chosen_fix(F), power(F,P), delay(D), P >= 1 + D.
outcome(risky) :- valid(_,_,_), chosen_fix(F), power(F,P), delay(D), P < 1 + D.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = [asp.fact("ship", SHIP.id), asp.fact("sense_min", SENSE_MIN)]
    for hid, hz in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if hz.makes_mess:
            lines.append(asp.fact("spillable", hid))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fx.sense))
        lines.append(asp.fact("power", fid, fx.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_fix", params.fix), asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos() vs ASP.")
        rc = 1
    else:
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    if set(asp_sensible()) != {f.id for f in sensible_fixes()}:
        print("MISMATCH in sensible fixes vs ASP.")
        rc = 1
    else:
        print("OK: sensible fixes match.")
    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
        assert sample.prompts
        print("OK: smoke test generate() produced a story.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    cases = [CURATED[0], CURATED[1]]
    bad = sum(1 for p in cases if asp_outcome(p) != "safe")
    if bad:
        print(f"MISMATCH: {bad} outcomes differ.")
        rc = 1
    else:
        print("OK: ASP outcome check passed on curated cases.")
    return rc


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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        for v in asp_valid_combos():
            print(v)
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
