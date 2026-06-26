#!/usr/bin/env python3
"""
storyworlds/worlds/precision_foreshadowing_transformation_pirate_tale.py
========================================================================

A small pirate-tale story world with precision, foreshadowing, and
transformation.

Premise:
A young pirate wants to sail after treasure, but a careful captain notices
tiny clues: a twitchy compass, a low cloud line, and a rope knot that is just
a little too loose. The crew must choose whether to rush out or make a precise
plan first.

Story shape:
- setup: introduce the pirate, the ship, and the prized item
- foreshadowing: small signs hint at trouble ahead
- turn: a careful adjustment prevents the larger problem
- resolution: the hero becomes more precise and the voyage succeeds

This file is self-contained and uses only stdlib plus the shared result
containers. ASP support is inline as a twin of the Python reasonableness gate.
"""

from __future__ import annotations

import argparse
import copy
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"precision": 0.0, "risk": 0.0, "damage": 0.0, "safety": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "worry": 0.0, "pride": 0.0, "trust": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    sea: str
    route: str
    weather: str = ""
    danger: str = ""
    safe_action: str = ""
    flourish: str = ""


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.ship)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _fired(world: World, *sig: str) -> bool:
    return tuple(sig) in world.fired


def _mark(world: World, *sig: str) -> None:
    world.fired.add(tuple(sig))


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    ship = world.ship
    for actor in world.characters():
        if actor.meters["precision"] < THRESHOLD:
            continue
        if ship.weather == "fog" and not _fired(world, "fog"):
            _mark(world, "fog")
            actor.memes["worry"] += 1
            out.append("A pale fog clung to the water like a whisper, and the captain narrowed her eyes.")
        if ship.danger == "reef" and not _fired(world, "reef"):
            _mark(world, "reef")
            out.append("A thin white line on the waves hinted at sharp rocks below.")
        if ship.danger == "loose_rope" and not _fired(world, "rope"):
            _mark(world, "rope")
            out.append("One knot looked neat from far away, but up close it twitched loose in the wind.")
    return out


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    ship = world.ship
    for actor in world.characters():
        if actor.meters["risk"] < THRESHOLD:
            continue
        if ship.danger == "reef" and not any(g.protective and "hull" in g.covers for g in world.worn_items(actor)):
            if not _fired(world, "reef_damage"):
                _mark(world, "reef_damage")
                ship.name = ship.name
                out.append("The ship scraped the reef and shuddered all the way through its belly.")
        if ship.danger == "storm" and not any(g.protective and "mast" in g.covers for g in world.worn_items(actor)):
            if not _fired(world, "storm_damage"):
                _mark(world, "storm_damage")
                out.append("The storm snapped at the sail and tore a long flap along its edge.")
    return out


