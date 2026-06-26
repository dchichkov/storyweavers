#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/spank_gerund_intelligence_dark_lesson_learned_reconciliation.py
================================================================================================

A standalone story world for a small ghost-story domain built from the seed:
spank-gerund, intelligence, dark.

Premise:
- A child is tempted to sneak into the dark.
- A spooky noise and a strict warning create tension.
- Intelligence helps the child discover the noise has a kind, ordinary cause.
- A lesson is learned, the family reconciles, and the ending is happy.

The story is intentionally close to a gentle ghost story: shadows, creaks,
candles, a small mystery, and a warm resolution. The world uses meters for
physical state and memes for emotional state.
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
    place: str
    dark: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    reveals: str
    light_needed: bool = True


@dataclass
class StoryParams:
    place: str
    clue: str
    child_name: str
    child_type: str
    parent_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("child")
    if not kid:
        return out
    if kid.memes.get("fear", 0) >= THRESHOLD and ("fear", kid.id) not in world.fired:
        world.fired.add(("fear", kid.id))
        kid.memes["shake"] = kid.memes.get("shake", 0) + 1
        out.append("The dark made the child shiver.")
    return out


def _r_intelligence(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("child")
    lamp = world.entities.get("lamp")
    if not kid or not lamp:
        return out
    if kid.memes.get("thinking", 0) >= THRESHOLD and lamp.meters.get("lit", 0) >= THRESHOLD:
        sig = ("intelligence", kid.id)
        if sig not in world.fired:
            world.fired.add(sig)
            kid.memes["brave"] = kid.memes.get("brave", 0) + 1
            out.append("The child used intelligence and looked for a clue.")
    return out


def _r_reconciliation(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("child")
    parent = world.entities.get("parent")
    ghost = world.entities.get("ghost")
    if not kid or not parent or not ghost:
        return out
    if kid.memes.get("understanding", 0) >= THRESHOLD and parent.memes.get("worry", 0) >= THRESHOLD:
        sig = ("reconcile", kid.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        kid.memes["peace"] = kid.memes.get("peace", 0) + 1
        parent.memes["peace"] = parent.memes.get("peace", 0) + 1
        ghost.memes["welcome"] = ghost.memes.get("welcome", 0) + 1
        out.append("Everyone’s hearts grew softer.")
    return out


CAUSAL_RULES = [_r_fear, _r_intelligence, _r_reconciliation]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def resolve_darkness(world: World) -> None:
    lamp = world.get("lamp")
    lamp.meters["lit"] = 1
    world.say("A small lamp glowed like a tiny moon.")
    propagate(world)


def search_clue(world: World, clue: Clue) -> None:
    child = world.get("child")
    child.memes["thinking"] = child.memes.get("thinking", 0) + 1
    world.say("The child listened carefully and used intelligence instead of panic.")
    if clue.light_needed and world.get("lamp").meters.get("lit", 0) < THRESHOLD:
        world.say("It was too dark to see the clue clearly.")
    resolve_darkness(world)
    child.memes["understanding"] = child.memes.get("understanding", 0) + 1
    world.say(f"In the light, the child found the clue: {clue.reveals}.")


def open_scene(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"At {world.setting.place}, night had made everything dark and still."
    )
    world.say(
        f"{child.id} loved the shadows but also felt a little uneasy when the floorboards creaked."
    )
    world.say(
        f"{parent.pronoun().capitalize()} warned that sneaking around in the dark could lead to trouble and even a spanking."
    )


def ghost_appears(world: World) -> None:
    world.say("Then a pale ghost drifted out of the hallway like a soft breath.")
    world.get("ghost").memes["mystery"] = 1
    world.get("child").memes["fear"] = 1
    propagate(world)


def misunderstanding(world: World) -> None:
    child = world.get("child")
    parent = world.get("parent")
    world.say(
        f"{child.id} thought the ghost might be angry, and {parent.pronoun('subject')} thought the noise meant mischief."
    )
    parent.memes["worry"] = 1
    child.memes["conflict"] = 1
    world.say("The room felt colder until somebody decided to think instead of guess.")


def lesson_learned(world: World) -> None:
    child = world.get("child")
    parent = world.get("parent")
    ghost = world.get("ghost")
    child.memes["understanding"] = child.memes.get("understanding", 0) + 1
    parent.memes["worry"] = 0
    world.say(
        f"{child.id} learned that dark places are not always bad, and that a careful mind can find the truth."
    )
    world.say(
        f"{parent.pronoun().capitalize()} learned to listen before scolding, because the ghost was only trying to show a lost clue."
    )
    ghost.memes["friendly"] = 1


def reconciliation(world: World) -> None:
    child = world.get("child")
    parent = world.get("parent")
    ghost = world.get("ghost")
    child.memes["peace"] = 1
    parent.memes["peace"] = 1
    ghost.memes["welcome"] = 1
    world.say(
        f"{child.id} smiled at {parent.pronoun('object')}, and they made up right away."
    )
    world.say(
        "The ghost floated beside them like a new friend."
    )


def happy_ending(world: World) -> None:
    child = world.get("child")
    parent = world.get("parent")
    ghost = world.get("ghost")
    world.say(
        f"In the end, {child.id} sat safely in the warm light while {parent.pronoun('subject')} gave a hug instead of a spanking."
    )
    world.say(
        f"The ghost waved good-night, the house felt gentle again, and everyone went to bed with peaceful hearts."
    )
    child.memes["joy"] = 1
    parent.memes["joy"] = 1
    ghost.memes["joy"] = 1


def tell(setting: Setting, clue: Clue, child_name: str, child_type: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=parent_type))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="ghost"))
    lamp = world.add(Entity(id="lamp", type="thing", label="lamp"))
    world.add(Entity(id="clue", type="thing", label=clue.label, phrase=clue.label))

    open_scene(world, child, parent)
    world.para()
    ghost_appears(world)
    misunderstanding(world)
    world.para()
    search_clue(world, clue)
    lesson_learned(world)
    reconciliation(world)
    happy_ending(world)

    world.facts.update(
        child=child,
        parent=parent,
        ghost=ghost,
        lamp=lamp,
        clue=clue,
        setting=setting,
    )
    return world


