#!/usr/bin/env python3
"""
A small storyworld for a gentle ghost story about a pomegranate surprise,
an anxious inner monologue, and a reconciliation with a ghostly helper.

Premise:
- A child discovers a pomegranate in a quiet garden at dusk.
- A ghost appears, surprising the child.
- The child worries in an inner monologue that the ghost wants the pomegranate.
- The ghost only wants to help open it.
- They reconcile and share the bright fruit.

The world model tracks:
- physical meters: surprise, hunger, cracked_shell, juice, chill
- emotional memes: fear, curiosity, trust, comfort, gratitude
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
    touched: bool = False
    seen: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["surprise", "hunger", "cracked_shell", "juice", "chill"]:
            self.meters.setdefault(k, 0.0)
        for k in ["fear", "curiosity", "trust", "comfort", "gratitude", "loneliness"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the garden"
    dusk: bool = True
    has_tree: bool = True
    quiet: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    ghost_name: str
    fruit: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _bump(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amt


def _bump_m(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amt


def setup_world(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    child = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    ghost = world.add(Entity(id=params.ghost_name, kind="character", type="ghost", label=params.ghost_name))
    fruit = world.add(Entity(id="fruit", kind="thing", type="fruit", label="pomegranate",
                             phrase=f"a red pomegranate with a hard shell", owner=child.id, caretaker=child.id))
    world.facts["child"] = child
    world.facts["ghost"] = ghost
    world.facts["fruit"] = fruit
    return world


def inner_monologue(world: World, child: Entity, ghost: Entity, fruit: Entity) -> None:
    _bump_m(child, "fear", 1)
    _bump_m(child, "curiosity", 1)
    _bump(child, "surprise", 1)
    world.say(
        f"{child.id} stopped short in {world.setting.place}. "
        f"In {child.pronoun('possessive')} mind, a little voice whispered, "
        f"“A ghost is here. Maybe {ghost.id} came for my pomegranate.”"
    )


def surprise_entry(world: World, ghost: Entity) -> None:
    _bump_m(ghost, "loneliness", 1)
    _bump(ghost, "chill", 1)
    world.say(
        f"Then {ghost.id} drifted out of the shadows with a soft rustle, "
        f"like cold air brushing leaves. The surprise made the night feel thinner."
    )


def offer_help(world: World, ghost: Entity, child: Entity, fruit: Entity) -> None:
    _bump_m(ghost, "curiosity", 1)
    world.say(
        f'“I do not want to scare you,” {ghost.id} said gently. '
        f'“I only saw your pomegranate and wondered if you would share it with me.”'
    )
    world.say(
        f"{child.id} looked at the fruit, then at the ghost, and listened to the small, careful voice in "
        f"{child.pronoun('possessive')} own head."
    )


def worry_turns(world: World, child: Entity, ghost: Entity, fruit: Entity) -> None:
    _bump_m(child, "fear", 1)
    _bump_m(child, "loneliness", 1)
    world.say(
        f"{child.id}'s inner monologue fluttered: “What if {ghost.id} takes it? What if I am alone with a hungry shadow?”"
    )
    world.say(
        f"Still, {child.id} held the pomegranate closer and waited."
    )


def open_fruit(world: World, child: Entity, ghost: Entity, fruit: Entity) -> None:
    _bump(fruit, "cracked_shell", 1)
    _bump(fruit, "juice", 1)
    _bump_m(child, "curiosity", 1)
    _bump_m(ghost, "trust", 1)
    world.say(
        f"{ghost.id} lifted one pale finger and tapped the pomegranate just once. "
        f"The hard shell cracked with a neat little pop, and bright red seeds glowed inside like tiny lanterns."
    )


def reconcile(world: World, child: Entity, ghost: Entity, fruit: Entity) -> None:
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    _bump_m(child, "trust", 2)
    _bump_m(child, "comfort", 1)
    _bump_m(child, "gratitude", 1)
    _bump_m(ghost, "comfort", 1)
    world.say(
        f"{child.id} breathed out slowly. “You were not here to steal it,” {child.id} said. "
        f"“You were here to help.”"
    )
    world.say(
        f"{ghost.id} gave a shy nod, and the two of them sat together in the quiet garden, "
        f"sharing the pomegranate one seed at a time."
    )
    world.say(
        f"By the end, {child.id} was no longer frightened, only warm and a little amazed, "
        f"while {ghost.id} looked less lonely than before."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    child = world.get(params.hero_name)
    ghost = world.get(params.ghost_name)
    fruit = world.get("fruit")

    world.say(
        f"At dusk in {world.setting.place}, {child.id} found a round pomegranate waiting on a stone bench."
    )
    world.say(
        f"{child.id} loved its glossy red skin and kept thinking about how sweet it might taste."
    )

    world.para()
    surprise_entry(world, ghost)
    inner_monologue(world, child, ghost, fruit)
    offer_help(world, ghost, child, fruit)

    world.para()
    worry_turns(world, child, ghost, fruit)
    open_fruit(world, child, ghost, fruit)
    reconcile(world, child, ghost, fruit)

    world.facts.update(child=child, ghost=ghost, fruit=fruit, params=params)
    return world


SETTINGS = {
    "garden": Setting(place="the garden"),
    "orchard": Setting(place="the orchard"),
    "courtyard": Setting(place="the courtyard"),
}

CHILD_NAMES = ["Mina", "Toby", "Lena", "Sami", "Ivy", "Owen"]
GHOST_NAMES = ["Murmur", "Pale Ben", "Mist", "Snowlight", "Wisp"]
HERO_TYPES = ["girl", "boy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: a pomegranate, a surprise, and a reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--ghost-name", choices=GHOST_NAMES)
    ap.add_argument("--gender", choices=HERO_TYPES)
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
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(CHILD_NAMES)
    gender = args.gender or rng.choice(HERO_TYPES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(place=place, hero_name=name, hero_type=gender, ghost_name=ghost_name, fruit="pomegranate")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    ghost = f["ghost"]
    return [
        f"Write a gentle ghost story about {child.id}, a pomegranate, and a surprising visitor.",
        f"Tell a short story where {ghost.id} appears in {world.setting.place} and helps open a pomegranate.",
        f"Write a child-friendly story with inner monologue, surprise, and reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, ghost, fruit = f["child"], f["ghost"], f["fruit"]
    return [
        QAItem(
            question=f"What did {child.id} find in {world.setting.place} at dusk?",
            answer=f"{child.id} found a pomegranate on a stone bench in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {child.id} feel scared when {ghost.id} appeared?",
            answer=f"{child.id} was surprised by the ghost and thought in an inner monologue that {ghost.id} might want to take the pomegranate.",
        ),
        QAItem(
            question=f"How did {child.id} and {ghost.id} reconcile?",
            answer=f"{ghost.id} helped crack open the pomegranate, and then they shared the seeds together so the fear turned into trust and comfort.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pomegranate?",
            answer="A pomegranate is a round fruit with a hard red shell and many juicy seeds inside.",
        ),
        QAItem(
            question="What is a ghost in a gentle story?",
            answer="In a gentle story, a ghost is a spooky-looking character who can still be kind, lonely, or helpful.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice a character hears in their own mind when they are thinking.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story q&a ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world q&a ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_story(P, N, G, H) :- valid_place(P), child_name(N), ghost_name(G), hero_type(H).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for n in CHILD_NAMES:
        lines.append(asp.fact("child_name", n))
    for g in GHOST_NAMES:
        lines.append(asp.fact("ghost_name", g))
    for h in HERO_TYPES:
        lines.append(asp.fact("hero_type", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = set((p, n, g, h) for p in SETTINGS for n in CHILD_NAMES for g in GHOST_NAMES for h in HERO_TYPES)
    if atoms == py:
        print(f"OK: clingo gate matches Python registry space ({len(atoms)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if atoms - py:
        print("  only in clingo:", sorted(atoms - py))
    if py - atoms:
        print("  only in python:", sorted(py - atoms))
    return 1


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for item in combos:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    for i in range(args.n if not args.all else 1):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        samples.append(generate(params))
        if not args.all:
            break

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
