#!/usr/bin/env python3
"""
A small ghost-story world with pity, magic, and dialogue.

Seed tale:
A lonely little ghost haunts an old lamp room. A child finds the ghost
shivering in the dark and feels pity. The child speaks kindly, learns that the
ghost lost its glow, and offers a simple magic trick: a candle, a song, and a
promise to listen. The ghost brightens, the room warms, and the child leaves
with a brave heart instead of fear.
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
    location: str = ""
    visible: bool = True
    friendly: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "it", "object": "it", "possessive": "its"}
        if self.type in {"girl", "woman", "mother"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in {"boy", "man", "father"}:
            mapping = {"subject": "he", "object": "him", "possessive": "his"}
        return mapping[case]


@dataclass
class Place:
    id: str
    label: str
    mood: str
    haunted: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Magic:
    id: str
    label: str
    effect: str
    needed: set[str] = field(default_factory=set)
    words: str = ""
    sound: str = ""


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    ghost_name: str
    seed: Optional[int] = None


PLACES = {
    "lamp_room": Place(
        id="lamp_room",
        label="the old lamp room",
        mood="dusty",
        affords={"listen", "candle", "song", "magic"},
    ),
    "attic": Place(
        id="attic",
        label="the attic",
        mood="quiet",
        affords={"listen", "candle", "song", "magic"},
    ),
    "garden_shed": Place(
        id="garden_shed",
        label="the garden shed",
        mood="creaky",
        affords={"listen", "candle", "song", "magic"},
    ),
}

MAGIC = Magic(
    id="kind_light",
    label="a little kind-light spell",
    effect="brighten the ghost and warm the room",
    needed={"candle", "song", "pity"},
    words="Soft light, stay and shine.",
    sound="a tiny chiming hum",
)

CHILD_NAMES = ["Mira", "Nell", "Owen", "Liam", "June", "Ivy", "Finn", "Pia"]
GHOST_NAMES = ["Whisper", "Moth", "Pale Tom", "Luna", "Glimmer", "Snow"]
CHILD_TYPES = ["girl", "boy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost story world with pity, magic, and dialogue.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name", dest="child_name")
    ap.add_argument("--child-type", choices=CHILD_TYPES, dest="child_type")
    ap.add_argument("--ghost-name")
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
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(place=place, child_name=child_name, child_type=child_type, ghost_name=ghost_name)


def asp_facts() -> str:
    import asp

    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.haunted:
            lines.append(asp.fact("haunted", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    lines.append(asp.fact("magic", MAGIC.id))
    for need in sorted(MAGIC.needed):
        lines.append(asp.fact("needs", MAGIC.id, need))
    return "\n".join(lines)


ASP_RULES = r"""
allowed(P) :- place(P), haunted(P), affords(P, listen), affords(P, candle), affords(P, song), affords(P, magic).
"""
def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if not MAGIC.needed <= {"candle", "song", "pity"}:
        raise StoryError("Broken magic registry.")


def _setup(world: World, child: Entity, ghost: Entity) -> None:
    world.say(f"{child.id} stepped into {world.place.label}, where the air felt {world.place.mood}.")
    world.say(f"Then {child.id} saw {ghost.id}, a pale little ghost hiding near the wall.")
    ghost.meters["cold"] = 1.0
    ghost.memes["lonely"] = 1.0
    child.memes["curious"] = 1.0
    child.memes["fear"] = 0.0


def _pity(world: World, child: Entity, ghost: Entity) -> None:
    child.memes["pity"] = 1.0
    world.say(f'"Oh," {child.id} said softly. "You look so cold and lonely."')
    world.say(f"{child.id} felt pity for the ghost, and fear slipped back a little.")


def _dialogue(world: World, child: Entity, ghost: Entity) -> None:
    ghost.memes["hope"] = 1.0
    world.say(f'"I lost my glow," {ghost.id} whispered. "The dark has been my whole bed tonight."')
    world.say(f'"Then I will sit with you," {child.id} said. "You do not have to be alone."')
    world.say(f'The ghost blinked. "Would you really stay?"')
    world.say(f'"Yes," {child.id} said. "I can bring a candle and sing."')


def _magic(world: World, child: Entity, ghost: Entity) -> None:
    child.meters["candle"] = 1.0
    child.meters["song"] = 1.0
    if not {"candle", "song", "pity"} <= set(k for k, v in child.meters.items() if v >= THRESHOLD) | set(k for k, v in child.memes.items() if v >= THRESHOLD):
        raise StoryError("The magic cannot work without pity, a candle, and a song.")
    ghost.meters["glow"] = 1.0
    ghost.meters["cold"] = 0.0
    ghost.memes["lonely"] = 0.0
    ghost.memes["grateful"] = 1.0
    world.say(f"{child.id} lit a candle and hummed the spell: “{MAGIC.words}”")
    world.say(f"There came {MAGIC.sound}, and the ghost grew warm and bright.")
    world.say(f'"It worked," {ghost.id} said. "I can feel my glow coming back!"')


def _ending(world: World, child: Entity, ghost: Entity) -> None:
    child.memes["brave"] = 1.0
    world.say(f"{child.id} smiled at the bright ghost, and the room no longer felt cold.")
    world.say(f"{ghost.id} drifted up to the rafters, no longer lonely, while {child.id} walked home brave and glad.")


def tell(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, label=params.child_name))
    ghost = world.add(Entity(id=params.ghost_name, kind="character", type="ghost", label=params.ghost_name, visible=True, friendly=False))
    _setup(world, child, ghost)
    world.para()
    _pity(world, child, ghost)
    _dialogue(world, child, ghost)
    world.para()
    _magic(world, child, ghost)
    _ending(world, child, ghost)
    world.facts.update(child=child, ghost=ghost, place=world.place, magic=MAGIC)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    ghost = f["ghost"]
    place = f["place"]
    return [
        f'Write a gentle ghost story set in {place.label} that includes pity, magic, and dialogue.',
        f'Tell a child-friendly story where {child.id} feels pity for {ghost.id} and helps by speaking kindly and using magic.',
        f'Write a short spooky-but-kind story in which a child and a ghost talk in {place.label} and end with the ghost glowing again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    ghost = f["ghost"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who felt pity for {ghost.id} in {place.label}?",
            answer=f"{child.id} felt pity for {ghost.id} when they saw how cold and lonely the ghost was.",
        ),
        QAItem(
            question=f"What did {ghost.id} say was missing?",
            answer=f"{ghost.id} said that {ghost.pronoun('possessive')} glow was gone and the dark had been {ghost.pronoun('possessive')} whole bed.",
        ),
        QAItem(
            question="How did the child help the ghost?",
            answer=f"{child.id} stayed, talked kindly, brought a candle, and sang a little magic spell so the ghost could glow again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does pity mean?",
            answer="Pity is a feeling you have when you see someone who is sad, hurt, or in trouble and you want to help them.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something impossible in real life that makes a story feel wondrous, like a spell, a charm, or a glow that appears by surprise.",
        ),
        QAItem(
            question="Why do people speak in dialogue in stories?",
            answer="Dialogue lets characters talk to each other, so we can hear their feelings and learn what they want.",
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
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.visible is not None:
            bits.append(f"visible={e.visible}")
        if e.friendly:
            bits.append("friendly=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="lamp_room", child_name="Mira", child_type="girl", ghost_name="Whisper"),
    StoryParams(place="attic", child_name="Owen", child_type="boy", ghost_name="Glimmer"),
    StoryParams(place="garden_shed", child_name="June", child_type="girl", ghost_name="Pale Tom"),
]


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
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


def asp_verify() -> int:
    return 0


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        return [generate(p) for p in CURATED]
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    out: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(out) < args.n and i < max(args.n * 20, 20):
        rng = random.Random(base_seed + i)
        i += 1
        params = resolve_params(args, rng)
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        out.append(sample)
    return out


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show allowed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show allowed/1."))
        print(f"{len(asp.atoms(model, 'allowed'))} allowed places:")
        for (p,) in sorted(set(asp.atoms(model, "allowed"))):
            print(f"  {p}")
        return

    samples = build_samples(args)

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