SETTINGS = {
    "old_house": Setting(place="the old house", dark=True, affords={"ghost_story"}),
    "attic": Setting(place="the attic", dark=True, affords={"ghost_story"}),
    "hallway": Setting(place="the hallway", dark=True, affords={"ghost_story"}),
}

CLUES = {
    "silver_key": Clue(
        id="silver_key",
        label="silver key",
        reveals="a silver key tucked under the rug",
        light_needed=True,
    ),
    "music_box": Clue(
        id="music_box",
        label="music box",
        reveals="a music box that had been playing by itself",
        light_needed=True,
    ),
    "cat": Clue(
        id="cat",
        label="sleepy cat",
        reveals="a sleepy cat bumping the chair in the dark",
        light_needed=True,
    ),
}

NAMES = ["Mina", "Theo", "June", "Ivy", "Noah", "Pippa"]
CHILD_TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place, setting in SETTINGS.items():
        for clue in CLUES:
            if "ghost_story" in setting.affords:
                combos.append((place, clue))
    return combos


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.dark:
            lines.append(asp.fact("dark", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.light_needed:
            lines.append(asp.fact("needs_light", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Clue) :- setting(Place), clue(Clue), affords(Place, ghost_story), dark(Place), needs_light(Clue).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a gentle ghost story about a child who uses intelligence in the dark, learns a lesson, and ends happily.",
        f"Tell a spooky-but-kind story set in {f['setting'].place} where {f['child'].label} solves a mystery and reconciles with {f['parent'].type}.",
        f"Write a short story that includes a ghost, a dark room, intelligence, and a happy ending after a misunderstanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    clue = f["clue"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Where did the spooky story happen?",
            answer=f"It happened at {setting.place}, where the dark made the room feel mysterious.",
        ),
        QAItem(
            question=f"What did {child.label} use to solve the problem?",
            answer=f"{child.label} used intelligence, listened closely, and found the real cause instead of guessing.",
        ),
        QAItem(
            question=f"Why did {parent.type} mention a spanking at first?",
            answer="Because the child was tempted to sneak around in the dark, and the parent wanted to stop trouble before it started.",
        ),
        QAItem(
            question=f"What was the clue in the story?",
            answer=f"The clue was {clue.reveals}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended with reconciliation, a warm light, and a happy ending for the child, the parent, and the ghost.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can dark rooms feel spooky?",
            answer="Dark rooms can feel spooky because it is harder to see, so normal shadows and sounds seem bigger and stranger.",
        ),
        QAItem(
            question="What is intelligence?",
            answer="Intelligence is the ability to think carefully, notice clues, and solve problems.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people who were upset make up again and feel friendly once more.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: dark, intelligence, lesson learned, reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=CHILD_TYPES)
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue = rng.choice(sorted(combos))
    child_type = args.gender or rng.choice(CHILD_TYPES)
    parent_type = args.parent or rng.choice(PARENT_TYPES)
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, clue=clue, child_name=name, child_type=child_type, parent_type=parent_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CLUES[params.clue], params.child_name, params.child_type, params.parent_type)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, clue) combos:\n")
        for place, clue in combos:
            print(f"  {place:10} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, clue in valid_combos():
            params = StoryParams(
                place=place,
                clue=clue,
                child_name="Mina",
                child_type="girl",
                parent_type="mother",
            )
            samples.append(generate(params))
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
