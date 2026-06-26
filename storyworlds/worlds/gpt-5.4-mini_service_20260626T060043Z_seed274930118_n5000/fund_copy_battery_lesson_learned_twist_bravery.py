#!/usr/bin/env python3
"""
A small space-adventure story world about a stranded crew, a shared fund,
a copied map, and a battery lesson that ends with bravery.

Seed premise:
---
A space ship drifts near a quiet moon base. The crew has a rescue fund, a copy
of the station map, and one stubborn battery pack that may or may not be enough
to power a tiny beacon. The captain wants to rush, but the engineer warns that
quick choices can waste precious supplies. A twist reveals that the copied map
has one marked hatch the crew missed, and the brave choice is to use the battery
carefully, learn from the mistake, and call for help the right way.

Narrative instruments:
- Lesson Learned: the crew stops wasting power and plans carefully.
- Twist: the copied map reveals a hidden route / hatch.
- Bravery: one character goes first through a risky tunnel to save the others.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "engineer", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moon base"
    backdrop: str = "the stars"
    affords: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Supply:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    fixes: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "moon_base": Setting(place="the moon base", backdrop="the silver stars", affords={"scan", "signal", "crawl"}),
    "dock": Setting(place="the docking ring", backdrop="the blue planet below", affords={"signal", "repair", "crawl"}),
    "asteroid": Setting(place="the asteroid outpost", backdrop="the dark ridge of rocks", affords={"scan", "repair", "crawl"}),
}

MISSIONS = {
    "signal": Mission(
        id="signal",
        verb="send a rescue signal",
        gerund="sending rescue signals",
        rush="rush to power the beacon",
        risk="battery drain",
        lesson="careless power use can leave everyone stuck",
        tags={"battery", "signal"},
    ),
    "repair": Mission(
        id="repair",
        verb="fix the broken hatch",
        gerund="repairing the hatch",
        rush="run to the hatch",
        risk="tool wear",
        lesson="a small mistake can become a big delay",
        tags={"copy", "twist"},
    ),
    "scan": Mission(
        id="scan",
        verb="scan the corridor",
        gerund="scanning the corridor",
        rush="dash to the scanner",
        risk="missed clue",
        lesson="slow looking can find the safest path",
        tags={"copy", "twist"},
    ),
    "crawl": Mission(
        id="crawl",
        verb="crawl through the narrow tunnel",
        gerund="crawling through the tunnel",
        rush="climb into the tunnel",
        risk="scraped knees",
        lesson="brave steps can help everyone",
        tags={"bravery"},
    ),
}

SUPPLIES = {
    "fund": Supply(
        label="rescue fund",
        phrase="the rescue fund",
        type="fund",
        region="cargo",
    ),
    "copy": Supply(
        label="map copy",
        phrase="a copy of the station map",
        type="copy",
        region="hand",
        plural=False,
    ),
    "battery": Supply(
        label="battery pack",
        phrase="one stubborn battery pack",
        type="battery",
        region="hand",
        plural=False,
    ),
}

TOOLS = [
    Tool(
        id="spool",
        label="a long tether spool",
        prep="use the tether spool first",
        tail="used the tether spool and climbed safely after",
        covers={"cargo"},
        fixes={"scraped knees"},
    ),
    Tool(
        id="lamp",
        label="a spare lamp",
        prep="turn on the spare lamp",
        tail="switched on the spare lamp and looked carefully",
        covers={"hand"},
        fixes={"missed clue"},
    ),
    Tool(
        id="shield_gloves",
        label="shield gloves",
        prep="put on shield gloves",
        tail="put on shield gloves and reached in without harm",
        covers={"hand"},
        fixes={"battery drain"},
        plural=True,
    ),
]

GROWNUPS = ["captain", "engineer", "pilot", "commander"]
HERO_NAMES = ["Nova", "Mira", "Rin", "Lio", "Tess", "Orin"]
TRAITS = ["brave", "careful", "curious", "steady", "quick", "hopeful"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def has_risk(mission: Mission, supply: Supply) -> bool:
    if mission.id == "signal" and supply.type == "battery":
        return True
    if mission.id in {"repair", "scan"} and supply.type == "copy":
        return True
    if mission.id == "crawl" and supply.type == "fund":
        return True
    return False


def select_tool(mission: Mission, supply: Supply) -> Optional[Tool]:
    for tool in TOOLS:
        if mission.risk in tool.fixes and supply.region in tool.covers:
            return tool
    return None


def predict(world: World, hero: Entity, mission: Mission, supply: Entity) -> dict:
    sim = world.copy()
    _do_mission(sim, sim.get(hero.id), mission, narrate=False)
    sup = sim.get(supply.id)
    return {
        "drained": sup.meters.get("drain", 0) >= THRESHOLD,
        "lost_clue": sup.meters.get("smear", 0) >= THRESHOLD,
    }


def _do_mission(world: World, hero: Entity, mission: Mission, narrate: bool = True) -> None:
    hero.memes["drive"] = hero.memes.get("drive", 0) + 1
    world.say(f"{hero.id} tried to {mission.verb}.")
    if mission.id == "signal":
        for e in world.entities.values():
            if e.type == "battery":
                e.meters["drain"] = e.meters.get("drain", 0) + 1
                if narrate:
                    world.say("The beacon blinked hard and the battery pack grew weak.")
    elif mission.id == "scan":
        for e in world.entities.values():
            if e.type == "copy":
                e.meters["smear"] = e.meters.get("smear", 0) + 1
                if narrate:
                    world.say("The copied map got creased and the markings looked harder to trust.")
    elif mission.id == "crawl":
        hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
        if narrate:
            world.say("The tunnel was tight and dark, but the brave choice was to go first.")


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.meters.get("traits", [])), None)
    world.say(
        f"{hero.id} was a {hero.memes.get('trait_word', 'brave')} crew member on {world.setting.place}."
    )


def tell_story(setting: Setting, mission: Mission, supply: Supply, hero_name: str, hero_type: str,
               parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={"traits": [trait]}, memes={"trait_word": trait}))
    leader = world.add(Entity(id="Leader", kind="character", type=parent_type, label="the captain"))

    sup = world.add(Entity(
        id=supply.type,
        kind="thing",
        type=supply.type,
        label=supply.label,
        phrase=supply.phrase,
        owner=hero.id,
        caretaker=leader.id,
        plural=supply.plural,
    ))

    world.say(f"Out near {setting.backdrop}, {hero.id} served on {setting.place}.")
    world.say(f"They carried {supply.phrase}, and the whole crew depended on it.")
    world.say(f"{hero.id} wanted to {mission.verb}, but {leader.label or 'the captain'} worried about the {supply.label}.")

    world.para()
    if mission.id == "signal":
        world.say("The rescue fund had already been spent on repairs, so the last battery pack mattered a lot.")
    elif mission.id in {"repair", "scan"}:
        world.say("A copied map was the only guide to the old passageways.")
    else:
        world.say("The ship had no easy way around the narrow tunnel.")

    _do_mission(world, hero, mission, narrate=True)

    world.para()
    pred = predict(world, hero, mission, sup)
    if has_risk(mission, supply) and (pred["drained"] or pred["lost_clue"]):
        if mission.id == "signal":
            world.say(
                f"{leader.label or 'The captain'} warned, 'If we waste the battery now, we may lose our only way home.'"
            )
        elif mission.id in {"repair", "scan"}:
            world.say(
                f"{leader.label or 'The captain'} pointed at the copy and said, 'That map may hold a twist we missed.'"
            )
        else:
            world.say(
                f"{leader.label or 'The captain'} took a breath and said, 'Bravery means choosing the safer path, not the faster one.'"
            )

    tool = select_tool(mission, supply)
    if tool is None and has_risk(mission, supply):
        raise StoryError("No reasonable tool fits this mission and supply.")

    if tool is not None:
        world.say(
            f"Then they found {tool.label}; {tool.prep} before trying again."
        )
        if mission.id == "signal":
            world.say(
                "Using the spare help, they saved the battery and the beacon still had enough power."
            )
        elif mission.id in {"repair", "scan"}:
            world.say(
                "The extra light revealed a hidden hatch in the copied map—a twist that changed everything."
            )
        else:
            world.say(
                "The tether let the brave crew member crawl ahead and guide the others through."
            )

    world.para()
    if mission.id == "signal":
        world.say(
            "The lesson learned was simple: careful power use can be its own kind of courage. "
            f"At the end, the battery pack stayed steady, and the rescue signal reached the stars."
        )
    elif mission.id in {"repair", "scan"}:
        world.say(
            f"The lesson learned was that a careful look can save a whole day. "
            f"The copied map showed the hidden hatch, and the crew found a way through."
        )
    else:
        world.say(
            "The lesson learned was that bravery is not rushing alone, but helping everyone move safely. "
            "The crew crossed the tunnel together and the moon base lights came back on."
        )

    world.facts.update(hero=hero, leader=leader, supply=sup, mission=mission, setting=setting, tool=tool)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure story for a young child that includes the words "fund", "copy", and "battery".',
        f"Tell a simple story about {f['hero'].id} at {f['setting'].place} where a {f['supply'].label} matters and a brave choice solves a problem.",
        f"Write a child-friendly space story with a twist, a lesson learned, and a brave ending near the stars.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    leader = f["leader"]
    supply = f["supply"]
    mission = f["mission"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at {f['setting'].place}?",
            answer=f"{hero.id} wanted to {mission.verb}, but the crew needed to think about {supply.phrase} first.",
        ),
        QAItem(
            question=f"Why did the captain worry about the {supply.label}?",
            answer=(
                f"The captain worried because the mission could hurt {supply.phrase}. "
                f"The story showed that {mission.lesson}."
            ),
        ),
        QAItem(
            question=f"What surprising twist helped the crew?",
            answer=(
                "The copied map showed a hidden hatch, and that new clue changed the plan. "
                "After that, the crew could move ahead more safely."
            ),
        ),
    ]
    if f.get("tool"):
        tool = f["tool"]
        qa.append(
            QAItem(
                question=f"How did {tool.label} help the crew?",
                answer=f"They used {tool.label} to make the mission safer, so they could keep going without wasting what mattered most.",
            )
        )
    if mission.id == "crawl":
        qa.append(
            QAItem(
                question="How did bravery change the ending?",
                answer="One crew member went first through the narrow tunnel, and that brave choice helped everyone get home safely.",
            )
        )
    return qa


KNOWLEDGE = {
    "fund": [
        ("What is a fund?", "A fund is money set aside for a special purpose, like fixing a ship or helping in an emergency."),
    ],
    "copy": [
        ("What is a copy?", "A copy is something made to look like the original, such as a copied map or a copied picture."),
    ],
    "battery": [
        ("What does a battery do?", "A battery stores energy and can power lights, toys, or small machines."),
    ],
    "bravery": [
        ("What is bravery?", "Bravery means doing something scary or hard because it helps others or does the right thing."),
    ],
    "twist": [
        ("What is a twist in a story?", "A twist is a surprising change that makes the story go in a new direction."),
    ],
    "lesson": [
        ("What is a lesson learned?", "A lesson learned is the good idea a character understands after something happens."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"fund", "copy", "battery", "bravery", "twist", "lesson"}
    out: list[QAItem] = []
    for tag in tags:
        for q, a in KNOWLEDGE.get(tag, []):
            out.append(QAItem(question=q, answer=a))
    return out


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
setting(moon_base).
setting(dock).
setting(asteroid_outpost).

affords(moon_base, scan).
affords(moon_base, signal).
affords(moon_base, crawl).
affords(dock, signal).
affords(dock, repair).
affords(dock, crawl).
affords(asteroid_outpost, scan).
affords(asteroid_outpost, repair).
affords(asteroid_outpost, crawl).

mission(signal).
mission(repair).
mission(scan).
mission(crawl).

supply(fund).
supply(copy).
supply(battery).

risk(signal, battery_drain).
risk(repair, missed_clue).
risk(scan, missed_clue).
risk(crawl, bravery_needed).

has_reasonable_fix(signal, battery) :- supply(battery).
has_reasonable_fix(repair, copy) :- supply(copy).
has_reasonable_fix(scan, copy) :- supply(copy).
has_reasonable_fix(crawl, fund) :- supply(fund).

valid(Place, Mission, Supply) :-
    affords(Place, Mission),
    risk(Mission, battery_drain), Supply = battery, has_reasonable_fix(Mission, Supply).

valid(Place, Mission, Supply) :-
    affords(Place, Mission),
    risk(Mission, missed_clue), Supply = copy, has_reasonable_fix(Mission, Supply).

valid(Place, Mission, Supply) :-
    affords(Place, Mission),
    risk(Mission, bravery_needed), Supply = fund, has_reasonable_fix(Mission, Supply).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
        for m in sorted(SETTINGS[pid].affords):
            lines.append(asp.fact("affords", pid, m))
    for mid in MISSIONS:
        lines.append(asp.fact("mission", mid))
    for sid in SUPPLIES:
        lines.append(asp.fact("supply", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Helpers and CLI
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for mid in setting.affords:
            mission = MISSIONS[mid]
            for sid, supply in SUPPLIES.items():
                if has_risk(mission, supply):
                    out.append((place, mid, sid))
    return out


@dataclass
class StoryParams:
    place: str
    mission: str
    supply: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with fund, copy, and battery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--supply", choices=SUPPLIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain", "engineer", "pilot", "commander"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mission is None or c[1] == args.mission)
              and (args.supply is None or c[2] == args.supply)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mission, supply = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(GROWNUPS)
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place=place, mission=mission, supply=supply, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        MISSIONS[params.mission],
        SUPPLIES[params.supply],
        params.name,
        "girl" if params.gender == "girl" else "boy",
        params.parent,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program(""))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="moon_base", mission="signal", supply="battery", name="Nova", gender="girl", parent="engineer", trait="careful"),
            StoryParams(place="dock", mission="scan", supply="copy", name="Mira", gender="girl", parent="captain", trait="curious"),
            StoryParams(place="asteroid_outpost", mission="crawl", supply="fund", name="Rin", gender="boy", parent="commander", trait="brave"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
