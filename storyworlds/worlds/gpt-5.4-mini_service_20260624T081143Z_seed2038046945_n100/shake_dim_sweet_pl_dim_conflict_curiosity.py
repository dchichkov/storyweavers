#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/shake_dim_sweet_pl_dim_conflict_curiosity.py
=============================================================================================================

A small bedtime-story world about a child, a quiet worry, a curious look back,
and a gentle fix.

Seed words:
- shake-dim
- sweet-pl-dim

Features:
- Conflict
- Curiosity
- Flashback

The domain is a soft indoor evening tale: a child wants to keep a special
night-light toy close, but its shaky dim glow worries the caregiver. The child
remembers an earlier night (flashback), gets curious about the problem, and
finally chooses a softer lamp and a tucked-in blanket scene that proves what
changed.

This script follows the Storyweavers contract:
- standalone stdlib script
- eager results import
- lazy ASP import in helpers
- StoryParams, parser, resolver, generate, emit, main
- Python reasonableness gate + inline ASP twin
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
    portable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    name: str
    indoor: bool = True
    cozy: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    glow: str
    style: str
    safe: str
    can_fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    room: str
    toy: str
    child_name: str
    child_type: str
    caregiver_type: str
    seed: Optional[int] = None


ROOMS = {
    "bedroom": Room(name="the bedroom", indoor=True, cozy=True, affords={"read", "tuck_in", "listen"}),
    "nursery": Room(name="the nursery", indoor=True, cozy=True, affords={"read", "tuck_in", "listen"}),
    "hall": Room(name="the hallway", indoor=True, cozy=False, affords={"walk", "listen"}),
}

TOYS = {
    "shake_dim": Toy(
        id="shake_dim",
        label="shake-dim toy",
        phrase="a shake-dim toy with a sleepy little rattle",
        glow="shaky dim",
        style="shaking and dim",
        safe="steady and soft",
        can_fix="night lamp",
        tags={"shake-dim", "curiosity"},
    ),
    "sweet_pl_dim": Toy(
        id="sweet_pl_dim",
        label="sweet-pl-dim lamp",
        phrase="a sweet-pl-dim lamp with a warm gold shade",
        glow="sweet-pl-dim",
        style="sweet and dim",
        safe="steady and warm",
        can_fix="night lamp",
        tags={"sweet-pl-dim", "curiosity"},
    ),
}

GENTLE_FIXES = {
    "night_lamp": "a night lamp",
    "blanket": "a soft blanket",
    "storybook": "a storybook",
}

NAMES = ["Maya", "Nina", "Ella", "Luna", "Owen", "Theo", "Iris", "Milo"]
GIRL_NAMES = ["Maya", "Nina", "Ella", "Luna", "Iris"]
BOY_NAMES = ["Owen", "Theo", "Milo"]


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_calm(world: World) -> list[str]:
    out = []
    child = world.get("child")
    toy = world.get("toy")
    if child.memes.get("curiosity", 0) < 1:
        return out
    if child.memes.get("conflict", 0) < 1:
        return out
    if toy.meters.get("steady", 0) >= 1:
        sig = ("calm",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["relief"] = child.memes.get("relief", 0) + 1
        out.append("The room grew quieter as the worry eased.")
    return out


def _r_flashback(world: World) -> list[str]:
    child = world.get("child")
    if child.memes.get("memory", 0) < 1:
        return []
    sig = ("flashback",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["wisdom"] = child.memes.get("wisdom", 0) + 1
    return ["__flashback__"]


CAUSAL_RULES = [_r_calm, _r_flashback]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(s for s in sents if s != "__flashback__")
    if narrate:
        for s in out:
            world.say(s)
    return out


def reasonableness_gate(room: Room, toy: Toy) -> bool:
    return room.indoor and room.cozy and toy.id in TOYS


def select_fix(toy: Toy) -> str:
    return toy.can_fix


def predict_story(world: World, child: Entity, toy: Entity) -> dict:
    sim = world.copy()
    sim.get("child").memes["curiosity"] = 1
    sim.get("child").memes["memory"] = 1
    sim.get("toy").meters["steady"] = 1
    propagate(sim, narrate=False)
    return {
        "resolved": sim.get("child").memes.get("relief", 0) >= 1,
        "conflict": sim.get("child").memes.get("conflict", 0) >= 1,
    }


def tell(room: Room, toy_cfg: Toy, child_name: str, child_type: str, caregiver_type: str) -> World:
    world = World(room)
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name))
    caregiver = world.add(Entity(id="caregiver", kind="character", type=caregiver_type, label="the caregiver"))
    toy = world.add(Entity(id="toy", type=toy_cfg.id, label=toy_cfg.label, phrase=toy_cfg.phrase, owner=child.id))
    lamp = world.add(Entity(id="lamp", type="thing", label=GENTLE_FIXES["night_lamp"], phrase="a little night lamp", caretaker=caregiver.id))

    world.say(f"{child_name} was a sleepy little {child_type} in {room.name}.")
    world.say(f"{child_name} loved {toy_cfg.phrase}, because its {toy_cfg.glow} glow made bedtime feel like a nest of stars.")
    world.para()
    world.say(f"One evening, {child_name} wanted to hold the toy close at bedtime.")
    child.memes["desire"] = 1
    toy.meters["shaky"] = 1
    toy.meters["dim"] = 1
    child.memes["curiosity"] = 1
    world.say(f"But the {toy_cfg.label} looked {toy_cfg.style}, and that made {caregiver.label} worry.")
    world.say(f'"It might be too {toy_cfg.safe}," {caregiver.pronoun("subject")} said softly, "and bedtime should stay gentle."')
    child.memes["conflict"] = 1
    world.para()
    child.memes["memory"] = 1
    world.say(f"{child_name} paused and remembered a different night, when the room had felt too dark and the tiny glow had helped {child.pronoun("object")} breathe slower.")
    world.say(f"That flashback made {child_name} curious instead of cross.")
    propagate(world, narrate=True)
    world.say(f"So {child_name} asked about the problem, and {caregiver.label} showed {child_name} a {lamp.label} and a soft blanket.")
    toy.meters["steady"] = 1
    lamp.meters["warm"] = 1
    world.say(f"They tucked the toy beside the {lamp.label}, where it could rest without shaking.")
    child.memes["conflict"] = 0
    child.memes["curiosity"] = 2
    child.memes["peace"] = 1
    world.say(f"At last, {child_name} lay down smiling, with the {toy_cfg.label} safe, the lamp glowing warmly, and the room quiet as a lullaby.")
    world.facts.update(child=child, caregiver=caregiver, toy=toy, lamp=lamp, room=room, toy_cfg=toy_cfg)
    return world


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for room_id, room in ROOMS.items():
        for toy_id, toy in TOYS.items():
            if reasonableness_gate(room, toy):
                out.append((room_id, toy_id))
    return out


