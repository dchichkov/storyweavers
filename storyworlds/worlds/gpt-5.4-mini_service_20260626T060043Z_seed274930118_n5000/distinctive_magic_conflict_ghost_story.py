#!/usr/bin/env python3
"""
A small ghost-story world with a magical misunderstanding.

Premise:
- A child visits a quiet old place and notices a ghostly presence.
- A distinctive magical object matters to the ghost.
- A conflict appears when the child wants to keep or use the magic item.
- The tension resolves through honesty, sharing, and a gentle spell.

This is a standalone storyworld script for the Storyweavers repo.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    present: bool = True
    visible: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the old house"
    mood: str = "quiet"
    affords: set[str] = field(default_factory=set)


@dataclass
class MagicItem:
    id: str
    label: str
    phrase: str
    glow: str
    effect: str
    kind: str = "thing"
    satisfies: set[str] = field(default_factory=set)
    risky: bool = True


@dataclass
class StoryParams:
    place: str
    magic: str
    conflict: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.magic_state: str = "sleeping"

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.magic_state = self.magic_state
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "old_house": Setting(place="the old house", mood="quiet", affords={"lantern", "mirror", "music_box"}),
    "attic": Setting(place="the attic", mood="dusty", affords={"lantern", "mirror"}),
    "garden": Setting(place="the moonlit garden", mood="still", affords={"lantern", "music_box"}),
    "library": Setting(place="the little library", mood="hushed", affords={"mirror", "music_box"}),
}

MAGIC_ITEMS = {
    "lantern": MagicItem(
        id="lantern",
        label="lantern",
        phrase="a small silver lantern",
        glow="a blue glow",
        effect="show the way through dark corners",
        satisfies={"light", "path"},
    ),
    "mirror": MagicItem(
        id="mirror",
        label="mirror",
        phrase="a round mirror with a star on the back",
        glow="a pale shimmer",
        effect="show a hidden feeling",
        satisfies={"truth", "memory"},
    ),
    "music_box": MagicItem(
        id="music_box",
        label="music box",
        phrase="a tiny music box with a chipped lid",
        glow="a soft golden twinkle",
        effect="calm frightened hearts",
        satisfies={"calm", "peace"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Ivy", "Nora", "Zoe", "Eve"]
BOY_NAMES = ["Leo", "Finn", "Eli", "Noah", "Theo", "Max"]
TRAITS = ["curious", "quiet", "brave", "gentle", "restless", "distinctive"]

CONFLICTS = {
    "fear": "the ghost was afraid the magic item would be taken away",
    "keeping": "the child wanted to keep the magic item too long",
    "broken": "the child thought the item was broken and pulled it apart",
}


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with magic and conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGIC_ITEMS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


def _gender_ok(magic_id: str, gender: str) -> bool:
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for magic in setting.affords:
            for conflict in CONFLICTS:
                out.append((place, magic, conflict))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.magic and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.place and args.magic and args.magic not in SETTINGS[args.place].affords:
        raise StoryError("That magic item does not fit this place.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.magic is None or c[1] == args.magic)
              and (args.conflict is None or c[2] == args.conflict)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, magic, conflict = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, magic=magic, conflict=conflict, name=name, gender=gender, parent=parent)


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _hero_type(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def _parent_label(parent: str) -> str:
    return "mom" if parent == "mother" else "dad"


def _setup_story(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity]:
    hero = world.add(Entity(id=params.name, kind="character", type=_hero_type(params.gender)))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the ghost"))
    item_cfg = MAGIC_ITEMS[params.magic]
    item = world.add(Entity(
        id=item_cfg.id,
        kind="thing",
        type=item_cfg.id,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=ghost.id,
        held_by=ghost.id,
    ))
    world.facts.update(hero=hero, ghost=ghost, item=item, item_cfg=item_cfg)
    return hero, ghost, item


def _tell(world: World, params: StoryParams) -> None:
    hero = world.facts["hero"]
    ghost = world.facts["ghost"]
    item = world.facts["item"]
    item_cfg = world.facts["item_cfg"]
    parent = _parent_label(params.parent)

    world.say(
        f"{hero.id} went into {world.setting.place} on a quiet evening. "
        f"The air felt hushed, and {hero.pronoun('possessive')} steps echoed softly."
    )
    world.say(
        f"Then {hero.id} saw {ghost.label} near a dusty corner, holding "
        f"{_article(item_cfg.label)} {item_cfg.label} with {item_cfg.glow}."
    )
    world.say(
        f"It was a distinctive little thing, and {hero.id} could tell at once that "
        f"it mattered."
    )

    world.para()
    if params.conflict == "fear":
        world.say(
            f"{ghost.label} whispered that {hero.id} should not touch it, because "
            f"the magic might vanish if it left {ghost.pronoun('possessive')} hands."
        )
        hero.memes["desire"] = 1
        world.say(
            f"But {hero.id} wanted to help and reached out anyway, which made the room feel tense."
        )
    elif params.conflict == "keeping":
        hero.memes["possessive"] = 1
        world.say(
            f"{hero.id} decided the {item.label} was too wonderful to put down, and "
            f"that made {ghost.label} drift back in worry."
        )
        world.say(
            f"The ghost asked for it back, but {hero.id} held on a moment too long."
        )
    else:
        world.say(
            f"{hero.id} thought the {item.label} was broken and tugged at the lid, "
            f"which startled {ghost.label} and made the glow flicker."
        )
        hero.memes["fear"] = 1

    world.para()
    if params.conflict == "fear":
        world.say(
            f"{hero.id} took a careful breath and said, 'I only want to help.' "
            f"{ghost.label} listened, and the {item.label} stopped shaking."
        )
    elif params.conflict == "keeping":
        world.say(
            f"{hero.id} gave the {item.label} back at last. That honest choice made "
            f"{ghost.label}'s pale face look calmer."
        )
    else:
        world.say(
            f"{hero.id} opened the lid gently instead of forcing it. Inside was not a broken piece at all, "
            f"but a tiny heart-shaped charm that needed a soft tap to wake up."
        )

    world.say(
        f"Then the magic worked: {item_cfg.effect}, and the room filled with "
        f"a quiet shimmer."
    )
    world.say(
        f"{ghost.label} smiled, less lonely now, and {hero.id} left with a brave, "
        f"distinctive memory instead of a fright."
    )

    world.facts["parent"] = parent
    world.facts["conflict"] = params.conflict


def tell_story(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    _setup_story(world, params)
    _tell(world, params)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item_cfg = f["item_cfg"]
    return [
        f'Write a short ghost story for a child named {hero.id} that includes {item_cfg.label} and a gentle magical conflict.',
        f'Tell a spooky-but-kind story where {hero.id} meets a ghost in {world.setting.place} and learns to share {item_cfg.phrase}.',
        f'Create a simple story with a distinctive magic object, a worried ghost, and a peaceful ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    item_cfg = f["item_cfg"]
    ghost = f["ghost"]
    parent = f["parent"]
    conflict = f["conflict"]
    return [
        QAItem(
            question=f"Who met the ghost in the story?",
            answer=f"{hero.id} met {ghost.label} in {world.setting.place}.",
        ),
        QAItem(
            question=f"What magical object was in the story?",
            answer=f"The magical object was {item_cfg.phrase}. It gave off {item_cfg.glow}.",
        ),
        QAItem(
            question=f"What was the conflict in the story?",
            answer=f"The conflict was that {CONFLICTS[conflict]}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the magic working kindly, the ghost calming down, and {hero.id} leaving with a brave memory.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    out.append(QAItem(
        question="What is a ghost?",
        answer="A ghost is a spooky spirit from a story, often pictured as pale, see-through, and able to drift through places quietly.",
    ))
    out.append(QAItem(
        question="What does magic mean in a story?",
        answer="Magic means something unusual can happen, like glowing light, special powers, or a charm that changes how someone feels.",
    ))
    out.append(QAItem(
        question="Why can old houses feel spooky?",
        answer="Old houses can feel spooky because they are quiet, creaky, and full of shadows that make people imagine hidden things.",
    ))
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid(Place, Magic, Conflict) :- place(Place), affords(Place, Magic), conflict(Conflict).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for magic in sorted(setting.affords):
            lines.append(asp.fact("affords", place, magic))
    for magic in MAGIC_ITEMS:
        lines.append(asp.fact("magic", magic))
    for conflict in CONFLICTS:
        lines.append(asp.fact("conflict", conflict))
    return "\n".join(lines)


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
    print("MISMATCH between clingo and valid_combos():")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation / emission
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams(place="attic", magic="lantern", conflict="fear", name="Mia", gender="girl", parent="mother"),
    StoryParams(place="garden", magic="music_box", conflict="keeping", name="Leo", gender="boy", parent="father"),
    StoryParams(place="library", magic="mirror", conflict="broken", name="Nora", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos")
        for row in combos:
            print(row)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.magic} at {p.place} ({p.conflict})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
