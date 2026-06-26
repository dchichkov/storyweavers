#!/usr/bin/env python3
"""
storyworlds/worlds/material_lad_stay_flashback_pirate_tale.py
=============================================================

A small pirate-tale story world with a flashback turn.

Seed premise:
A lad wants to use a particular material to make or repair something aboard a
ship, but an old flashback reminds the crew why caution matters. The story
turns on whether the lad stays with the safe plan or rushes into trouble.

This world keeps the prose child-facing and concrete:
- a lad, a parent/captain figure, a material, and a ship task
- a flashback that explains a past mishap
- a tension beat where the lad wants to act fast
- a resolution where the crew chooses a safer pirate solution

The world is intentionally small and constraint-driven. Only combinations that
make narrative sense are generated.
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
        male = {"boy", "lad", "man", "father", "captain", "pirate"}
        female = {"girl", "woman", "mother", "matey"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class Material:
    id: str
    label: str
    phrase: str
    kind: str
    use: str
    hazard: str
    flashback: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    consequence: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Safety:
    id: str
    label: str
    phrase: str
    helps: set[str]
    keeps: str
    has: str
    tail: str


MATERIALS = {
    "canvas": Material(
        id="canvas",
        label="canvas",
        phrase="sturdy canvas",
        kind="cloth",
        use="patch the sail",
        hazard="it can tear in a hard wind",
        flashback="the last canvas patch ripped during a storm",
        tags={"cloth", "sail", "storm", "flashback"},
    ),
    "rope": Material(
        id="rope",
        label="rope",
        phrase="thick rope",
        kind="fiber",
        use="tie the broken mast",
        hazard="it can snap if it is frayed",
        flashback="the old rope knot slipped and sent a bucket flying",
        tags={"rope", "mast", "flashback"},
    ),
    "wood": Material(
        id="wood",
        label="wood",
        phrase="smooth wood",
        kind="timber",
        use="patch the little boat",
        hazard="it can split when the sea hits hard",
        flashback="a wooden plank once cracked and made a splash",
        tags={"wood", "boat", "flashback"},
    ),
    "tarcloth": Material(
        id="tarcloth",
        label="tarcloth",
        phrase="dark tarcloth",
        kind="covering",
        use="cover the cargo",
        hazard="it can slip if tied too fast",
        flashback="a tarcloth cover once slid loose and soaked the deck",
        tags={"cloth", "cargo", "flashback"},
    ),
}

TASKS = {
    "patch_sail": Task(
        id="patch_sail",
        verb="patch the sail",
        gerund="patching the sail",
        rush="dash up to the rigging with the canvas",
        consequence="the sail would tear again in the wind",
        zone="sail",
        tags={"sail", "wind"},
    ),
    "tie_mast": Task(
        id="tie_mast",
        verb="tie the mast",
        gerund="tying the mast",
        rush="run to the mast with the rope",
        consequence="the mast could wobble and scare the crew",
        zone="mast",
        tags={"mast", "wind"},
    ),
    "fix_boat": Task(
        id="fix_boat",
        verb="fix the little boat",
        gerund="fixing the little boat",
        rush="hurry to the side boat with the wood",
        consequence="the boat could stay leaky",
        zone="boat",
        tags={"boat", "water"},
    ),
    "cover_cargo": Task(
        id="cover_cargo",
        verb="cover the cargo",
        gerund="covering the cargo",
        rush="scramble to the cargo hold with the tarcloth",
        consequence="the cargo could get wet",
        zone="cargo",
        tags={"cargo", "rain"},
    ),
}

SAFETY = [
    Safety(
        id="needle",
        label="a bent needle and thread",
        phrase="a bent needle and thread",
        helps={"canvas"},
        keeps="stitch the patch slowly",
        has="the captain's sewing kit",
        tail="sat together and stitched the canvas patch slowly",
    ),
    Safety(
        id="fresh_rope",
        label="a fresh coil of rope",
        phrase="a fresh coil of rope",
        helps={"rope"},
        keeps="replace the frayed rope",
        has="the spare rope chest",
        tail="walked down to the spare rope chest and chose a fresh coil",
    ),
    Safety(
        id="planks",
        label="two spare planks",
        phrase="two spare planks",
        helps={"wood"},
        keeps="bolt the planks carefully",
        has="the workbench chest",
        tail="picked up two spare planks and bolted them carefully",
    ),
    Safety(
        id="clips",
        label="little cargo clips",
        phrase="little cargo clips",
        helps={"tarcloth"},
        keeps="clip the cover steady",
        has="the cargo box",
        tail="used little cargo clips to hold the cover steady",
    ),
]

SETTINGS = {
    "deck": "the deck of a small pirate ship",
    "harbor": "the harbor beside the ship",
    "hold": "the ship's hold",
}


# ---------------------------------------------------------------------------
# Parameters and story world
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    material: str
    task: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_world(params: StoryParams) -> World:
    world = World(setting=params.setting)
    lad = world.add(Entity(id=params.name, kind="character", type="boy"))
    parent = world.add(Entity(id="Captain", kind="character", type=params.parent, label="the captain"))
    material = world.add(Entity(
        id=params.material,
        kind="thing",
        type="material",
        label=MATERIALS[params.material].label,
        phrase=MATERIALS[params.material].phrase,
        caretaker=parent.id,
    ))
    task = TASKS[params.task]
    world.facts.update(
        lad=lad,
        parent=parent,
        material=material,
        task=task,
        setting=params.setting,
        safety=None,
        flashback=False,
        solved=False,
    )

    # Act 1
    world.say(f"{lad.id} was a little {params.trait} lad on a small pirate ship.")
    world.say(
        f"{lad.id} loved the salty wind, the creak of the ropes, and the way the crew stayed busy."
    )
    world.say(
        f"One morning, the captain showed {lad.id} a piece of {material.label} and said it could {task.verb}."
    )
    world.say(
        f"{lad.id} liked the idea at once, because {material.label} looked strong and useful."
    )

    # Flashback turn
    world.para()
    world.say(
        f"Then the captain had a flashback about an old trip, when {MATERIALS[params.material].flashback}."
    )
    world.say(
        f"That memory made the captain stay calm and say, \"Slow work is safer work on a pirate ship.\""
    )

    # Conflict
    world.para()
    world.say(
        f"{lad.id} still wanted to hurry. {lad.pronoun().capitalize()} tried to {task.rush}."
    )
    world.say(
        f"But the captain held up a hand and warned that if they rushed, {task.consequence}."
    )

    # Resolution
    safety = choose_safety(material.id, task.id)
    if safety is None:
        raise StoryError("No reasonable safety choice exists for this material and task.")
    world.facts["safety"] = safety

    world.say(
        f"At last, {lad.id}'s eyes landed on {safety.phrase} in {safety.has}."
    )
    world.say(
        f"The captain smiled and said they could {safety.keeps} instead of rushing."
    )

    world.para()
    world.say(
        f"So {lad.id} and the captain {safety.tail}, and {task.gerund} went much better."
    )
    world.say(
        f"By the end, the {material.label} was put to good use, the ship stayed safe, and {lad.id} stayed beside the captain, proud to help."
    )

    world.facts["flashback"] = True
    world.facts["solved"] = True
    return world


def choose_safety(material_id: str, task_id: str) -> Optional[Safety]:
    for s in SAFETY:
        if material_id in s.helps and task_id in TASKS:
            return s
    return None


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lad = f["lad"]
    parent = f["parent"]
    material = f["material"]
    task = f["task"]
    return [
        f'Write a short pirate tale for a child about a lad named {lad.id}, a flashback, and {material.label}.',
        f"Tell a story where {lad.id} wants to {task.verb}, but {parent.label} remembers a flashback and slows things down.",
        f'Write a gentle pirate story that includes the words "material", "lad", and "stay".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    lad = f["lad"]
    parent = f["parent"]
    material = f["material"]
    task = f["task"]
    safety: Safety = f["safety"]

    return [
        QAItem(
            question=f"What did {lad.id} want to do with the {material.label}?",
            answer=f"{lad.id} wanted to {task.verb}. The {material.label} looked useful for the job.",
        ),
        QAItem(
            question=f"Why did the captain have a flashback?",
            answer=(
                f"The captain remembered that {MATERIALS[material.id].flashback}. "
                f"That flashback made the captain want the crew to stay careful."
            ),
        ),
        QAItem(
            question=f"What safer plan did they choose instead of rushing?",
            answer=(
                f"They chose {safety.phrase} and decided to {safety.keeps}. "
                f"That let {lad.id} help without making a big mistake."
            ),
        ),
        QAItem(
            question=f"How did {lad.id} feel at the end?",
            answer=(
                f"{lad.id} felt proud and happy. {lad.id} stayed with the captain and helped finish the job the safe way."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened before, so the characters remember an old event.",
        ),
        QAItem(
            question="What is a material?",
            answer="A material is a thing you can use to make or fix something, like cloth, rope, wood, or metal.",
        ),
        QAItem(
            question="What does it mean to stay calm?",
            answer="To stay calm means to keep your body and voice steady, even when something feels tricky or exciting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.kind:
            bits.append(f"kind={ent.kind}")
        if ent.type:
            bits.append(f"type={ent.type}")
        if ent.phrase:
            bits.append(f"phrase={ent.phrase}")
        if ent.caretaker:
            bits.append(f"caretaker={ent.caretaker}")
        lines.append(f"{ent.id}: " + ", ".join(bits))
    lines.append(f"facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(deck).
setting(harbor).
setting(hold).

material(canvas).
material(rope).
material(wood).
material(tarcloth).

task(patch_sail).
task(tie_mast).
task(fix_boat).
task(cover_cargo).

safety(needle).
safety(fresh_rope).
safety(planks).
safety(clips).

helps(needle, canvas).
helps(fresh_rope, rope).
helps(planks, wood).
helps(clips, tarcloth).

valid_combo(S, T, M) :- safety(S), task(T), material(M), helps(S, M).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MATERIALS:
        lines.append(asp.fact("material", m))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for s in SAFETY:
        lines.append(asp.fact("safety", s.id))
        for m in s.helps:
            lines.append(asp.fact("helps", s.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation logic
# ---------------------------------------------------------------------------

GENDERS = {"boy"}
NAMES = ["Finn", "Ned", "Toby", "Jory", "Pip", "Cal", "Owen", "Liam"]
TRAITS = ["brave", "curious", "cheerful", "steady", "spry", "bold"]

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting in SETTINGS:
        for task in TASKS:
            for material in MATERIALS:
                if choose_safety(material, task) is not None:
                    combos.append((setting, task, material))
    return combos


@dataclass
class StoryParams:
    setting: str
    material: str
    task: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale world with a flashback turn.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father", "captain"], default="captain")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.task is None or c[1] == args.task)
        and (args.material is None or c[2] == args.material)
    ]
    if not combos:
        raise StoryError("No valid pirate story matches the given options.")
    setting, task, material = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    parent = args.parent or "captain"
    return StoryParams(setting=setting, material=material, task=task, name=name, parent=parent, trait=trait)


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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="deck", material="canvas", task="patch_sail", name="Finn", parent="captain", trait="curious"),
    StoryParams(setting="harbor", material="rope", task="tie_mast", name="Toby", parent="captain", trait="bold"),
    StoryParams(setting="hold", material="wood", task="fix_boat", name="Pip", parent="captain", trait="steady"),
    StoryParams(setting="deck", material="tarcloth", task="cover_cargo", name="Ned", parent="captain", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_combo/3."))
        triples = sorted(set(asp.atoms(model, "valid_combo")))
        print(f"{len(triples)} valid combo(s):")
        for t in triples:
            print(" ", t)
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
