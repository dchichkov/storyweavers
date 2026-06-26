#!/usr/bin/env python3
"""
storyworlds/worlds/federation_reconciliation_fable.py
====================================================

A small fable-style storyworld about a federation that falls into quarrel and
finds reconciliation through a wise shared act.

Premise:
- A federation of small animal towns shares a river bridge, a bell, and a seed
  store.
- One town feels ignored, another feels rushed, and their shared work begins to
  fray.
- A mediator helps them name the hurt, return what was borrowed, and make a new
  pact.

The world is state-driven:
- Each faction has meters (missing goods, stress, trust, repair).
- Each faction has memes (pride, hurt, patience, relief).
- Reconciliation lowers hurt and raises trust, but only when the right repair
  step is taken.

This script follows the Storyweavers contract: it provides params, registries,
CLI, generation, QA, and an ASP twin for the reasonableness gate.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"missing": 0.0, "repair": 0.0, "stress": 0.0, "trust": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "hurt": 0.0, "patience": 0.0, "relief": 0.0}

    def pronoun(self) -> str:
        return "it"

    def poss(self) -> str:
        return "its"


@dataclass
class Federation:
    name: str
    place: str
    members: list[str] = field(default_factory=list)
    shared_goods: list[str] = field(default_factory=list)
    pact: str = "old pact"


@dataclass
class Town:
    id: str
    label: str
    patience: float = 1.0
    trust: float = 1.0
    hurt: float = 0.0
    pride: float = 0.0
    missing: float = 0.0


@dataclass
class Bridge:
    id: str
    label: str
    uses: list[str] = field(default_factory=list)
    fragile: bool = False


@dataclass
class StoryParams:
    federation: str
    place: str
    dispute: str
    mediator: str
    seed: Optional[int] = None


class World:
    def __init__(self, federation: Federation) -> None:
        self.federation = federation
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


FEDS = {
    "river": Federation(
        name="the River Federation",
        place="the river valley",
        members=["Northbank", "Southbank"],
        shared_goods=["bridge bell", "seed store"],
        pact="the old river pact",
    ),
    "orchard": Federation(
        name="the Orchard Federation",
        place="the orchard",
        members=["Pear Hollow", "Apple Rise"],
        shared_goods=["ladder", "basket cart"],
        pact="the orchard pact",
    ),
}

TOWNS = {
    "northbank": Town(id="Northbank", label="Northbank", patience=0.8, trust=0.9, pride=1.1),
    "southbank": Town(id="Southbank", label="Southbank", patience=0.8, trust=0.9, pride=1.0),
    "pear": Town(id="Pear Hollow", label="Pear Hollow", patience=0.9, trust=0.85, pride=1.0),
    "apple": Town(id="Apple Rise", label="Apple Rise", patience=0.9, trust=0.85, pride=1.0),
}

DISPUTES = {
    "bell": {
        "item": "bridge bell",
        "hurt_item": "the bridge bell",
        "cause": "the bell was rung without asking",
        "repair": "return the bell and ring it together",
        "act": "ring",
    },
    "seed": {
        "item": "seed store",
        "hurt_item": "the seed store keys",
        "cause": "some seeds were taken early",
        "repair": "bring back the borrowed seeds and count them fairly",
        "act": "carry",
    },
    "road": {
        "item": "bridge road",
        "hurt_item": "the bridge planks",
        "cause": "heavy carts wore the bridge down",
        "repair": "fix the planks together",
        "act": "cross",
    },
}

MEDIATORS = {
    "owl": "an old owl",
    "hare": "a patient hare",
    "beaver": "a careful beaver",
}

TRAIT_WORDS = ["wise", "calm", "patient", "gentle", "steady"]


def reasonableness_gate(fed: Federation, dispute: str) -> bool:
    return fed.name and dispute in DISPUTES


def valid_choices() -> list[tuple[str, str, str]]:
    return [(fid, "fable", d) for fid in FEDS for d in DISPUTES]


def explain_rejection(dispute: str) -> str:
    return f"(No story: the dispute '{dispute}' does not fit this federation's shared world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small fable about a federation and reconciliation."
    )
    ap.add_argument("--federation", choices=list(FEDS))
    ap.add_argument("--place", choices=["valley", "orchard"])
    ap.add_argument("--dispute", choices=list(DISPUTES))
    ap.add_argument("--mediator", choices=list(MEDIATORS))
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
    fid = args.federation or rng.choice(list(FEDS))
    dispute = args.dispute or rng.choice(list(DISPUTES))
    if not reasonableness_gate(FEDS[fid], dispute):
        raise StoryError(explain_rejection(dispute))
    place = args.place or ("valley" if fid == "river" else "orchard")
    mediator = args.mediator or rng.choice(list(MEDIATORS))
    return StoryParams(federation=fid, place=place, dispute=dispute, mediator=mediator)


def make_world(params: StoryParams) -> World:
    fed = FEDS[params.federation]
    world = World(fed)
    dis = DISPUTES[params.dispute]
    mediator = world.add(Entity(id=params.mediator, kind="character", type=params.mediator, label=MEDIATORS[params.mediator]))
    t1 = world.add(Entity(id="TownA", kind="character", type="town", label=fed.members[0]))
    t2 = world.add(Entity(id="TownB", kind="character", type="town", label=fed.members[1]))
    bridge = world.add(Entity(id="Bridge", type="bridge", label="the bridge", phrase="the shared bridge"))
    item = world.add(Entity(id="SharedItem", type="thing", label=dis["item"], phrase=dis["hurt_item"]))
    world.facts.update(federation=fed, params=params, mediator=mediator, town_a=t1, town_b=t2, bridge=bridge, item=item, dispute=dis)
    return world


def narrate_setup(world: World) -> None:
    fed: Federation = world.facts["federation"]
    t1, t2 = world.facts["town_a"], world.facts["town_b"]
    item = world.facts["item"]
    world.say(
        f"In {fed.place}, there was a small federation called {fed.name}. "
        f"{t1.label} and {t2.label} shared the road, the work, and the little things that held the towns together."
    )
    world.say(
        f"They also shared {item.label}, and that made their days smoother when everyone remembered the pact."
    )


def narrate_conflict(world: World) -> None:
    dis = world.facts["dispute"]
    t1, t2 = world.facts["town_a"], world.facts["town_b"]
    item = world.facts["item"]
    t1.memes["hurt"] += 1
    t2.memes["pride"] += 1
    t1.meters["stress"] += 1
    t2.meters["stress"] += 1
    world.say(
        f"One day, {dis['cause']}, and the good feeling between the towns grew thin."
    )
    world.say(
        f"{t1.label} felt hurt, while {t2.label} grew proud and said the matter was small."
    )


def narrate_mediator(world: World) -> None:
    med = world.facts["mediator"]
    t1, t2 = world.facts["town_a"], world.facts["town_b"]
    dis = world.facts["dispute"]
    world.say(
        f"Then {med.label} came along and listened to both sides without hurrying them."
    )
    world.say(
        f'"If a federation is to stay strong," {med.label} said, "it must mend what is cracked, not only guard what is easy."'
    )
    world.say(
        f"{med.label} asked each town to name the hurt before touching the shared thing again."
    )


def reconcile(world: World) -> None:
    dis = world.facts["dispute"]
    t1, t2 = world.facts["town_a"], world.facts["town_b"]
    item = world.facts["item"]
    med = world.facts["mediator"]
    if dis["act"] == "ring":
        item.meters["repair"] += 1
    elif dis["act"] == "carry":
        item.meters["missing"] += 1
    else:
        item.meters["repair"] += 1
    t1.memes["patience"] += 1
    t2.memes["patience"] += 1
    t1.memes["hurt"] = max(0.0, t1.memes["hurt"] - 1)
    t2.memes["pride"] = max(0.0, t2.memes["pride"] - 1)
    t1.meters["trust"] += 1
    t2.meters["trust"] += 1
    world.say(
        f"So they chose to {dis['repair']}, and the work was done side by side."
    )
    world.say(
        f"By dusk, {t1.label} and {t2.label} had a fairer pact, and the federation felt whole again."
    )


def tell(params: StoryParams) -> World:
    world = make_world(params)
    narrate_setup(world)
    world.para()
    narrate_conflict(world)
    world.para()
    narrate_mediator(world)
    reconcile(world)
    return world


def generation_prompts(world: World) -> list[str]:
    fed: Federation = world.facts["federation"]
    dis = world.facts["dispute"]
    med = world.facts["mediator"]
    return [
        f"Write a fable about {fed.name} where {dis['cause']} and {med.label} helps the towns reconcile.",
        f"Tell a short child-friendly story about a federation learning to share again after a quarrel over {dis['item']}.",
        f"Write a moral tale where a calm mediator guides two towns in a federation back to trust.",
    ]


def story_qa(world: World) -> list[QAItem]:
    fed: Federation = world.facts["federation"]
    t1, t2 = world.facts["town_a"], world.facts["town_b"]
    med = world.facts["mediator"]
    dis = world.facts["dispute"]
    return [
        QAItem(
            question=f"What was the story about in {fed.name}?",
            answer=f"It was about {t1.label} and {t2.label} learning how to live peacefully inside {fed.name}.",
        ),
        QAItem(
            question=f"Why did the towns feel upset at first?",
            answer=f"They felt upset because {dis['cause']}, and that made the shared work feel unfair.",
        ),
        QAItem(
            question=f"Who helped the towns find reconciliation?",
            answer=f"{med.label} helped by listening, speaking calmly, and guiding them toward a fair repair.",
        ),
        QAItem(
            question=f"What changed by the end of the tale?",
            answer=f"The towns stopped quarreling, made a fairer pact, and the federation felt whole again.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "federation": [
        (
            "What is a federation?",
            "A federation is a group of towns or places that agree to work together and share rules for common things.",
        )
    ],
    "reconciliation": [
        (
            "What is reconciliation?",
            "Reconciliation is when people or groups make peace after a disagreement and begin trusting each other again.",
        )
    ],
    "fable": [
        (
            "What is a fable?",
            "A fable is a short story that often uses animals or simple characters to teach a lesson.",
        )
    ],
    "bridge": [
        (
            "Why are bridges useful?",
            "Bridges help people cross water or gaps so they can reach places on the other side more easily.",
        )
    ],
    "pact": [
        (
            "What is a pact?",
            "A pact is an agreement that says what each side will do.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["fable", "federation", "reconciliation", "pact", "bridge"]:
        out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[key])
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} ({e.type}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_federation(F) :- federation(F).
valid_dispute(D) :- dispute(D).
reconciliation_possible(F, D) :- valid_federation(F), valid_dispute(D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for fid in FEDS:
        lines.append(asp.fact("federation", fid))
    for d in DISPUTES:
        lines.append(asp.fact("dispute", d))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reconciliation_possible/2."))
    return sorted(set(asp.atoms(model, "reconciliation_possible")))


def asp_verify() -> int:
    py = {(fid, d) for fid in FEDS for d in DISPUTES}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python valid_combos():")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(federation="river", place="valley", dispute="bell", mediator="owl"),
    StoryParams(federation="river", place="valley", dispute="seed", mediator="beaver"),
    StoryParams(federation="orchard", place="orchard", dispute="road", mediator="hare"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reconciliation_possible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible federation/dispute combos:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.federation} / {p.dispute} / {p.mediator}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
