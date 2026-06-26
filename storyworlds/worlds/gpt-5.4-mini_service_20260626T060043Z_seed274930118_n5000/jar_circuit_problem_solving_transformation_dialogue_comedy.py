#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/jar_circuit_problem_solving_transformation_dialogue_comedy.py
====================================================================================================

A small comedy storyworld about a jar, a circuit, and a problem-solving fix
that changes what the child can do. The story is built from a simulated world
with physical state (meters) and emotional state (memes), and the tale is
narrated from that state rather than from a frozen template.

Seed premise:
- A child wants to make a little circuit work.
- A glass jar, used as a tidy cover, accidentally causes trouble.
- The child and a helper talk, test ideas, and transform the setup into
  something better.
- The ending proves the change with a working circuit and a funny image.

The comedy comes from the jar being overconfident, the circuit being stubborn,
and the fix requiring a playful transformation of the setup.
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
# Core world entities
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
    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        for k in ["stuck", "spark", "glow", "mess", "heat", "work", "helped", "conflict", "joy", "curiosity", "pride", "surprise"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def short(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the kitchen table"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Circuit:
    id: str
    name: str
    needs: set[str]
    action: str
    reveal: str
    problem: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Container:
    id: str
    label: str
    phrase: str
    clear: bool = True
    heavy: bool = False
    covers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Transform:
    id: str
    label: str
    action: str
    result: str
    reveal: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    circuit: str
    container: str
    transform: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace_notes: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen table", indoors=True, affords={"circuit"}),
    "garage": Setting(place="the garage workbench", indoors=True, affords={"circuit"}),
    "porch": Setting(place="the porch", indoors=False, affords={"circuit"}),
}

CIRCUITS = {
    "blink": Circuit(
        id="blink",
        name="little blinking circuit",
        needs={"battery", "wire", "bulb"},
        action="make the little blinking circuit work",
        reveal="blinked like a tiny robot eye",
        problem="would not blink",
        fix="needed the jar moved away so the air could reach the warm parts",
        tags={"circuit", "problem", "solve"},
    ),
    "hum": Circuit(
        id="hum",
        name="tiny humming circuit",
        needs={"battery", "wire", "motor"},
        action="make the tiny humming circuit hum",
        reveal="hummed like a sleepy bee",
        problem="kept stopping",
        fix="needed a lighter cover and a better setup",
        tags={"circuit", "problem", "solve"},
    ),
}

CONTAINERS = {
    "jar": Container(
        id="jar",
        label="jar",
        phrase="a big glass jar",
        clear=True,
        heavy=False,
        covers={"top"},
        tags={"jar"},
    ),
    "cup": Container(
        id="cup",
        label="cup",
        phrase="a clear cup",
        clear=True,
        heavy=False,
        covers={"top"},
        tags={"jar"},
    ),
    "bowl": Container(
        id="bowl",
        label="bowl",
        phrase="a shiny bowl",
        clear=False,
        heavy=False,
        covers={"top"},
        tags={"jar"},
    ),
}

TRANSFORMS = {
    "lift": Transform(
        id="lift",
        label="lifted the jar up on a small book",
        action="lift the jar onto a little book",
        result="made a little room under it",
        reveal="the circuit had room to breathe",
        tags={"transformation", "problem_solving"},
    ),
    "flip": Transform(
        id="flip",
        label="flipped the jar over onto a coaster",
        action="flip the jar onto a coaster",
        result="turned the cover into a neat stand",
        reveal="the circuit no longer felt squashed",
        tags={"transformation", "problem_solving"},
    ),
    "remove": Transform(
        id="remove",
        label="removed the jar completely",
        action="take the jar away",
        result="changed the whole setup",
        reveal="the circuit could work openly",
        tags={"transformation", "problem_solving"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tia", "Zoe", "Ella"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Theo", "Ben", "Leo"]
HELPERS = [("mother", "mother"), ("father", "father"), ("grandparent", "grandparent"), ("friend", "friend")]
TRAITS = ["curious", "cheerful", "silly", "patient", "brave"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, circuit: Circuit, container: Container, transform: Transform) -> bool:
    if "circuit" not in SETTINGS[place].affords:
        return False
    if container.label != "jar" and transform.id == "remove":
        return True
    if container.clear and transform.id in {"lift", "flip", "remove"}:
        return True
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in SETTINGS:
        for cid, circ in CIRCUITS.items():
            for kid, cont in CONTAINERS.items():
                for tid, tr in TRANSFORMS.items():
                    if valid_combo(place, circ, cont, tr):
                        out.append((place, cid, kid, tid))
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Place,Circuit,Container,Transform) :- affords(Place,circuit), circuit(Circuit), container(Container), transform(Transform).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CIRCUITS.items():
        lines.append(asp.fact("circuit", cid))
        for n in sorted(c.needs):
            lines.append(asp.fact("needs", cid, n))
    for kid, k in CONTAINERS.items():
        lines.append(asp.fact("container", kid))
        if k.clear:
            lines.append(asp.fact("clear", kid))
    for tid, t in TRANSFORMS.items():
        lines.append(asp.fact("transform", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
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
# Simulation
# ---------------------------------------------------------------------------
def cause_stuck(world: World, circuit: Entity, container: Entity) -> None:
    sig = ("stuck", circuit.id, container.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    circuit.meters["stuck"] += 1
    if container.label == "jar":
        circuit.memes["conflict"] += 1


def solve_problem(world: World, child: Entity, helper: Entity, circuit: Entity, container: Entity, transform: Transform) -> None:
    if transform.id == "lift":
        world.say(f'{helper.short} said, "Maybe the jar is being a little too bossy."')
        world.say(f"{child.short} nodded, laughed, and {transform.action}.")
    elif transform.id == "flip":
        world.say(f'"What if we turn the jar into a stand?" {helper.short} asked.')
        world.say(f"{child.short} grinned and {transform.action}.")
    else:
        world.say(f'"Let’s stop arguing with the jar," {helper.short} said.')
        world.say(f"{child.short} blinked, then {transform.action}.")
    circuit.meters["stuck"] = 0
    circuit.memes["conflict"] = 0
    circuit.meters["spark"] = 1
    circuit.meters["glow"] = 1
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    helper.memes["joy"] += 1
    helper.memes["surprise"] += 1
    world.facts["resolved"] = True


def tell(setting: Setting, circuit_cfg: Circuit, container_cfg: Container, transform_cfg: Transform,
         hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    circuit = world.add(Entity(id="Circuit", kind="thing", type="circuit", label="circuit", phrase=circuit_cfg.name))
    jar = world.add(Entity(id="Jar", kind="thing", type=container_cfg.label, label=container_cfg.label, phrase=container_cfg.phrase))

    world.say(f"{child.short} was a {random.choice(TRAITS)} little {hero_type} who loved tinkering with a circuit.")
    world.say(f"{child.short} had a {circuit_cfg.name}, and the oddest helper in the room was a {jar.label} on the table.")
    world.say(f"{child.short} kept saying, \"I can fix it!\" even when the {circuit.label} {circuit_cfg.problem}.")

    world.para()
    world.say(f"At {setting.place}, {child.short} tried to hide the circuit under the {jar.label}, but that made it grumble.")
    cause_stuck(world, circuit, jar)
    child.memes["curiosity"] += 1
    child.memes["conflict"] += 1
    world.say(f'The jar said nothing, which was rude for a jar, and the circuit {circuit_cfg.reveal} only if nobody squashed it.')

    world.para()
    solve_problem(world, child, helper, circuit, jar, transform_cfg)
    world.say(f'Then the {circuit.label} {circuit_cfg.reveal}, and the jar finally became part of the joke instead of the problem.')
    world.say(f"{child.short} and {helper.short} laughed because the fix worked, and the jar looked proud of its new job.")

    world.facts.update(
        child=child,
        helper=helper,
        circuit=circuit,
        jar=jar,
        circuit_cfg=circuit_cfg,
        container_cfg=container_cfg,
        transform_cfg=transform_cfg,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny short story for a child about a "{f["circuit_cfg"].name}" and a jar.',
        f"Tell a problem-solving story where {f['child'].short} and {f['helper'].short} fix a circuit using a jar-shaped transformation.",
        f"Write a comedy story with dialogue, a small circuit, and a surprising jar-based solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    circuit_cfg: Circuit = f["circuit_cfg"]
    jar: Entity = f["jar"]
    return [
        QAItem(
            question=f"What did {child.short} want to do with the circuit at first?",
            answer=f"{child.short} wanted to {circuit_cfg.action}.",
        ),
        QAItem(
            question=f"Why did the circuit cause trouble before the fix?",
            answer=f"It {circuit_cfg.problem}, because the jar made the setup too cramped and bossy.",
        ),
        QAItem(
            question=f"What did {child.short} and {helper.short} do to solve the problem?",
            answer=f"They changed the setup by moving the jar so the circuit had room to work.",
        ),
        QAItem(
            question=f"What funny thing changed at the end of the story?",
            answer=f"The jar stopped being a nuisance and became part of the solution while the circuit worked again.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "jar": [
        QAItem(
            question="What is a jar used for?",
            answer="A jar is a container with a lid or open top that can hold small things like food, buttons, or little treasures.",
        )
    ],
    "circuit": [
        QAItem(
            question="What is a circuit?",
            answer="A circuit is a path that lets electricity move so a light, motor, or other gadget can work.",
        )
    ],
    "problem": [
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to figure out a good way to fix something that is not working right.",
        )
    ],
    "transformation": [
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change that makes something become different, like a setup turning into a better one.",
        )
    ],
    "dialogue": [
        QAItem(
            question="What is dialogue in a story?",
            answer="Dialogue is when characters talk to each other using their own words.",
        )
    ],
    "comedy": [
        QAItem(
            question="What makes a story funny?",
            answer="A story can be funny when characters are a little silly, say surprising things, or get into harmless trouble.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["jar"])
    out.extend(WORLD_KNOWLEDGE["circuit"])
    out.extend(WORLD_KNOWLEDGE["problem"])
    out.extend(WORLD_KNOWLEDGE["transformation"])
    out.extend(WORLD_KNOWLEDGE["dialogue"])
    out.extend(WORLD_KNOWLEDGE["comedy"])
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: jar, circuit, problem solving, transformation, dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--circuit", choices=CIRCUITS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "grandparent", "friend"])
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
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.circuit is None or c[1] == args.circuit)
              and (args.container is None or c[2] == args.container)
              and (args.transform is None or c[3] == args.transform)]
    if not combos:
        raise StoryError("No valid story matches the chosen options.")

    place, circuit, container, transform = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([h[0] for h in HELPERS])
    return StoryParams(place=place, circuit=circuit, container=container, transform=transform, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CIRCUITS[params.circuit],
        CONTAINERS[params.container],
        TRANSFORMS[params.transform],
        params.name,
        params.gender,
        params.helper,
    )
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="kitchen", circuit="blink", container="jar", transform="lift", name="Mina", gender="girl", helper="mother"),
    StoryParams(place="garage", circuit="hum", container="jar", transform="flip", name="Owen", gender="boy", helper="father"),
    StoryParams(place="porch", circuit="blink", container="cup", transform="remove", name="Lila", gender="girl", helper="friend"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
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
            header = f"### {p.name}: {p.circuit} / {p.container} / {p.transform}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
