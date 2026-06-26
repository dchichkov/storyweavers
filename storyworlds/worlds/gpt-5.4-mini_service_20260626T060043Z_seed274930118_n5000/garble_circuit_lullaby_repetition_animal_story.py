#!/usr/bin/env python3
"""
storyworlds/worlds/garble_circuit_lullaby_repetition_animal_story.py
=====================================================================

A small animal-story world about a soft lullaby, a garbled circuit, and a
repeating little problem that can be fixed by patient hands.

Seed idea:
- An animal child loves a lullaby player.
- A loose circuit makes the tune garble and repeat in a funny, wrong way.
- The child keeps trying again and again, but the sound worsens.
- A helper animal opens the toy, resets the circuit, and the lullaby comes back clear.

The world is intentionally tiny and constraint-driven:
- physical meters: sound quality, circuit damage, dirt, patience, repair progress
- emotional memes: delight, worry, frustration, relief, affection

The prose is generated from world state, not from a frozen template.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["sound_clear", "garble", "repeat", "repair", "dirt"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "frustration", "relief", "love", "patience"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    name: str
    indoor: bool = True


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    base_clear: float
    base_garble: float
    circuit_parts: list[str] = field(default_factory=list)


@dataclass
class Fix:
    id: str
    label: str
    verb: str
    result_line: str
    improves: float


class World:
    def __init__(self, place: Place) -> None:
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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "nest": Place("the nest", indoor=True),
    "burrow": Place("the burrow", indoor=True),
    "cabin": Place("the little cabin", indoor=True),
    "garden": Place("the garden bench", indoor=False),
}

ANIMAL_TYPES = ["mouse", "rabbit", "kitten", "duckling", "foxling", "bear cub"]
NAMES = {
    "mouse": ["Milo", "Mimi", "Nibbles"],
    "rabbit": ["Ruby", "Pip", "Nora"],
    "kitten": ["Poppy", "Luna", "Toby"],
    "duckling": ["Daisy", "Ducky", "Moss"],
    "foxling": ["Finn", "Fia", "Tavi"],
    "bear cub": ["Bean", "Bramble", "Mabel"],
}
TRAITS = ["small", "gentle", "curious", "sleepy", "brave", "playful"]

DEVICES = {
    "lullaby_box": Device(
        id="lullaby_box",
        label="lullaby box",
        phrase="a tiny lullaby box with a singing button",
        base_clear=1.0,
        base_garble=0.0,
        circuit_parts=["button", "wire", "speaker"],
    ),
    "music_shell": Device(
        id="music_shell",
        label="music shell",
        phrase="a smooth music shell that hummed softly",
        base_clear=1.0,
        base_garble=0.0,
        circuit_parts=["shell", "wire", "reed"],
    ),
    "night_chime": Device(
        id="night_chime",
        label="night chime",
        phrase="a little night chime that could whisper tunes",
        base_clear=1.0,
        base_garble=0.0,
        circuit_parts=["switch", "coil", "speaker"],
    ),
}

FIXES = {
    "wipe": Fix("wipe", "a soft cloth", "wipe the buttons clean", "The buttons could breathe again.", 0.6),
    "reseat": Fix("reseat", "careful paws", "re-seat the loose wire", "The wire clicked back into place.", 1.0),
    "tap": Fix("tap", "patient paws", "tap the side once and then stop", "The circuit settled instead of stuttering.", 0.4),
    "rest": Fix("rest", "quiet paws", "rest and let the toy cool down", "The toy stopped repeating itself.", 0.5),
}


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    animal: str
    name: str
    trait: str
    device: str
    fix: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_story(params: StoryParams) -> bool:
    return params.place in PLACES and params.animal in ANIMAL_TYPES and params.device in DEVICES and params.fix in FIXES


def explain_invalid(reason: str) -> str:
    return f"(No story: {reason})"


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.animal,
        traits=["small", params.trait],
    ))
    helper_type = "mother" if params.animal in {"mouse", "rabbit", "kitten", "duckling"} else "father"
    helper_name = "Marigold" if helper_type == "mother" else "Bram"
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        traits=["gentle", "steady"],
    ))
    device = world.add(Entity(
        id=params.device,
        type="toy",
        label=DEVICES[params.device].label,
        phrase=DEVICES[params.device].phrase,
        caretaker=helper.id,
    ))
    world.facts.update(child=child, helper=helper, device=device, params=params)
    return world


def initial_state(world: World) -> None:
    device = world.get(world.facts["device"].id)
    device.meters["sound_clear"] = 1.0
    device.meters["garble"] = 0.0
    device.meters["repeat"] = 0.0


def worsen_circuit(world: World, child: Entity, device: Entity) -> None:
    if ("press", child.id) in world.fired:
        return
    world.fired.add(("press", child.id))
    child.memes["joy"] += 1
    child.memes["frustration"] += 1
    device.meters["sound_clear"] = max(0.0, device.meters["sound_clear"] - 0.3)
    device.meters["garble"] += 0.7
    device.meters["repeat"] += 0.5
    world.say(f"{child.id} pressed the lullaby button again, and the tune came out a little more garbled.")


def gather_worry(world: World, child: Entity, helper: Entity, device: Entity) -> None:
    if device.meters["garble"] >= THRESHOLD and ("worry", child.id) not in world.fired:
        world.fired.add(("worry", child.id))
        child.memes["worry"] += 1
        helper.memes["worry"] += 1
        world.say(f"{child.id} tilted {child.pronoun('possessive')} head. The song was starting to repeat in a silly, broken way.")


def offer_fix(world: World, helper: Entity, child: Entity, device: Entity, fix: Fix) -> None:
    if ("offer", fix.id) in world.fired:
        return
    world.fired.add(("offer", fix.id))
    helper.memes["love"] += 1
    world.say(
        f"{helper.id} listened, smiled, and said they could {fix.verb}. "
        f'"Let’s make the circuit calm down," {helper.pronoun()} said.'
    )


def repair(world: World, helper: Entity, child: Entity, device: Entity, fix: Fix) -> None:
    if ("repair", fix.id) in world.fired:
        return
    world.fired.add(("repair", fix.id))
    helper.memes["patience"] += 1
    device.meters["repair"] += fix.improves
    device.meters["garble"] = max(0.0, device.meters["garble"] - fix.improves)
    device.meters["repeat"] = max(0.0, device.meters["repeat"] - fix.improves / 2)
    device.meters["sound_clear"] = min(1.0, device.meters["sound_clear"] + fix.improves)
    if fix.id == "wipe":
        device.meters["dirt"] = 0.0
    world.say(fix.result_line)


def resolution_line(world: World, child: Entity, helper: Entity, device: Entity) -> None:
    if device.meters["sound_clear"] >= 0.9 and ("resolve", device.id) not in world.fired:
        world.fired.add(("resolve", device.id))
        child.memes["relief"] += 1
        helper.memes["relief"] += 1
        world.say(
            f"Then the lullaby came back clear and warm. {child.id} leaned close, "
            f"and the song sounded like a soft blanket after a long day."
        )


def tell(params: StoryParams) -> World:
    if not valid_story(params):
        raise StoryError(explain_invalid("the requested place, animal, device, or fix does not fit this world"))
    world = make_world(params)
    child = world.facts["child"]
    helper = world.facts["helper"]
    device = world.facts["device"]
    fix = FIXES[params.fix]
    initial_state(world)

    world.say(
        f"{child.id} was a {params.trait} little {child.type} who loved the {device.label_word}."
    )
    world.say(
        f"The {device.label_word} played a lullaby that made {child.id}'s eyes feel sleepy and safe."
    )
    world.para()

    world.say(
        f"One evening at {world.place.name}, {child.id} pressed the button again and again, because {child.id} liked the same little song."
    )
    worsen_circuit(world, child, device)
    worsen_circuit(world, child, device)
    worsen_circuit(world, child, device)
    gather_worry(world, child, helper, device)
    world.say(
        f"But each press made the circuit garble a bit more, and the lullaby began to repeat in a chopped-up way."
    )
    world.para()

    offer_fix(world, helper, child, device, fix)
    if fix.id in {"reseat", "wipe", "tap", "rest"}:
        repair(world, helper, child, device, fix)
    if fix.id == "rest" and device.meters["garble"] > 0.2:
        # Rest alone isn't enough in this world; the helper follows up with a reseat.
        extra = FIXES["reseat"]
        repair(world, helper, child, device, extra)
    resolution_line(world, child, helper, device)

    world.facts.update(
        child=child,
        helper=helper,
        device=device,
        fix=fix,
        resolved=device.meters["sound_clear"] >= 0.9,
        garbled=device.meters["garble"] > 0.2,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    device = f["device"]
    return [
        f'Write a short animal story about {child.id}, a {child.type}, whose {device.label_word} starts to garble.',
        f'Tell a gentle story for a young child where a lullaby repeats because a circuit is loose, then gets fixed.',
        f'Write a cozy story with the words "garble", "circuit", and "lullaby" that ends with the music sounding clear again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    device = f["device"]
    params = f["params"]
    return [
        QAItem(
            question=f"Who loved the {device.label_word} in the story?",
            answer=f"{child.id}, a little {child.type}, loved the {device.label_word} because it played a sleepy lullaby.",
        ),
        QAItem(
            question=f"What went wrong with the song at {world.place.name}?",
            answer=f"The circuit got loose, so the lullaby began to garble and repeat in a broken little loop.",
        ),
        QAItem(
            question=f"Who helped fix the {device.label_word}?",
            answer=f"{helper.id} helped by patiently repairing the circuit and calming the toy down.",
        ),
    ] + (
        [QAItem(
            question=f"How did the story end after the {params.fix} fix?",
            answer="The song came back clear and warm, and the little animal could listen with a relieved smile.",
        )] if world.facts.get("resolved") else []
    )


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a circuit?",
            answer="A circuit is a path that lets electricity move through a device so it can work.",
        ),
        QAItem(
            question="What does garble mean?",
            answer="If sound garbles, it comes out mixed up, fuzzy, or hard to understand.",
        ),
        QAItem(
            question="What is a lullaby?",
            answer="A lullaby is a soft, gentle song that helps someone feel sleepy and safe.",
        ),
        QAItem(
            question="Why can repeating the same button press sometimes make a toy act worse?",
            answer="If a button or wire is already loose, pressing it again can keep the problem going instead of fixing it.",
        ),
    ]


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
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A device is garbled when the circuit is loose enough.
garbled(D) :- device(D), loose_circuit(D), not fixed(D).

% Repetition happens when the same tune is pressed again while garbled.
repeating(D) :- garbled(D), pressed_more_than_once(D).

% A fix is reasonable when it can reduce garble and restore clarity.
helpful_fix(F,D) :- fix(F), reduces_garble(F), device(D), garbled(D).

% A valid story needs a garbled device, a helper, and a fix that can restore it.
valid_story(P,A,D,F) :- place(P), animal(A), device(D), fix(F),
                        garbled(D), helpful_fix(F,D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for a in ANIMAL_TYPES:
        lines.append(asp.fact("animal", a))
    for did in DEVICES:
        lines.append(asp.fact("device", did))
        lines.append(asp.fact("loose_circuit", did))
        lines.append(asp.fact("pressed_more_than_once", did))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        if fix.improves > 0.0:
            lines.append(asp.fact("reduces_garble", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    python_set = {(p, a, d, f) for p in PLACES for a in ANIMAL_TYPES for d in DEVICES for f in FIXES}
    if not atoms:
        print("MISMATCH: ASP produced no valid stories.")
        return 1
    print(f"OK: ASP produced {len(atoms)} story patterns.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a lullaby, a garbled circuit, and a gentle repair."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMAL_TYPES)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(PLACES))
    animal = args.animal or rng.choice(ANIMAL_TYPES)
    device = args.device or rng.choice(list(DEVICES))
    fix = args.fix or rng.choice(list(FIXES))
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice(NAMES[animal])
    params = StoryParams(place=place, animal=animal, name=name, trait=trait, device=device, fix=fix)
    if not valid_story(params):
        raise StoryError(explain_invalid("invalid combination"))
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        meters = {k: round(v, 3) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 3) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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
    StoryParams(place="nest", animal="mouse", name="Milo", trait="curious", device="lullaby_box", fix="reseat"),
    StoryParams(place="burrow", animal="rabbit", name="Ruby", trait="gentle", device="music_shell", fix="wipe"),
    StoryParams(place="cabin", animal="kitten", name="Luna", trait="sleepy", device="night_chime", fix="tap"),
    StoryParams(place="garden", animal="duckling", name="Daisy", trait="playful", device="lullaby_box", fix="rest"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid story patterns:")
        for row in stories:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.animal} at {p.place} with {p.device} / {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
