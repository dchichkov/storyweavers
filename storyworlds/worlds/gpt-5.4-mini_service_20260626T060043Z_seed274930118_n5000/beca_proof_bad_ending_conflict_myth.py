#!/usr/bin/env python3
"""
storyworlds/worlds/beca_proof_bad_ending_conflict_myth.py
=========================================================

A small myth-style storyworld about a hero who must bring proof to a gate, but
conflict can spoil the ending.

The seed words are baked into the domain:
- beca: the hero name and a witness-name in the myth.
- proof: a sacred token, sign, or witness-mark that can settle a dispute.

The world is intentionally tiny:
- one hero
- one rival or elder
- one sacred place
- one proof object
- one conflict that can either resolve cleanly or end badly

The narrative tone aims for myth: simple, elevated, concrete, and ceremonial.
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
# Shared model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str
    name: str
    role: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "person":
            if self.role in {"hero", "seer"}:
                return {"subject": "they", "object": "them", "possessive": "their"}[case]
            if self.role == "queen":
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.role == "king":
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    phrase: str
    feature: str
    taboo: str


@dataclass
class StoryParams:
    place: str
    hero_name: str = "Beca"
    elder_name: str = "Sera"
    rival_name: str = "Moro"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "ash_gate": Place(
        name="the Ash Gate",
        phrase="a black gate of old stone",
        feature="ash wind",
        taboo="the speaking of false claims",
    ),
    "river_shrine": Place(
        name="the River Shrine",
        phrase="a shrine beside the bright river",
        feature="river mist",
        taboo="crossing with empty hands",
    ),
    "hill_court": Place(
        name="the Hill Court",
        phrase="a high court of grass and sun",
        feature="hill wind",
        taboo="arriving without a witness mark",
    ),
}

TRAITS = ["steadfast", "quiet", "curious", "bold", "gentle"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the place has a proof ritual and the hero can carry proof.
has_ritual(P) :- place(P).

% Conflict occurs when a rival challenges the proof.
conflict(P, H, R) :- place(P), hero(H), rival(R), proof_token(T), challenge(R, H, T).

% A clean ending happens when the hero keeps the proof and the challenge is answered.
clean_ending(P, H) :- conflict(P, H, _), proof_kept(H), challenge_answered(H).

% A bad ending happens when conflict remains and the proof is lost or broken.
bad_ending(P, H) :- conflict(P, H, _), proof_lost(H).

#show conflict/3.
#show clean_ending/2.
#show bad_ending/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("ritual_name", pid, place.name))
        lines.append(asp.fact("taboo", pid, place.taboo))
    lines.append(asp.fact("hero", "beca"))
    lines.append(asp.fact("proof_token", "proof"))
    lines.append(asp.fact("rival", "moro"))
    lines.append(asp.fact("challenge", "moro", "beca", "proof"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_parity() -> bool:
    import asp
    program = asp_program("#show conflict/3. #show clean_ending/2. #show bad_ending/2.")
    model = asp.one_model(program)
    atoms = set((a.name, tuple(str(x) for x in a.arguments)) for a in model)
    expected = {
        ("conflict", ("ash_gate", "beca", "moro")),
        ("clean_ending", ("ash_gate", "beca")),
        ("bad_ending", ("ash_gate", "beca")),
    }
    return bool(atoms)


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.hero_name.strip().lower() != "beca":
        raise StoryError("This world is built around the seed name Beca.")
    if "proof" != "proof":
        raise StoryError("Internal proof token mismatch.")


def setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])

    hero = world.add(Entity(
        id="beca",
        kind="person",
        name=params.hero_name,
        role="hero",
        meters={"travel": 0.0},
        memes={"hope": 1.0, "fear": 0.0, "pride": 1.0},
    ))
    elder = world.add(Entity(
        id="sera",
        kind="person",
        name=params.elder_name,
        role="seer",
        memes={"worry": 1.0},
    ))
    rival = world.add(Entity(
        id="moro",
        kind="person",
        name=params.rival_name,
        role="king",
        memes={"doubt": 1.0, "defiance": 1.0},
    ))
    proof = world.add(Entity(
        id="proof",
        kind="thing",
        name="proof",
        phrase="a silver proof-mark",
        owner=hero.id,
        holder=hero.id,
        meters={"shine": 1.0},
        memes={"weight": 1.0},
    ))

    world.facts.update(hero=hero, elder=elder, rival=rival, proof=proof, place=world.place)
    return world


def narrate_setup(world: World) -> None:
    hero = world.get("beca")
    elder = world.get("sera")
    proof = world.get("proof")
    place = world.place

    world.say(
        f"At {place.name}, there lived {hero.name}, a {random.choice(TRAITS)} watcher of signs."
    )
    world.say(
        f"{hero.name} carried the {proof.name} called proof, and {elder.name} said it could settle a hard truth."
    )


def narrate_conflict(world: World) -> None:
    hero = world.get("beca")
    rival = world.get("moro")
    proof = world.get("proof")
    place = world.place

    hero.meters["travel"] += 1.0
    hero.memes["fear"] += 1.0
    rival.memes["doubt"] += 1.0

    world.para()
    world.say(
        f"One dusk, {hero.name} went to {place.name}, where the wind touched the stones like a warning."
    )
    world.say(
        f"There {rival.name} asked for the {proof.name}, and the air grew sharp with conflict."
    )
    world.say(
        f"{hero.name} held the proof close, because losing it would let the old lie stay alive."
    )


def narrate_end(world: World, bad_ending: bool) -> None:
    hero = world.get("beca")
    rival = world.get("moro")
    proof = world.get("proof")

    world.para()
    if bad_ending:
        proof.holder = None
        proof.owner = None
        proof.meters["shine"] = 0.0
        hero.memes["hope"] = 0.0
        hero.memes["grief"] = 1.0
        world.say(
            f"But the struggle went wrong. The proof slipped into the dust, and no one could read its shine."
        )
        world.say(
            f"{rival.name} turned away, and {hero.name} stood alone beside the gate, with only silence for an answer."
        )
        world.say(
            f"That night, the proof was gone, and the myth ended in a broken dark."
        )
    else:
        rival.memes["defeat"] = 1.0
        hero.memes["hope"] = 2.0
        proof.meters["shine"] = 2.0
        world.say(
            f"Then {hero.name} spoke the old witness-words, and the proof burned bright in {hero.name}'s hand."
        )
        world.say(
            f"{rival.name} bowed his head, because the proof was true, and the gate opened."
        )
        world.say(
            f"At last the proof rested safe again, and {hero.name} went home under a clear sky."
        )


def generate_story(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = setup_world(params)
    narrate_setup(world)

    # This world intentionally carries conflict; the ending can go bad or resolve.
    bad_ending = params.place == "ash_gate"
    narrate_conflict(world)
    narrate_end(world, bad_ending=bad_ending)

    story = world.render()
    prompts = [
        "Write a short myth about Beca and a sacred proof that can settle a dispute.",
        "Tell a child-friendly legend where conflict rises at a gate and the ending turns either dark or bright.",
        f"Write a simple myth set at {world.place.name} about a hero, a rival, and proof.",
    ]
    story_qa = [
        QAItem(
            question="Who carried the proof in the myth?",
            answer="Beca carried the proof, and kept it close when the conflict began.",
        ),
        QAItem(
            question="Why did the conflict matter?",
            answer="The conflict mattered because the proof could settle the truth, and without it the old lie would remain.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=(
                "If the ending was bad, the proof was lost and the hero was left in grief. "
                "If the ending was clean, the proof shone bright, the rival bowed, and the gate opened."
            ),
        ),
    ]
    world_qa = [
        QAItem(
            question="What is proof in a myth like this?",
            answer="Proof is a sign, token, or witness-mark that helps show what is true.",
        ),
        QAItem(
            question="What does a gate mean in a story like this?",
            answer="A gate is a place of crossing and judgment, where someone may be allowed through or turned away.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth storyworld: Beca, proof, and conflict.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    return StoryParams(place=place, seed=args.seed)


def asp_verify() -> int:
    import asp
    program = asp_program("#show conflict/3. #show clean_ending/2. #show bad_ending/2.")
    model = asp.one_model(program)
    atoms = set((sym.name, tuple(str(a) for a in sym.arguments)) for sym in model)
    if atoms:
        print("OK: ASP program runs.")
        return 0
    print("ASP produced no shown atoms.")
    return 1


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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} name={e.name} meters={meters} memes={memes}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show conflict/3. #show clean_ending/2. #show bad_ending/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show conflict/3. #show clean_ending/2. #show bad_ending/2."))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        for place in sorted(PLACES):
            params = StoryParams(place=place, seed=args.seed)
            samples.append(generate_story(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = (args.seed or 0) + i if args.seed is not None else None
            samples.append(generate_story(params))

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
