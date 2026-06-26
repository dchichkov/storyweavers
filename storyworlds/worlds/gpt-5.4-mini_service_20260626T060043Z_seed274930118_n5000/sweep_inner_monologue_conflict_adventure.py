#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sweep_inner_monologue_conflict_adventure.py
========================================================================================================================

A standalone story world about a child on a small adventure who must sweep up
a troublesome mess while thinking through a conflict in an inner monologue.

Premise:
- A child wants to go on a treasure-hunt-style adventure right away.
- The room contains a messy patch that makes the path unsafe or unpleasant.
- Another character asks for the mess to be swept first.
- The hero argues inwardly, then chooses a practical way forward.

This world is intentionally small and state-driven:
- physical meters track dust, clean floor, blocked paths, and sweeping progress
- emotional memes track eagerness, irritation, concern, and resolve
- prose is generated from simulated state rather than from a fixed paragraph
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old hall"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    obstacle: str
    tag: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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


def _sweep(world: World, actor: Entity, activity: Activity) -> list[str]:
    out: list[str] = []
    if world.facts.get("path_blocked") and actor.meters.get("sweeping", 0.0) >= THRESHOLD:
        sig = ("clear", actor.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["path_blocked"] = False
            actor.meters["dust"] = max(0.0, actor.meters.get("dust", 0.0) - 1.0)
            actor.meters["clean_path"] = 1.0
            out.append("The broom pushed the dust into a neat little pile.")
    return out


def _resolve_conflict(world: World, hero: Entity) -> list[str]:
    if hero.memes.get("conflict", 0.0) < THRESHOLD:
        return []
    sig = ("resolve", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1.0
    hero.memes["conflict"] = 0.0
    return ["__resolve__"]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if actor.meters.get("sweeping", 0.0) >= THRESHOLD:
                sents = _sweep(world, actor, world.facts["activity"])
                if sents:
                    changed = True
                    produced.extend(sents)
        for actor in world.characters():
            sents = _resolve_conflict(world, actor)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            if s != "__resolve__":
                world.say(s)
    return produced


def _do_sweep(world: World, hero: Entity, narrate: bool = True) -> None:
    hero.meters["sweeping"] = hero.meters.get("sweeping", 0.0) + 1.0
    hero.meters["dust"] = hero.meters.get("dust", 0.0) + 1.0
    hero.memes["determination"] = hero.memes.get("determination", 0.0) + 1.0
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, helper: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved adventure stories and secret maps."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {activity.verb} through {world.setting.place}, "
        f"because every echo there sounded like the start of a quest."
    )
    helper_name = helper.label or helper.id
    world.say(
        f"But {helper_name} pointed at the dust and said the path needed a sweep first."
    )


def inner_monologue(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["eagerness"] = hero.memes.get("eagerness", 0.0) + 1.0
    hero.memes["irritation"] = hero.memes.get("irritation", 0.0) + 1.0
    world.say(
        f"{hero.id} looked at the broom and thought, "
        f"“I want to {activity.verb} now, not spend the morning sweeping.”"
    )
    world.say(
        f"Still, another thought whispered back: “If the floor stays dusty, the adventure could go wrong.”"
    )


def conflict_beat(world: World, hero: Entity, helper: Entity, activity: Activity) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1.0
    world.say(
        f"{helper.label or helper.id} stayed firm, so {hero.id} frowned and hugged the broom handle."
    )
    world.say(
        f"{hero.id} wanted the fast route, but {hero.pronoun('possessive')} own mind kept asking whether the safe route was wiser."
    )


def compromise(world: World, hero: Entity, helper: Entity, activity: Activity, tool: Tool) -> None:
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1.0
    hero.memes["conflict"] = 0.0
    hero.meters["sweeping"] = hero.meters.get("sweeping", 0.0) + 1.0
    world.say(
        f"At last {hero.id} took a breath, picked up {tool.phrase}, and began to sweep in strong, careful strokes."
    )
    world.say(
        f"{helper.label or helper.id} watched the dust pile grow and nodded at the steady work."
    )
    propagate(world, narrate=True)
    if not world.facts.get("path_blocked"):
        world.say(
            f"When the floor was clear, {hero.id} stepped forward for the adventure, "
            f"and the hall looked bright and ready."
        )


def tell(setting: Setting, activity: Activity, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"dust": 0.0, "sweeping": 0.0, "clean_path": 0.0},
        memes={"eagerness": 0.0, "irritation": 0.0, "conflict": 0.0, "resolve": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the keeper of the hall",
        memes={"firmness": 1.0},
    ))
    broom = world.add(Entity(
        id="Broom",
        type="tool",
        label="the broom",
        phrase="the broom",
        owner=hero.id,
    ))
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["activity"] = activity
    world.facts["tool"] = broom
    world.facts["path_blocked"] = True

    introduce(world, hero, helper, activity)
    world.para()
    inner_monologue(world, hero, activity)
    conflict_beat(world, hero, helper, activity)
    world.para()
    compromise(world, hero, helper, activity, Tool(id="broom", label="broom", phrase="the broom", guards={"dust"}))
    return world


SETTINGS = {
    "hall": Setting(place="the old hall", indoor=True, affords={"sweep"}),
    "attic": Setting(place="the attic", indoor=True, affords={"sweep"}),
    "porch": Setting(place="the front porch", indoor=True, affords={"sweep"}),
}

ACTIVITIES = {
    "sweep": Activity(
        id="sweep",
        verb="sweep the floor",
        gerund="sweeping the floor",
        rush="dash down the hallway",
        mess="dust",
        soil="dusty",
        obstacle="dusty patches",
        tag="sweep",
    ),
}

HERO_NAMES = ["Milo", "Tessa", "Nina", "Owen", "Iris", "Pip"]
HERO_TYPES = ["boy", "girl"]
HELPER_TYPES = ["father", "mother", "grandmother", "grandfather"]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An adventure story world about sweeping, conflict, and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--helper", choices=HELPER_TYPES)
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
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or "sweep"
    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_TYPES)
    return StoryParams(place=place, activity=activity, name=name, gender=gender, helper=helper)


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    activity = world.facts["activity"]
    return [
        f"Write a short adventure story about {hero.id} who has to {activity.verb} before the quest can begin.",
        f"Tell a child-friendly story with inner monologue and conflict where {hero.id} debates sweeping first.",
        f"Write a gentle adventure tale that ends with {hero.id} finishing the sweep and stepping into the journey.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    activity = world.facts["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do before sweeping the floor?",
            answer=f"{hero.id} wanted to {activity.verb} and start the adventure right away.",
        ),
        QAItem(
            question=f"Why was there a conflict in the story?",
            answer=f"There was a conflict because {helper.label or helper.id} wanted the dusty floor swept first, while {hero.id} wanted to hurry off on the adventure.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} chose to sweep carefully first, and then the path was clear for the adventure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sweeping do?",
            answer="Sweeping uses a broom to push dust and crumbs into a pile so a floor becomes cleaner and easier to walk on.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice of a character's thoughts inside their own mind.",
        ),
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a problem or disagreement that makes a character pause, choose, or work hard before things get better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
path_blocked :- dust_present.
clean_path :- swept.
resolve :- conflict, chose_sweep.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("tag", aid, act.tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(place, act) for place, s in SETTINGS.items() for act in s.affords if act in ACTIVITIES]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], params.name, params.gender, params.helper)
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
    StoryParams(place="hall", activity="sweep", name="Milo", gender="boy", helper="father"),
    StoryParams(place="attic", activity="sweep", name="Tessa", gender="girl", helper="mother"),
    StoryParams(place="porch", activity="sweep", name="Iris", gender="girl", helper="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, act in combos:
            print(f"  {place:10} {act}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