def _r_precision_reward(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["precision"] < 2 * THRESHOLD or _fired(world, "reward"):
            continue
        _mark(world, "reward")
        actor.memes["pride"] += 1
        actor.memes["trust"] += 1
        out.append("The crew saw how careful eyes could save a whole voyage.")
    return out


CAUSAL_RULES = [_r_foreshadow, _r_damage, _r_precision_reward]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def solve_route(world: World, hero: Entity) -> bool:
    if hero.meters["precision"] < THRESHOLD:
        hero.memes["worry"] += 1
        return False
    world.ship.safe_action = "trim the sail and follow the cleanest line"
    hero.meters["risk"] = 0.0
    hero.meters["safety"] += 1
    hero.memes["trust"] += 1
    return True


def predict_trouble(world: World, hero: Entity) -> dict:
    sim = world.copy()
    sim_hero = sim.get(hero.id)
    sim_hero.meters["risk"] += 1
    propagate(sim, narrate=False)
    trouble = sim.ship.danger
    return {
        "damage": any("scraped the reef" in s or "tore a long flap" in s for p in sim.paragraphs for s in p),
        "danger": trouble,
    }


def introduce(world: World, hero: Entity, captain: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a small pirate with a big wish to reach the hidden cove. "
        f"{hero.pronoun().capitalize()} loved {prize.phrase} and dreamed of {prize.label} glittering in the sun."
    )
    world.say(
        f"{captain.id} watched the sea with calm eyes, because a pirate voyage was best when every line was precise."
    )
    hero.memes["hope"] += 1
    captain.memes["trust"] += 1


def foreshadow(world: World, hero: Entity, captain: Entity) -> None:
    world.para()
    world.say(
        f"At dawn, {hero.id} and {captain.id} boarded the ship named {world.ship.name}."
    )
    if world.ship.flourish:
        world.say(world.ship.flourish)
    world.say(
        f"{hero.id} wanted to sail right away, but the captain pointed to the little signs that mattered."
    )
    if world.ship.weather == "fog":
        world.say("The water looked smooth from far off, yet the fog made every shape hard to judge.")
    if world.ship.danger == "reef":
        world.say("Near the cove, the tide pulled back enough to show a line of pale reef teeth.")
    if world.ship.danger == "storm":
        world.say("Far above, one gray cloud thickened while the rest of the sky stayed bright.")
    propagate(world, narrate=True)


def turn(world: World, hero: Entity, captain: Entity, prize: Entity, gear: Gear) -> None:
    world.para()
    world.say(
        f"{hero.id} frowned at first, because waiting felt slower than chasing treasure."
    )
    hero.memes["worry"] += 1
    hero.meters["precision"] += 1
    world.say(
        f"Then {captain.id} handed over {gear.label} and showed {hero.id} how careful hands could fix a risky plan."
    )
    gear_ent = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=captain.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    gear_ent.worn_by = hero.id
    world.say(f"{hero.id} took {gear.label} and {gear.prep}.")
    hero.meters["precision"] += 1
    hero.memes["trust"] += 1
    if solve_route(world, hero):
        world.say(
            f"With the fix in place, {hero.id} could follow the safe course and still chase {prize.label}."
        )
    propagate(world, narrate=True)


def resolve(world: World, hero: Entity, captain: Entity, prize: Entity) -> None:
    world.para()
    world.say(
        f"In the end, {hero.id} steered by a tiny mark on the chart instead of guessing."
    )
    hero.memes["pride"] += 1
    captain.memes["pride"] += 1
    world.say(
        f"The ship slipped past danger, the treasure stayed safe, and {hero.id} was no longer a rushing pirate but a precise one."
    )
    world.say(
        f"That night, the crew cheered as {hero.id} held {prize.it()} aloft, proud to have learned that small clues can save a whole sea journey."
    )


@dataclass
class StoryParams:
    name: str
    gender: str
    captain_name: str
    place: str
    danger: str
    prize: str
    seed: Optional[int] = None


SETTINGS = {
    "cove": Ship(name="The Lantern Fox", sea="the bright sea", route="the hidden cove", weather="fog", danger="reef", safe_action="follow the chalk line", flourish="A lantern swung gently from the mast, blinking like a yellow eye."),
    "island": Ship(name="The Gull's Prize", sea="the open sea", route="the moon island", weather="storm", danger="storm", safe_action="trim the sail", flourish="The deck creaked softly as the gulls wheeled overhead."),
}

PRIZES = {
    "map": Prize(label="map", phrase="an old treasure map with a red X", type="map", region="hand"),
    "compass": Prize(label="compass", phrase="a brass compass with a tiny crack in its glass", type="compass", region="hand"),
    "key": Prize(label="key", phrase="a bright brass key tied to a blue string", type="key", region="neck"),
}

GEAR = {
    "gloves": Gear(id="gloves", label="fingerless chart gloves", covers={"hand"}, guards={"splinter"}, prep="slipped on the chart gloves and traced the route again", tail="kept the charts steady", plural=True),
    "cloak": Gear(id="cloak", label="a storm cloak", covers={"mast"}, guards={"wind"}, prep="buttoned the storm cloak tight around the mast line", tail="held fast against the wind"),
    "lens": Gear(id="lens", label="a small spyglass lens", covers={"eye"}, guards={"mist"}, prep="fit the spyglass lens to check the far rocks", tail="made the rocks easier to see"),
}

NAMES = ["Mira", "Pip", "Taro", "Jory", "Nina", "Beck", "Sloane", "Luca"]
CAPTAINS = ["Captain Wave", "Captain Alder", "Captain Brine", "Captain Marlow"]
TRAITS = ["bold", "curious", "restless", "quick", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, ship in SETTINGS.items():
        for prize_id in PRIZES:
            if place == "cove" and prize_id in {"map", "compass"}:
                combos.append((place, ship.danger, prize_id))
            if place == "island" and prize_id in {"key", "compass"}:
                combos.append((place, ship.danger, prize_id))
    return combos


def prize_requires_precise_handling(prize: Prize) -> bool:
    return prize.label in {"map", "compass", "key"}


def select_gear(ship: Ship, prize: Prize) -> Optional[Gear]:
    if ship.danger == "reef":
        return GEAR["gloves"]
    if ship.danger == "storm":
        return GEAR["cloak"]
    return None


def tell(ship: Ship, prize_cfg: Prize, hero_name: str, hero_type: str, captain_name: str) -> World:
    world = World(ship)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    captain = world.add(Entity(id=captain_name, kind="character", type="captain", label=captain_name))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=captain.id, region=prize_cfg.region))

    hero.meters["precision"] = 0.0
    captain.meters["precision"] = 1.0

    introduce(world, hero, captain, prize)
    foreshadow(world, hero, captain)
    gear = select_gear(ship, prize_cfg)
    if gear is None:
        raise StoryError("No reasonable gear exists for this pirate tale.")
    turn(world, hero, captain, prize, gear)
    resolve(world, hero, captain, prize)

    world.facts.update(hero=hero, captain=captain, prize=prize, ship=ship, gear=gear, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    prize = f["prize"]
    ship = f["ship"]
    return [
        f"Write a short pirate story for a young child about {hero.id}, {captain.id}, and a careful voyage on {ship.route}.",
        f"Tell a story where a pirate notices tiny warning signs and learns to be more precise while protecting {prize.phrase}.",
        f"Write a gentle pirate tale that includes foreshadowing, a safer plan, and an ending where {hero.id} becomes a precise sailor.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, prize, ship = f["hero"], f["captain"], f["prize"], f["ship"]
    return [
        QAItem(
            question=f"Who was the pirate story about?",
            answer=f"It was about {hero.id}, who sailed with {captain.id} on {ship.name}.",
        ),
        QAItem(
            question=f"What treasure item did {hero.id} care about?",
            answer=f"{hero.id} cared about {prize.phrase}, and that was the prize they wanted to protect.",
        ),
        QAItem(
            question=f"What clue came first to warn the crew?",
            answer=f"A small clue appeared first, like the fog or the reef line, and it hinted that the voyage needed a careful plan.",
        ),
        QAItem(
            question=f"How did {hero.id} change by the end?",
            answer=f"{hero.id} changed from wanting to rush ahead into becoming more precise and careful about the route.",
        ),
    ]


KNOWLEDGE = {
    "map": [("What is a map?", "A map is a drawing that shows places and helps people find the way.")],
    "compass": [("What does a compass do?", "A compass helps sailors know which direction they are facing.")],
    "key": [("What is a key for?", "A key is used to open a lock or a box.")],
    "fog": [("What is fog?", "Fog is a thick cloud near the ground or water that makes it hard to see far away.")],
    "reef": [("What is a reef?", "A reef is a line of rocks under the water, and ships must steer carefully around it.")],
    "storm": [("What is a storm?", "A storm is very rough weather with strong wind, rain, and clouds.")],
}


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    prize = world.facts["prize"]
    ship = world.facts["ship"]
    for tag in [prize.label, ship.danger, "map", "compass", "key"]:
        if tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({sig[0] for sig in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mira", gender="girl", captain_name="Captain Wave", place="cove", danger="reef", prize="map"),
    StoryParams(name="Pip", gender="boy", captain_name="Captain Brine", place="cove", danger="reef", prize="compass"),
    StoryParams(name="Nina", gender="girl", captain_name="Captain Marlow", place="island", danger="storm", prize="key"),
]


def explain_rejection(ship: Ship, prize: Prize) -> str:
    return f"(No story: this pirate tale needs a prize that can be protected by a precise plan, and {prize.label} does not fit the chosen voyage.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with precision and foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=CAPTAINS)
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
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid pirate story matches those options.)")
    place, _danger, prize_id = rng.choice(sorted(combos))
    ship = SETTINGS[place]
    prize = PRIZES[prize_id]
    if args.prize and not prize_requires_precise_handling(prize):
        raise StoryError(explain_rejection(ship, prize))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    captain = args.captain or rng.choice(CAPTIONS if False else CAPTAINS)
    return StoryParams(name=name, gender=gender, captain_name=captain, place=place, danger=ship.danger, prize=prize_id)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PRIZES[params.prize], params.name, params.gender, params.captain_name)
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
prize_at_risk(P) :- prize(P).
needs_precision(P) :- prize_at_risk(P).
compatible(cove,map).
compatible(cove,compass).
compatible(island,key).
valid_story(Place,Prize) :- compatible(Place,Prize), prize(Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
        lines.append(asp.fact("compatible", place, "map"))
        lines.append(asp.fact("compatible", place, "compass"))
        if place == "island":
            lines.append(asp.fact("compatible", place, "key"))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((p, prize) for p, _d, prize in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def asp_program_text() -> str:
    return asp_program("#show valid_story/2.")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, ship in SETTINGS.items():
        for prize_id in PRIZES:
            if place == "cove" and prize_id in {"map", "compass"}:
                combos.append((place, ship.danger, prize_id))
            if place == "island" and prize_id in {"key"}:
                combos.append((place, ship.danger, prize_id))
    return combos


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program_text())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(t)
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
            header = f"### {p.name}: {p.prize} on {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
