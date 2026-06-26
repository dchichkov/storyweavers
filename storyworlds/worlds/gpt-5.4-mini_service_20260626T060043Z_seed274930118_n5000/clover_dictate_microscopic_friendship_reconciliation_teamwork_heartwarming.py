#!/usr/bin/env python3
"""
A heartwarming story world about a tiny garden team, a bossy directive,
and a friendship repaired through teamwork.

Seed inspiration:
- clover
- dictate
- microscopic

Premise:
A little child or garden helper wants to arrange a microscopic clover patch
their own way, but their friends have better ideas. A small disagreement grows
until they listen to one another, work together, and make something lovely.

This script models physical meters and emotional memes, supports ASP parity
verification, and emits complete story + QA samples.
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
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "windowsill": {
        "label": "the sunny windowsill",
        "setting": "indoor",
        "affords": {"arrange", "water", "grow"},
    },
    "garden": {
        "label": "the small garden bed",
        "setting": "outdoor",
        "affords": {"arrange", "water", "grow", "share"},
    },
    "greenhouse": {
        "label": "the little greenhouse",
        "setting": "indoor",
        "affords": {"arrange", "water", "grow", "share"},
    },
}

ACTIVITIES = {
    "arrange": {
        "label": "arrange the clover patch",
        "verb": "arrange the clover patch",
        "gerund": "arranging the clover patch",
        "mess": "scattered",
        "turn": "scattered all over",
        "zone": {"hands", "table"},
        "keyword": "clover",
        "tags": {"clover", "friendship"},
    },
    "water": {
        "label": "water the tiny plants",
        "verb": "water the tiny plants",
        "gerund": "watering the tiny plants",
        "mess": "wet",
        "turn": "wet and slippery",
        "zone": {"hands", "table"},
        "keyword": "microscopic",
        "tags": {"microscopic", "teamwork"},
    },
    "grow": {
        "label": "care for the microscopic clover",
        "verb": "care for the microscopic clover",
        "gerund": "caring for the microscopic clover",
        "mess": "tired",
        "turn": "a little tired",
        "zone": {"hands"},
        "keyword": "clover",
        "tags": {"microscopic", "clover"},
    },
    "share": {
        "label": "share the clover seeds",
        "verb": "share the clover seeds",
        "gerund": "sharing the clover seeds",
        "mess": "mixed-up",
        "turn": "mixed up",
        "zone": {"hands", "basket"},
        "keyword": "clover",
        "tags": {"friendship", "reconciliation"},
    },
}

TOOLS = {
    "watering_can": {
        "label": "a tiny watering can",
        "guards": {"wet"},
        "covers": {"hands"},
        "prep": "carefully use the tiny watering can together",
        "tail": "carefully used the tiny watering can together",
    },
    "tray": {
        "label": "a shallow tray",
        "guards": {"scattered"},
        "covers": {"table", "hands"},
        "prep": "set everything on a shallow tray first",
        "tail": "set everything on a shallow tray first",
    },
    "brush": {
        "label": "a soft brush",
        "guards": {"scattered", "wet"},
        "covers": {"hands", "table"},
        "prep": "use a soft brush and slow hands",
        "tail": "used a soft brush and slow hands",
    },
}

NAMES = ["Milo", "Nia", "Poppy", "Theo", "Luna", "Eli", "Ruby", "Owen"]
ROLES = ["friend", "helper", "child"]
GENTLE_TRAITS = ["kind", "patient", "curious", "gentle", "thoughtful", "warm"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for k in ["mess", "dirty", "workload"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "love", "hurt", "pride", "bossy", "distance", "trust", "conflict"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    key: str
    label: str
    setting: str
    affords: set[str]


@dataclass
class Activity:
    key: str
    label: str
    verb: str
    gerund: str
    mess: str
    turn: str
    zone: set[str]
    keyword: str
    tags: set[str]


@dataclass
class Tool:
    key: str
    label: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.timeline: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.timeline.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.timeline = list(self.timeline)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    tool: str
    name: str
    role: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Rules and simulation
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    act = world.facts.get("activity")
    if not act:
        return out
    for ent in world.entities.values():
        if ent.meters["mess"] < THRESHOLD:
            continue
        sig = ("spread", ent.id, act.key)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["conflict"] += 1
        out.append(f"{ent.id} made the little space feel {act.turn}.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["dirty"] < THRESHOLD or not ent.caretaker:
            continue
        sig = ("workload", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(ent.caretaker)
        caretaker.meters["workload"] += 1
        out.append(f"That would mean more cleaning for {caretaker.label}.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_spread, _r_workload):
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, actor: Entity, activity: Activity, target_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    target = sim.entities[target_id]
    return {
        "mess": target.meters["mess"] >= THRESHOLD,
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters["mess"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def title_line(hero: Entity, friend: Entity, activity: Activity) -> str:
    return (
        f"{hero.id} and {friend.id} loved the tiny, microscopic clover patch, "
        f"but they did not always love the same plan."
    )


def introduce(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    world.say(title_line(hero, friend, activity))
    world.say(
        f"{hero.id} was a {next((t for t in hero.traits if t != 'little'), 'kind')} {hero.type} "
        f"who liked to {activity.verb} on {world.place.label}."
    )
    world.say(
        f"{friend.id} was a {next((t for t in friend.traits if t != 'little'), 'patient')} {friend.type} "
        f"who loved the clover leaves because they looked like tiny green hearts."
    )


def bossy_start(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    hero.memes["bossy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} began to dictate the whole plan, telling {friend.id} where every clover leaf should go."
    )
    world.say(
        f"{friend.id} listened at first, but {hero.id} sounded more like a little ruler than a helper."
    )


def hurt_response(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    friend.memes["hurt"] += 1
    friend.memes["distance"] += 1
    world.say(
        f"{friend.id}'s smile slipped away. {friend.pronoun().capitalize()} wanted to help, not just be told what to do."
    )
    world.say(
        f"The microscopic clover pieces looked smaller than ever as the air between them grew quiet."
    )


def apology(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["bossy"] = 0.0
    hero.memes["hurt"] += 0.0
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{hero.id} looked down and said sorry for trying to dictate everything."
    )
    world.say(
        f"{friend.id} looked back, and the two friends breathed easier right away."
    )


def offer_teamwork(world: World, hero: Entity, friend: Entity, activity: Activity, tool: Tool) -> None:
    world.say(
        f"Then {hero.id} asked {friend.id} to share the job. "
        f"Together they would {tool.prep} and {activity.verb} as a team."
    )


def complete(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["love"] += 1
    friend.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    friend.memes["conflict"] = 0.0
    world.say(
        f"Soon they were both {activity.gerund}, side by side, with careful hands and matching smiles."
    )
    world.say(
        f"The clover patch stayed neat, and the little garden felt warm again, like a place built for friends."
    )


def tell(place: Place, activity: Activity, tool: Tool, hero_name: str, role: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=role, traits=["little", trait, "bossy"]
    ))
    friend = world.add(Entity(
        id="Friend", kind="character", type="child", label="the friend", traits=["little", "kind", "patient"]
    ))
    clover = world.add(Entity(
        id="CloverPatch", type="thing", label="the microscopic clover patch",
        phrase="a microscopic clover patch", caretaker=friend.id
    ))
    tool_ent = world.add(Entity(
        id=tool.key, type="tool", label=tool.label, protective=True, covers=set(tool.covers)
    ))
    tool_ent.worn_by = hero.id

    world.facts.update(hero=hero, friend=friend, clover=clover, activity=activity, tool=tool_ent, place=place)

    introduce(world, hero, friend, activity)
    world.para()
    bossy_start(world, hero, friend, activity)
    world.say(
        f"They were caring for {clover.label} on {place.label}, but the plan was getting tense."
    )
    hurt_response(world, hero, friend, activity)

    world.para()
    hero.memes["conflict"] += 1
    friend.memes["conflict"] += 1
    if predict(world, hero, activity, clover.id)["mess"]:
        world.say(
            f"{hero.id} noticed that the clover bits would get {activity.turn} if they hurried alone."
        )
    apology(world, hero, friend)
    offer_teamwork(world, hero, friend, activity, tool)
    complete(world, hero, friend, activity)
    return world


# ---------------------------------------------------------------------------
# Constraint checks
# ---------------------------------------------------------------------------

def activity_can_affect(activity: Activity, place: Place) -> bool:
    return activity.key in place.affords


def compatible_tool(activity: Activity, tool: Tool) -> bool:
    return activity.mess in tool.guards


def valid_combo(place_key: str, activity_key: str, tool_key: str) -> bool:
    place = Place(place_key, PLACES[place_key]["label"], PLACES[place_key]["setting"], set(PLACES[place_key]["affords"]))
    act = Activity(activity_key, **ACTIVITIES[activity_key])
    tool = Tool(tool_key, **TOOLS[tool_key])
    return activity_can_affect(act, place) and compatible_tool(act, tool)


# ---------------------------------------------------------------------------
# Content selection
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pk in PLACES:
        for ak in ACTIVITIES:
            for tk in TOOLS:
                if valid_combo(pk, ak, tk):
                    out.append((pk, ak, tk))
    return out


def explain_rejection(activity: Activity, tool: Tool) -> str:
    return (
        f"(No story: {activity.verb} would not be reasonably helped by {tool.label}. "
        f"The fix has to match the mess and the place, so this combination is rejected.)"
    )


# ---------------------------------------------------------------------------
# Story QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    act = f["activity"]
    return [
        f'Write a heartwarming story about friendship and teamwork with the word "{act.keyword}".',
        f"Tell a gentle tale where {hero.id} starts out bossy, then apologizes, and {friend.id} helps fix the microscopic clover patch.",
        f"Write a short story about two friends who reconcile by working together around a tiny clover garden.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    act = f["activity"]
    place = f["place"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who was trying to dictate the plan at {place.label}?",
            answer=f"{hero.id} was the one who started out dictating the plan, but {hero.id} later apologized."
        ),
        QAItem(
            question=f"What did the friends work on together?",
            answer=f"They worked on {f['clover'].label}, a tiny clover patch that needed careful hands."
        ),
        QAItem(
            question=f"How did {tool.label} help with {act.label}?",
            answer=f"It helped them keep the work neat, so they could {act.verb} together without making the little space messy."
        ),
        QAItem(
            question=f"What changed between the two friends by the end?",
            answer=f"They moved from hurt feelings to reconciliation, and their teamwork brought them back together."
        ),
    ]


WORLD_KNOWLEDGE = {
    "clover": [
        QAItem(
            question="What is a clover?",
            answer="A clover is a small green plant with round leaves, and some clovers have three leaves while others may have a lucky-looking shape."
        ),
        QAItem(
            question="Why do people like clover patches?",
            answer="People like clover patches because they look soft, green, and cheerful, like a tiny carpet made by nature."
        ),
    ],
    "microscopic": [
        QAItem(
            question="What does microscopic mean?",
            answer="Microscopic means so tiny that you usually need a microscope or very close looking to see it well."
        ),
    ],
    "friendship": [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between people who care about each other, share, listen, and help."
        ),
    ],
    "reconciliation": [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and make peace again after a disagreement."
        ),
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together, each helping in a way that makes the job easier and better."
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE["clover"] + WORLD_KNOWLEDGE["microscopic"] + WORLD_KNOWLEDGE["friendship"] + WORLD_KNOWLEDGE["reconciliation"] + WORLD_KNOWLEDGE["teamwork"]


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
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- act(A).
tool(T) :- aid(T).

valid(P,A,T) :- place(P), activity(A), tool(T), affords(P,A), can_fix(T,A).
friendship_story(P,A,T) :- valid(P,A,T).
reconciliation_story(P,A,T) :- valid(P,A,T).
teamwork_story(P,A,T) :- valid(P,A,T).

can_fix(T,A) :- tool(T), mess_of(A,M), guards(T,M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pk, p in PLACES.items():
        lines.append(asp.fact("setting", pk))
        for a in sorted(p["affords"]):
            lines.append(asp.fact("affords", pk, a))
    for ak, a in ACTIVITIES.items():
        lines.append(asp.fact("act", ak))
        lines.append(asp.fact("mess_of", ak, a["mess"]))
    for tk, t in TOOLS.items():
        lines.append(asp.fact("aid", tk))
        for g in sorted(t["guards"]):
            lines.append(asp.fact("guards", tk, g))
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
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming clover friendship story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["girl", "boy", "child"], default=None)
    ap.add_argument("--trait", choices=GENTLE_TRAITS)
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
    combos = valid_combos()
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, tool = rng.choice(sorted(combos))
    role = args.role or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(GENTLE_TRAITS)
    return StoryParams(place=place, activity=activity, tool=tool, name=name, role=role, trait=trait)


def generate(params: StoryParams) -> StorySample:
    place = Place(params.place, **PLACES[params.place])
    act = Activity(params.activity, **ACTIVITIES[params.activity])
    tool = Tool(params.tool, **TOOLS[params.tool])
    world = tell(place, act, tool, params.name, params.role, params.trait)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:12} ({e.kind:10}) {' '.join(bits)}")
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(f"{len(asp.atoms(model, 'valid'))} compatible combos:")
        for item in sorted(set(asp.atoms(model, "valid"))):
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for pk, ak, tk in sorted(valid_combos()):
            params = StoryParams(
                place=pk,
                activity=ak,
                tool=tk,
                name="Milo",
                role="child",
                trait="kind",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
