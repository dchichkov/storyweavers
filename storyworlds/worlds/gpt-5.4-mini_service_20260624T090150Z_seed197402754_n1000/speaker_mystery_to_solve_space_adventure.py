#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/speaker_mystery_to_solve_space_adventure.py
=============================================================================================================

A small story world for a Space Adventure style mystery: a crew hears a strange
speaker signal on a starship, looks for clues, and solves the mystery.

The story is driven by a tiny world model with physical meters and emotional
memes:
- physical meters: noise, damage, dust, power, found
- emotional memes: worry, curiosity, relief, pride, teamwork

The seed word is "speaker", and the central premise is "mystery to solve" in a
child-facing space adventure setting.
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

    def __post_init__(self) -> None:
        for k in ["noise", "damage", "dust", "power", "found"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "curiosity", "relief", "pride", "teamwork"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    place: str = "the starship"
    rooms: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
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
        clone = World(self.ship)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    name: str
    role: str
    companion: str
    ship: str
    room: str
    mystery: str
    seed: Optional[int] = None


ROOMS = {
    "bridge": "the bridge",
    "hall": "the long hall",
    "cargo": "the cargo bay",
    "engine": "the engine room",
    "observatory": "the observatory",
}

MYSTERIES = {
    "speaker_static": {
        "label": "speaker",
        "phrase": "a crackly speaker",
        "noise": "static",
        "cause": "a loose sparkly sticker had drifted over the speaker grille",
        "clue": "the sticker was stuck to the vent pipe nearby",
        "fix": "peel the sticker away and clean the grille",
    },
    "speaker_echo": {
        "label": "speaker",
        "phrase": "a round ship speaker",
        "noise": "echo",
        "cause": "the speaker was bouncing sound off a shiny metal wall",
        "clue": "the wall was polished like a mirror",
        "fix": "move the speaker a little and point it at a softer wall",
    },
    "speaker_beep": {
        "label": "speaker",
        "phrase": "the wall speaker",
        "noise": "beep",
        "cause": "a tiny helper drone was tapping the alert button by mistake",
        "clue": "little metal footprints led to the control panel",
        "fix": "find the drone and guide it away from the button",
    },
}

SHIP_NAMES = ["Comet Fox", "Star Nest", "Moon Kite", "Rocket Bean", "Little Orbit"]
NAMES = ["Ari", "Nova", "Milo", "Luna", "Kai", "Zia", "Rin", "Tala"]
ROLES = ["pilot", "captain", "engineer", "navigator", "scout"]
COMPANIONS = ["robot", "friend", "helper", "mate"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_noise(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.kind != "thing" or e.label != "speaker":
            continue
        if e.meters["noise"] < THRESHOLD:
            continue
        sig = ("noise", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("hero").memes["worry"] += 1
        out.append("The strange sound made everyone listen closely.")
    return out


def _r_find(world: World) -> list[str]:
    out = []
    if world.facts.get("clue_seen") and world.facts.get("mystery_solved"):
        return out
    if world.facts.get("clue_seen"):
        world.get("hero").meters["found"] += 1
        world.get("hero").memes["curiosity"] += 1
        out.append("That clue led them closer to the answer.")
    return out


RULES = [Rule("noise", _r_noise), Rule("find", _r_find)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_resolution(world: World) -> bool:
    return bool(world.facts.get("clue_seen")) and bool(world.facts.get("fix_ready"))


def setup_story(world: World, hero: Entity, companion: Entity, speaker: Entity, mystery: dict) -> None:
    world.say(
        f"{hero.id} was a brave {hero.type} aboard {world.ship.name}, a small ship with bright windows."
    )
    world.say(
        f"{hero.id} liked exploring with {companion.label}, and both of them trusted the hum of the engines."
    )
    world.say(
        f"One day, they heard {mystery['phrase']} making {mystery['noise']} sounds from {world.ship.place}."
    )
    speaker.meters["noise"] += 1


def search_scene(world: World, hero: Entity, companion: Entity, mystery: dict) -> None:
    world.para()
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} held up a little hand light and {companion.label} floated beside {hero.pronoun('object')}."
    )
    world.say(
        f'They went to {world.ship.place} and looked near {world.facts["room"]}.'
    )
    world.say(
        f"At last, they spotted a clue: {mystery['clue']}."
    )
    world.facts["clue_seen"] = True
    propagate(world, narrate=True)


def solve_scene(world: World, hero: Entity, companion: Entity, speaker: Entity, mystery: dict) -> None:
    world.para()
    world.say(
        f"{hero.id} smiled and said the mystery was not scary at all."
    )
    world.say(
        f"They followed the clue and found out that {mystery['cause']}."
    )
    world.say(
        f"Together, they {mystery['fix']}."
    )
    speaker.meters["noise"] = 0
    speaker.meters["damage"] = 0
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    hero.memes["teamwork"] += 1
    companion.memes["relief"] += 1
    world.facts["fix_ready"] = True
    world.facts["mystery_solved"] = True
    if predict_resolution(world):
        world.say(
            f"After that, the speaker was quiet again, and the ship felt calm and safe."
        )


def tell(params: StoryParams) -> World:
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery choice.")
    if params.room not in ROOMS:
        raise StoryError("Unknown room choice.")
    ship = Ship(name=params.ship, place=ROOMS[params.room], rooms=list(ROOMS.values()))
    world = World(ship)
    mystery = MYSTERIES[params.mystery]
    hero = world.add(Entity(id="hero", kind="character", type=params.role, label=params.name))
    companion = world.add(Entity(id="companion", kind="character", type="robot", label=params.companion))
    speaker = world.add(Entity(id="speaker", kind="thing", type="thing", label="speaker", phrase=mystery["phrase"]))
    world.facts.update(hero=hero, companion=companion, speaker=speaker, mystery=mystery, room=ROOMS[params.room])

    setup_story(world, hero, companion, speaker, mystery)
    search_scene(world, hero, companion, mystery)
    solve_scene(world, hero, companion, speaker, mystery)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for mystery in MYSTERIES:
            combos.append((room, mystery, "speaker"))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for r in ROOMS:
        lines.append(asp.fact("room", r))
    for m, data in MYSTERIES.items():
        lines.append(asp.fact("mystery", m))
        lines.append(asp.fact("speaker_label", m, data["label"]))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Room, Mystery, speaker) :- room(Room), mystery(Mystery).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure mystery story world with a speaker clue.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--companion", choices=["Bot", "Pip", "Glint", "Moss"])
    ap.add_argument("--ship", choices=SHIP_NAMES)
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--mystery", choices=MYSTERIES)
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
    room = args.room or rng.choice(list(ROOMS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    companion = args.companion or rng.choice(["Bot", "Pip", "Glint", "Moss"])
    ship = args.ship or rng.choice(SHIP_NAMES)
    return StoryParams(name=name, role=role, companion=companion, ship=ship, room=room, mystery=mystery)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m = f["mystery"]
    return [
        "Write a short space adventure where a crew hears a strange speaker sound and solves the mystery.",
        f"Tell a child-friendly story about {f['hero'].label}, {f['companion'].label}, and a speaker that makes {m['noise']}.",
        f"Write a simple ship story that ends with the speaker being fixed after the clue is found in {f['room']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    m = f["mystery"]
    return [
        QAItem(
            question=f"What mystery did {hero.label} and {companion.label} hear on the ship?",
            answer=f"They heard a strange speaker sound that turned into a mystery to solve.",
        ),
        QAItem(
            question=f"What clue helped them solve the speaker mystery?",
            answer=f"The clue was that {m['clue']}.",
        ),
        QAItem(
            question=f"What fixed the speaker at the end?",
            answer=f"They solved the mystery by following the clue and then {m['fix']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a speaker on a ship?",
            answer="A speaker is a device that lets a ship play voices, beeps, or alerts so the crew can hear them.",
        ),
        QAItem(
            question="Why do space crews use clues?",
            answer="Space crews use clues to figure out what is happening when something strange or unexpected appears.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story q&a ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world q&a ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(name="Ari", role="pilot", companion="Bot", ship="Comet Fox", room="bridge", mystery="speaker_static"),
    StoryParams(name="Nova", role="engineer", companion="Pip", ship="Moon Kite", room="cargo", mystery="speaker_echo"),
    StoryParams(name="Milo", role="navigator", companion="Glint", ship="Rocket Bean", room="observatory", mystery="speaker_beep"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible room/mystery combos:\n")
        for room, mystery, speaker in triples:
            print(f"  {room:10} {mystery:16} {speaker}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
