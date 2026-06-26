#!/usr/bin/env python3
"""
storyworlds/worlds/pin_caricature_transformation_humor_detective_story.py
=========================================================================

A small detective-style story world about a curious pin, a funny caricature,
and a transformation that changes what the characters can see.

Premise:
- A child detective investigates a tiny missing pin in a cheerful art room.
- A caricature artist has drawn a silly picture that makes everyone laugh.
- The clue trail leads to a transformation: the pin is moved from a coat to a
  costume board, where it becomes part of a new look.

Story shape:
- Setup: the detective notices the pin and the caricature.
- Tension: the wrong owner is accused because the clue is small and confusing.
- Turn: the detective follows practical clues in the room.
- Resolution: the pin is returned and the caricature is updated; the scene
  transforms from suspicion into laughter.

This file follows the Storyworld contract:
- stdlib-only script
- StoryParams, registries, parser, resolve_params, generate, emit, main
- eager import of results
- lazy import of asp inside ASP helpers
- inline ASP twin and a Python reasonableness gate
- QA and trace support
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
    kind: str = "thing"          # character | thing
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
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    place: str = "the art room"
    clue_places: set[str] = field(default_factory=lambda: {"table", "board", "coat rack"})
    has_mirror: bool = True
    has_ink: bool = True


@dataclass
class Pin:
    label: str
    phrase: str
    location: str
    transform_to: str
    sparkle: bool = True


@dataclass
class Caricature:
    subject: str
    style: str = "funny"
    size: str = "big"
    grin: str = "huge"
    note: str = "a silly clue"


@dataclass
class StoryParams:
    room: str
    pin: str
    caricature: str
    name: str
    gender: str
    detective: str
    artist: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _say_cap(world: World, s: str) -> None:
    world.say(s[:1].upper() + s[1:] if s else s)


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes.get("revealed", 0) >= THRESHOLD and e.meters.get("focus", 0) >= THRESHOLD:
            sig = ("transform", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["relief"] = e.memes.get("relief", 0) + 1
            out.append(f"{e.id} suddenly looked different in the bright light.")
    return out


def _r_laughter(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes.get("humor", 0) >= THRESHOLD and e.memes.get("relief", 0) >= THRESHOLD:
            sig = ("laugh", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"{e.id} laughed, and the room felt lighter.")
    return out


RULES = [
    ("transformation", _r_transformation),
    ("humor", _r_laughter),
]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    for s in produced:
        world.say(s)
    return produced


def pin_reasonable(pin: Pin, caricature: Caricature) -> bool:
    return pin.label == "pin" and "funny" in caricature.style


def predict_story(world: World, detective: Entity, pin: Entity) -> dict:
    sim = world.copy()
    sim.get(detective.id).meters["focus"] = 1
    sim.get(pin.id).memes["revealed"] = 1
    propagate(sim)
    return {
        "solved": sim.get(pin.id).owner == detective.id or sim.get(pin.id).owner == sim.facts["artist"].id,
        "relief": sum(e.memes.get("relief", 0) for e in sim.entities.values()),
    }


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world about a pin, a caricature, and a transformation.")
    ap.add_argument("--room", choices=ROOMS.keys())
    ap.add_argument("--pin", choices=PINS.keys())
    ap.add_argument("--caricature", choices=CARICATURES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--detective")
    ap.add_argument("--artist")
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for pid, p in PINS.items():
        lines.append(asp.fact("pin", pid))
        lines.append(asp.fact("located_at", pid, p.location))
    for cid, c in CARICATURES.items():
        lines.append(asp.fact("caricature", cid))
        lines.append(asp.fact("style", cid, c.style))
    return "\n".join(lines)


ASP_RULES = r"""
relevant_pin(P) :- pin(P), located_at(P, coat_rack).
funny_story(C) :- caricature(C), style(C, funny).
compatible(P, C) :- relevant_pin(P), funny_story(C).
#show relevant_pin/1.
#show funny_story/1.
#show compatible/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_relevant() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show relevant_pin/1."))
    return sorted(set(asp.atoms(model, "relevant_pin")))


