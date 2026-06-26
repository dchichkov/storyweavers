#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/allow_sensitive_problem_solving_repetition_suspense_ghost.py
==============================================================================================================

A tiny ghost-story world with a gentle suspense arc: a child hears a noise,
finds a sensitive ghost, solves a small problem, and learns that the ghost will
allow help when treated kindly.

The domain is intentionally compact. The story turns on:
- suspense: repeated sounds in the dark
- problem solving: noticing a clue and using the right tool
- repetition: a recurring knock / whisper pattern
- sensitivity: the ghost is easily upset by loud voices and rough touch
- allow: the ghost allows passage once the child proves careful
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old house"
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    reveal: str
    needs: str
    room: str


@dataclass
class Ghost:
    id: str
    label: str
    temperament: str
    allows_after: str
    clue_hint: str
    sound: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_bits: list[str] = []

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


def _default_meters() -> dict[str, float]:
    return {"fear": 0.0, "curiosity": 0.0, "trust": 0.0, "noise": 0.0, "blocked": 0.0}


def _default_memes() -> dict[str, float]:
    return {"worry": 0.0, "relief": 0.0, "bravery": 0.0, "suspense": 0.0, "care": 0.0}


SETTING = Setting(place="the old house", affords={"listen", "search", "solve"})

GHOST = Ghost(
    id="ghost",
    label="the pale ghost",
    temperament="sensitive",
    allows_after="the child is quiet and careful",
    clue_hint="three knocks from the locked attic door",
    sound="tap-tap-tap",
)

CLUES = {
    "attic_key": Clue(
        id="attic_key",
        label="small brass key",
        phrase="a small brass key with a blue ribbon",
        reveal="the attic door was locked",
        needs="listen",
        room="the hallway",
    ),
    "music_box": Clue(
        id="music_box",
        label="music box",
        phrase="an old music box",
        reveal="the ghost wanted its song heard again",
        needs="search",
        room="the attic",
    ),
}


@dataclass
class StoryParams:
    clue: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class StoryWorld:
    pass


def introduce(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"{child.id} lived in {world.setting.place} with {parent.label}. "
        f"At night, the halls felt long and quiet."
    )


def suspense_beats(world: World, ghost: Entity) -> None:
    world.say(
        f"Then came a sound: {ghost.label} made {GHOST.sound} from somewhere above."
    )
    world.say(
        f"{ghost.label.capitalize()} made {GHOST.sound} again. The sound seemed to wait in the dark."
    )


def problem(world: World, child: Entity, clue: Clue) -> None:
    child.meters["curiosity"] += 1
    child.memes["suspense"] += 1
    world.say(
        f"{child.id} listened hard. The repeats felt like a message, not just a noise."
    )
    world.say(
        f"{child.id} thought about the clue: {clue.phrase}."
    )


def solve(world: World, child: Entity, clue: Clue, ghost: Entity) -> None:
    if clue.id == "attic_key":
        world.say(
            f"{child.id} found the key by the vase in the hallway and held it with both hands."
        )
        world.say(
            f"The key opened the attic door, and the dark room breathed out a dusty little sigh."
        )
    else:
        world.say(
            f"{child.id} climbed the stairs, followed the soft trail, and found the old music box under a sheet."
        )
        world.say(
            f"When {child.id} wound it up, the tune floated through the room like moonlight."
        )
    ghost.meters["blocked"] = 0.0
    child.memes["bravery"] += 1
    child.memes["relief"] += 1


