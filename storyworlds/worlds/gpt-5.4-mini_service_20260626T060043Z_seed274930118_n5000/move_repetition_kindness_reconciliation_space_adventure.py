#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/move_repetition_kindness_reconciliation_space_adventure.py
====================================================================================================

A small, standalone Storyweavers world: a space family moves a few precious
things from an old moon room to a new habitat module. The tension comes from
repeating the same heavy move many times, a helper offers kindness, and a
simple reconciliation makes the final trip feel like an adventure instead of a
chore.

The world is built around:
- move: carrying objects across a zero-gravity corridor
- repetition: the same route must be traveled again and again
- kindness: one character helps with a hard load
- reconciliation: a small conflict is repaired before the last trip

Style target:
- Space Adventure
- child-facing, concrete, and state-driven
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
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the moon base"
    route: str = "the blue tunnel"


@dataclass
class MoveTask:
    id: str
    verb: str
    gerund: str
    repeat: str
    strain: str
    keyword: str = "move"


@dataclass
class Cargo:
    label: str
    phrase: str
    weight: str
    plural: bool = False


@dataclass
class HelpItem:
    id: str
    label: str
    prep: str
    tail: str
    aid: str = "kindness"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_repeat_strain(world: World) -> list[str]:
    out: list[str] = []
    mover = world.entities.get("Mover")
    if not mover:
        return out
    if mover.meters.get("heavy_load", 0) < THRESHOLD:
        return out
    if mover.memes.get("repetition", 0) < THRESHOLD:
        return out
    sig = ("strain", mover.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mover.memes["tired"] = mover.memes.get("tired", 0) + 1
    out.append("The repeated trip made the work feel long and heavy.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    mover = world.entities.get("Mover")
    helper = world.entities.get("Helper")
    cargo = world.entities.get("Cargo")
    if not mover or not helper or not cargo:
        return out
    if helper.memes.get("kindness", 0) < THRESHOLD:
        return out
    if cargo.carried_by != mover.id:
        return out
    sig = ("kindness", helper.id, cargo.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cargo.carried_by = helper.id
    mover.memes["relief"] = mover.memes.get("relief", 0) + 1
    out.append("A kind helper took the heavier side of the cargo.")
    return out


def _r_reconciliation(world: World) -> list[str]:
    out: list[str] = []
    mover = world.entities.get("Mover")
    helper = world.entities.get("Helper")
    if not mover or not helper:
        return out
    if mover.memes.get("hurt", 0) < THRESHOLD:
        return out
    if helper.memes.get("apology", 0) < THRESHOLD:
        return out
    sig = ("reconcile", mover.id, helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mover.memes["hurt"] = 0
    mover.memes["trust"] = mover.memes.get("trust", 0) + 1
    helper.memes["trust"] = helper.memes.get("trust", 0) + 1
    out.append("The apology turned the tense silence into a fresh start.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_repeat_strain, _r_kindness, _r_reconciliation):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_move(world: World, mover: Entity, task: MoveTask) -> dict:
    sim = world.copy()
    sim.get(mover.id).meters["heavy_load"] = mover.meters.get("heavy_load", 0)
    sim.get(mover.id).memes["repetition"] = mover.memes.get("repetition", 0)
    propagate(sim, narrate=False)
    return {
        "strain": bool(sim.get(mover.id).memes.get("tired", 0) >= THRESHOLD),
        "relief": bool(sim.get(mover.id).memes.get("relief", 0) >= THRESHOLD),
    }


def setup_story(world: World, hero: Entity, helper: Entity, cargo: Entity, task: MoveTask) -> None:
    world.say(
        f"{hero.id} lived at {world.setting.place}, where the corridor lights glowed like tiny stars."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had to {task.verb} the same cargo again and again across {world.setting.route}."
    )
    world.say(
        f"The cargo was {cargo.phrase}, and every trip felt like another lap around the moon."
    )


def conflict_story(world: World, hero: Entity, helper: Entity, cargo: Entity, task: MoveTask) -> None:
    world.para()
    hero.meters["heavy_load"] = 1
    hero.memes["repetition"] = 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"At first, {hero.id} tried to do it alone."
    )
    world.say(
        f"{hero.pronoun().capitalize()} dragged {hero.pronoun('possessive')} boots, pushed the crate, and sighed at the long route."
    )
    world.say(
        f"After the third trip, {hero.id} felt grumpy, because the same job kept coming back."
    )
    if predict_move(world, hero, task)["strain"]:
        world.say(
            f"{helper.id} saw the tired face and wanted to help."
        )
    helper.memes["kindness"] = 1
    helper.memes["apology"] = 1
    helper.memes["hurt"] = 1
    world.say(
        f"But {helper.id} had first snapped, \"I was only trying to be quick,\" and that had made {hero.id} feel stung."
    )


def resolution_story(world: World, hero: Entity, helper: Entity, cargo: Entity, task: MoveTask) -> None:
    world.para()
    world.say(
        f"Then {helper.id} took a breath and said sorry."
    )
    world.say(
        f"{hero.id} looked at {helper.id}, nodded, and let the apology land softly between them."
    )
    propagate(world, narrate=True)
    cargo.carried_by = helper.id
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    world.say(
        f"Together they made one careful trip, and the crate slid into the new room like a small silver comet."
    )
    world.say(
        f"By the end, the moon base felt warmer, and the repeated move had become a shared space adventure."
    )


def tell(setting: Setting, task: MoveTask, cargo_cfg: Cargo, hero_name: str = "Mira",
         helper_name: str = "Juno") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl"))
    helper = world.add(Entity(id=helper_name, kind="character", type="girl"))
    cargo = world.add(Entity(
        id="Cargo",
        type="crate",
        label=cargo_cfg.label,
        phrase=cargo_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))
    world.add(Entity(id="Mover", kind="character", type="girl"))
    world.add(Entity(id="Helper", kind="character", type="girl"))
    world.add(Entity(id="CargoProxy", type="crate"))

    cargo.carried_by = hero.id

    setup_story(world, hero, helper, cargo, task)
    conflict_story(world, hero, helper, cargo, task)
    resolution_story(world, hero, helper, cargo, task)

    world.facts.update(hero=hero, helper=helper, cargo=cargo, task=task, setting=setting)
    return world


SETTINGS = {
    "moonbase": Setting(place="the moon base", route="the silver tunnel"),
    "orbital": Setting(place="the orbital station", route="the ring corridor"),
    "dome": Setting(place="the glass dome", route="the east hatch"),
}

TASKS = {
    "move": MoveTask(
        id="move",
        verb="move",
        gerund="moving",
        repeat="over and over",
        strain="tired",
        keyword="move",
    )
}

CARGOES = {
    "box": Cargo(label="box", phrase="a light blue box of saved moon rocks", weight="medium"),
    "plant": Cargo(label="plant", phrase="a leafy plant in a round pot", weight="careful"),
    "helmet": Cargo(label="helmet", phrase="a shiny helmet with a cracked sticker", weight="small"),
}

CURATED = [
    ("moonbase", "move", "box"),
    ("orbital", "move", "plant"),
    ("dome", "move", "helmet"),
]

GIRL_NAMES = ["Mira", "Juno", "Ari", "Nova", "Lumi", "Tess"]
TRAITS = ["brave", "gentle", "curious", "steady"]


@dataclass
class StoryParams:
    place: str
    task: str
    cargo: str
    name: str = "Mira"
    helper: str = "Juno"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world: move, repetition, kindness, reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    choices = [(p, t, c) for p, t, c in CURATED
               if (args.place is None or p == args.place)
               and (args.task is None or t == args.task)
               and (args.cargo is None or c == args.cargo)]
    if not choices:
        raise StoryError("No valid combination matches the given options.")
    place, task, cargo = rng.choice(choices)
    return StoryParams(
        place=place,
        task=task,
        cargo=cargo,
        name=args.name or rng.choice(GIRL_NAMES),
        helper=args.helper or rng.choice([n for n in GIRL_NAMES if n != args.name]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short space adventure about a child who has to {f['task'].verb} the same cargo again and again.",
        f"Tell a gentle story where {f['hero'].id} gets tired of repeating the move, then a kind helper makes it better.",
        f"Write a child-friendly story about a moon base move that ends with reconciliation and a happy final trip.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    cargo = f["cargo"]
    task = f["task"]
    return [
        QAItem(
            question=f"What did {hero.id} have to do again and again at {world.setting.place}?",
            answer=f"{hero.id} had to {task.verb} {cargo.phrase} across {world.setting.route} more than once.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel grumpy during the move?",
            answer=f"{hero.id} felt grumpy because the same trip kept repeating, and the work felt long and heavy.",
        ),
        QAItem(
            question=f"What did {helper.id} do to help after the hard move got tiring?",
            answer=f"{helper.id} took the heavier side, said sorry for snapping, and helped turn the job into a shared trip.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a moon base?",
            answer="A moon base is a place people can live or work on the moon, often with rooms, corridors, and bright control lights.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means doing something caring or helpful for someone else, especially when they are having a hard time.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who were upset make peace again and feel okay with each other.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
kindness(H, C) :- helper(H), cargo(C), helped(H, C).
repetition(M) :- mover(M), repeated_trip(M).
reconcile(M, H) :- mover(M), helper(H), apology(H), hurt(M).
final_ok(M, H, C) :- kindness(H, C), reconcile(M, H).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("mover", "Mover"),
        asp.fact("helper", "Helper"),
        asp.fact("cargo", "Cargo"),
        asp.fact("repeated_trip", "Mover"),
        asp.fact("helped", "Helper", "Cargo"),
        asp.fact("apology", "Helper"),
        asp.fact("hurt", "Mover"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show final_ok/3."))
    atoms = set(asp.atoms(model, "final_ok"))
    py = {("Mover", "Helper", "Cargo")}
    if atoms == py:
        print("OK: clingo gate matches Python reasoning (1 final_ok tuple).")
        return 0
    print("MISMATCH between clingo and Python reasoning.")
    print("clingo:", sorted(atoms))
    print("python:", sorted(py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], CARGOES[params.cargo], params.name, params.helper)
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
        print(asp_program("#show final_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show final_ok/3."))
        print(sorted(set(asp.atoms(model, "final_ok"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(place=p, task=t, cargo=c, name="Mira", helper="Juno")) for p, t, c in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
