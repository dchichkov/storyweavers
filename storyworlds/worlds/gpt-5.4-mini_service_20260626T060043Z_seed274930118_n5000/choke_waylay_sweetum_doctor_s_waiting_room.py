#!/usr/bin/env python3
"""
Story world: doctor's waiting room nursery-rhyme suspense tale.

A little child waits in a doctor's waiting room, reaches for a sweet treat,
and is gently waylaid because it could cause a choke risk. The parent, nurse,
and doctor use teamwork and caution to keep the child safe and calm.

The story is intentionally small, classical, and constraint-driven:
- Suspense: the child wants the treat now, but there is a real danger.
- Teamwork: adults and child cooperate.
- Cautionary: a close call becomes a careful lesson.
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
        feminine = {"girl", "mother", "mom", "woman", "nurse"}
        masculine = {"boy", "father", "dad", "man", "doctor"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str = "the doctor's waiting room"
    can_settle: set[str] = field(default_factory=set)
    has_books: bool = True
    has_chairs: bool = True


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    risky: bool = False
    safe_alternative: str = ""
    texture: str = "soft"


@dataclass
class StoryParams:
    snack: str
    name: str
    gender: str
    parent: str
    helper: str
    seed: Optional[int] = None


SNACKS = {
    "sweetum": Snack(
        id="sweetum",
        label="Sweetum",
        phrase="a sticky Sweetum candy",
        risky=True,
        safe_alternative="a soft banana slice",
        texture="sticky",
    ),
    "cookie": Snack(
        id="cookie",
        label="cookie",
        phrase="a crumbly cookie",
        risky=True,
        safe_alternative="a soft rice cake",
        texture="crumbly",
    ),
    "berry": Snack(
        id="berry",
        label="berry cup",
        phrase="a cup of soft berries",
        risky=False,
        safe_alternative="a cup of soft berries",
        texture="soft",
    ),
}

NAMES_GIRL = ["Mia", "Lily", "Nora", "Ava", "Rose", "Ella"]
NAMES_BOY = ["Leo", "Ben", "Theo", "Max", "Finn", "Sam"]
HELPERS = ["nurse", "doctor"]
PARENTS = ["mother", "father"]

ROOM = Room(can_settle={"books", "breathing", "water"})

THRESHOLD = 1.0


class World:
    def __init__(self, room: Room):
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy

        w = World(self.room)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _mem(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _add_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _add_mem(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _set_mem(ent: Entity, key: str, val: float) -> None:
    ent.memes[key] = val


def introduce(world: World, child: Entity, parent: Entity, helper: Entity, snack: Snack) -> None:
    world.say(
        f"Down in the waiting room bright, {child.id} sat with a sigh, "
        f"and {child.pronoun('possessive')} {parent.type} sat close by."
    )
    world.say(
        f"{helper.type.capitalize()} {helper.id} smiled, so kind and so neat, "
        f"while {child.id} held {child.pronoun('possessive')} {snack.label} treat."
    )


def suspense_build(world: World, child: Entity, snack: Snack) -> None:
    _add_mem(child, "curiosity", 1)
    _add_mem(child, "desire", 1)
    world.say(
        f"{child.id} eyed the {snack.label}, all shiny and sweet; "
        f"the room felt still, with a hush on the seat."
    )


def foresee_risk(world: World, child: Entity, snack: Snack) -> bool:
    if not snack.risky:
        return False
    sim = world.copy()
    child2 = sim.get(child.id)
    _add_meter(child2, "throat_risk", 1.0)
    return True


def warn_and_waylay(world: World, parent: Entity, helper: Entity, child: Entity, snack: Snack) -> None:
    _add_mem(child, "frustration", 1)
    _add_mem(child, "fear", 1)
    world.say(
        f'"Not yet, sweetum," said {parent.type} {parent.id}, with a soft and steady plea. '
        f'"That crumb or chew could choke you, you see."'
    )
    world.say(
        f"Then {helper.type} {helper.id} waylaid the nibble with care, "
        f"and guided {child.id} to sit still on the chair."
    )


def teamwork_fix(world: World, parent: Entity, helper: Entity, child: Entity, snack: Snack) -> None:
    safe = snack.safe_alternative
    _add_meter(child, "water", 1)
    _add_mem(child, "calm", 1)
    _set_mem(child, "fear", 0)
    _set_mem(child, "frustration", 0)
    _add_mem(parent, "relief", 1)
    _add_mem(helper, "helpfulness", 1)
    world.say(
        f"Together they made a small teamwork song: a sip of water, a slower breath, "
        f"and {safe} in place of the risky treat."
    )
    world.say(
        f"By and by, {child.id} was smiling again, and the waiting room seemed warm and bright, "
        f"with everyone keeping the little one right."
    )


def ending_image(world: World, child: Entity, parent: Entity, helper: Entity, snack: Snack) -> None:
    world.say(
        f"So {child.id} kept {snack.label} near but did not take a bite; "
        f"{child.id} learned that caution can keep a small day light."
    )


def tell_world(params: StoryParams) -> World:
    world = World(ROOM)
    snack = SNACKS[params.snack]
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=params.helper))

    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["helper"] = helper
    world.facts["snack"] = snack

    child.meters["waiting"] = 1.0
    child.memes["hope"] = 1.0

    introduce(world, child, parent, helper, snack)
    world.para()
    suspense_build(world, child, snack)
    if foresee_risk(world, child, snack):
        world.para()
        warn_and_waylay(world, parent, helper, child, snack)
        world.para()
        teamwork_fix(world, parent, helper, child, snack)
    else:
        world.para()
        world.say(
            f"The little one munched safely, and the room stayed merry and calm."
        )
    world.para()
    ending_image(world, child, parent, helper, snack)
    return world


# ---------------------------
# Registries and QA
# ---------------------------
KNOWLEDGE = {
    "waiting_room": [
        (
            "What is a doctor's waiting room?",
            "A doctor's waiting room is a place where people sit and wait before they see the doctor.",
        )
    ],
    "caution": [
        (
            "Why should children be careful with small hard candy?",
            "Children should be careful because small hard candy can go down the wrong way and choke them.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other and do something together.",
        )
    ],
    "water": [
        (
            "Why can a sip of water help after a dry cough?",
            "A sip of water can help because it can moisten a dry mouth and make swallowing feel easier.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    snack = f["snack"]
    return [
        f"Write a short nursery-rhyme story set in a doctor's waiting room about {child.id} and {snack.label}.",
        f"Tell a gentle story where a child is waylaid from a risky sweetum and adults use teamwork.",
        f"Write a cautionary story in rhyme with suspense, teamwork, and a safe ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    helper = f["helper"]
    snack = f["snack"]
    return [
        QAItem(
            question=f"Where was {child.id} waiting?",
            answer="They were waiting in the doctor's waiting room.",
        ),
        QAItem(
            question=f"Why was {child.id} waylaid from {snack.label}?",
            answer=f"{child.id} was waylaid because {snack.label} could choke them if they tried to eat it too fast.",
        ),
        QAItem(
            question=f"Who helped keep {child.id} safe?",
            answer=f"{parent.id} and {helper.id} helped together, showing teamwork and careful watching.",
        ),
        QAItem(
            question=f"What did {child.id} choose instead of the risky treat?",
            answer=f"{child.id} took a sip of water and a softer snack, which was safer than the risky treat.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"waiting_room", "caution", "teamwork", "water"}
    out: list[QAItem] = []
    for tag in ["waiting_room", "caution", "teamwork", "water"]:
        for q, a in KNOWLEDGE[tag]:
            out.append(QAItem(question=q, answer=a))
    return out


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------
# ASP twin
# ---------------------------
ASP_RULES = r"""
risk(S) :- snack(S), risky(S).
waylay_needed(C, S) :- child(C), holds(C, S), risk(S).
resolved(C, S) :- waylay_needed(C, S), teamwork(parent, helper, C), safer_swap(S, Safe), safe(Safe).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if s.risky:
            lines.append(asp.fact("risky", sid))
        if s.safe_alternative:
            lines.append(asp.fact("safer_swap", sid, s.safe_alternative))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("teamwork", "parent", "helper", "child"))
    lines.append(asp.fact("safe", "water"))
    lines.append(asp.fact("safe", "soft_snack"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show resolved/2.\n#show waylay_needed/2."))
    resolved = set(asp.atoms(model, "resolved"))
    waylays = set(asp.atoms(model, "waylay_needed"))
    py_waylay = {("child", sid) for sid, s in SNACKS.items() if s.risky}
    py_resolved = {("child", sid) for sid, s in SNACKS.items() if s.risky}
    if resolved != py_resolved or waylays != py_waylay:
        print("MISMATCH between ASP and Python gate.")
        print("ASP resolved:", sorted(resolved))
        print("PY resolved:", sorted(py_resolved))
        print("ASP waylay_needed:", sorted(waylays))
        print("PY waylay_needed:", sorted(py_waylay))
        return 1
    print("OK: ASP and Python parity verified.")
    return 0


# ---------------------------
# CLI
# ---------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world in a doctor's waiting room.")
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--helper", choices=HELPERS)
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
    snack = args.snack or rng.choice(list(SNACKS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(PARENTS)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(snack=snack, name=name, gender=gender, parent=parent, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/2.\n#show waylay_needed/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for snack_id in SNACKS:
            params = StoryParams(
                snack=snack_id,
                name="Mia",
                gender="girl",
                parent="mother",
                helper="nurse",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