def asp_compatible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = {(pid,) for pid, p in PINS.items() if p.location == "coat_rack"}
    cl = set(asp_relevant())
    if py != cl:
        print("MISMATCH between Python and ASP relevant-pin sets:")
        print("python:", sorted(py))
        print("clingo:", sorted(cl))
        return 1
    print(f"OK: Python and ASP agree on relevant pins ({len(py)}).")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.pin and args.caricature:
        if not pin_reasonable(PINS[args.pin], CARICATURES[args.caricature]):
            raise StoryError("That pin and caricature do not make a reasonable detective story here.")
    rooms = [r for r in ROOMS if args.room in (None, r)]
    pins = [p for p in PINS if args.pin in (None, p)]
    cs = [c for c in CARICATURES if args.caricature in (None, c)]
    if not rooms or not pins or not cs:
        raise StoryError("No valid combination matches the given options.")
    room = rng.choice(rooms)
    pin = rng.choice(pins)
    caricature = rng.choice(cs)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    detective = args.detective or "Detective"
    artist = args.artist or "Ari"
    return StoryParams(room=room, pin=pin, caricature=caricature, name=name, gender=gender, detective=detective, artist=artist)


def generate(params: StoryParams) -> StorySample:
    world = World(ROOMS[params.room])
    detective = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    artist = world.add(Entity(id=params.artist, kind="character", type="artist", label=params.artist))
    pin_cfg = PINS[params.pin]
    caricature_cfg = CARICATURES[params.caricature]
    pin = world.add(Entity(
        id="pin",
        type="pin",
        label="pin",
        phrase=pin_cfg.phrase,
        owner=artist.id,
        caretaker=artist.id,
    ))
    caricature = world.add(Entity(
        id="caricature",
        type="caricature",
        label="caricature",
        phrase=f"a {caricature_cfg.style} caricature of {caricature_cfg.subject}",
        owner=artist.id,
        caretaker=artist.id,
    ))

    world.facts.update(detective=detective, artist=artist, pin=pin, caricature=caricature, params=params)

    _say_cap(world, f"{detective.id} was a little detective who loved tiny clues in {world.room.place}.")
    world.say(f"{detective.pronoun().capitalize()} noticed {pin.phrase} near the coat rack and a {caricature_cfg.style} caricature on the wall.")
    world.say(f"{artist.id} had drawn the caricature with a huge grin, and the funny picture made the whole room feel playful.")
    world.para()

    world.say(f"Then the pin disappeared from sight, and {detective.id} thought the wrong person might have moved it.")
    detective.memes["worry"] = detective.memes.get("worry", 0) + 1
    pin.meters["hidden"] = 1
    world.say(f"{detective.id} looked at the table, the board, and the coat rack like a careful clue hunter.")
    world.para()

    world.say(f"{detective.id} noticed a small shine on the costume board and a paint dot under the clip.")
    detective.meters["focus"] = 1
    pin.memes["revealed"] = 1
    pin.owner = artist.id
    pin.location = "board"
    caricature.memes["humor"] = 1
    caricature.memes["revealed"] = 1
    if not propagate(world):
        pass

    world.say(f"That clue showed the pin had been used to hold the caricature in place during the joke drawing.")
    world.say(f"{artist.id} smiled and moved the pin back to the coat rack, where it belonged.")
    detective.memes["relief"] = detective.memes.get("relief", 0) + 1
    world.para()

    world.say(f"Now the caricature looked even sillier with its missing corner fixed, and {detective.id} laughed at the transformed scene.")
    world.say(f"The little mystery ended with the pin safe, the caricature finished, and the art room bright again.")

    world.facts["solved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f"Write a child-friendly detective story about a {p.gender} detective finding a {p.pin} in {world.room.place}.",
        f"Tell a short mystery with a {p.caricature} caricature, a tiny clue, and a funny transformation.",
        "Write a gentle detective story where the clue is small, the mood is funny, and the ending explains what changed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    detective: Entity = f["detective"]
    artist: Entity = f["artist"]
    pin: Entity = f["pin"]
    caricature: Entity = f["caricature"]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {detective.id}, who carefully looked for clues in {params.room}.",
        ),
        QAItem(
            question=f"What funny thing did the artist make?",
            answer=f"The artist made a caricature, a silly drawing with a big grin and a playful look.",
        ),
        QAItem(
            question=f"What happened to the pin?",
            answer=f"The pin was found on the costume board and then moved back to the coat rack where it belonged.",
        ),
        QAItem(
            question=f"Why did the detective laugh at the end?",
            answer=f"The detective laughed because the mystery was solved, the pin was safe, and the caricature made the room feel funny instead of tense.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks carefully for clues to solve a mystery.",
        ),
        QAItem(
            question="What is a caricature?",
            answer="A caricature is a funny drawing that makes some parts look extra big or silly on purpose.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="A transformation is a change from one way of being or looking into another.",
        ),
        QAItem(
            question="Why can a pin be useful?",
            answer="A pin can hold paper, cloth, or a picture in place so it does not slip away.",
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, _ in RULES})}")
    return "\n".join(lines)


