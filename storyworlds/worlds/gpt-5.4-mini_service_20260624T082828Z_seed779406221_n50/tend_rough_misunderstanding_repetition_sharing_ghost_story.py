#!/usr/bin/env python3
"""
A small story world for a gentle ghost story with misunderstanding, repetition,
and sharing.

The premise: a child finds a shy ghost near a rough old blanket. At first, the
child misunderstands the ghost's spooky habits, but repeated visits reveal the
ghost is only trying to tend the blanket and keep it from fraying. In the end,
they share the blanket and the room feels warmer.

The simulated world uses:
- meters for physical conditions like roughness, fray, warmth, and dust
- memes for emotional states like worry, curiosity, trust, and calm

The story is intentionally small, causal, and child-facing.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "boy", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the attic"
    afford_tend: bool = True


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        return World(
            setting=self.setting,
            entities=copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=dict(self.facts),
            fired=set(self.fired),
        )


# ---------------------------------------------------------------------------
# Parameters / registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    ghost_name: str
    seed: Optional[int] = None


SETTINGS = {
    "attic": Setting(place="the attic", afford_tend=True),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Ava", "Rose"]
BOY_NAMES = ["Ben", "Leo", "Finn", "Max", "Theo", "Eli"]
GHOST_NAMES = ["Pip", "Moss", "Wisp", "Sable", "Hush"]

# Physical and emotional registries for the ghost story domain.
ENTITY_REGISTRY = {
    "child": {"kind": "character", "type": "child"},
    "ghost": {"kind": "character", "type": "ghost"},
    "blanket": {"kind": "thing", "type": "blanket", "label": "old blanket", "phrase": "a rough old blanket"},
    "lamp": {"kind": "thing", "type": "lamp", "label": "small lamp", "phrase": "a small lamp"},
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A blanket is at risk when it is rough and fraying.
at_risk(B) :- rough(B), fraying(B).

% Repeating a gentle action can reduce fear and increase trust.
trust_builds(C, G) :- repeat_visit(C, G).

% Sharing the blanket resolves the misunderstanding when trust is high.
resolved(C, G, B) :- trust_builds(C, G), shares(C, G, B), at_risk(B).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    lines.append(asp.fact("rough", "blanket"))
    lines.append(asp.fact("fraying", "blanket"))
    lines.append(asp.fact("repeat_visit", "child", "ghost"))
    lines.append(asp.fact("shares", "child", "ghost", "blanket"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show at_risk/1. #show resolved/3."))
    atoms = {(s.name, tuple(a.number if a.type.name == "Number" else a.string if a.type.name == "String" else a.name for a in s.arguments)) for s in model}
    expected = {("at_risk", ("blanket",)), ("resolved", ("child", "ghost", "blanket"))}
    if atoms == expected:
        print("OK: ASP twin matches the Python reasoner.")
        return 0
    print("MISMATCH: ASP twin does not match the Python reasoner.")
    print("  got:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Story world logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.name,
        meters={"warmth": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "trust": 0.0, "calm": 0.0, "misunderstanding": 0.0},
    ))
    ghost = world.add(Entity(
        id=params.ghost_name,
        kind="character",
        type="ghost",
        label=params.ghost_name,
        meters={"glow": 1.0},
        memes={"shy": 1.0, "care": 1.0, "worry": 0.0, "calm": 0.0},
    ))
    blanket = world.add(Entity(
        id="blanket",
        kind="thing",
        type="blanket",
        label="blanket",
        phrase="a rough old blanket",
        owner=params.name,
        caretaker=params.name,
        meters={"rough": 1.0, "fraying": 1.0, "warmth": 0.0, "dust": 1.0},
        memes={"familiar": 1.0},
    ))
    world.add(Entity(
        id="lamp",
        kind="thing",
        type="lamp",
        label="lamp",
        phrase="a small lamp",
        meters={"warmth": 1.0},
    ))

    world.facts.update(child=child, ghost=ghost, blanket=blanket, setting=world.setting)
    return world


def predict_misunderstanding(world: World) -> bool:
    sim = world.copy()
    child = sim.get(sim.facts["child"].id)
    ghost = sim.get(sim.facts["ghost"].id)
    blanket = sim.get("blanket")
    # Shy ghost plus rough, fraying blanket causes a spooky misunderstanding.
    child.memes["worry"] += 1.0
    ghost.memes["shy"] += 0.5
    if blanket.meters["rough"] >= THRESHOLD and blanket.meters["fraying"] >= THRESHOLD:
        child.memes["misunderstanding"] += 1.0
    return child.memes["misunderstanding"] >= THRESHOLD


def tend_blanket(world: World, ghost: Entity, blanket: Entity) -> None:
    if not world.setting.afford_tend:
        raise StoryError("This place does not support tending the blanket.")
    blanket.meters["fraying"] = max(0.0, blanket.meters["fraying"] - 0.5)
    blanket.meters["dust"] = max(0.0, blanket.meters["dust"] - 0.5)
    ghost.memes["care"] += 1.0
    world.say(f"{ghost.label} hovered close and tried to tend the rough blanket.")


def repeated_knocks(world: World, child: Entity, ghost: Entity) -> None:
    # Repetition is a narrative instrument: the child keeps hearing the same soft knock.
    for _ in range(3):
        world.say(f"{child.label} heard a soft knock from the attic door again.")
        child.memes["worry"] += 0.2
    child.memes["misunderstanding"] += 1.0


def share_blanket(world: World, child: Entity, ghost: Entity, blanket: Entity) -> None:
    child.memes["trust"] += 1.0
    child.memes["worry"] = 0.0
    child.memes["calm"] += 1.0
    ghost.memes["calm"] += 1.0
    blanket.meters["warmth"] += 1.0
    blanket.meters["rough"] = max(0.0, blanket.meters["rough"] - 0.5)
    world.say(f"{child.label} shared the blanket with {ghost.label}, and the room felt warmer.")


def tell_story(world: World) -> None:
    child = world.facts["child"]
    ghost = world.facts["ghost"]
    blanket = world.facts["blanket"]

    world.say(f"One evening, {child.label} climbed into {world.setting.place} and found {ghost.label}.")
    world.say(f"Near the wall was {blanket.phrase}, and it looked rough and tired.")

    if predict_misunderstanding(world):
        world.say(f"{child.label} thought {ghost.label} was trying to scare {child.pronoun('object')}.")
    else:
        world.say(f"{child.label} did not feel scared at first, but the attic was still very quiet.")

    world.para()
    repeated_knocks(world, child, ghost)
    world.say(f"Each time the knocking came back, {child.label} felt more unsure about what {ghost.label} wanted.")
    world.say(f"But {ghost.label} was only trying to tend the blanket so it would not fray any more.")

    world.para()
    tend_blanket(world, ghost, blanket)
    world.say(f"{child.label} listened a little longer and noticed the ghost's hands were careful, not spooky.")
    share_blanket(world, child, ghost, blanket)
    world.say(f"In the end, {child.label} and {ghost.label} sat together under the blanket, and the attic stayed quiet and kind.")

    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, ghost, blanket = f["child"], f["ghost"], f["blanket"]
    return [
        f'Write a short ghost story for a young child that includes the words "tend" and "rough".',
        f"Tell a gentle story where {child.label} misunderstands {ghost.label}, then learns the ghost is trying to tend a rough blanket.",
        f"Write a child-friendly story with repetition, sharing, and a happy ending in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, ghost, blanket = f["child"], f["ghost"], f["blanket"]
    return [
        QAItem(
            question=f"Who found the rough old blanket in the attic?",
            answer=f"{child.label} found the rough old blanket in the attic and noticed {ghost.label} nearby.",
        ),
        QAItem(
            question=f"Why did {child.label} first misunderstand {ghost.label}?",
            answer=f"{child.label} thought {ghost.label} was trying to scare {child.label}, because the attic was quiet and the repeated knocking felt spooky.",
        ),
        QAItem(
            question=f"What was {ghost.label} really doing?",
            answer=f"{ghost.label} was only trying to tend the rough blanket so it would not fray any more.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{child.label} shared the blanket with {ghost.label}, and the room felt warmer and calmer at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to tend something?",
            answer="To tend something means to care for it, watch over it, or help it stay in good shape.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing about what another person means.",
        ),
        QAItem(
            question="Why can repeating something feel important in a story?",
            answer="Repetition can make a story feel steady and can help show that a feeling or action keeps happening.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something with you.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="attic", name="Mia", gender="girl", ghost_name="Wisp"),
    StoryParams(place="attic", name="Ben", gender="boy", ghost_name="Pip"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world with misunderstanding, repetition, and sharing.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--ghost-name")
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
    place = args.place or "attic"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(place=place, name=name, gender=gender, ghost_name=ghost_name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
    for eid, ent in world.entities.items():
        meters = {k: round(v, 3) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 3) for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {eid:8} ({ent.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        print(asp_program("#show at_risk/1. #show resolved/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
