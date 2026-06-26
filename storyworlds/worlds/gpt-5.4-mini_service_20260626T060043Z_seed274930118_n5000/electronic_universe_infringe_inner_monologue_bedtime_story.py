#!/usr/bin/env python3
"""
storyworlds/worlds/electronic_universe_infringe_inner_monologue_bedtime_story.py
================================================================================

A bedtime-story world about a child, a glowing electronic object, and the
gentle rule that one tiny universe should not be infringed by a brighter one.

Premise:
- A child loves a small electronic star projector at bedtime.
- The projector makes a private "universe" of little lights on the ceiling.
- But if the light and sound are too strong, they infringe on sleep.

Tension:
- The child wants to keep the projector on.
- A parent worries it will make bedtime harder and disturb the room.

Turn:
- The child notices this in an inner monologue and realizes the room has two
  needs: a dreamy universe and quiet darkness.

Resolution:
- They dim the device, choose a softer mode, and the projector becomes a tiny
  calm sky rather than an intruder.

This script models the world with meters and memes, supports story generation,
Q&A, trace, JSON, and ASP parity verification.
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
    portable: bool = False
    electronic: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    place: str
    quiet: bool = True
    dark: bool = True
    universe_name: str = "little universe"


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    glow: float
    hum: float
    can_dim: bool
    soft_mode: str


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.room)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    parent_type: str
    setting: str
    device: str
    seed: Optional[int] = None


ROOMS = {
    "bedroom": Room(place="the bedroom", quiet=True, dark=True, universe_name="little universe"),
    "nursery": Room(place="the nursery", quiet=True, dark=True, universe_name="dream universe"),
    "shared_room": Room(place="the shared room", quiet=True, dark=True, universe_name="shared universe"),
}

DEVICES = {
    "projector": Device(
        id="projector",
        label="star projector",
        phrase="a small electronic star projector",
        glow=2.0,
        hum=1.0,
        can_dim=True,
        soft_mode="twinkle",
    ),
    "lamp": Device(
        id="lamp",
        label="night lamp",
        phrase="a little electronic night lamp",
        glow=1.2,
        hum=0.4,
        can_dim=True,
        soft_mode="soft glow",
    ),
    "tablet": Device(
        id="tablet",
        label="tablet",
        phrase="a tiny electronic tablet",
        glow=1.8,
        hum=0.8,
        can_dim=True,
        soft_mode="night reading",
    ),
}

CHILDREN = {
    "girl": ["Maya", "Luna", "Ivy", "Nora", "Mina"],
    "boy": ["Theo", "Eli", "Milo", "Finn", "Noah"],
}

TRAITS = ["sleepy", "curious", "gentle", "bright-eyed", "dreamy"]


def _m(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _v(e: Entity, key: str, amt: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amt


def _mv(e: Entity, key: str, amt: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amt


def _device_is_infringing(world: World, device: Device) -> bool:
    return device.glow > 1.0 or device.hum > 0.5


def _predict_infringe(world: World, child: Entity, device: Device) -> dict:
    sim = world.copy()
    _use_device(sim, sim.get(child.id), device, narrate=False)
    return {
        "infringe": sim.room.dark is False or sim.room.quiet is False,
        "sleepy": sim.get(child.id).memes.get("sleepy", 0.0),
    }


def _use_device(world: World, child: Entity, device: Device, narrate: bool = True) -> None:
    if device.id not in world.entities:
        world.add(Entity(
            id=device.id,
            kind="thing",
            type="device",
            label=device.label,
            phrase=device.phrase,
            electronic=True,
            portable=True,
        ))
    dev = world.get(device.id)
    _v(dev, "glow", device.glow)
    _v(dev, "hum", device.hum)
    _v(child, "wonder", 1.0)
    _v(child, "awake", 1.0)
    world.room.dark = False
    world.room.quiet = False if device.hum > 0.5 else world.room.quiet
    if narrate:
        world.say(f"{child.id} turned on {device.phrase}, and the ceiling bloomed with tiny stars.")


def _dim_device(world: World, child: Entity, device: Device, narrate: bool = True) -> None:
    dev = world.get(device.id)
    if device.can_dim:
        dev.meters["glow"] = max(0.0, dev.meters.get("glow", 0.0) - 1.2)
        dev.meters["hum"] = max(0.0, dev.meters.get("hum", 0.0) - 0.5)
        world.room.dark = True
        world.room.quiet = True
        _mv(child, "care", 1.0)
        if narrate:
            world.say(f"{child.id} dimmed it to a {device.soft_mode}, and the room grew soft again.")


def _reasonableness_gate(room: Room, device: Device) -> bool:
    return room.dark and room.quiet and device.electronic and device.can_dim


def build_story(world: World, child: Entity, parent: Entity, device: Device) -> None:
    world.say(f"{child.id} was a little {child.type} who loved bedtime and the quiet after the lights went out.")
    world.say(f"{child.pronoun().capitalize()} also loved {device.phrase}, because it made a whole {world.room.universe_name} on the ceiling.")
    world.say(f"At the end of the day, {parent.label} tucked the blanket to the chin and said the room was ready for sleep.")

    world.para()
    world.say(f"That night, {child.id} held the {device.label} close and listened to the soft buzz of its little light.")
    _mv(child, "want", 1.0)
    _use_device(world, child, device, narrate=True)

    if _device_is_infringing(world, device):
        world.say(f"But the bright glow and tiny hum felt like they might infringe on the room's sleepy peace.")
        _mv(child, "worry", 1.0)
        _mv(parent, "concern", 1.0)
        world.say(f'"If it stays this bright, it could infringe on bedtime," {parent.pronoun("subject")} whispered, so the child listened carefully.')

    world.para()
    child_thought = (
        f"{child.id} thought, 'I want my little universe, but I do not want to crowd out the sleep in this room.'"
    )
    world.say(child_thought)
    _mv(child, "thoughtful", 1.0)

    if _predict_infringe(world, child, device)["infringe"]:
        world.say(f"{child.id} knew the answer before anyone else did: the universe could stay, if it became smaller and gentler.")
        _dim_device(world, child, device, narrate=True)
        world.say(f"Then the stars only twinkled, and the hum faded to almost nothing.")
        _mv(child, "relief", 1.0)
        _mv(parent, "relief", 1.0)

    world.para()
    world.say(f"{child.id} curled under the blanket and watched the tiny stars drift over the ceiling like friendly fireflies.")
    world.say(f"The little electronic universe still shone, but it no longer infringed on the hush of bedtime.")
    world.say(f"And soon enough, {child.pronoun('subject')} was asleep with a calm smile, while the room kept its soft and gentle dark.")


def tell(setting: Room, device: Device, child_name: str = "Maya", child_type: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, label=child_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom" if parent_type == "mother" else "dad"))
    world.add(Entity(
        id=device.id,
        kind="thing",
        type="device",
        label=device.label,
        phrase=device.phrase,
        electronic=True,
        portable=True,
    ))
    build_story(world, child, parent, device)
    world.facts.update(child=child, parent=parent, device=device, room=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    device = f["device"]
    return [
        f'Write a bedtime story for a child about an electronic {device.label} and a tiny universe on the ceiling.',
        f"Tell a gentle story where {child.id} wants to keep the {device.label} on, but the light might infringe on bedtime.",
        f"Write a simple inner-monologue bedtime story about choosing a softer way to enjoy a glowing electronic toy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    device = f["device"]
    room = f["room"]
    return [
        QAItem(
            question=f"What did {child.id} love about the {device.label}?",
            answer=f"{child.id} loved that the {device.label} made a tiny {room.universe_name} on the ceiling.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the light?",
            answer=f"{parent.label} worried the bright glow and small hum might infringe on the room's bedtime peace.",
        ),
        QAItem(
            question=f"What did {child.id} realize in the inner monologue?",
            answer=f"{child.id} realized the little universe could stay, but it had to become softer and smaller so sleep could still come.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the device dimmed to a gentle twinkle and {child.id} asleep under a calm ceiling of stars.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is electronic energy used for in a device?",
            answer="Electronic energy helps a device light up, make sounds, or do other jobs when it is switched on.",
        ),
        QAItem(
            question="What is a universe in a story like this?",
            answer="In a bedtime story like this, a universe can mean a tiny imagined sky or world filled with stars and wonder.",
        ),
        QAItem(
            question="What does it mean to infringe on something?",
            answer="To infringe on something means to crowd it, disturb it, or push into its space in an unwelcome way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"room: {world.room.place} dark={world.room.dark} quiet={world.room.quiet}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.electronic:
            bits.append("electronic=True")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {"bedroom": ROOMS["bedroom"], "nursery": ROOMS["nursery"], "shared_room": ROOMS["shared_room"]}
DEV_ORDER = ["projector", "lamp", "tablet"]
CURATED = [
    StoryParams(child_name="Maya", child_type="girl", parent_type="mother", setting="bedroom", device="projector"),
    StoryParams(child_name="Theo", child_type="boy", parent_type="father", setting="nursery", device="lamp"),
    StoryParams(child_name="Luna", child_type="girl", parent_type="mother", setting="shared_room", device="tablet"),
]


ASP_RULES = r"""
device(D) :- device_name(D).
electronic(D) :- electronic_device(D).
can_dim(D) :- dimmable(D).