ROOMS = {
    "art_room": Room(place="the art room"),
    "gallery": Room(place="the little gallery"),
    "studio": Room(place="the paint studio"),
}

PINS = {
    "safety_pin": Pin(label="pin", phrase="a shiny safety pin", location="coat_rack", transform_to="board"),
    "badge_pin": Pin(label="pin", phrase="a bright badge pin", location="coat_rack", transform_to="board"),
    "clip_pin": Pin(label="pin", phrase="a small clip pin", location="coat_rack", transform_to="board"),
}

CARICATURES = {
    "laughing_cat": Caricature(subject="a cat", style="funny"),
    "big_nose_uncle": Caricature(subject="an uncle", style="very funny"),
    "silly_robot": Caricature(subject="a robot", style="funny"),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ava", "Zoe", "Lily", "Ella", "Maya"]
BOY_NAMES = ["Finn", "Leo", "Theo", "Noah", "Eli", "Ben", "Max", "Owen"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for pin_id, pin in PINS.items():
            for caricature_id, caricature in CARICATURES.items():
                if pin_reasonable(pin, caricature):
                    combos.append((room, pin_id, caricature_id))
    return combos


def explain_rejection(pin: Pin, caricature: Caricature) -> str:
    return (
        f"(No story: this world wants a funny detective turn, but {pin.phrase} and "
        f"{caricature.subject} do not give a clear, child-friendly clue chain.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.pin and args.caricature:
        if not pin_reasonable(PINS[args.pin], CARICATURES[args.caricature]):
            raise StoryError(explain_rejection(PINS[args.pin], CARICATURES[args.caricature]))
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.pin is None or c[1] == args.pin)
              and (args.caricature is None or c[2] == args.caricature)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, pin, caricature = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    detective = args.detective or "Detective"
    artist = args.artist or "Ari"
    return StoryParams(room=room, pin=pin, caricature=caricature, name=name, gender=gender, detective=detective, artist=artist)


def asp_verify_and_models() -> int:
    return asp_verify()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_show_program() -> str:
    return asp_program("#show relevant_pin/1.\n#show funny_story/1.\n#show compatible/2.")


def generate_story(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_show_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        print(f"{len(asp.atoms(model, 'compatible'))} compatible pin/caricature pairs")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for room, pin, caricature in valid_combos():
            params = StoryParams(
                room=room,
                pin=pin,
                caricature=caricature,
                name="Mia",
                gender="girl",
                detective="Detective",
                artist="Ari",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.pin} in {p.room} with {p.caricature}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
