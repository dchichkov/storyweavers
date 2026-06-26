#!/usr/bin/env python3
"""
storyworlds/worlds/ghost_friendship_rhyme.py
============================================

A small story world in a ghost-story mood: a lonely little ghost, a new friend,
a soft conversation, and a rhyme that helps them become kind to each other.

The seed idea:
- A shy ghost wants attention and tries to flatter a new visitor.
- The visitor is scared at first, but they find a conversation-al rhythm that
  turns the scare into friendship.
- A tiny rhyme becomes the shared tool that changes the ending image.

This world keeps the story grounded in state:
- physical meters: lantern glow, chill, distance, echo, paper, chalk
- emotional memes: fear, trust, friendliness, pride, loneliness, relief
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["glow", "chill", "distance", "echo", "paper", "chalk"]:
            self.meters.setdefault(k, 0.0)
        for k in ["fear", "trust", "friendliness", "pride", "loneliness", "relief", "curiosity"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the moonlit attic"
    mood: str = "ghostly"
    affords: set[str] = field(default_factory=set)


@dataclass
class Ornament:
    id: str
    label: str
    spark: str
    soothing: str
    rhyme_word: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _set_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _set_meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def flatter(world: World, ghost: Entity, guest: Entity) -> None:
    _set_meme(ghost, "pride", 1)
    _set_meme(ghost, "loneliness", -0.5)
    _set_meme(guest, "fear", 0.5)
    _set_meter(ghost, "echo", 1)
    world.say(
        f"The little ghost floated by {world.setting.place} and tried to flatter {guest.id}. "
        f'"You look very brave," {ghost.id} said in a hushy voice.'
    )


def converse_tional(world: World, ghost: Entity, guest: Entity) -> None:
    _set_meme(ghost, "friendliness", 1)
    _set_meme(guest, "curiosity", 1)
    _set_meme(guest, "fear", -0.5)
    _set_meter(ghost, "distance", -1)
    world.say(
        f"Then they began a converse-tion-al talk, slow and careful, with pauses like little steps. "
        f"{guest.id} listened, and {ghost.id} listened back."
    )


def rhyme_time(world: World, ghost: Entity, guest: Entity, ornament: Ornament) -> None:
    _set_meter(ghost, "glow", 1)
    _set_meter(guest, "paper", 1)
    _set_meter(guest, "chalk", 1)
    _set_meme(ghost, "relief", 1)
    _set_meme(guest, "trust", 1)
    world.say(
        f"{ghost.id} whispered a tiny rhyme: "
        f'"A soft hello can slow the snow, and kind words help new friends grow." '
        f"{guest.id} smiled and wrote it on {ornament.label}, and the room felt less cold."
    )


def warm_end(world: World, ghost: Entity, guest: Entity, ornament: Ornament) -> None:
    _set_meter(ghost, "glow", 1)
    _set_meme(guest, "friendliness", 1)
    _set_meme(ghost, "loneliness", -1)
    world.say(
        f"At the end, the ghost and {guest.id} kept the rhyme near {ornament.label}, "
        f"and {ghost.id} no longer felt alone. "
        f"They were friends now, bright as a candle in a dark hall."
    )


def tell(place: Setting, ornament: Ornament, ghost_name: str, guest_name: str) -> World:
    world = World(place)
    ghost = world.add(Entity(id=ghost_name, kind="character", type="ghost", label="little ghost"))
    guest = world.add(Entity(id=guest_name, kind="character", type="child", label="new guest"))

    world.say(
        f"In {place.place}, a little ghost named {ghost.id} hovered beside an old desk. "
        f"{guest.id} had come there with a curious heart and careful feet."
    )
    world.say(
        f"The air was ghostly and still, but the room held a small promise of friendship."
    )

    world.para()
    flatter(world, ghost, guest)
    converse_tional(world, ghost, guest)

    if guest.memes["fear"] > 0:
        world.say(
            f"{guest.id} was still a bit scared, but not enough to run away. "
            f"The voice was strange, yet the kindness sounded real."
        )

    world.para()
    rhyme_time(world, ghost, guest, ornament)
    warm_end(world, ghost, guest, ornament)

    world.facts.update(
        ghost=ghost,
        guest=guest,
        ornament=ornament,
        setting=place,
    )
    return world


SETTINGS = {
    "attic": Setting(place="the moonlit attic", mood="ghostly", affords={"flatter", "conversation", "rhyme"}),
    "library": Setting(place="the quiet library", mood="whispery", affords={"flatter", "conversation", "rhyme"}),
    "hall": Setting(place="the long hallway", mood="echoing", affords={"flatter", "conversation", "rhyme"}),
}

ORNAMENTS = {
    "mirror": Ornament(
        id="mirror",
        label="an old mirror",
        spark="silver light",
        soothing="soft shine",
        rhyme_word="glow",
    ),
    "lantern": Ornament(
        id="lantern",
        label="a small lantern",
        spark="gold light",
        soothing="warm shine",
        rhyme_word="grow",
    ),
    "chalkboard": Ornament(
        id="chalkboard",
        label="a dusty chalkboard",
        spark="white dust",
        soothing="gentle marks",
        rhyme_word="slow",
    ),
}

NAMES = ["Mira", "Eli", "Nora", "Theo", "Lina", "Ben"]
GHOST_NAMES = ["Whisp", "Murmur", "Pale", "Boo", "Sable", "Moth"]


@dataclass
class StoryParams:
    place: str
    ornament: str
    ghost_name: str
    guest_name: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a young child about {f["ghost"].id} and {f["guest"].id} finding friendship through a rhyme.',
        f"Tell a gentle, spooky-but-kind story set in {f['setting'].place} where a ghost tries to flatter a visitor, then they converse and become friends.",
        f'Write a simple story that includes a conversation, a rhyme, and an ending image of friendship near {f["ornament"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    ghost, guest, orn = f["ghost"], f["guest"], f["ornament"]
    return [
        QAItem(
            question=f"Who was the little ghost trying to talk to in {f['setting'].place}?",
            answer=f"The little ghost was trying to talk to {guest.id}, a new visitor who came with a curious heart.",
        ),
        QAItem(
            question=f"What did {ghost.id} do first to get {guest.id}'s attention?",
            answer=f"First, {ghost.id} tried to flatter {guest.id} with a quiet compliment.",
        ),
        QAItem(
            question=f"What helped the spooky feeling turn into friendship?",
            answer=f"Their converse-tion-al talk and the tiny rhyme helped them feel safe, kind, and friendly with each other.",
        ),
        QAItem(
            question=f"What did they keep near the end of the story?",
            answer=f"They kept the rhyme near {orn.label}, so they could remember their new friendship.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in stories?",
            answer="A ghost in a story is usually a spooky spirit, but in a gentle story it can also be shy, lonely, and kind.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like glow and grow.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, being kind to them, and liking to spend time together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


def explain_rejection(place: str, ornament: str) -> str:
    return f"(No story: {place!r} and {ornament!r} do not make a reasonable ghost-friendship scene here.)"


ASP_RULES = r"""
ghost_story(P,O) :- place(P), ornament(O), allows(P, flatter), allows(P, conversation), allows(P, rhyme).
friendly_end(P,O) :- ghost_story(P,O).
#show ghost_story/2.
#show friendly_end/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("allows", pid, a))
    for oid in ORNAMENTS:
        lines.append(asp.fact("ornament", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show ghost_story/2."))
    return sorted(set(asp.atoms(model, "ghost_story")))


def asp_verify() -> int:
    py = {(p, o) for p in SETTINGS for o in ORNAMENTS}
    cl = set(asp_reasonable_pairs())
    if py == cl:
        print(f"OK: clingo parity matches python ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and python:")
    print(" only in clingo:", sorted(cl - py))
    print(" only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world about friendship and rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--ornament", choices=ORNAMENTS)
    ap.add_argument("--ghost-name")
    ap.add_argument("--guest-name")
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
    place = args.place or rng.choice(list(SETTINGS))
    ornament = args.ornament or rng.choice(list(ORNAMENTS))
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    guest_name = args.guest_name or rng.choice(NAMES)
    if place not in SETTINGS or ornament not in ORNAMENTS:
        raise StoryError(explain_rejection(place, ornament))
    return StoryParams(place=place, ornament=ornament, ghost_name=ghost_name, guest_name=guest_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ORNAMENTS[params.ornament], params.ghost_name, params.guest_name)
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
    StoryParams(place="attic", ornament="lantern", ghost_name="Whisp", guest_name="Mira"),
    StoryParams(place="library", ornament="mirror", ghost_name="Murmur", guest_name="Theo"),
    StoryParams(place="hall", ornament="chalkboard", ghost_name="Pale", guest_name="Nora"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show ghost_story/2.\n#show friendly_end/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_reasonable_pairs()
        print(f"{len(pairs)} compatible ghost-story pairs:")
        for p, o in pairs:
            print(f"  {p:10} {o}")
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
            header = f"### {p.ghost_name} / {p.guest_name} at {p.place} with {p.ornament}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
