#!/usr/bin/env python3
"""
A small pirate-tale storyworld with a twist: a captain must choose who gets the
top lookout spot, but a preferential choice turns out to be unfair and the crew
finds a cleverer fix.

The seed words are echoed in-world as "preferential" and "top".
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    label: str = ""
    title: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.title in {"captain", "sailor", "mate", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.title in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class ShipSetting:
    place: str = "the little ship"
    sea_state: str = "calm"
    affords: set[str] = field(default_factory=lambda: {"lookout", "storm"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


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
    def __init__(self, setting: ShipSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.weather: str = ""

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "harbor": ShipSetting(place="the harbor", sea_state="calm", affords={"lookout"}),
    "open_sea": ShipSetting(place="the open sea", sea_state="windy", affords={"lookout", "storm"}),
    "stormy": ShipSetting(place="the stormy sea", sea_state="stormy", affords={"storm"}),
}

ACTIVITIES = {
    "lookout": Activity(
        id="lookout",
        verb="climb the mast to keep watch",
        gerund="keeping lookout",
        rush="dash up the ladder",
        risk="be spotted too late by a sneaky ship",
        weather="windy",
        zone={"top"},
        tags={"sea", "wind"},
    ),
    "storm": Activity(
        id="storm",
        verb="haul sails through the storm",
        gerund="hauling sails in the storm",
        rush="run for the ropes",
        risk="slip on wet boards",
        weather="stormy",
        zone={"top", "deck"},
        tags={"storm", "rain", "sea"},
    ),
}

PRIZES = {
    "hat": Prize(id="hat", label="hat", phrase="a fine feathered hat", region="top"),
    "coat": Prize(id="coat", label="coat", phrase="a warm captain's coat", region="top"),
    "scarf": Prize(id="scarf", label="scarf", phrase="a striped scarf", region="top"),
}

GEAR = [
    Gear(
        id="slick_boots",
        label="slick sea boots",
        covers={"deck"},
        guards={"storm"},
        prep="pull on slick sea boots first",
        tail="wore the slick sea boots",
    ),
    Gear(
        id="hood",
        label="a rain hood",
        covers={"top"},
        guards={"storm"},
        prep="tie on a rain hood first",
        tail="tied on the rain hood",
    ),
    Gear(
        id="rope_belt",
        label="a rope belt",
        covers={"top"},
        guards={"lookout"},
        prep="strap on a rope belt first",
        tail="strapped on the rope belt",
    ),
]

NAMES = ["Mara", "Jory", "Nell", "Pip", "Tess", "Rook", "Finn", "Bess"]
TITLES = ["captain", "mate", "sailor"]
TRAITS = ["bold", "curious", "quick", "stubborn", "cheerful"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.id in gear.guards:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            activity = ACTIVITIES[act]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(activity, prize) and select_gear(activity, prize):
                    out.append((place, act, prize_id))
    return out


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} does not reach the {prize.label}, "
            f"so there is no honest pirate worry and no reason to twist the tale.)"
        )
    return (
        f"(No story: the ship has no sensible fix for a {prize.label} against "
        f"{activity.gerund}, so this setup is too weak for a proper pirate twist.)"
    )


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), prize_region(P,R).
protects(G,A,P) :- prize_at_risk(A,P), gear(G), guards(G,A), covers(G,R), prize_region(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), protects(_,A,P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for z in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for gd in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, gd))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - ap:
        print("  only in python:", sorted(py - ap))
    if ap - py:
        print("  only in clingo:", sorted(ap - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def top_word(prize: Prize) -> str:
    return "top"


def choose_combo(args, rng: random.Random) -> tuple[str, str, str]:
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    return rng.choice(sorted(combos))


def build_world(params) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    prize_cfg = PRIZES[params.prize]
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=params.name, kind="character", title=params.title, label=params.name,
        memes={"pride": 1.0, "desire": 1.0},
    ))
    captain = world.add(Entity(
        id="captain", kind="character", title="captain", label="Captain Brine",
        memes={"authority": 1.0},
    ))
    mate = world.add(Entity(
        id="mate", kind="character", title="mate", label="First Mate Wren",
        memes={"fairness": 1.0},
    ))
    prize = world.add(Entity(
        id="prize", label=prize_cfg.label, title=prize_cfg.label, plural=prize_cfg.plural,
        owner=hero.id, worn_by=hero.id,
    ))

    world.say(
        f"{hero.id} was a {params.trait} pirate who loved the high sea and every "
        f"top place on the ship."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wore {prize_cfg.phrase} and liked how it made "
        f"{hero.id} look ready for a grand voyage."
    )

    world.para()
    world.say(
        f"One {activity.weather} day, the ship reached {world.setting.place}, "
        f"and the crew knew they would need {activity.gerund}."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, but {captain.label} worried that "
        f"{prize_cfg.label} could get {activity.risk}."
    )
    world.say(
        f"The captain made a preferential choice and said the {top_word(prize_cfg)} "
        f"spot was for the fastest sailor."
    )

    world.para()
    hero.memes["defiance"] = 1.0
    world.say(
        f"{hero.id} frowned and climbed anyway, because the shiny {prize_cfg.label} "
        f"made {hero.id} feel too proud to wait."
    )
    world.say(
        f"Then the wind rose hard, and the {top_word(prize_cfg)} boards shook under "
        f"{hero.id}'s boots."
    )
    if activity.id == "storm":
        world.say(
            f"Rain snapped against the mast, and the {prize_cfg.label} would surely "
            f"be ruined if the crew kept rushing."
        )

    world.para()
    gear = select_gear(activity, prize_cfg)
    if not gear:
        raise StoryError(explain_rejection(activity, prize_cfg))
    world.say(
        f"First Mate Wren pointed to {gear.label} and said they could keep the "
        f"{top_word(prize_cfg)} gear safe without stopping the whole ship."
    )
    world.say(
        f"The captain blinked, because the smart fix was not to favor the fastest "
        f"sailor at all, but to choose the right helper for the job."
    )
    world.say(
        f"So {hero.id} {gear.tail}, went back up, and {activity.gerund} safely."
    )
    world.say(
        f"In the end, the crew worked together, and the {top_word(prize_cfg)} spot "
        f"belonged to the lookout, while the {prize_cfg.label} stayed dry and bright."
    )

    world.facts.update(
        hero=hero,
        captain=captain,
        mate=mate,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        gear=gear,
        resolved=True,
        conflict=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    prize = f["prize_cfg"]
    return [
        "Write a short pirate tale for a young child that includes the words "
        '"preferential" and "top".',
        f"Tell a story where {hero.id} wants to {activity.verb} but must not ruin "
        f"{prize.phrase}.",
        "Write a pirate story with a twist ending where the fairest choice is not "
        "the first choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize_cfg"]
    activity = f["activity"]
    captain = f["captain"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do on the ship?",
            answer=f"{hero.id} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"Why did {captain.label} worry about {prize.label}?",
            answer=f"{captain.label} worried because {prize.phrase} could get {activity.risk}.",
        ),
        QAItem(
            question="What was the preferential choice on the ship?",
            answer="The captain first chose the top spot for the fastest sailor.",
        ),
        QAItem(
            question="What fixed the problem?",
            answer=f"The crew used {gear.label} so the story could continue safely.",
        ),
        QAItem(
            question="What was the twist?",
            answer="The captain learned that fairness meant choosing the right helper, not just the fastest pirate.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is the top of a ship?",
            answer="The top of a ship is the highest place, like the mast or lookout spot.",
        ),
        QAItem(
            question="What does preferential mean?",
            answer="Preferential means giving one person special choice or advantage before others.",
        ),
        QAItem(
            question="Why do pirates watch the sea from high places?",
            answer="Pirates watch from high places so they can spot other ships or danger sooner.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    title: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--title", choices=["captain", "mate", "sailor"], default=None)
    ap.add_argument("--trait", choices=TRAITS, default=None)
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
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        pr = PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        title=args.title or rng.choice(TITLES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="harbor", activity="lookout", prize="hat", name="Mara", title="captain", trait="bold"),
    StoryParams(place="open_sea", activity="storm", prize="coat", name="Nell", title="mate", trait="quick"),
    StoryParams(place="open_sea", activity="lookout", prize="scarf", name="Pip", title="sailor", trait="curious"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for row in combos:
            print(" ", row)
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
            header = f"### {p.name}: {p.activity} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
