#!/usr/bin/env python3
"""
A small story world for a pirate-style tale set in a storage closet, with a
flashback about a fridge used as a hiding place for treasure snacks.

Premise:
- A tiny pirate child and a grown-up are in a storage closet.
- The child wants to open a fridge that is being used as a storage cupboard.
- The grown-up worries the fridge will spill cold snacks and make a mess.

Turn:
- A flashback remembers how the fridge was once used to keep a party cake cold
  during a stormy ship-toy game, which gives the child a clue about careful use.

Resolution:
- They move the jar of sea-salt lemons aside, open the fridge slowly, and find
  the snack treasure without making a mess.
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
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    opened: bool = False
    hidden: bool = False
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
class Location:
    name: str = "the storage closet"
    affords: set[str] = field(default_factory=set)


@dataclass
class FlashbackCue:
    trigger: str
    memory_line: str
    lesson: str


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    treasure: str
    seed: Optional[int] = None


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.flashback_seen: bool = False

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

LOCATION = Location(name="the storage closet", affords={"open_fridge", "move_crate", "remember"})
FLASHBACK = FlashbackCue(
    trigger="the fridge hummed",
    memory_line="That hum made the child remember a stormy night when the fridge kept a birthday cake safe and cold.",
    lesson="When treasure needs care, slow hands work better than rushed ones.",
)

TREASURES = {
    "cookies": {
        "label": "tin of ship-shaped cookies",
        "phrase": "a tin of ship-shaped cookies",
        "mess": "crumbly",
    },
    "pear": {
        "label": "pear slices",
        "phrase": "a bowl of pear slices",
        "mess": "juicy",
    },
    "jam": {
        "label": "jar of berry jam",
        "phrase": "a jar of berry jam",
        "mess": "sticky",
    },
    "cake": {
        "label": "small cake",
        "phrase": "a small cake",
        "mess": "frosty",
    },
}

GIRL_NAMES = ["Mina", "Pia", "Nora", "Lina", "Ruby", "Tess"]
BOY_NAMES = ["Finn", "Jett", "Kip", "Owen", "Rafi", "Theo"]
PARENT_NAMES = {"mother": "mom", "father": "dad"}


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def introduce(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"{child.id} was a little pirate who loved quiet treasure hunts, "
        f"and {child.pronoun('possessive')} {parent.label} watched over the storage closet."
    )


def setup_closet(world: World, fridge: Entity, treasure: Entity) -> None:
    world.say(
        f"In the storage closet, an old fridge sat beside stacked boxes and a coiled rope."
    )
    world.say(
        f"Inside the fridge was {treasure.phrase}, tucked away like secret pirate loot."
    )


def want_treasure(world: World, child: Entity, fridge: Entity, treasure: Entity) -> None:
    child.memes["want"] = child.memes.get("want", 0) + 1
    world.say(
        f"{child.id} wanted to open the fridge right away, because {treasure.label} "
        f"felt like a treasure chest waiting to be found."
    )


def warning(world: World, parent: Entity, child: Entity, treasure: Entity) -> None:
    parent.memes["worry"] = parent.memes.get("worry", 0) + 1
    world.say(
        f'"Easy now," {parent.label} said. "If we rush, {treasure.label} could spill or break."'
    )


def flashback(world: World, child: Entity, fridge: Entity) -> None:
    world.flashback_seen = True
    world.say(
        f"{FLASHBACK.trigger}."
    )
    world.say(
        f"Flashback: {FLASHBACK.memory_line}"
    )
    world.say(
        f"That memory taught {child.id} {FLASHBACK.lesson.lower()}"
    )


def move_crate(world: World, child: Entity) -> None:
    child.meters["care"] = child.meters.get("care", 0) + 1
    world.say(
        f"{child.id} pushed a crate of old maps aside so the fridge door could open without bumping anything."
    )


def open_fridge(world: World, child: Entity, fridge: Entity, treasure: Entity) -> None:
    fridge.opened = True
    treasure.hidden = False
    child.memes["pride"] = child.memes.get("pride", 0) + 1
    world.say(
        f"{child.id} opened the fridge slowly, and the cool air puffed out like a gentle sea breeze."
    )
    world.say(
        f"Inside, {treasure.label} was still safe, and no one had to clean up a mess."
    )


def ending(world: World, child: Entity, parent: Entity, treasure: Entity) -> None:
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    world.say(
        f"{child.id} grinned, {child.pronoun('possessive')} {parent.label} laughed, "
        f"and the two of them shared the treasure while the closet stayed neat and tidy."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
child_wants_open(C) :- child(C).
need_flashback(C) :- child_wants_open(C), fridge(F), treasure_in(F,T), risky(T).
flashback(C) :- need_flashback(C).
safe_open(C) :- child(C), parent(P), fridge(F), treasure_in(F,T), careful(T), remembers(C).
valid_story(C,P,T) :- child(C), parent(P), fridge(F), treasure_in(F,T), safe_open(C), location(closet).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("location", "closet"))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("parent", "parent"))
    lines.append(asp.fact("fridge", "fridge"))
    lines.append(asp.fact("remembers", "child"))
    for tid, info in TREASURES.items():
        lines.append(asp.fact("treasure_in", "fridge", tid))
        if info["mess"] in {"crumbly", "sticky", "juicy", "frosty"}:
            lines.append(asp.fact("risky", tid))
        lines.append(asp.fact("careful", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {("child", "parent", tid) for tid in TREASURES}
    if atoms == py:
        print(f"OK: ASP and Python agree on {len(atoms)} story shapes.")
        return 0
    print("MISMATCH between ASP and Python story shapes.")
    print("ASP:", sorted(atoms))
    print("PY:", sorted(py))
    return 1


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(LOCATION)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=PARENT_NAMES[params.parent]))
    fridge = world.add(Entity(id="fridge", type="fridge", label="fridge", opened=False))
    treasure_info = TREASURES[params.treasure]
    treasure = world.add(Entity(
        id=params.treasure,
        type="treasure",
        label=treasure_info["label"],
        phrase=treasure_info["phrase"],
        hidden=True,
        caretaker=parent.id,
    ))

    introduce(world, child, parent)
    setup_closet(world, fridge, treasure)
    world.para()
    want_treasure(world, child, fridge, treasure)
    warning(world, parent, child, treasure)
    flashback(world, child, fridge)
    move_crate(world, child)
    open_fridge(world, child, fridge, treasure)
    ending(world, child, parent, treasure)

    world.facts.update(
        child=child,
        parent=parent,
        fridge=fridge,
        treasure=treasure,
        flashback=True,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    treasure: Entity = f["treasure"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    return [
        'Write a pirate-style story for a small child in a storage closet that includes a fridge.',
        f"Tell a gentle story about {child.id}, {child.pronoun('possessive')} {parent.label}, and {treasure.label} with a flashback.",
        "Write a short story where a child remembers a past moment and then uses that memory to open a fridge carefully.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    treasure: Entity = f["treasure"]  # type: ignore[assignment]
    fridge: Entity = f["fridge"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Where did {child.id} find the treasure?",
            answer=f"{child.id} found it in the fridge in the storage closet.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry when {child.id} wanted to open the fridge?",
            answer=f"{parent.label} worried because {treasure.label} could spill or break if they rushed.",
        ),
        QAItem(
            question="What did the flashback help the child remember?",
            answer="It helped the child remember that slow hands can keep treasure safe.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The fridge was opened carefully, the treasure stayed safe, and the storage closet stayed neat.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fridge for?",
            answer="A fridge keeps food cold so it stays fresh longer.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a memory of something that happened before the main part of the story.",
        ),
        QAItem(
            question="What is a storage closet?",
            answer="A storage closet is a small room where people keep boxes, tools, and other things they do not use all the time.",
        ),
        QAItem(
            question="Why do pirates like treasure?",
            answer="Pirates like treasure because it feels exciting and special, like a reward from an adventure.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-style storage-closet story world with a flashback and a fridge.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--treasure", choices=sorted(TREASURES))
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
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    treasure = args.treasure or rng.choice(sorted(TREASURES))
    return StoryParams(name=name, gender=gender, parent=parent, treasure=treasure)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.kind == "character":
            bits.append(f"memes={dict(e.memes)}")
            bits.append(f"meters={dict(e.meters)}")
        if e.type == "fridge":
            bits.append(f"opened={e.opened}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"{e.id}: {', '.join(bits) if bits else 'no state'}")
    lines.append(f"flashback_seen={world.flashback_seen}")
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
    StoryParams(name="Mina", gender="girl", parent="mother", treasure="cookies"),
    StoryParams(name="Finn", gender="boy", parent="father", treasure="jam"),
    StoryParams(name="Ruby", gender="girl", parent="mother", treasure="cake"),
]


def asp_list() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_list()
        print(f"{len(triples)} compatible story shapes:")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