def asp_facts() -> str:
    import asp
    lines = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        if room.indoor:
            lines.append(asp.fact("indoor", rid))
        if room.cozy:
            lines.append(asp.fact("cozy", rid))
        for a in sorted(room.affords):
            lines.append(asp.fact("affords", rid, a))
    for tid, toy in TOYS.items():
        lines.append(asp.fact("toy", tid))
        lines.append(asp.fact("safe_style", tid, toy.safe))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Room, Toy) :- room(Room), indoor(Room), cozy(Room), toy(Toy), safe_style(Toy, _).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    toy_cfg: Toy = f["toy_cfg"]  # type: ignore[assignment]
    child: Entity = f["child"]  # type: ignore[assignment]
    room: Room = f["room"]  # type: ignore[assignment]
    return [
        f'Write a bedtime story about a child named {child.label} who loves a {toy_cfg.label} with a {toy_cfg.glow} glow.',
        f"Tell a cozy story set in {room.name} where {child.label} feels conflict, gets curious, and remembers a past night.",
        f'Write a gentle tale that includes the words "{toy_cfg.id}" and ends with a calm lamp and a quieter room.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    caregiver: Entity = world.facts["caregiver"]  # type: ignore[assignment]
    toy_cfg: Toy = world.facts["toy_cfg"]  # type: ignore[assignment]
    room: Room = world.facts["room"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who is the bedtime story about in {room.name}?",
            answer=f"It is about {child.label}, a sleepy little {child.type}, and {caregiver.label}, who helps keep bedtime gentle.",
        ),
        QAItem(
            question=f"What did {child.label} love about the {toy_cfg.label}?",
            answer=f"{child.label} loved its {toy_cfg.glow} glow, because it made the room feel safe and dreamy.",
        ),
        QAItem(
            question=f"Why did the caregiver worry about the {toy_cfg.label} at first?",
            answer=f"The caregiver worried because the toy looked {toy_cfg.style}, and bedtime should stay steady and calm.",
        ),
        QAItem(
            question=f"What helped {child.label} change from conflict to curiosity?",
            answer=f"A flashback to an older night helped {child.label} remember why the glow mattered, so the worry softened into curiosity.",
        ),
        QAItem(
            question=f"How did the story end for the child and the toy?",
            answer=f"The toy rested beside a soft lamp, and {child.label} fell asleep smiling while the room grew quiet.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    toy_cfg: Toy = world.facts["toy_cfg"]  # type: ignore[assignment]
    out = [
        QAItem(
            question="What does a night lamp do?",
            answer="A night lamp gives a small, soft light that helps a room feel less dark at bedtime.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to look, ask, and understand something better.",
        ),
    ]
    if toy_cfg.id == "shake_dim":
        out.append(QAItem(question="What is shaky dim light like?", answer="It is light that wobbles a little and glows softly, so it feels sleepy rather than bright."))
    if toy_cfg.id == "sweet_pl_dim":
        out.append(QAItem(question="What is sweet-pl-dim light like?", answer="It is a sweet, low light that feels warm, gentle, and cozy in a bedtime room."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", ""]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(room="bedroom", toy="shake_dim", child_name="Maya", child_type="girl", caregiver_type="mother"),
    StoryParams(room="nursery", toy="sweet_pl_dim", child_name="Owen", child_type="boy", caregiver_type="father"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with conflict, curiosity, and flashback.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--caregiver-type", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.toy is None or c[1] == args.toy)]
    if not combos:
        raise StoryError("(No valid bedtime-story combination matches the given options.)")
    room, toy = rng.choice(sorted(combos))
    toy_cfg = TOYS[toy]
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    caregiver_type = args.caregiver_type or rng.choice(["mother", "father"])
    return StoryParams(room=room, toy=toy, child_name=child_name, child_type=child_type, caregiver_type=caregiver_type)


def generate(params: StoryParams) -> StorySample:
    room = ROOMS[params.room]
    toy_cfg = TOYS[params.toy]
    world = tell(room, toy_cfg, params.child_name, params.child_type, params.caregiver_type)
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
        print(f"{len(asp_valid_combos())} compatible bedtime combos:")
        for room, toy in asp_valid_combos():
            print(f"  {room:8} {toy}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