def allow(world: World, child: Entity, ghost: Entity, clue: Clue) -> None:
    child.meters["trust"] += 1
    ghost.memes["care"] += 1
    world.say(
        f"The pale ghost watched closely, sensitive to every step and every whisper."
    )
    world.say(
        f"At last, {ghost.label} nodded and allowed {child.id} into the attic."
    )
    world.say(
        f"{ghost.label.capitalize()} was no longer scary once {child.id} solved the little mystery with care."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters=_default_meters(),
        memes=_default_memes(),
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters=_default_meters(),
        memes=_default_memes(),
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label="the pale ghost",
        meters={"fear": 0.0, "blocked": 1.0},
        memes={"suspense": 1.0, "care": 0.0, "worry": 0.0},
    ))
    clue = CLUES[params.clue]
    world.facts.update(child=child, parent=parent, ghost=ghost, clue=clue)

    introduce(world, child, parent)
    world.para()
    suspense_beats(world, ghost)
    problem(world, child, clue)
    world.say(
        f"{child.id} did not shout. {child.id} only listened, because the house felt sensitive to loud voices."
    )
    world.para()
    solve(world, child, clue, ghost)
    allow(world, child, ghost, clue)
    world.para()
    world.say(
        f"After that, the hall was quiet. The ghost kept tapping softly, but now the taps sounded like thanks."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    clue: Clue = f["clue"]
    return [
        f'Write a short ghost story for a child named {child.id} that includes repeated knocking and a gentle solution.',
        f'Tell a suspenseful story where {child.id} hears {GHOST.sound} in {SETTING.place} and solves the mystery of {clue.label}.',
        f'Write a child-friendly ghost story about a sensitive ghost that allows help only after the child listens carefully.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    clue: Clue = f["clue"]
    ghost: Entity = f["ghost"]
    return [
        QAItem(
            question=f"Who heard the repeated tapping in {world.setting.place}?",
            answer=f"{child.id} heard the tapping and stayed quiet so {parent.label} would not miss the clue.",
        ),
        QAItem(
            question=f"What was the mystery clue {child.id} followed?",
            answer=f"The clue was {clue.phrase}. It helped {child.id} understand what the ghost wanted.",
        ),
        QAItem(
            question=f"Why did the ghost allow {child.id} into the attic?",
            answer=f"The ghost was sensitive and wanted careful help. After {child.id} listened, solved the problem, and stayed gentle, {ghost.label} allowed {child.id} in.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At the end, the scary noise became a soft thanks, and the house felt calmer because the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is often a spooky-looking spirit in a story, but in a child-friendly tale it can be lonely, gentle, or misunderstood.",
        ),
        QAItem(
            question="What does sensitive mean?",
            answer="Sensitive means something or someone can be easily affected by feelings, sounds, or touch.",
        ),
        QAItem(
            question="Why can repeated sounds feel spooky at night?",
            answer="Repeated sounds can feel spooky because they make you wonder what is making them, especially when it is dark and quiet.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps you solve a mystery.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "old_house"))
    lines.append(asp.fact("ghost", "ghost"))
    lines.append(asp.fact("sensitive", "ghost"))
    lines.append(asp.fact("allows_after", "ghost", "quiet_and_careful"))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("in_room", cid, clue.room.replace(" ", "_")))
    return "\n".join(lines)


ASP_RULES = r"""
allow(G) :- ghost(G), sensitive(G), allows_after(G, quiet_and_careful).
problem(C) :- clue(C), in_room(C, hallway).
resolved(C) :- problem(C), allow(ghost).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show allow/1.\n#show problem/1.\n#show resolved/1."))
    atoms = set(asp.atoms(model, "allow")) | set(asp.atoms(model, "problem")) | set(asp.atoms(model, "resolved"))
    expected = {("ghost",), ("attic_key",), ("attic_key",)}
    if ("ghost",) in atoms and ("attic_key",) in atoms:
        print("OK: ASP facts are wired for allow + sensitive + problem solving.")
        return 0
    print("MISMATCH: ASP reasoning did not produce expected atoms.")
    print("Atoms:", sorted(atoms))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story world with suspense, repetition, and problem solving.")
    ap.add_argument("--clue", choices=CLUES)
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


NAMES = {"girl": ["Mina", "Lily", "Eva", "Nora"], "boy": ["Theo", "Ben", "Finn", "Owen"]}


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    clue = args.clue or rng.choice(list(CLUES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(clue=clue, name=name, gender=gender, parent=parent)


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
        print(asp_program("#show allow/1.\n#show problem/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, clue in enumerate(CLUES):
            params = StoryParams(clue=clue, name=NAMES["girl"][i % len(NAMES["girl"])], gender="girl", parent="mother", seed=base_seed + i)
            samples.append(generate(params))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
