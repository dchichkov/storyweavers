#!/usr/bin/env python3
"""
A standalone story world for a heartwarming playroom tale about posey,
gibberish, kindness, and reconciliation.

The simulated domain:
- A child plays in a playroom.
- A treasured posey toy/book/box is at risk of being disrupted by gibberish play.
- A parent or caregiver warns gently.
- Kindness opens the door to reconciliation.
- The ending proves a state change: the room is calm, the toy is safe, and the people feel closer.

This script follows the Storyweavers world contract.
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
# Domain model
# ---------------------------------------------------------------------------

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
    touched_by: Optional[str] = None
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
    place: str = "the playroom"
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
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    risk: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Compromise:
    id: str
    label: str
    prep: str
    finish: str
    helps: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def is_kind(self, actor_id: str) -> bool:
        return self.entities[actor_id].memes.get("kindness", 0.0) > 0.5

    def is_reconciled(self) -> bool:
        return self.facts.get("reconciled", False)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "playroom": Setting(place="the playroom", indoor=True, affords={"gibberish", "kindness"}),
}

ACTIVITIES = {
    "gibberish": Activity(
        id="gibberish",
        verb="say silly gibberish words",
        gerund="saying silly gibberish words",
        rush="blurt out another silly string of sounds",
        mess="scatter",
        soil="messy",
        keyword="gibberish",
        tags={"gibberish", "voice"},
    ),
    "kindness": Activity(
        id="kindness",
        verb="help clean up kindly",
        gerund="helping kindly",
        rush="reach for the crayons and wipe the table",
        mess="soften",
        soil="gentle",
        keyword="kindness",
        tags={"kindness", "help"},
    ),
}

PRIZES = {
    "posey": Prize(
        label="posey",
        phrase="a little posey paper flower",
        type="posey",
        risk="torn",
        genders={"girl", "boy"},
    ),
    "book": Prize(
        label="storybook",
        phrase="a neat picture book",
        type="book",
        risk="smudged",
    ),
    "tower": Prize(
        label="block tower",
        phrase="a tall block tower",
        type="tower",
        risk="knocked over",
    ),
}

COMPROMISES = {
    "quiet_game": Compromise(
        id="quiet_game",
        label="a quiet pretend game",
        prep="switch to a quiet pretend game first",
        finish="They played a quiet pretend game together",
        helps={"gibberish"},
        covers={"smudge", "scatter"},
    ),
    "cleanup": Compromise(
        id="cleanup",
        label="a cleanup game",
        prep="make a cleanup game out of the mess",
        finish="They turned the cleanup into a small game and laughed softly",
        helps={"gibberish", "kindness"},
        covers={"scatter"},
    ),
}

NAMES = ["Posey", "Mina", "Theo", "Lily", "Noah", "Ava", "Ben", "Maya"]
PARENT_NAMES = ["Mom", "Dad", "Mama", "Papa"]
TRAITS = ["gentle", "curious", "cheerful", "playful", "thoughtful"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    if prize.id if hasattr(prize, "id") else None:
        pass
    return True if activity.id == "gibberish" and prize.label in {"posey", "storybook", "block tower"} else False


def select_compromise(activity: Activity, prize: Prize) -> Optional[Compromise]:
    for c in COMPROMISES.values():
        if activity.id in c.helps:
            return c
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                act = ACTIVITIES[act_id]
                pr = PRIZES[prize_id]
                if prize_at_risk(act, pr) and select_compromise(act, pr):
                    combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not create a believable problem for {prize.label}, "
        f"or there is no gentle compromise that fits. Try a different prize.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def _mutate_gibberish(world: World, child: Entity, prize: Entity, activity: Activity) -> None:
    child.meters["noise"] = child.meters.get("noise", 0.0) + 1
    child.memes["glee"] = child.memes.get("glee", 0.0) + 1
    prize.meters["risk"] = prize.meters.get("risk", 0.0) + 1
    world.trace_notes.append("gibberish raised noise and risk")


def _mutate_kindness(world: World, child: Entity, parent: Entity, prize: Entity) -> None:
    child.memes["kindness"] = child.memes.get("kindness", 0.0) + 1
    parent.memes["relief"] = parent.memes.get("relief", 0.0) + 1
    world.trace_notes.append("kindness softened the room")


def _mutate_reconciliation(world: World, child: Entity, parent: Entity) -> None:
    child.memes["reconciliation"] = child.memes.get("reconciliation", 0.0) + 1
    parent.memes["reconciliation"] = parent.memes.get("reconciliation", 0.0) + 1
    world.facts["reconciled"] = True
    world.trace_notes.append("reconciliation settled the disagreement")


def predict_risk(world: World, child: Entity, prize: Entity, activity: Activity) -> dict:
    sim = world.copy()
    sim_child = sim.get(child.id)
    sim_prize = sim.get(prize.id)
    _mutate_gibberish(sim, sim_child, sim_prize, activity)
    return {"risk": sim_prize.meters.get("risk", 0.0) >= THRESHOLD}


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, parent_name: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type="girl" if hero_name in {"Posey", "Lily", "Ava", "Maya"} else "boy"))
    parent = world.add(Entity(id=parent_name, kind="character", type="mother" if parent_name in {"Mom", "Mama"} else "father"))
    prize = world.add(Entity(id="prize", kind="thing", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=child.id, caretaker=parent.id))
    child.memes["joy"] = 1.0
    child.memes["love"] = 1.0
    prize.meters["clean"] = 1.0

    world.say(f"{hero_name} was a little {trait} child who loved the playroom.")
    world.say(f"{child.pronoun().capitalize()} had {prize_cfg.phrase}, and {prize_cfg.label} made the room feel extra special.")
    world.para()

    world.say(f"One afternoon, {hero_name} began {activity.gerund}.")
    _mutate_gibberish(world, child, prize, activity)
    world.say(f"The silly sounds made the playroom feel lively, but they also made {prize_cfg.label} at risk of being {prize_cfg.risk}.")
    world.say(f"{parent_name} noticed and gently said, \"Let's slow down so we don't hurt {prize_cfg.label}.\"")
    child.memes["upset"] = 1.0
    world.para()

    world.say(f"{hero_name} wanted to keep going, but the warning sat in {child.pronoun('possessive')} chest like a small cloud.")
    world.say(f"Then {hero_name} looked at {parent_name} and tried something kinder.")
    _mutate_kindness(world, child, parent, prize)
    world.say(f"{hero_name} said sorry, picked up the fallen pieces, and offered {parent_name} a careful hand.")
    _mutate_reconciliation(world, child, parent)

    compromise = select_compromise(activity, prize_cfg)
    if compromise is None:
        raise StoryError(explain_rejection(activity, prize_cfg))

    world.say(f"{parent_name} smiled back and suggested {compromise.prep}.")
    world.say(f"{compromise.finish}.")
    prize.meters["risk"] = 0.0
    prize.meters["clean"] = 1.0
    child.memes["upset"] = 0.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    parent.memes["relief"] = parent.memes.get("relief", 0.0) + 1
    world.say(f"In the end, {hero_name} was {activity.gerund}, {prize_cfg.label} was safe, and the room felt warm again.")

    world.facts.update(
        child=child,
        parent=parent,
        prize=prize,
        activity=activity,
        compromise=compromise,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    prize = f["prize"]
    act = f["activity"]
    return [
        f'Write a heartwarming story in the playroom that uses the word "{act.keyword}" and ends with kindness.',
        f"Tell a gentle tale about {child.id} and {prize.label} where silly {act.keyword} words cause a small problem and reconciliation fixes it.",
        f"Write a child-friendly story about a playroom, a {prize.label}, and a caring apology.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    comp = f["compromise"]
    return [
        QAItem(
            question=f"What was {child.id} doing when the playroom started to feel messy?",
            answer=f"{child.id} was {act.gerund}, and the silly sounds made the room lively but a little risky for {prize.label}.",
        ),
        QAItem(
            question=f"Why did {parent.id} speak up about {prize.label}?",
            answer=f"{parent.id} was worried that {prize.label} could get {prize_cfg(prize).risk} if the gibberish play kept going.",
        ),
        QAItem(
            question=f"What helped {child.id} and {parent.id} make up?",
            answer=f"Kindness helped them pause, apologize, and choose {comp.label} so they could feel close again.",
        ),
        QAItem(
            question=f"What was the ending image in the playroom?",
            answer=f"By the end, {child.id} was {act.gerund}, {prize.label} was safe, and the room felt warm and calm again.",
        ),
    ]


def prize_cfg(prize: Entity) -> Prize:
    return PRIZES[prize.id if prize.id in PRIZES else "posey"]


WORLD_KNOWLEDGE = {
    "posey": [
        QAItem(
            question="What is a posey?",
            answer="A posey can be a small flower or a little bouquet, something pretty and delicate that people like to hold carefully.",
        )
    ],
    "gibberish": [
        QAItem(
            question="What is gibberish?",
            answer="Gibberish is a string of sounds or words that does not make normal sense, often used for silly play.",
        )
    ],
    "kindness": [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        )
    ],
    "reconciliation": [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making up after a disagreement so people can feel friendly again.",
        )
    ],
    "playroom": [
        QAItem(
            question="What is a playroom for?",
            answer="A playroom is a room where children can play with toys, books, blocks, and pretend games.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"posey", "gibberish", "kindness", "reconciliation", "playroom"}
    out: list[QAItem] = []
    for tag in ["posey", "gibberish", "kindness", "reconciliation", "playroom"]:
        out.extend(WORLD_KNOWLEDGE[tag])
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
risk(A,P) :- activity(A), prize(P), A = gibberish, P = posey.
kind_fix(A,P) :- activity(A), prize(P), A = gibberish, P = posey.
valid(Place, A, P) :- setting(Place), afford(Place, A), risk(A,P), kind_fix(A,P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("afford", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
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


# ---------------------------------------------------------------------------
# Story sample generation
# ---------------------------------------------------------------------------

def valid_story_params(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_story_params(args)
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.parent, params.trait)
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
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    if world.trace_notes:
        lines.append("  notes: " + "; ".join(world.trace_notes))
    return "\n".join(lines)


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
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming playroom story world with posey, gibberish, kindness, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name")
    ap.add_argument("--parent")
    ap.add_argument("--trait")
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


CURATED = [
    StoryParams(place="playroom", activity="gibberish", prize="posey", name="Posey", parent="Mom", trait="gentle"),
    StoryParams(place="playroom", activity="gibberish", prize="book", name="Mina", parent="Dad", trait="thoughtful"),
    StoryParams(place="playroom", activity="gibberish", prize="tower", name="Theo", parent="Mama", trait="curious"),
]


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.activity} in {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
