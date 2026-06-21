#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/freight_rhyme_reconciliation_pirate_tale.py
============================================================================

A tiny storyworld for a pirate tale about freight, rhyme, and reconciliation.

Core premise:
- A ship's freight is sorted for a harbor fair.
- A rhyming disagreement causes a mishap.
- The crew reconciles, repairs the cargo plan, and ends with a cheerful rhyme.

The world is intentionally small and classical:
typed entities, physical meters, emotional memes, forward causal rules,
a reasonableness gate, inline ASP twin, and grounded QA.

Run:
    python storyworlds/worlds/gpt-5.4-mini/freight_rhyme_reconciliation_pirate_tale.py
    python storyworlds/worlds/gpt-5.4-mini/freight_rhyme_reconciliation_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/freight_rhyme_reconciliation_pirate_tale.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Ship:
    id: str
    name: str
    freight: str
    rhyme_line: str
    hold: str
    dock: str
    cargo_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    weight: int
    fragile: bool
    noisy: bool
    rhyme_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Dispute:
    id: str
    line_a: str
    line_b: str
    blame_word: str
    apology_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    action: str
    effect: str
    rhyme_word: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    ship: str
    cargo: str
    dispute: str
    remedy: str
    captain_name: str
    captain_gender: str
    mate_name: str
    mate_gender: str
    seed: Optional[int] = None


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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_shame(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.meters["spilled"] < THRESHOLD:
            continue
        sig = ("shame", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for e in world.entities.values():
            if e.role in {"captain", "mate"}:
                e.memes["hurt"] += 1
        out.append("__hurt__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out = []
    if world.facts.get("mended") and not world.facts.get("reconciled_rule"):
        world.fired.add(("reconcile",))
        for e in world.entities.values():
            if e.role in {"captain", "mate"}:
                e.memes["warmth"] += 1
                e.memes["hurt"] = 0.0
        world.facts["reconciled_rule"] = True
        out.append("__reconcile__")
    return out


CAUSAL_RULES = [_r_shame, _r_reconcile]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhyme_ok(dispute: Dispute, cargo: Cargo) -> bool:
    return cargo.noisy and dispute.blame_word[-1] == dispute.apology_word[-1]


def cargo_risk(cargo: Cargo, ship: Ship) -> bool:
    return cargo.fragile and ship.cargo_kind == cargo.tags and True


def cargo_risk_reasonable(cargo: Cargo, ship: Ship) -> bool:
    return cargo.fragile and ship.cargo_kind in ship.tags and True


def is_reasonable(ship: Ship, cargo: Cargo, dispute: Dispute, remedy: Remedy) -> bool:
    return cargo.fragile and cargo.noisy and remedy.power >= 1 and rhyme_ok(dispute, cargo)


def predict_damage(world: World, cargo: Cargo, remedy: Remedy) -> dict:
    sim = world.copy()
    sim.get("cargo").meters["spilled"] += 1
    propagate(sim, narrate=False)
    return {"spilled": sim.get("cargo").meters["spilled"] >= THRESHOLD, "hurt": sim.get("captain").memes["hurt"]}


def _spill(world: World, cargo: Cargo) -> None:
    world.get("cargo").meters["spilled"] += 1
    world.get("cargo").meters["scattered"] += 1
    propagate(world, narrate=False)


def tell(ship: Ship, cargo: Cargo, dispute: Dispute, remedy: Remedy,
         captain_name: str = "Finn", captain_gender: str = "boy",
         mate_name: str = "Wren", mate_gender: str = "girl") -> World:
    world = World()
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_gender, role="captain"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    harbor = world.add(Entity(id="harbor", kind="place", type="place", label="the harbor"))
    ship_ent = world.add(Entity(id="ship", kind="thing", type="ship", label=ship.name, attrs={"freight": ship.freight}))
    cargo_ent = world.add(Entity(id="cargo", kind="thing", type="cargo", label=cargo.label, attrs={"weight": cargo.weight}))
    captain.memes["pride"] = 2
    mate.memes["care"] = 2

    world.say(f"On {ship.dock}, {captain.id} and {mate.id} worked aboard {ship.name}.")
    world.say(f"They had freight to sort: {ship.freight}, and the hold smelled like salt and rope.")
    world.say(f"{captain.id} liked to boast in rhyme, and {mate.id} could rhyme right back.")

    world.para()
    world.say(f'"{dispute.line_a}" said {captain.id}.')
    world.say(f'"{dispute.line_b}" answered {mate.id}, and the words grew sharp as sea wind.')
    mate.memes["warning"] += 1
    if rhyme_ok(dispute, cargo):
        world.say(f'For a moment, their rhymes sounded funny, but the {cargo.label} was already wobbling.')

    world.para()
    _spill(world, cargo)
    world.say(f"A crate of {cargo.label} tipped in the hold, and the freight spilled across the planks.")
    world.say(f"{mate.id} gasped because the cargo was {cargo.rhyme_word} and could be ruined by a hard tumble.")

    world.para()
    world.say(f"{captain.id} looked at {mate.id}, and the hot words cooled a little.")
    world.say(f'"{dispute.apology_word}," said {captain.id}. "{dispute.apology_word}, mate."')
    mate.memes["soften"] += 1
    captain.memes["soften"] += 1
    world.say(f"{mate.id} nodded. "{dispute.line_b}" sounded silly now, and both of them knew it.")

    world.para()
    world.facts["mended"] = True
    if remedy.power >= 1:
        world.say(f'Together they used the {remedy.action}, which {remedy.effect}.')
        cargo_ent.meters["spilled"] = 0.0
        cargo_ent.meters["packed"] += 1
        world.say(f"They packed the freight back neat and safe, then tied the rope with steady hands.")
        world.say(f"By sunset, the hold was calm again, and the crew could hear the mast creak instead of the quarrel.")
    else:
        world.say(f'They tried to {remedy.action}, but the freight stayed a mess and the hold stayed gloomy.')

    world.para()
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(f"{captain.id} and {mate.id} smiled again and shared the last task.")
    world.say(f'They sang a little rhyme: "{ship.rhyme_line}"')
    world.say(f"The freight was ready, the argument was gone, and the pirate ship sailed on in peace.")

    world.facts.update(
        captain=captain,
        mate=mate,
        ship=ship,
        cargo_cfg=cargo,
        dispute=dispute,
        remedy=remedy,
        harbor=harbor,
        outcome="reconciled",
    )
    return world


SHIPS = {
    "briny": Ship(id="briny", name="The Briny Gull", freight="boxes of apples, lantern oil, and a red ribbon", rhyme_line="No fret, no fight, the freight is right!", hold="the hold", dock="the west dock", cargo_kind="cargo", tags={"cargo"}),
    "tide": Ship(id="tide", name="The Tide Song", freight="barrels of pears, a crate of shells, and a roll of canvas", rhyme_line="Kind words mend, and cargo can mend!", hold="the hold", dock="the east pier", cargo_kind="cargo", tags={"cargo"}),
}

CARGOS = {
    "eggs": Cargo(id="eggs", label="eggs", weight=2, fragile=True, noisy=False, rhyme_word="fragile", tags={"cargo", "fragile"}),
    "glass": Cargo(id="glass", label="glass bottles", weight=3, fragile=True, noisy=True, rhyme_word="tall", tags={"cargo", "fragile"}),
    "fruit": Cargo(id="fruit", label="pears", weight=2, fragile=True, noisy=True, rhyme_word="bright", tags={"cargo", "fragile"}),
}

DISPUTES = {
    "boom": Dispute(id="boom", line_a="My rhyme is first and full of thunder!", line_b="Your rhyme is loud but clumsy as plunder!", blame_word="thunder", apology_word="wonder", tags={"rhyme"}),
    "shore": Dispute(id="shore", line_a="I say the freight must stay by me!", line_b="I say it should be stacked by the sea!", blame_word="sea", apology_word="tea", tags={"rhyme"}),
    "gold": Dispute(id="gold", line_a="I called it tidy, trim, and bold!", line_b="I called it ready, red, and gold!", blame_word="bold", apology_word="told", tags={"rhyme"}),
}

REMEDIES = {
    "rope": Remedy(id="rope", action="recoil the rope and right the crate", effect="kept the freight from sliding", rhyme_word="rope", power=1, tags={"repair"}),
    "sort": Remedy(id="sort", action="sort the crates by weight", effect="made the hold tidy again", rhyme_word="shore", power=1, tags={"repair"}),
    "patch": Remedy(id="patch", action="patch the torn sack and sweep the boards", effect="made the freight neat again", rhyme_word="match", power=1, tags={"repair"}),
}

NAMES = ["Finn", "Mira", "Wren", "Pip", "Juno", "Tessa", "Moss", "Nell"]
GENDERS = ["boy", "girl"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, ship in SHIPS.items():
        for cid, cargo in CARGOS.items():
            for did, dispute in DISPUTES.items():
                for rid, remedy in REMEDIES.items():
                    if cargo.fragile and cargo.noisy and rhyme_ok(dispute, cargo) and remedy.power >= 1:
                        combos.append((sid, cid, did, rid))
    return combos


def explain_rejection(ship: Ship, cargo: Cargo, dispute: Dispute, remedy: Remedy) -> str:
    if not cargo.fragile:
        return f"(No story: {cargo.label} is not fragile enough to make the freight mishap matter.)"
    if not cargo.noisy:
        return f"(No story: {cargo.label} is too quiet for the rhyme-and-mishap premise.)"
    if not rhyme_ok(dispute, cargo):
        return f"(No story: the dispute does not rhyme closely enough for this pirate tale.)"
    return f"(No story: the chosen remedy is too weak to repair the freight.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with freight, rhyme, and reconciliation.")
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--dispute", choices=DISPUTES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--captain-name", dest="captain_name")
    ap.add_argument("--captain-gender", dest="captain_gender", choices=GENDERS)
    ap.add_argument("--mate-name", dest="mate_name")
    ap.add_argument("--mate-gender", dest="mate_gender", choices=GENDERS)
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
    if args.ship and args.cargo and args.dispute and args.remedy:
        ship, cargo, dispute, remedy = SHIPS[args.ship], CARGOS[args.cargo], DISPUTES[args.dispute], REMEDIES[args.remedy]
        if not is_reasonable(ship, cargo, dispute, remedy):
            raise StoryError(explain_rejection(ship, cargo, dispute, remedy))
    combos = [c for c in valid_combos()
              if (args.ship is None or c[0] == args.ship)
              and (args.cargo is None or c[1] == args.cargo)
              and (args.dispute is None or c[2] == args.dispute)
              and (args.remedy is None or c[3] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    ship, cargo, dispute, remedy = rng.choice(sorted(combos))
    return StoryParams(
        ship=ship,
        cargo=cargo,
        dispute=dispute,
        remedy=remedy,
        captain_name=args.captain_name or rng.choice(NAMES),
        captain_gender=args.captain_gender or rng.choice(GENDERS),
        mate_name=args.mate_name or rng.choice([n for n in NAMES if n != args.captain_name]),
        mate_gender=args.mate_gender or rng.choice(GENDERS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale that includes the word "freight" and ends with reconciliation.',
        f'Tell a child-friendly story about {f["captain"].id} and {f["mate"].id} arguing over rhyme while sorting freight on a ship.',
        f'Write a short story where a freight mishap is fixed with calm words, a rhyme, and a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain: Entity = f["captain"]
    mate: Entity = f["mate"]
    ship: Ship = f["ship"]
    cargo: Cargo = f["cargo_cfg"]
    dispute: Dispute = f["dispute"]
    remedy: Remedy = f["remedy"]
    return [
        QAItem(
            question="What was the freight on the pirate ship?",
            answer=f"The freight was {ship.freight}. It was the load they had to sort in the hold."
        ),
        QAItem(
            question=f"Why did {captain.id} and {mate.id} stop arguing?",
            answer=f"They realized the rhyme was making the quarrel bigger than it needed to be. Then they said sorry, worked together, and put the freight right again."
        ),
        QAItem(
            question="How was the problem fixed?",
            answer=f"They used the {remedy.action} so the freight could be packed neatly again. That calm repair matched the rhyme and helped them reconcile."
        ),
    ]


def world_qa(_: World) -> list[QAItem]:
    return [
        QAItem("What does freight mean?", "Freight means cargo or goods being carried, often by ship or truck. It is the load that has to be moved safely."),
        QAItem("What is a rhyme?", "A rhyme is when words sound alike at the end. It can make a song or story sound playful."),
        QAItem("What does reconciliation mean?", "Reconciliation means making up after a disagreement. People forgive each other and work together again."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.ship not in SHIPS or params.cargo not in CARGOS or params.dispute not in DISPUTES or params.remedy not in REMEDIES:
        raise StoryError("Invalid story parameters.")
    world = tell(
        SHIPS[params.ship],
        CARGOS[params.cargo],
        DISPUTES[params.dispute],
        REMEDIES[params.remedy],
        captain_name=params.captain_name,
        captain_gender=params.captain_gender,
        mate_name=params.mate_name,
        mate_gender=params.mate_gender,
    )
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            m = {k: v for k, v in e.meters.items() if v}
            mm = {k: v for k, v in e.memes.items() if v}
            bits = []
            if m:
                bits.append(f"meters={dict(m)}")
            if mm:
                bits.append(f"memes={dict(mm)}")
            if e.role:
                bits.append(f"role={e.role}")
            print(f"  {e.id}: {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
rhyme_ok(D) :- dispute(D), blame(D,B), apology(D,A), last(B,L), last(A,L).
reasonable(S,C,D,R) :- ship(S), cargo(C), dispute(D), remedy(R), fragile(C), noisy(C), rhyme_ok(D), power(R,P), P >= 1.
outcome(reconciled) :- reasonable(S,C,D,R).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SHIPS:
        lines.append(asp.fact("ship", sid))
    for cid, c in CARGOS.items():
        lines.append(asp.fact("cargo", cid))
        if c.fragile:
            lines.append(asp.fact("fragile", cid))
        if c.noisy:
            lines.append(asp.fact("noisy", cid))
    for did, d in DISPUTES.items():
        lines.append(asp.fact("dispute", did))
        lines.append(asp.fact("blame", did, d.blame_word))
        lines.append(asp.fact("apology", did, d.apology_word))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show reasonable/4."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_outcome(_: StoryParams) -> str:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(ship=None, cargo=None, dispute=None, remedy=None, captain_name=None, captain_gender=None, mate_name=None, mate_gender=None, n=1, all=False, seed=None, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


CURATED = [
    StoryParams(ship="briny", cargo="fruit", dispute="boom", remedy="rope", captain_name="Finn", captain_gender="boy", mate_name="Wren", mate_gender="girl"),
    StoryParams(ship="tide", cargo="glass", dispute="shore", remedy="sort", captain_name="Mira", captain_gender="girl", mate_name="Pip", mate_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show reasonable/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
                params.seed = base_seed + i
                sample = generate(params)
            except StoryError as e:
                print(e)
                return
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
