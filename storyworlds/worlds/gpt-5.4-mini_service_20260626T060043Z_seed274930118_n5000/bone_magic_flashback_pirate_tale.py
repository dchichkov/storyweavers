#!/usr/bin/env python3
"""
A standalone storyworld for a small pirate tale about a magical bone and a
flashback that helps a child pirate solve a problem.

Theme: pirate tale, magic, flashback, bone.
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretakers: list[str] = field(default_factory=list)
    place: str = ""
    magical: bool = False
    lost: bool = False
    found: bool = False
    polished: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters.setdefault("dust", 0.0)
        self.meters.setdefault("shine", 0.0)
        self.memes.setdefault("hope", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("nostalgia", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "captain-girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "captain-boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    flashback_used: bool = False

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.flashback_used = self.flashback_used
        return clone


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "the deck"
    hero_type: str = "boy"
    name: str = "Finn"
    parent_type: str = "captain"
    treasure: str = "bone"
    seed: Optional[int] = None


PLACES = {
    "deck": "the deck",
    "cove": "the hidden cove",
    "dock": "the moonlit dock",
    "island": "the tiny island",
}

NAMES_BOY = ["Finn", "Jace", "Nico", "Toby", "Milo", "Pip"]
NAMES_GIRL = ["Mara", "Luna", "Sia", "Nell", "Ivy", "Rae"]


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label="the captain"))
    bone = world.add(Entity(
        id="bone",
        kind="thing",
        type="bone",
        label="bone",
        phrase="a small ivory bone with a moon-shaped mark",
        owner=hero.id,
        place=world.place,
        magical=True,
        lost=True,
        meters={"dust": 1.0, "shine": 0.0},
        memes={"hope": 0.0, "worry": 0.0, "joy": 0.0, "nostalgia": 0.0},
    ))
    world.facts.update(hero=hero, parent=parent, bone=bone)
    return world


def story_setup(world: World) -> None:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    bone: Entity = world.facts["bone"]

    world.say(
        f"{hero.label} was a little pirate who loved moonlit maps and salty songs."
    )
    world.say(
        f"One day, {hero.label} found {bone.phrase} tucked in a sea chest, and the bone seemed to glow."
    )
    bone.magical = True
    bone.memes["hope"] += 1
    hero.memes["joy"] += 1
    hero.memes["nostalgia"] += 1
    world.say(
        f"{hero.label} held the bone close, because it felt like it remembered an old story from the sea."
    )


def story_conflict(world: World) -> None:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    bone: Entity = world.facts["bone"]

    world.para()
    world.say(
        f"That evening, {hero.label} took the bone up onto {world.place}, but a gust of wind knocked it behind a crate."
    )
    bone.lost = True
    bone.found = False
    hero.memes["worry"] += 2
    hero.memes["joy"] -= 0.25
    world.say(
        f"{hero.label} searched every rope coil and every barrel, but the little bone was gone."
    )
    world.say(
        f"{parent.label} frowned and said the sea was tricky, then promised to help if {hero.label} could think of a clue."
    )


def flashback(world: World) -> None:
    hero: Entity = world.facts["hero"]
    bone: Entity = world.facts["bone"]

    world.para()
    world.flashback_used = True
    hero.memes["nostalgia"] += 2
    world.say(
        f"{hero.label} closed {hero.pronoun('possessive')} eyes, and a flashback swept in like a warm tide."
    )
    world.say(
        f"In the flashback, an old sailor had tapped the moon mark on the bone and whispered that it would shine near home."
    )
    bone.meters["shine"] += 1
    bone.meters["dust"] -= 0.5


def resolution(world: World) -> None:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    bone: Entity = world.facts["bone"]

    world.para()
    hero.memes["hope"] += 2
    world.say(
        f"{hero.label} ran to the oldest rope ladder on the deck and looked where the moonlight pooled."
    )
    bone.lost = False
    bone.found = True
    bone.place = "under the ladder"
    world.say(
        f"There, under the ladder, the bone gleamed like a tiny lantern."
    )
    world.say(
        f"{hero.label} laughed, and {parent.label} smiled as the magical bone glowed brighter than before."
    )
    hero.memes["joy"] += 3
    hero.memes["worry"] = 0
    bone.polished = True
    bone.meters["shine"] += 2
    world.say(
        f"By the end, {hero.label} tucked the bone safely into {hero.pronoun('possessive')} pocket, and the pirate ship felt lucky again."
    )


def generate_story_world(params: StoryParams) -> World:
    world = build_world(params)
    story_setup(world)
    story_conflict(world)
    flashback(world)
    resolution(world)
    return world


# ---------------------------------------------------------------------------
# Validation and text generation helpers
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError(f"Unknown place: {args.place}")
    place = args.place or rng.choice(list(PLACES))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(NAMES_GIRL if hero_type == "girl" else NAMES_BOY)
    parent_type = args.parent_type or "captain"
    treasure = args.treasure or "bone"
    if treasure != "bone":
        raise StoryError("This world only supports the magical bone treasure.")
    return StoryParams(
        place=place,
        hero_type=hero_type,
        name=name,
        parent_type=parent_type,
        treasure=treasure,
    )


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    return [
        f"Write a short pirate tale for a child named {hero.label} about a magical bone and a helpful flashback.",
        f"Tell a gentle sea adventure where {hero.label} loses a magical bone and remembers a clue from the past.",
        "Write a small pirate story with a glowing bone, a flashback, and a happy ending on the ship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    bone: Entity = world.facts["bone"]
    return [
        QAItem(
            question=f"What did {hero.label} lose on the pirate ship?",
            answer=f"{hero.label} lost the magical bone after the wind knocked it behind a crate.",
        ),
        QAItem(
            question="Why was the flashback helpful?",
            answer="The flashback reminded the child pirate that the bone would shine near home, which gave a clue for where to look.",
        ),
        QAItem(
            question=f"How did the story end for {hero.label} and {parent.label}?",
            answer=f"They found the bone under the ladder, and the magical bone gleamed while they smiled together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that shows something from earlier in time, often to help explain a clue or memory.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something can do surprising things that do not happen in ordinary life, like glowing or guiding someone.",
        ),
        QAItem(
            question="What is a bone?",
            answer="A bone is a hard part inside a body, and in stories it can also be a special object or treasure.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A bone is magical when the registry marks it magical.
magical(T) :- thing(T), kind(T,bone), special(T,magic).

% A flashback helps when it reveals a clue about where the treasure will shine.
helps(hero, bone) :- flashback(hero), clue(hero, bone), magical(bone).

% A story is reasonable when it includes the magical bone, a loss, a flashback, and a recovery.
valid_story(place, bone) :- setting(place), magical(bone), lost(bone), flashback_scene, found(bone).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "deck"),
        asp.fact("setting", "cove"),
        asp.fact("setting", "dock"),
        asp.fact("setting", "island"),
        asp.fact("thing", "bone"),
        asp.fact("kind", "bone", "bone"),
        asp.fact("special", "bone", "magic"),
        asp.fact("flashback_scene"),
        asp.fact("lost", "bone"),
        asp.fact("found", "bone"),
        asp.fact("clue", "hero", "bone"),
        asp.fact("flashback", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("deck", "bone"), ("cove", "bone"), ("dock", "bone"), ("island", "bone")}
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


# ---------------------------------------------------------------------------
# Generation / emit / CLI
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
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
        print()
        print("--- trace ---")
        for eid, ent in sample.world.entities.items():
            print(
                f"{eid}: kind={ent.kind} type={ent.type} label={ent.label} "
                f"lost={ent.lost} found={ent.found} magical={ent.magical} "
                f"shine={ent.meters.get('shine', 0)} joy={ent.memes.get('joy', 0)} "
                f"worry={ent.memes.get('worry', 0)}"
            )
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with a magical bone and a helpful flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--name")
    ap.add_argument("--parent-type", choices=["captain"], default="captain")
    ap.add_argument("--treasure", choices=["bone"], default="bone")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams(place="deck", hero_type="boy", name="Finn"),
            StoryParams(place="cove", hero_type="girl", name="Mara"),
            StoryParams(place="dock", hero_type="boy", name="Toby"),
            StoryParams(place="island", hero_type="girl", name="Luna"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        samples = []
        seen = set()
        for i in range(max(1, args.n) * 50):
            if len(samples) >= max(1, args.n):
                break
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
