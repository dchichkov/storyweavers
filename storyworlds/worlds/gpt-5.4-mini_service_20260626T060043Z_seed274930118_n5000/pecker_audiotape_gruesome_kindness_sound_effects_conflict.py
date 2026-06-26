#!/usr/bin/env python3
"""
A tiny space-adventure storyworld about a pecker, an audiotape, and a gruesome
soundboard dispute that is solved with kindness.

The domain is intentionally small:
- A crew on a ship finds a strange audiotape.
- The tape's sound effects are useful, but the wrong playback can make a
  gruesome mess of the ship's mood.
- Conflict rises when one crewmate wants to use the tape loudly.
- Kindness turns the moment around and the crew discovers the tape's true value.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    fragile: bool = False
    loud: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for key in ("noise", "damage", "stain", "harmony"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"pilot", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str
    compartments: set[str] = field(default_factory=set)
    quiet_limit: int = 2
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    crew_name: str
    crew_type: str
    captain_name: str
    captain_type: str
    place: str
    tape_style: str
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------

def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    tape = world.entities.get("audiotape")
    if not tape or tape.held_by is None:
        return out
    holder = world.get(tape.held_by)
    if tape.meters["noise"] < THRESHOLD:
        return out
    sig = ("noise", holder.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    holder.memes["conflict"] += 1
    holder.meters["noise"] += 1
    out.append(f"The ship's speakers crackled, and the noise made the cabin feel tight.")
    return out


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    tape = world.entities.get("audiotape")
    if not tape:
        return out
    if tape.meters["noise"] < THRESHOLD:
        return out
    if tape.fragile and tape.meters["damage"] < THRESHOLD:
        sig = ("damage", tape.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        tape.meters["damage"] += 1
        out.append("The tape almost snapped from the rough handling.")
    return out


def _r_harmony(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["kindness"] < THRESHOLD:
            continue
        sig = ("harmony", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["conflict"] = max(0.0, e.memes["conflict"] - 1.0)
        e.memes["harmony"] += 1
        out.append(f"Kindness softened the room, like a warm light over the control panel.")
    return out


RULES = [_r_noise, _r_damage, _r_harmony]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            pieces = rule(world)
            if pieces:
                changed = True
                out.extend(pieces)
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "bridge": "the bridge",
    "hangar": "the hangar",
    "galley": "the galley",
    "observation_deck": "the observation deck",
}

TAPES = {
    "pecker": {
        "label": "pecker audiotape",
        "phrase": "a pecker audiotape with a scuffed blue label",
        "style": "pecker",
        "noise": 2,
        "danger": "grinding pecks and chirps",
        "safe": "tiny pecks and bright chirps",
    },
    "sound_effects": {
        "label": "sound effects audiotape",
        "phrase": "an audiotape full of sound effects",
        "style": "sound effects",
        "noise": 1,
        "danger": "thunderclaps and shrieks",
        "safe": "whooshes and cheerful beeps",
    },
    "gruesome": {
        "label": "gruesome audiotape",
        "phrase": "a gruesome audiotape with a red warning stripe",
        "style": "gruesome",
        "noise": 3,
        "danger": "screeches and terrible rumbles",
        "safe": "soft echoes that only sound scary on purpose",
    },
}

TRAITS = ["curious", "brave", "gentle", "stubborn", "careful", "kind"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def choose_tape(style: str) -> dict:
    if style not in TAPES:
        raise StoryError("unknown tape style")
    return TAPES[style]


def build_world(params: StoryParams) -> World:
    ship = Ship(name="Star Lantern", compartments=set(PLACES.values()))
    world = World(ship)

    crew = world.add(Entity(
        id=params.crew_name,
        kind="character",
        type=params.crew_type,
        label=params.crew_name,
        memes={"kindness": 0.0, "conflict": 0.0, "curiosity": 1.0, "joy": 0.0},
    ))
    captain = world.add(Entity(
        id=params.captain_name,
        kind="character",
        type=params.captain_type,
        label=f"Captain {params.captain_name}",
        memes={"kindness": 1.0, "conflict": 0.0, "worry": 1.0},
    ))
    tape_cfg = choose_tape(params.tape_style)
    tape = world.add(Entity(
        id="audiotape",
        kind="thing",
        type="audiotape",
        label=tape_cfg["label"],
        phrase=tape_cfg["phrase"],
        fragile=True,
        loud=True,
        meters={"noise": 0.0, "damage": 0.0, "stain": 0.0},
    ))
    world.facts.update(
        crew=crew,
        captain=captain,
        tape=tape,
        tape_cfg=tape_cfg,
        place=params.place,
    )
    return world


def intro(world: World, params: StoryParams) -> None:
    crew = world.facts["crew"]
    captain = world.facts["captain"]
    tape_cfg = world.facts["tape_cfg"]
    world.say(
        f"On the {world.ship.name}, {crew.id} was a {params.crew_type} who loved strange finds."
    )
    world.say(
        f"{crew.id} found {tape_cfg['phrase']} in {params.place}, and {crew.id} wanted to hear it at once."
    )
    world.say(
        f"{captain.label} frowned a little, because every tape on a ship can become a problem if it is too loud."
    )


def setup_conflict(world: World, params: StoryParams) -> None:
    crew = world.facts["crew"]
    captain = world.facts["captain"]
    tape_cfg = world.facts["tape_cfg"]
    tape = world.facts["tape"]

    crew.held_by = crew.id
    tape.held_by = crew.id
    tape.meters["noise"] += tape_cfg["noise"]
    crew.memes["curiosity"] += 1
    crew.memes["conflict"] += 1
    world.say(
        f"{crew.id} turned the dial up, and the tape answered with {tape_cfg['danger']}."
    )
    world.say(
        f"The sound bounced off the walls of {params.place}, and the cabin felt gruesome and cramped."
    )
    propagate(world, narrate=True)
    captain.memes["worry"] += 1
    world.say(
        f'"Please be careful," {captain.label} said. "That tape is useful, but kindness matters more than noise."'
    )


def turn_to_kindness(world: World, params: StoryParams) -> None:
    crew = world.facts["crew"]
    captain = world.facts["captain"]
    tape_cfg = world.facts["tape_cfg"]
    tape = world.facts["tape"]

    crew.memes["kindness"] += 1
    crew.memes["joy"] += 1
    world.say(
        f"{crew.id} heard the worry, lowered the dial, and handed the audiotape to {captain.label} with a smile."
    )
    world.say(
        f'"I can share it," {crew.id} said. "We can use the sound effects without hurting the ship."'
    )
    tape.meters["noise"] = 1
    tape.held_by = captain.id
    propagate(world, narrate=True)
    world.say(
        f"{captain.label} pressed play again, and the tape made {tape_cfg['safe']} instead of the harsh sounds."
    )
    crew.memes["conflict"] = 0.0
    captain.memes["worry"] = max(0.0, captain.memes["worry"] - 1.0)
    world.say(
        f"The bridge felt lighter at once, as if the stars themselves had taken a calmer breath."
    )


def ending(world: World, params: StoryParams) -> None:
    crew = world.facts["crew"]
    captain = world.facts["captain"]
    tape_cfg = world.facts["tape_cfg"]
    world.say(
        f"In the end, {crew.id} and {captain.label} kept the pecker audiotape safe in a soft pouch."
    )
    world.say(
        f"Their ship still loved sound effects, but now the sounds were shared kindly, without any gruesome conflict."
    )
    world.say(
        f"Outside {params.place}, the stars blinked on, and the little crew listened together like a team."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    intro(world, params)
    world.para()
    setup_conflict(world, params)
    world.para()
    turn_to_kindness(world, params)
    ending(world, params)

    world.facts.update(params=params)
    return world


# ---------------------------------------------------------------------------
# Q&A and prompts
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    tape_cfg = f["tape_cfg"]
    return [
        f'Write a short space-adventure story for a child about a {params.crew_type} finding {tape_cfg["phrase"]}.',
        f"Tell a gentle story where {params.crew_name} and {f['captain'].label} disagree about a loud audiotape, but kindness solves the conflict.",
        f'Write a story that includes the words "pecker", "audiotape", and "gruesome" in a starship setting.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    crew: Entity = f["crew"]
    captain: Entity = f["captain"]
    tape_cfg = f["tape_cfg"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {crew.id} find in {place}?",
            answer=f"{crew.id} found {tape_cfg['phrase']} in {place}.",
        ),
        QAItem(
            question=f"Why did {captain.label} worry about the audiotape?",
            answer=f"{captain.label} worried because the tape was loud and could make the ship feel gruesome and cramped.",
        ),
        QAItem(
            question=f"How did the conflict get better?",
            answer=f"It got better when {crew.id} used kindness, lowered the sound, and shared the tape with {captain.label}.",
        ),
        QAItem(
            question=f"What kind of sounds did the tape make at the end?",
            answer=f"At the end, it made {tape_cfg['safe']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special recorded sounds, like beeps, whooshes, or bangs, that help tell a story or make a game feel lively.",
        ),
        QAItem(
            question="What does kindness do in a disagreement?",
            answer="Kindness helps people listen, share, and calm down so a disagreement can turn into a better plan.",
        ),
        QAItem(
            question="What is an audiotape?",
            answer="An audiotape is a tape that can store sound so it can be played back later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} held_by={e.held_by} "
            f"meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for tape_style in TAPES:
            combos.append((place, tape_style, "audiotape"))
    return combos


def explain_rejection(place: str, tape_style: str) -> str:
    return f"(No story: the {tape_style} tape does not fit the space-adventure setup at {place}.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- place_name(P).
tape(T) :- tape_style(T).
compatible(P,T) :- place(P), tape(T).
valid(P,T) :- compatible(P,T).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place_name", p))
    for t in TAPES:
        lines.append(asp.fact("tape_style", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, t) for (p, t, _) in valid_combos()}
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - asp_set))
    print("asp only:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(
        crew_name="Mira",
        crew_type="pilot",
        captain_name="Nova",
        captain_type="captain",
        place="the bridge",
        tape_style="pecker",
    ),
    StoryParams(
        crew_name="Tavi",
        crew_type="engineer",
        captain_name="Sol",
        captain_type="captain",
        place="the hangar",
        tape_style="sound_effects",
    ),
    StoryParams(
        crew_name="Jules",
        crew_type="pilot",
        captain_name="Iris",
        captain_type="captain",
        place="the observation deck",
        tape_style="gruesome",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny space-adventure storyworld about an audiotape and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tape-style", choices=TAPES)
    ap.add_argument("--crew-name")
    ap.add_argument("--crew-type", choices=["pilot", "engineer", "navigator", "scout"])
    ap.add_argument("--captain-name")
    ap.add_argument("--captain-type", choices=["captain", "commander"])
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
    if args.place and args.tape_style:
        if (args.place, args.tape_style, "audiotape") not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.tape_style))
    place = args.place or rng.choice(list(PLACES))
    tape_style = args.tape_style or rng.choice(list(TAPES))
    crew_type = args.crew_type or rng.choice(["pilot", "engineer", "navigator", "scout"])
    captain_type = args.captain_type or "captain"
    crew_name = args.crew_name or rng.choice(["Mira", "Tavi", "Jules", "Rin", "Zed", "Kiri"])
    captain_name = args.captain_name or rng.choice(["Nova", "Sol", "Iris", "Orion"])
    return StoryParams(
        crew_name=crew_name,
        crew_type=crew_type,
        captain_name=captain_name,
        captain_type=captain_type,
        place=PLACES[place],
        tape_style=tape_style,
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible place/tape combos:")
        for c in combos:
            print(" ", c)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.crew_name} / {p.tape_style} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
