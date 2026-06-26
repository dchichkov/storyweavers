#!/usr/bin/env python3
"""
storyworlds/worlds/psychiatry_sticky_palm_sound_effects_transformation_cautionary.py
===================================================================================

A compact storyworld about a small space-adventure mishap in a clinic-like
corner of a starship. A curious child meets a strange sticky palm, hears odd
sound effects, sees a cautious transformation, and learns a gentle lesson.

Premise
-------
A child on a space trip visits the ship's psychiatry room because the crew
thinks the little sticky palm plant might be harmless. The palm turns out to be
mischievous: it makes funny sound effects, sticks to everything, and changes
shape when touched.

Turn
----
The child reaches for it anyway, gets the palm stuck to a glove, and the room
fills with squeaks and zips as the thing transforms.

Resolution
----------
A calm doctor warns the child to use a tool, not bare hands. The child listens,
uses a scoop, and the sticky palm settles down in a safe case.

The simulated state drives narration:
- meters: stickiness, noise, caution, transformation, calm
- memes: worry, wonder, relief, confidence
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
    contains_sticky: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "doctor"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man", "pilot"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class SpaceBase:
    place: str = "the psychiatry room"
    has_panel: bool = True
    has_locker: bool = True


@dataclass
class Creature:
    id: str
    label: str
    phrase: str
    sound: str
    sticky_level: float
    transform_to: str
    caution_needed: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    purpose: str


class World:
    def __init__(self, base: SpaceBase) -> None:
        self.base = base
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        import copy as _copy

        clone = World(self.base)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


CREATURES = {
    "sticky_palm": Creature(
        id="sticky_palm",
        label="sticky palm",
        phrase="a sticky little palm with glossy green fronds",
        sound="squelch-whirr",
        sticky_level=1.0,
        transform_to="lantern palm",
    ),
    "echo_palm": Creature(
        id="echo_palm",
        label="echo palm",
        phrase="a small palm that hummed like a radio",
        sound="ping-ping",
        sticky_level=0.5,
        transform_to="bright palm",
    ),
}

TOOLS = {
    "scoop": Tool(
        id="scoop",
        label="scoop",
        phrase="a long silver scoop",
        purpose="move the plant without touching it",
    ),
    "gloves": Tool(
        id="gloves",
        label="gloves",
        phrase="soft gloves",
        purpose="keep hands from getting sticky",
    ),
}

NAMES = ["Mina", "Tobias", "Lena", "Arin", "Juno", "Sasha"]
ROLES = ["boy", "girl"]
DOCTORS = ["doctor", "psychiatrist", "medic"]
TRAITS = ["curious", "careful", "brave", "small", "thoughtful"]


@dataclass
class StoryParams:
    creature: str
    tool: str
    name: str
    role: str
    doctor: str
    trait: str
    seed: Optional[int] = None


def _now(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _set(entity: Entity, key: str, val: float) -> None:
    entity.meters[key] = val


def _mem(entity: Entity, key: str, val: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + val


def _do_touch(world: World, hero: Entity, creature: Creature, narrate: bool = True) -> None:
    palm = world.get(creature.id)
    if ("touch", hero.id) in world.fired:
        return
    world.fired.add(("touch", hero.id))
    _mem(hero, "wonder", 1.0)
    _set(palm, "sticky", palm.meters.get("sticky", 0.0) + creature.sticky_level)
    _set(palm, "noise", palm.meters.get("noise", 0.0) + 1.0)
    if narrate:
        world.say(f'{hero.id} reached out, and the room went "{creature.sound}!"')


def _do_transform(world: World, creature: Creature, narrate: bool = True) -> None:
    palm = world.get(creature.id)
    if palm.meters.get("sticky", 0.0) < THRESHOLD:
        return
    if ("transform", palm.id) in world.fired:
        return
    world.fired.add(("transform", palm.id))
    _set(palm, "transforming", 1.0)
    _mem(palm, "restless", 1.0)
    if narrate:
        world.say(
            f"The sticky palm shivered, then changed into a {creature.transform_to} "
            f'with a "zip-zap" sound.'
        )


def _do_caution(world: World, doctor: Entity, hero: Entity, tool: Tool, narrate: bool = True) -> None:
    if ("caution", hero.id) in world.fired:
        return
    world.fired.add(("caution", hero.id))
    _mem(hero, "caution", 1.0)
    _mem(doctor, "calm", 1.0)
    if narrate:
        world.say(
            f'{doctor.id} lifted a calm hand and said, "No bare palms. Use the {tool.label}."'
        )


def _do_safe_move(world: World, hero: Entity, creature: Creature, tool: Tool, narrate: bool = True) -> None:
    if ("safe", hero.id) in world.fired:
        return
    world.fired.add(("safe", hero.id))
    palm = world.get(creature.id)
    _set(palm, "sticky", 0.0)
    _set(palm, "noise", 0.0)
    _set(palm, "caged", 1.0)
    _mem(hero, "relief", 1.0)
    _mem(hero, "confidence", 1.0)
    if narrate:
        world.say(
            f"{hero.id} took the {tool.label} and slid the palm into a clear case. "
            f"The squelch stopped, and the starship felt peaceful again."
        )


def tell(creature: Creature, tool: Tool, name: str, role: str, doctor_role: str, trait: str) -> World:
    world = World(SpaceBase())
    hero = world.add(Entity(id=name, kind="character", type=role))
    doctor = world.add(Entity(id=doctor_role, kind="character", type=doctor_role))
    palm = world.add(Entity(
        id=creature.id,
        kind="thing",
        type=creature.label,
        label=creature.label,
        phrase=creature.phrase,
        contains_sticky=True,
    ))
    world.facts.update(hero=hero, doctor=doctor, palm=palm, creature=creature, tool=tool)

    world.say(
        f"{name} was a {trait} {role} aboard a little starship, where even the "
        f"{world.base.place} had blinking lights and soft chairs."
    )
    world.say(
        f'The crew brought in {creature.phrase}, and everyone heard a tiny "{creature.sound}."'
    )
    world.para()
    world.say(
        f"{name} wanted to poke the {creature.label} because it looked friendly, "
        f"but {doctor_role} watched carefully."
    )
    _do_caution(world, doctor, hero, tool)
    _do_touch(world, hero, creature)
    _do_transform(world, creature)
    world.para()
    world.say(
        f"{name} frowned at the sticky fingers on the glove, then remembered the warning."
    )
    _do_safe_move(world, hero, creature, tool)
    world.say(
        f'By the end, the {creature.label} rested safely in the case, and the room '
        f'was quiet except for one last "hmm."'
    )

    world.facts["resolved"] = True
    world.facts["cautionary"] = True
    return world


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for cid, creature in CREATURES.items():
        for tid, tool in TOOLS.items():
            if creature.sticky_level >= THRESHOLD and tool.id in {"scoop", "gloves"}:
                combos.append((cid, tid))
    return combos


def explain_rejection(creature: Creature, tool: Tool) -> str:
    return (
        f"(No story: the {tool.label} does not create a clear cautionary solution "
        f"for the {creature.label}. Try the scoop or gloves.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.creature and args.tool:
        if (args.creature, args.tool) not in valid_combos():
            raise StoryError(explain_rejection(CREATURES[args.creature], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.creature is None or c[0] == args.creature)
              and (args.tool is None or c[1] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    creature_id, tool_id = rng.choice(sorted(combos))
    return StoryParams(
        creature=creature_id,
        tool=tool_id,
        name=args.name or rng.choice(NAMES),
        role=args.role or rng.choice(ROLES),
        doctor=args.doctor or rng.choice(DOCTORS),
        trait=args.trait or rng.choice(TRAITS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c: Creature = f["creature"]
    return [
        f'Write a short space-adventure story for a young child about a "{c.label}" and a careful warning.',
        f"Tell a cautionary story where {f['hero'].id} meets a sticky palm in a psychiatry room on a starship.",
        f"Write a story with sound effects like {c.sound} and a safe ending after a strange transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, doctor, palm, creature, tool = f["hero"], f["doctor"], f["palm"], f["creature"], f["tool"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a small {hero.type} on a starship who learned to be careful around the sticky palm.",
        ),
        QAItem(
            question=f"What sound did the {creature.label} make?",
            answer=f"The {creature.label} made a little \"{creature.sound}\" sound, which made the room feel strange and exciting.",
        ),
        QAItem(
            question=f"What did {doctor.id} tell {hero.id} to use?",
            answer=f"{doctor.id} told {hero.id} to use the {tool.label} instead of bare hands, so the sticky palm would stay safe.",
        ),
        QAItem(
            question=f"What changed about the palm?",
            answer=f"The sticky palm transformed into a {creature.transform_to} after it got touched and started to shimmer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is psychiatry for?",
            answer="Psychiatry is a kind of medical care that helps people understand feelings, worries, and thoughts.",
        ),
        QAItem(
            question="Why can sticky things be hard to hold?",
            answer="Sticky things cling to surfaces, so they can tug at fingers and make hands pull away slowly.",
        ),
        QAItem(
            question="What is a palm in a plant story?",
            answer="A palm can be a kind of tree or plant with long leaves that spread out like hands.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: meters={meters} memes={memes}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
sticky(X) :- palm(X), has_meter(X, sticky).
noisy(X) :- palm(X), has_meter(X, noise).
transforming(X) :- palm(X), has_meter(X, transforming).
cautionary(X) :- character(X), has_meter(X, caution).

safe_story(Creature, Tool) :- sticky_creature(Creature), safe_tool(Tool).
valid_story(Creature, Tool) :- sticky_creature(Creature), safe_tool(Tool), cautionary_theme.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = ["cautionary_theme."]
    for cid, c in CREATURES.items():
        lines.append(asp.fact("sticky_creature", cid))
        lines.append(asp.fact("palm", cid))
        lines.append(asp.fact("sound_of", cid, c.sound))
        lines.append(asp.fact("transforms_to", cid, c.transform_to))
    for tid, t in TOOLS.items():
        if t.id in {"scoop", "gloves"}:
            lines.append(asp.fact("safe_tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def generate(params: StoryParams) -> StorySample:
    world = tell(
        CREATURES[params.creature],
        TOOLS[params.tool],
        params.name,
        params.role,
        params.doctor,
        params.trait,
    )
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure cautionary story world.")
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--doctor", choices=DOCTORS)
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


CURATED = [
    StoryParams(creature="sticky_palm", tool="scoop", name="Mina", role="girl", doctor="doctor", trait="curious"),
    StoryParams(creature="sticky_palm", tool="gloves", name="Arin", role="boy", doctor="medic", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
