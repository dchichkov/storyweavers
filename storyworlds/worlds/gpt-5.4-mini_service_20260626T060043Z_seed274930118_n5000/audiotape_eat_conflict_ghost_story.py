#!/usr/bin/env python3
"""
A tiny storyworld about a restless ghost, a brave child, and an old audiotape.

Premise:
- A child finds an audiotape in an old room.
- The tape carries a ghostly voice asking to eat a saved snack before it vanishes.
- The child feels a chill, but the ghost is not trying to scare; it is asking for help.

Tension:
- The audiotape crackles and a conflict starts when the child thinks the voice is creepy.
- The ghost wants the snack to be shared before midnight.
- The child is torn between fear and kindness.

Turn:
- The child plays the tape again, listens carefully, and realizes the ghost is lonely.
- The ghost explains the snack was left for a lost friend.

Resolution:
- The child leaves the snack on the table and listens until the tape ends.
- The room feels warmer, and the ghost fades with a grateful sigh.

This world models one narrow domain with a reasonableness gate:
- The conflict is only meaningful when the tape is old enough to crackle and the
  ghost can speak through it.
- The resolution is only meaningful when the child can offer food or a shared
  moment of listening.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaken_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the attic"
    dim: bool = True
    echoes: bool = True


@dataclass
class Tape:
    label: str
    phrase: str
    age: str
    voice: str
    signal: str
    can_house_ghost: bool = True


@dataclass
class Snack:
    label: str
    phrase: str
    edible: bool = True
    shared: bool = True


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    trait: str
    tape: str
    snack: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "attic": Setting(place="the attic", dim=True, echoes=True),
    "hall": Setting(place="the old hall", dim=True, echoes=True),
    "basement": Setting(place="the basement", dim=False, echoes=False),
}

TAPES = {
    "lullaby": Tape(
        label="a dusty audiotape",
        phrase="a dusty audiotape with a bent label",
        age="old",
        voice="soft and faraway",
        signal="crackly",
    ),
    "message": Tape(
        label="an audiotape",
        phrase="an audiotape wrapped in a paper sleeve",
        age="old",
        voice="trembly and clear",
        signal="hissing",
    ),
}

SNACKS = {
    "cookie": Snack(
        label="cookie",
        phrase="a small butter cookie",
    ),
    "cake": Snack(
        label="cake",
        phrase="a slice of sweet cake",
    ),
    "apple": Snack(
        label="apple",
        phrase="a red apple",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ruby", "Ivy", "Ava"]
BOY_NAMES = ["Theo", "Finn", "Noah", "Leo", "Ben", "Eli"]
TRAITS = ["curious", "careful", "brave", "quiet", "gentle", "nervous"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def reasonableness_gate(tape: Tape, snack: Snack) -> None:
    if not tape.can_house_ghost:
        raise StoryError("The tape cannot reasonably carry a ghost voice.")
    if not snack.edible:
        raise StoryError("The chosen snack must be edible for the ghost story to work.")


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for tape_id, tape in TAPES.items():
        for snack_id, snack in SNACKS.items():
            try:
                reasonableness_gate(tape, snack)
            except StoryError:
                continue
            combos.append((tape_id, snack_id))
    return combos


def intro(world: World, child: Entity, tape: Entity) -> None:
    world.say(
        f"{child.id} was a {next(t for t in child.traits if t != 'little')} {child.type} "
        f"who liked quiet rooms and strange little discoveries."
    )
    world.say(
        f"One day, {child.id} found {tape.phrase} tucked behind a box."
    )


def setup_ghost(world: World, child: Entity, tape: Entity, snack: Entity) -> None:
    world.say(
        f"The tape looked old, and when {child.id} touched it, the room felt colder."
    )
    world.say(
        f"From the machine came a {tape.meters.get('signal', 0)}"
    )


def play_tape(world: World, child: Entity, tape: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    tape.meters["played"] = tape.meters.get("played", 0) + 1
    world.say(
        f"When the tape played, a {tape.label} voice whispered, "
        f'"Please do not be afraid. I am only a ghost on the line."'
    )


def conflict(world: World, child: Entity, ghost: Entity, snack: Entity) -> None:
    child.memes["fear"] = child.memes.get("fear", 0) + 1
    child.memes["conflict"] = child.memes.get("conflict", 0) + 1
    ghost.memes["hope"] = ghost.memes.get("hope", 0) + 1
    world.say(
        f"{child.id} took a step back. The voice sounded spooky, and {child.id} did not know "
        f"if {ghost.id} wanted help or trouble."
    )
    world.say(
        f'"I am lonely," the ghost said. "I only ask because I want to eat {snack.phrase} '
        f'before it goes cold and I fade away."'
    )


def turn(world: World, child: Entity, ghost: Entity, snack: Entity) -> None:
    child.memes["understanding"] = child.memes.get("understanding", 0) + 1
    child.memes["conflict"] = 0
    ghost.memes["relief"] = ghost.memes.get("relief", 0) + 1
    world.say(
        f"{child.id} listened again, slower this time, and heard sadness hiding under the static."
    )
    world.say(
        f"The ghost was not trying to frighten anyone. It only wanted to eat and remember a friend."
    )


def resolution(world: World, child: Entity, ghost: Entity, snack: Entity) -> None:
    child.memes["kindness"] = child.memes.get("kindness", 0) + 1
    ghost.meters["fading"] = ghost.meters.get("fading", 0) + 1
    snack.meters["served"] = snack.meters.get("served", 0) + 1
    world.say(
        f"{child.id} set {snack.phrase} on the table and said, "
        f'"You can have it. I will listen until the tape ends."'
    )
    world.say(
        f"The room warmed up. The ghost gave one grateful sigh, and the audiotape fell quiet at last."
    )


def tell(setting: Setting, tape_cfg: Tape, snack_cfg: Snack,
         name: str = "Mia", gender: str = "girl",
         hero_traits: Optional[list[str]] = None, parent: str = "mother") -> World:
    reasonableness_gate(tape_cfg, snack_cfg)
    world = World(setting)

    child = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        traits=["little"] + (hero_traits or ["curious", "gentle"]),
    ))
    guardian = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent,
        label=f"the {parent}",
    ))
    tape = world.add(Entity(
        id="tape",
        kind="thing",
        type="tape",
        label=tape_cfg.label,
        phrase=tape_cfg.phrase,
        meters={"signal": 1.0},
        memes={},
    ))
    snack = world.add(Entity(
        id="snack",
        kind="thing",
        type="snack",
        label=snack_cfg.label,
        phrase=snack_cfg.phrase,
        owner=child.id,
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label="the ghost",
        phrase="the ghost in the tape",
        meters={"fading": 0.0},
        memes={"lonely": 1.0},
    ))

    intro(world, child, tape)
    world.say(
        f"{child.id} wanted to listen, but the old machine hissed like something hidden was awake."
    )
    world.para()
    world.say(
        f"Then the tape spoke in a {tape_cfg.voice} voice, and {child.id} felt a little conflict rise."
    )
    conflict(world, child, ghost, snack)
    world.para()
    turn(world, child, ghost, snack)
    resolution(world, child, ghost, snack)

    world.facts.update(
        child=child,
        guardian=guardian,
        tape=tape,
        snack=snack,
        ghost=ghost,
        setting=setting,
        tape_cfg=tape_cfg,
        snack_cfg=snack_cfg,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    tape = f["tape_cfg"]
    snack = f["snack_cfg"]
    return [
        f'Write a spooky but gentle story for a young child about an audiotape and a ghost who wants to eat {snack.phrase}.',
        f"Tell a child-friendly ghost story where {child.id} hears a ghost on {tape.label} and solves the conflict with kindness.",
        f'Write a short Halloween-style story that includes an audiotape, a snack, and the word "eat".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    snack = f["snack"]
    tape = f["tape_cfg"]
    ghost = f["ghost"]
    return [
        QAItem(
            question=f"What did {child.id} find in the old room?",
            answer=f"{child.id} found {tape.phrase}.",
        ),
        QAItem(
            question=f"Why did the ghost on the tape cause a conflict?",
            answer=f"The ghost sounded spooky at first, and {child.id} did not know what it wanted. "
                   f"Then the ghost explained that it only wanted to eat {snack.phrase} and not scare anyone.",
        ),
        QAItem(
            question=f"How did {child.id} help the ghost?",
            answer=f"{child.id} listened carefully, set {snack.phrase} on the table, and stayed with the tape until the end.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The room felt warmer, the ghost became calm, and the audiotape went quiet instead of crackling.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "audiotape": (
        "What is an audiotape?",
        "An audiotape is a tape that can store sound, like a voice or music, so people can listen to it later.",
    ),
    "ghost": (
        "What is a ghost in a story?",
        "A ghost in a story is usually a spooky spirit character. It can be scary, lonely, funny, or friendly depending on the tale.",
    ),
    "eat": (
        "What does it mean to eat?",
        "To eat means to take food into your body so it can give you energy and help you grow.",
    ),
    "conflict": (
        "What is a conflict in a story?",
        "A conflict is a problem or disagreement that makes the character worry, choose, or try harder.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE.values()]


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
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
tape(T) :- tape_fact(T).
snack(S) :- snack_fact(S).
compatible(T,S) :- tape(T), snack(S), can_house_ghost(T), edible(S).

% The story is reasonable only if the tape can carry a ghostly voice and the
% snack can be eaten by the ghost.
valid_story(T,S) :- compatible(T,S).

#show valid_story/2.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid, t in TAPES.items():
        lines.append(asp.fact("tape_fact", tid))
        if t.can_house_ghost:
            lines.append(asp.fact("can_house_ghost", tid))
    for sid, s in SNACKS.items():
        lines.append(asp.fact("snack_fact", sid))
        if s.edible:
            lines.append(asp.fact("edible", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost storyworld with an audiotape and a conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tape", choices=TAPES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.tape and args.snack and (args.tape, args.snack) not in combos:
        raise StoryError("That tape and snack do not make a reasonable ghost story together.")
    tape = args.tape or rng.choice(sorted(TAPES))
    snack = args.snack or rng.choice(sorted(SNACKS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    place = args.place or rng.choice(sorted(SETTINGS))
    if (tape, snack) not in combos:
        raise StoryError("No valid combination matches the given options.")
    return StoryParams(place=place, name=name, gender=gender, parent=parent, trait=trait, tape=tape, snack=snack)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        TAPES[params.tape],
        SNACKS[params.snack],
        name=params.name,
        gender=params.gender,
        hero_traits=[params.trait, "little"],
        parent=params.parent,
    )
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


CURATED = [
    StoryParams(place="attic", name="Mia", gender="girl", parent="mother", trait="curious", tape="lullaby", snack="cookie"),
    StoryParams(place="hall", name="Theo", gender="boy", parent="father", trait="brave", tape="message", snack="cake"),
    StoryParams(place="basement", name="Nora", gender="girl", parent="mother", trait="gentle", tape="message", snack="apple"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible tape/snack combos:")
        for t, s in combos:
            print(f"  {t:10} {s}")
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
            header = f"### {p.name}: {p.tape} with {p.snack} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