infringe(R, D) :- room(R), device(D), glow(D, G), G > 1, quiet_need(R).
infringe(R, D) :- room(R), device(D), hum(D, H), H > 0.5, sleep_need(R).

soften(D) :- can_dim(D), electronic(D).
valid_story(R, D) :- room(R), device(D), electronic(D), can_dim(D), soft_space(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid, room in SETTINGS.items():
        lines.append(asp.fact("room", rid))
        if room.quiet:
            lines.append(asp.fact("quiet_need", rid))
        if room.dark:
            lines.append(asp.fact("sleep_need", rid))
        lines.append(asp.fact("soft_space", rid))
    for did, d in DEVICES.items():
        lines.append(asp.fact("device_name", did))
        lines.append(asp.fact("electronic_device", did))
        if d.can_dim:
            lines.append(asp.fact("dimmable", did))
        lines.append(asp.fact("glow", did, int(d.glow * 10)))
        lines.append(asp.fact("hum", did, int(d.hum * 10)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(r, d) for r in SETTINGS for d, dev in DEVICES.items() if _reasonableness_gate(SETTINGS[r], dev)}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: an electronic universe that must not infringe on sleep.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.setting and args.device:
        room, dev = SETTINGS[args.setting], DEVICES[args.device]
        if not _reasonableness_gate(room, dev):
            raise StoryError("No story: this device setting is not a gentle bedtime fit.")
    setting = args.setting or rng.choice(list(SETTINGS))
    device = args.device or rng.choice(DEV_ORDER)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILDREN[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(child_name=name, child_type=gender, parent_type=parent, setting=setting, device=device)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], DEVICES[params.device], params.child_name, params.child_type, params.parent_type)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print("Compatible (room, device) combos:\n")
        for room, device in sorted(set(asp.atoms(model, "valid_story"))):
            print(f"  {room:12} {device}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
