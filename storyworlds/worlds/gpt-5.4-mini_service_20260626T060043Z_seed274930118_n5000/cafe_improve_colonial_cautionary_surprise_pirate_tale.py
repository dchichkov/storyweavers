#!/usr/bin/env python3
"""
storyworlds/worlds/cafe_improve_colonial_cautionary_surprise_pirate_tale.py
===========================================================================

A small story world with a pirate-tale flavor set around a colonial cafe.
The core pattern is cautionary: a pirate wants to improve something in the cafe,
ignores a warning, discovers a surprise hazard, and then makes a safer fix.

The world is intentionally compact:
- a pirate crew member wants to improve the cafe
- a careful warning points out the risk
- a surprise reveals why the warning mattered
- the resolution uses the proper tool or method, improving the cafe safely

The prose is child-facing and state-driven rather than a frozen template.
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

# Physical and emotional thresholds for narration.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "damage": 0.0, "improve": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "surprise": 0.0, "caution": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"pirate", "boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    colonial: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
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
        import copy

        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.zone = set(self.zone)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(e.protective and region in e.covers for e in self.worn_items(actor))


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "cafe": Setting(place="the colonial cafe", affords={"brew", "clean", "improve"}),
    "dock": Setting(place="the dockside cafe", affords={"brew", "clean", "improve"}),
    "harbor": Setting(place="the harbor cafe", affords={"brew", "clean", "improve"}),
}

ACTIVITIES = {
    "improve": Activity(
        id="improve",
        verb="improve the cafe",
        gerund="improving the cafe",
        rush="rush to fix the bright counter",
        mess="spilled",
        soil="spilled and sticky",
        zone={"floor", "counter"},
        keyword="improve",
        tags={"improve", "cafe"},
    ),
    "brew": Activity(
        id="brew",
        verb="brew tea",
        gerund="brewing tea",
        rush="dash to the kettle",
        mess="steam",
        soil="steamed up",
        zone={"counter"},
        keyword="tea",
        tags={"tea", "cafe"},
    ),
    "clean": Activity(
        id="clean",
        verb="clean the cafe floor",
        gerund="cleaning the floor",
        rush="swoop with a mop",
        mess="wet",
        soil="wet",
        zone={"floor"},
        keyword="clean",
        tags={"clean", "cafe"},
    ),
}

TOOLS = [
    Tool(
        id="cloth",
        label="a dry cloth",
        covers={"counter"},
        guards={"spilled"},
        prep="use a dry cloth first",
        tail="used a dry cloth to wipe the counter",
    ),
    Tool(
        id="mop",
        label="a long mop",
        covers={"floor"},
        guards={"wet", "spilled"},
        prep="use a long mop first",
        tail="used the long mop on the floor",
    ),
    Tool(
        id="lid",
        label="a snug kettle lid",
        covers={"counter"},
        guards={"steam"},
        prep="put the kettle lid on first",
        tail="set the kettle lid in place",
    ),
]

NAMES = ["Mara", "Ned", "Ivy", "Finn", "Rosa", "Jett"]
TRAITS = ["brave", "curious", "bouncy", "stern", "cheery", "bold"]


@dataclass
class StoryParams:
    place: str
    activity: str
    tool: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def at_risk(activity: Activity, tool: Tool) -> bool:
    return bool(activity.zone & tool.covers)


def select_tool(activity: Activity) -> Optional[Tool]:
    for tool in TOOLS:
        if activity.mess in tool.guards and at_risk(activity, tool):
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for tool in TOOLS:
                if at_risk(act, tool) and act.mess in tool.guards:
                    out.append((place, act_id, tool.id))
    return out


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} pirate who loved the little cafe by the harbor."
    )


def want_improve(world: World, hero: Entity, act: Activity) -> None:
    hero.memes["joy"] += 1
    hero.memes["worry"] += 0.0
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {act.verb} and make it shine like a ship deck."
    )


def warn(world: World, hero: Entity, act: Activity) -> bool:
    if act.id != "improve":
        return False
    hero.memes["caution"] += 1
    world.say(
        f"A careful old mate said, \"Mind the fresh glue and loose sugar, or the cafe will get {act.soil}.\""
    )
    return True


def surprise(world: World, hero: Entity, act: Activity) -> None:
    hero.memes["surprise"] += 1
    world.zone = set(act.zone)
    hero.meters[act.mess] += 1
    if act.id == "improve":
        hero.meters["damage"] += 1
    world.say(
        f"Then came a surprise: a tray tipped, and the counter turned {act.soil} in a blink."
    )


def predict_soil(world: World, hero: Entity, act: Activity, tool: Tool) -> bool:
    sim = world.copy()
    sim.zone = set(act.zone)
    sim.get(hero.id).meters[act.mess] += 1
    return not (act.mess in tool.guards and sim.covered(sim.get(hero.id), next(iter(tool.covers), "")))


def offer_fix(world: World, hero: Entity, act: Activity, tool: Tool) -> None:
    world.say(
        f"At last, {hero.pronoun('possessive')} mate brought {tool.label} and said, \"{tool.prep}.\""
    )
    hero.memes["joy"] += 1
    hero.memes["surprise"] += 0.5


def accept_fix(world: World, hero: Entity, act: Activity, tool: Tool) -> None:
    hero.meters["improve"] += 1
    hero.meters[act.mess] = 0.0
    hero.memes["worry"] = 0.0
    world.say(
        f"{hero.id} nodded, took the tool, and improved the cafe safely. By sunset, {tool.tail}, and the colonial cafe smelled clean and warm again."
    )


def tell(setting: Setting, activity: Activity, tool: Tool, hero_name: str = "Mara", trait: str = "bold") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="pirate", traits=[trait, "careful"]))
    world.facts.update(hero=hero, activity=activity, tool=tool, setting=setting)

    introduce(world, hero)
    world.para()
    want_improve(world, hero, activity)
    warn(world, hero, activity)
    surprise(world, hero, activity)
    world.para()
    offer_fix(world, hero, activity, tool)
    accept_fix(world, hero, activity, tool)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f'Write a short pirate tale for a young child about a pirate who wants to {act.verb} at a colonial cafe.',
        f"Tell a cautionary story where {hero.id} hears a warning, meets a surprise, and then improves the cafe safely.",
        f'Write a gentle story using the word "{act.keyword}" that ends with a safer way to work in the cafe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at the cafe?",
            answer=f"{hero.id} wanted to {act.verb} and make the place shine.",
        ),
        QAItem(
            question="Why was the warning important?",
            answer=f"The warning mattered because the cafe was in danger of getting {act.soil}.",
        ),
        QAItem(
            question=f"What helped {hero.id} improve the cafe safely?",
            answer=f"{tool.label} helped because it matched the problem and let {hero.id} fix the cafe without making a bigger mess.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cafe?",
            answer="A cafe is a small place where people can sit and have drinks or a snack.",
        ),
        QAItem(
            question="What does improve mean?",
            answer="To improve something means to make it better, cleaner, safer, or more useful.",
        ),
        QAItem(
            question="What is a cautionary story?",
            answer="A cautionary story shows a warning and helps the listener learn to be careful.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that changes what the characters thought would happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
at_risk(A,T) :- zone(A,R), covers(T,R), activity(A), tool(T).
compatible(P,A,T) :- place(P), affords(P,A), at_risk(A,T), guards(T,M), mess(A,M).
valid_story(P,A,T) :- compatible(P,A,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for r in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, r))
        for m in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A pirate tale storyworld around a colonial cafe, with caution and surprise."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--tool", choices=[t.id for t in TOOLS])
    ap.add_argument("--name")
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
    if args.activity and args.tool:
        act = ACTIVITIES[args.activity]
        tool = next(t for t in TOOLS if t.id == args.tool)
        if not (at_risk(act, tool) and act.mess in tool.guards):
            raise StoryError("That tool does not safely fit the surprise at the cafe.")
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, tool = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, tool=tool, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], next(t for t in TOOLS if t.id == params.tool), params.name, params.trait)
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
    StoryParams(place="cafe", activity="improve", tool="cloth", name="Mara", trait="bold"),
    StoryParams(place="dock", activity="brew", tool="lid", name="Finn", trait="curious"),
    StoryParams(place="harbor", activity="clean", tool="mop", name="Rosa", trait="cheery"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
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
