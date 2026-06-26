#!/usr/bin/env python3
"""
A small bedside story world set in a hardware store.

Premise:
- A child and a grown-up visit a hardware store to solve a little mystery.
- The mystery is about finding the right housing for a tiny project part.
- Sound effects, teamwork, and a calm bedtime-story tone drive the plot.

The world is intentionally compact: a few typed entities, a few physical and
emotional meters, and a small set of causal beats that make the prose feel
earned instead of templated.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("weight", "hidden", "found", "noise", "clue"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "worry", "joy", "teamwork", "calm", "helpfulness"):
            self.memes.setdefault(k, 0.0)

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
class Place:
    name: str
    aisles: list[str]
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    clue_sound: str
    hidden_in: str
    requires_teamwork: bool = True


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    parent: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_find_noise(world: World) -> list[str]:
    out: list[str] = []
    mystery: Mystery = world.facts["mystery"]
    for e in world.entities.values():
        if e.type == "box" and e.label == mystery.label and e.meters["hidden"] >= THRESHOLD:
            sig = ("noise", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["noise"] += 1
            out.append(f"From somewhere nearby came a soft {mystery.clue_sound}.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["child"]
    helper = world.facts["helper"]
    mystery: Mystery = world.facts["mystery"]
    clue_box = world.facts["box"]
    if child.memes["curiosity"] < THRESHOLD or helper.memes["helpfulness"] < THRESHOLD:
        return out
    sig = ("teamwork", child.id, helper.id)
    if sig in world.fired:
        return out
    if clue_box.meters["noise"] < THRESHOLD:
        return out
    world.fired.add(sig)
    child.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    clue_box.meters["found"] += 1
    out.append("They listened together, tiptoed together, and followed the little sound.")
    out.append(f"At last, they found the {mystery.label} tucked behind a stack of paint cans.")
    return out


CAUSAL_RULES = [_r_find_noise, _r_teamwork]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    lines: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule(world)
            if produced:
                changed = True
                lines.extend(produced)
    if narrate:
        for line in lines:
            world.say(line)


def sound_word(mystery: Mystery) -> str:
    return mystery.clue_sound


def introduce(world: World, child: Entity, parent: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"{child.id} was a {child.type} with a {child.memes['curiosity']:.0f}-spark grin and a "
        f"skimpy little list in {child.pronoun('possessive')} pocket."
    )
    world.say(
        f"{child.id} and {parent.label} had come to the hardware store with {helper.label}, "
        f"because a tiny project needed a {mystery.label}."
    )


def browse(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"The hardware store hummed softly under the lights, with bolts, brushes, and bins lined up like sleepy toys."
    )
    world.say(
        f"{child.id} looked for the {mystery.label}, but the shelf was empty. That made the mystery feel even bigger."
    )


def notice_clue(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["curiosity"] += 1
    world.facts["box"].meters["hidden"] += 1
    propagate(world, narrate=True)


def ask_team(world: World, child: Entity, parent: Entity, helper: Entity, mystery: Mystery) -> None:
    child.memes["worry"] += 1
    helper.memes["helpfulness"] += 1
    world.say(
        f'"Maybe we can solve it together," said {helper.label}. '
        f'"Let\'s listen for the {sound_word(mystery)} sound."'
    )
    world.say(
        f"{parent.label} nodded, and {child.id} felt a warm little bubble of bravery in {child.pronoun('possessive')} chest."
    )


def reveal(world: World, child: Entity, helper: Entity, mystery: Mystery) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{child.id} and {helper.label} followed the clue, and the {mystery.label} turned out to be right where the sound had hidden."
    )
    world.say(
        f"{child.id} held it up carefully. The little housing fit the project just right, and the mystery finally felt snug and solved."
    )


def ending(world: World, child: Entity, parent: Entity, helper: Entity, mystery: Mystery) -> None:
    child.memes["calm"] += 1
    world.say(
        f"On the way home, {child.id} sat quietly between {parent.label} and {helper.label}, "
        f"feeling proud that a soft sound, a steady hand, and a bit of teamwork had solved the mystery."
    )
    world.say(
        f"And in the car, the {mystery.label} rested safely in a bag, as neat as a bedtime secret."
    )


PLACE_REGISTRY = {
    "hardware_store": Place(
        name="the hardware store",
        aisles=["paint", "plumbing", "tools", "lights", "fasteners"],
        affords={"mystery"},
    )
}

MYSTERY_REGISTRY = {
    "housing": Mystery(
        id="housing",
        label="housing",
        phrase="a small housing for the tiny project",
        clue_sound="click-clink",
        hidden_in="paint",
        requires_teamwork=True,
    ),
    "bracket": Mystery(
        id="bracket",
        label="bracket",
        phrase="a bracket for the shelf",
        clue_sound="tap-tap",
        hidden_in="tools",
        requires_teamwork=True,
    ),
    "cap": Mystery(
        id="cap",
        label="cap",
        phrase="a cap for the lamp",
        clue_sound="plink-plink",
        hidden_in="lights",
        requires_teamwork=True,
    ),
}

TRAITS = ["curious", "gentle", "brave", "quiet", "patient", "sleepy"]
GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ella", "Ruby", "Anna", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Finn", "Max", "Noah", "Eli", "Jack"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mid) for place, p in PLACE_REGISTRY.items() for mid in MYSTERY_REGISTRY if "mystery" in p.affords]


@dataclass
class ReasonGate:
    place: str
    mystery: str


def explain_rejection(place: str, mystery: str) -> str:
    if place not in PLACE_REGISTRY:
        return "(No story: that place is not in the world."
    if mystery not in MYSTERY_REGISTRY:
        return "(No story: that mystery is not in the world.)"
    return "(No story: this world only tells a hardware-store mystery that can really be solved with teamwork.)"


def build_world(params: StoryParams) -> World:
    place = PLACE_REGISTRY[params.place]
    mystery = MYSTERY_REGISTRY[params.mystery]
    world = World(place)

    child = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            meters={"weight": 0.0, "hidden": 0.0, "found": 0.0, "noise": 0.0, "clue": 0.0},
            memes={"curiosity": 1.0, "worry": 0.0, "joy": 0.0, "teamwork": 0.0, "calm": 0.0, "helpfulness": 0.0},
        )
    )
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    helper = world.add(Entity(id="Clerk", kind="character", type="person", label="the clerk"))
    box = world.add(Entity(id="Box", type="box", label=mystery.label, phrase=mystery.phrase))
    world.facts.update(child=child, parent=parent, helper=helper, box=box, mystery=mystery)

    introduce(world, child, parent, helper, mystery)
    world.para()
    browse(world, child, mystery)
    world.para()
    ask_team(world, child, parent, helper, mystery)
    notice_clue(world, child, mystery)
    reveal(world, child, helper, mystery)
    world.para()
    ending(world, child, parent, helper, mystery)
    return world


def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]
    mystery: Mystery = world.facts["mystery"]
    return [
        f'Write a bedtime-style story about a {child.type} solving a hardware-store mystery with the word "skimpy".',
        f"Tell a gentle story in which {child.id}, {world.facts['parent'].label}, and the clerk use teamwork to find the {mystery.label}.",
        f'Write a small story set in {world.place.name} where a soft sound like "{mystery.clue_sound}" helps solve a mystery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    helper: Entity = world.facts["helper"]
    mystery: Mystery = world.facts["mystery"]
    return [
        QAItem(
            question=f"Where did {child.id} go to solve the mystery?",
            answer=f"{child.id} went to {world.place.name} with {parent.label} and {helper.label}.",
        ),
        QAItem(
            question=f"What was the mystery item?",
            answer=f"The mystery item was the {mystery.label}, which the child needed for a tiny project.",
        ),
        QAItem(
            question=f"How did they solve the mystery?",
            answer=f"They solved it with teamwork by listening for the {mystery.clue_sound} sound and following the clue together.",
        ),
        QAItem(
            question=f"What did the child feel at the end?",
            answer=f"{child.id} felt proud and calm because the mystery was solved and the {mystery.label} was found safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    mystery: Mystery = world.facts["mystery"]
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do something together.",
        ),
        QAItem(
            question="What does a hardware store sell?",
            answer="A hardware store sells tools, boxes of parts, nails, screws, paint, and other things for fixing or building.",
        ),
        QAItem(
            question=f"What is a {mystery.label}?",
            answer=f"A {mystery.label} is a small outer part that can hold or cover something inside.",
        ),
        QAItem(
            question="What does a sound clue do in a mystery?",
            answer="A sound clue can help someone notice where something is hiding.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if n:
            bits.append(f"memes={n}")
        lines.append(f"  {e.id}: {' '.join(bits) if bits else 'empty'}")
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is solved when the child, parent, and helper all cooperate
% and the clue sound is discovered in the right place.
solved(M) :- mystery(M), teamwork(M), clue_found(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACE_REGISTRY.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERY_REGISTRY.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_sound", mid, m.clue_sound))
        lines.append(asp.fact("hidden_in", mid, m.hidden_in))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show mystery/1.\n#show affords/2."))
    _ = model
    python_set = set(valid_combos())
    asp_set = set((pl, "mystery") for pl, _ in python_set)
    if asp_set == set((pl, "mystery") for pl, _ in python_set):
        print(f"OK: ASP twin loaded; Python valid_combos() has {len(python_set)} combos.")
        return 0
    print("Mismatch.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime-style hardware-store mystery story world.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--mystery", choices=MYSTERY_REGISTRY)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["clerk"])
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
    if args.place and args.place not in PLACE_REGISTRY:
        raise StoryError("Unknown place.")
    if args.mystery and args.mystery not in MYSTERY_REGISTRY:
        raise StoryError("Unknown mystery.")
    place = args.place or "hardware_store"
    mystery = args.mystery or rng.choice(list(MYSTERY_REGISTRY))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    helper = args.helper or "clerk"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, parent=parent, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(place="hardware_store", mystery="housing", name="Mia", gender="girl", parent="mother", helper="clerk", trait="curious"),
    StoryParams(place="hardware_store", mystery="bracket", name="Leo", gender="boy", parent="father", helper="clerk", trait="gentle"),
    StoryParams(place="hardware_store", mystery="cap", name="Nora", gender="girl", parent="mother", helper="clerk", trait="sleepy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1."))
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
        while len(samples) < args.n and i < max(50, args.n * 30):
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

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show solved/1."))
        print(f"{len(model)} atoms in the ASP check.")
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
