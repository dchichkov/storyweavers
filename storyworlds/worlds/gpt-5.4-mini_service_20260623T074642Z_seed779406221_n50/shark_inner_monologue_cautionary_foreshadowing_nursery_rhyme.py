#!/usr/bin/env python3
"""
Standalone storyworld: shark_inner_monologue_cautionary_foreshadowing_nursery_rhyme

A tiny, self-contained nursery-rhyme style story simulation about a curious
shark, a caution from a grown-up, a foreshadowed problem, and an inner
monologue that changes the outcome.

The world is deliberately small:
- a child shark wants to explore a bright reef
- a cautionary voice warns about a snaggy net and a sleeping tide
- the shark's inner monologue moves from bravado to care
- the ending image proves the change in state

This script follows the Storyweavers contract:
- self-contained stdlib script
- imports results eagerly, asp lazily
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports the standard CLI flags
- includes a Python reasonableness gate plus inline ASP_RULES twin
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
# Entities and world model
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "shark":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    water: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class ObjectDef:
    id: str
    label: str
    phrase: str
    risk: str
    region: str


@dataclass
class Hazard:
    id: str
    label: str
    warning: str
    foreshadow: str
    neutralizer: str
    avoids: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, line: str) -> None:
        if line:
            self.events.append(line)

    def render(self) -> str:
        out: list[str] = []
        for line in self.events:
            if line == "":
                out.append("")
            else:
                if out and out[-1] != "":
                    out[-1] += " " + line
                else:
                    out.append(line)
        return "\n\n".join(p for p in out if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "reef": Setting(place="the bright reef", water="blue water", affordances={"swim", "peek"}),
    "cove": Setting(place="the small cove", water="silver water", affordances={"swim", "peek"}),
    "kelp": Setting(place="the kelp garden", water="green water", affordances={"swim", "hide"}),
}

SHARKS = {
    "small": {"kind": "child shark", "type": "shark", "traits": ["small", "brave", "curious"]},
    "young": {"kind": "young shark", "type": "shark", "traits": ["young", "bouncy", "curious"]},
}

HUMANS = {
    "child": {"kind": "sea friend", "type": "friend"},
}

OBJECTS = {
    "shell": ObjectDef(id="shell", label="shell", phrase="a shiny shell", risk="nicks", region="fin"),
    "pearl": ObjectDef(id="pearl", label="pearl", phrase="a pearl in a clam cup", risk="scratches", region="side"),
}

HAZARDS = {
    "net": Hazard(
        id="net",
        label="snaggy net",
        warning="snags",
        foreshadow="a loop of line bobbed like a sleepy spider web",
        neutralizer="turn away from the net",
        avoids={"swim"},
    ),
    "tide": Hazard(
        id="tide",
        label="sleeping tide",
        warning="pulls",
        foreshadow="the tide tucked itself low and quiet under the moon",
        neutralizer="wait for the tide to turn",
        avoids={"peek"},
    ),
}


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    shark: str
    object: str
    hazard: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is reasonable when the setting allows the shark's activity,
% the chosen object sits in a region the hazard threatens, and a hazard exists.
reason(Setting, Shark, Object, Hazard) :-
    setting(Setting), shark(Shark), object(Object), hazard(Hazard),
    allows(Setting, swim),
    threatened(Object, Hazard).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("allows", sid, a))
    for sid in SHARKS:
        lines.append(asp.fact("shark", sid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("threatened", oid, "net" if o.risk == "nicks" else "tide"))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    python_ok = valid_combos()
    model = asp.one_model(asp_program("#show reason/4."))
    clingo_ok = sorted(set(asp.atoms(model, "reason")))
    expected = sorted(python_ok)
    if clingo_ok == expected:
        print(f"OK: clingo gate matches python gate ({len(expected)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    print("python:", expected)
    print("clingo:", clingo_ok)
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for shark_id in SHARKS:
            for obj_id, obj in OBJECTS.items():
                for haz_id, haz in HAZARDS.items():
                    if "swim" in setting.affordances:
                        if obj.region in {"fin", "side"}:
                            combos.append((setting_id, shark_id, obj_id, haz_id))
    return combos


def explain_rejection(setting: str, shark: str, obj: str, hazard: str) -> str:
    return (
        f"(No story: {shark} and {obj} do not make a reasonable rhyme with {hazard} "
        f"in {setting}. The little reef tale needs a real caution and a real turn.)"
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def _inner_monologue(world: World, shark: Entity, hazard: Hazard) -> None:
    world.say(
        f'{"The shark" if shark.id == "shark" else "He"} thought, '
        f'"I can dart and dither, I can dash through the blue."'
    )
    world.facts["first_thought"] = "brave"


def _foreshadow(world: World, hazard: Hazard) -> None:
    world.say(f"Yet {hazard.foreshadow}.")
    world.facts["foreshadowed"] = True


def _caution(world: World, shark: Entity, hazard: Hazard) -> None:
    world.say(
        f"A coral crab called out, \"Careful now, little swimmer; {hazard.warning} where the line lies.\""
    )
    world.facts["warning"] = hazard.warning


def _turn(world: World, shark: Entity, hazard: Hazard) -> None:
    shark.memes["worry"] = shark.memes.get("worry", 0.0) + 1
    world.say(
        f'The shark thought, "A snug little turn is wiser than a splashy rush."'
    )
    world.say(f"So {shark.id} chose to {hazard.neutralizer}.")
    world.facts["turn"] = "care"


def _ending(world: World, shark: Entity, obj: Entity) -> None:
    world.say(
        f"In the still blue hush, {shark.id} found {obj.phrase}, safe and sound, "
        f"and the reef shone round like a moonlit crown."
    )
    world.facts["ending"] = "safe"


def tell(setting: Setting, shark_id: str, object_id: str, hazard_id: str) -> World:
    world = World(setting)
    shark = world.add(Entity(id="shark", kind="character", type="shark", traits=SHARKS[shark_id]["traits"]))
    objdef = OBJECTS[object_id]
    obj = world.add(Entity(id=objdef.id, label=objdef.label, phrase=objdef.phrase))
    hazard = HAZARDS[hazard_id]

    world.say(f"At {setting.place}, a little shark glided through {setting.water}.")
    world.say(f"{shark.id.capitalize()} loved the gleam of every shell and pebble.")
    _foreshadow(world, hazard)
    _caution(world, shark, hazard)
    _inner_monologue(world, shark, hazard)
    _turn(world, shark, hazard)
    _ending(world, shark, obj)
    world.facts.update(setting=setting, shark=shark, object=obj, hazard=hazard)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        'Write a nursery-rhyme style story about a shark who hears a caution and changes course.',
        'Tell a gentle sea story with foreshadowing, inner monologue, and a safe ending for a curious shark.',
        'Write a short rhyme in which a little shark almost gets into trouble, then wisely turns away.',
    ]


def story_qa(world: World) -> list[QAItem]:
    haz: Hazard = world.facts["hazard"]  # type: ignore[assignment]
    obj: Entity = world.facts["object"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What did the shark first think before the warning?",
            answer="The shark first thought he could dart and dither and dash through the blue.",
        ),
        QAItem(
            question="What clue foreshadowed trouble in the story?",
            answer=f"{haz.foreshadow.capitalize()}. That was a clue that the shark should move with care.",
        ),
        QAItem(
            question="What caution did the crab give?",
            answer=f'The crab warned that {haz.warning} where the line lay.',
        ),
        QAItem(
            question="How did the shark answer the warning?",
            answer="He decided a small, careful turn was wiser than a splashy rush.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The shark found {obj.phrase} in the calm water, and the reef stayed safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shark?",
            answer="A shark is a fish that lives in the sea and swims with a strong tail.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a clue that hints something may happen later.",
        ),
        QAItem(
            question="What is a caution?",
            answer="A caution is a warning that helps someone stay safe.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme shark story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--shark", choices=SHARKS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--hazard", choices=HAZARDS)
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.shark is None or c[1] == args.shark)
        and (args.object is None or c[2] == args.object)
        and (args.hazard is None or c[3] == args.hazard)
    ]
    if not filtered:
        raise StoryError("(No valid shark story matches the given options.)")
    setting, shark, obj, hazard = rng.choice(sorted(filtered))
    return StoryParams(setting=setting, shark=shark, object=obj, hazard=hazard)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.shark, params.object, params.hazard)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reason/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show reason/4."))
        print(asp.atoms(model, "reason"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for setting in SETTINGS:
            for shark in SHARKS:
                for obj in OBJECTS:
                    for hazard in HAZARDS:
                        p = StoryParams(setting, shark, obj, hazard)
                        samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
