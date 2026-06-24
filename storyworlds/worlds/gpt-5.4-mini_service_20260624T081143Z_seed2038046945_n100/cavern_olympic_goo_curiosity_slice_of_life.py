#!/usr/bin/env python3
"""
storyworlds/worlds/cavern_olympic_goo_curiosity_slice_of_life.py
=================================================================

A small standalone storyworld about a child in a cavern-side athletic club,
where curiosity leads to a goo mishap and a gentle slice-of-life fix.

Seed image:
- A curious kid wanders near a cavern training hall where a local olympic-style
  games day is being prepared.
- A shiny goo used for equipment maintenance becomes the source of trouble.
- The story turns on a simple, grounded fix: ask, listen, clean, and continue.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- eager import of shared result containers
- lazy import of storyworlds.asp in ASP helpers
- StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and inline ASP twin
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Make shared containers importable when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

LOCATIONS = {
    "cavern": {
        "label": "the cavern hall",
        "indoor": True,
        "affords": {"training", "games"},
    },
    "gallery": {
        "label": "the stone gallery",
        "indoor": True,
        "affords": {"training"},
    },
    "courtyard": {
        "label": "the courtyard",
        "indoor": False,
        "affords": {"games"},
    },
}

ACTIVITIES = {
    "relay": {
        "verb": "join the relay race",
        "gerund": "running the relay",
        "rush": "dash to the starting line",
        "mess": "gooey",
        "soil": "sticky with goo",
        "zone": {"hands", "shoes"},
        "keyword": "relay",
        "tags": {"olympic", "goo"},
    },
    "balance": {
        "verb": "practice the balance beam",
        "gerund": "balancing on the beam",
        "rush": "run to the beam",
        "mess": "gooey",
        "soil": "slick with goo",
        "zone": {"shoes"},
        "keyword": "beam",
        "tags": {"olympic", "goo"},
    },
    "shotput": {
        "verb": "try the shot put",
        "gerund": "pushing the heavy ball",
        "rush": "hurry to the circle",
        "mess": "gooey",
        "soil": "spotted with goo",
        "zone": {"hands"},
        "keyword": "shot put",
        "tags": {"olympic", "goo"},
    },
}

PRIZES = {
    "towel": {
        "label": "towel",
        "phrase": "a soft blue towel",
        "region": "hands",
        "plural": False,
    },
    "shoes": {
        "label": "shoes",
        "phrase": "fresh white shoes",
        "region": "shoes",
        "plural": True,
    },
}

GEAR = [
    {
        "id": "gloves",
        "label": "clean gloves",
        "covers": {"hands"},
        "guards": {"gooey"},
        "prep": "put on clean gloves first",
        "tail": "went back for the clean gloves",
        "plural": True,
    },
    {
        "id": "wraps",
        "label": "shoe wraps",
        "covers": {"shoes"},
        "guards": {"gooey"},
        "prep": "wrap the shoes first",
        "tail": "came back with the shoe wraps",
        "plural": True,
    },
]

GIVEN_NAMES = {
    "child": ["Mina", "Toby", "Lena", "Omar", "Iris", "Nico", "Suri", "Evan"],
    "adult": ["Rae", "Jules", "Noor", "Kai"],
}

TRAITS = ["curious", "gentle", "bright-eyed", "thoughtful", "careful"]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    location: str
    activity: str
    prize: str
    name: str
    role: str = "child"
    helper: str = "coach"
    trait: str = "curious"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    worn_by: Optional[str] = None
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"gooey": 0.0, "dirty": 0.0, "workload": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "joy": 0.0, "conflict": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


class World:
    def __init__(self, location: str) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def prize_at_risk(activity: dict, prize: dict) -> bool:
    return prize["region"] in activity["zone"]


def select_gear(activity: dict, prize: dict) -> Optional[dict]:
    for gear in GEAR:
        if activity["mess"] in gear["guards"] and prize["region"] in gear["covers"]:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for loc, loc_cfg in LOCATIONS.items():
        for act_id, act in ACTIVITIES.items():
            if act_id not in loc_cfg["affords"]:
                continue
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((loc, act_id, prize_id))
    return out


def explain_rejection(activity: dict, prize: dict) -> str:
    return (
        f"(No story: {activity['gerund']} does not realistically threaten the "
        f"{prize['label']}, so there is no honest tension or fix.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def propagate(world: World) -> None:
    for ent in world.entities.values():
        if ent.meters["gooey"] >= THRESHOLD and ent.kind == "character":
            for item in world.entities.values():
                if item.worn_by == ent.id and item.region in world.facts.get("zone", set()):
                    sig = ("soil", item.id)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.meters["dirty"] += 1
                    world.say(f"The {item.label} got sticky with goo.")


def tell(params: StoryParams) -> World:
    loc = LOCATIONS[params.location]
    act = ACTIVITIES[params.activity]
    prize_cfg = PRIZES[params.prize]

    world = World(loc["label"])
    hero = world.add(Entity(id=params.name, kind="character", type="child"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    prize = world.add(Entity(
        id="prize",
        label=prize_cfg["label"],
        type=prize_cfg["label"],
        plural=prize_cfg["plural"],
        owner=hero.id,
        caretaker=helper.id,
        region=prize_cfg["region"],
    ))

    gear_def = select_gear(act, prize_cfg)
    if gear_def is None:
        raise StoryError(explain_rejection(act, prize_cfg))

    world.say(f"{hero.id} was a {params.trait} child who liked peeking into {world.location}.")
    world.say(f"{hero.pronoun().capitalize()} had a question about every rope, chalk mark, and shiny bucket.")
    world.say(f"That morning, the group was getting ready for a small olympic day in the cavern hall.")
    world.say(f"{hero.id} saw {prize.label} set near the lane and wanted to {act['verb']} right away.")
    world.say(f"But the bucket beside the lane held a slippery layer of goo for polishing gear.")

    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1
    world.facts["zone"] = set(act["zone"])

    if prize["region"] in act["zone"]:
        world.say(f"{params.helper.capitalize()} smiled and warned that the {prize.label} could get {act['soil']}.")
        world.say(f"{hero.id} leaned closer, still curious, and almost stepped into the goo.")
        hero.meters["gooey"] += 1
        propagate(world)
        if prize.meters["dirty"] >= THRESHOLD:
            world.say(f"The sight made {hero.id} pause and look down at {hero.pronoun('possessive')} own shoes.")
    world.say(f"{params.helper.capitalize()} then said, \"Let's do it the careful way.\"")
    world.say(f"They {gear_def['prep']} and walked back to the lane together.")
    world.say(f"This time, {hero.id} could {act['verb']} without ruining the {prize.label}.")
    world.say(f"After the run, the cavern hall felt calm again, and the shiny bucket stayed in its place.")

    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0.0
    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        activity=act,
        location=params.location,
        gear=gear_def,
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
fixable(A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
valid_story(L,A,P) :- affords(L,A), prize_at_risk(A,P), fixable(A,P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for loc, cfg in LOCATIONS.items():
        lines.append(asp.fact("location", loc))
        for a in sorted(cfg["affords"]):
            lines.append(asp.fact("affords", loc, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act["mess"]))
        for r in sorted(act["zone"]):
            lines.append(asp.fact("splashes", aid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize["region"]))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear["id"]))
        for m in sorted(gear["guards"]):
            lines.append(asp.fact("guards", gear["id"], m))
        for c in sorted(gear["covers"]):
            lines.append(asp.fact("covers", gear["id"], c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in python:", sorted(py - asp_set))
    print("only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = f["activity"]
    return [
        f'Write a child-friendly slice-of-life story set in {f["location"]} with the word "goo".',
        f"Tell a gentle story about {f['hero'].id}, who is curious about an olympic practice and wants to {act['verb']}.",
        f"Write a short story where a curious child notices goo near a small games day and finds a careful way to keep playing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    prize: Entity = f["prize"]
    helper: Entity = f["helper"]
    act = f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Why did {hero.id} slow down near the lane?",
            answer=f"{hero.id} slowed down because {hero.pronoun('possessive')} curiosity led {hero.pronoun('object')} to notice the goo, and the helper warned that the {prize.label} could get {act['soil']}.",
        ),
        QAItem(
            question=f"What helped {hero.id} keep going without ruining the {prize.label}?",
            answer=f"They used {gear['label']} first, so {hero.id} could {act['verb']} while the {prize.label} stayed clean.",
        ),
        QAItem(
            question=f"Who reminded {hero.id} to choose the careful way?",
            answer=f"The {helper.type} reminded {hero.id} to take the careful way in the cavern hall.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cavern?",
            answer="A cavern is a large cave-like space with rock walls and a roof of stone.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn about something new.",
        ),
        QAItem(
            question="Why can goo be messy?",
            answer="Goo can be messy because it is sticky and can cling to shoes, hands, and clothes.",
        ),
        QAItem(
            question="What is an olympic game?",
            answer="An olympic game is a sport event where people try skills like running, balancing, or throwing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cavern olympic goo curiosity slice-of-life storyworld.")
    ap.add_argument("--location", choices=sorted(LOCATIONS))
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["child"])
    ap.add_argument("--helper", choices=["coach", "helper"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.location or args.activity or args.prize:
        combos = [
            c for c in combos
            if (args.location is None or c[0] == args.location)
            and (args.activity is None or c[1] == args.activity)
            and (args.prize is None or c[2] == args.prize)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    loc, act, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIVEN_NAMES["child"])
    helper = args.helper or "coach"
    trait = args.trait or "curious"
    return StoryParams(location=loc, activity=act, prize=prize, name=name, role="child", helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.kind, e.label, e.region, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for loc, act, prize in valid_combos():
            params = StoryParams(location=loc, activity=act, prize=prize, name="Mina", helper="coach", trait="curious")
            samples.append(generate(params))
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
