#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/soggy_wasp_shotgun_mystery_to_solve_curiosity.py
===============================================================================================================

A small standalone storyworld in a ghost-story mood:
a child, a soggy clue, a wasp, and a shotgun-shaped mystery object.

The seed prompt suggests:
- soggy
- wasp
- shotgun
- Mystery to Solve
- Curiosity
- style close to Ghost Story

This world keeps the tone eerie-but-child-safe. The "shotgun" is always an
old, harmless object from the story's setting: a rusted shotgun-shaped sign,
an antique shotgun on a wall, or a broken farm shotgun locked away. It is never
used as a weapon in the story. Instead, it serves as the mysterious thing the
curious child must understand.

The simulation is intentionally small:
- a child explores a spooky place
- a soggy clue makes the mystery visible
- a wasp's nest or wasp trail points the way
- a hidden object is discovered and the fear turns into a solved mystery

World model:
- entities have physical meters and emotional memes
- state changes drive the narration
- curiosity increases when clues are found
- fear rises in the dark and falls when the mystery is solved

The story ends with a concrete image proving what changed.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    hidden: bool = False
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    reveals: str
    cause: str
    wetline: str


@dataclass
class StoryParams:
    place: str
    clue: str
    hero: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


SETTINGS = {
    "attic": Setting("the attic", "dusty and dim", {"soggy", "wasp", "shotgun"}),
    "shed": Setting("the old shed", "creaky and dark", {"soggy", "wasp", "shotgun"}),
    "barn": Setting("the barn", "wide and echoing", {"soggy", "wasp", "shotgun"}),
    "cellar": Setting("the cellar", "cold and whispery", {"soggy", "wasp", "shotgun"}),
}

CLUES = {
    "soggy_note": Clue(
        id="soggy_note",
        label="a soggy note",
        phrase="a soggy folded note",
        kind="paper",
        reveals="the hidden latch",
        cause="rainwater from a cracked roof",
        wetline="The paper had turned soft at the edges.",
    ),
    "wasp_nest": Clue(
        id="wasp_nest",
        label="a wasp nest",
        phrase="a wasp nest tucked in the beam",
        kind="nest",
        reveals="the old wall panel",
        cause="warm wood and quiet corners",
        wetline="The nest hummed like a tiny drum in the dark.",
    ),
    "soggy_bootprints": Clue(
        id="soggy_bootprints",
        label="soggy bootprints",
        phrase="soggy bootprints on the floor",
        kind="prints",
        reveals="the shotgun case",
        cause="water carried in by someone long ago",
        wetline="Each print shone where the lantern touched it.",
    ),
}

GHOST_WORDS = [
    "whisper", "creak", "hush", "shiver", "moonlight", "shadow", "lantern"
]

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Elsie", "Mabel"]
BOY_NAMES = ["Owen", "Theo", "Ben", "Finn", "Jasper", "Eli"]
TRAITS = ["curious", "brave", "gentle", "quiet", "bold"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story mystery world with a soggy clue and a wasp.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
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
    place = args.place or rng.choice(sorted(SETTINGS))
    clue = args.clue or rng.choice(sorted(CLUES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, clue=clue, hero=name, gender=gender, parent=parent, trait=trait)


def _hero_type(g: str) -> str:
    return "girl" if g == "girl" else "boy"


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=_hero_type(params.gender), label=params.hero))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    clue = CLUES[params.clue]
    hidden = world.add(Entity(
        id="mystery", type="object", label="old shotgun",
        phrase="an old shotgun locked in a glass case", hidden=True
    ))
    nest = world.add(Entity(
        id="wasp", type="thing", label="wasp",
        phrase="a little wasp with bright wings",
    ))
    note = world.add(Entity(
        id="clue", type="clue", label=clue.label, phrase=clue.phrase, hidden=False
    ))

    # Act 1: eerie setup.
    world.say(f"{hero.label} was a {params.trait} child who liked to listen for whispers in {world.setting.place}.")
    world.say(f"{world.setting.place.capitalize()} felt {world.setting.mood}, and the air seemed to hold its breath.")
    world.say(f"Near the back wall, {hero.pronoun('subject')} noticed {clue.phrase} and a tiny wasp moving close by.")
    world.para()

    # State-driven tension.
    hero.memes["curiosity"] = 1.0
    hero.memes["fear"] = 0.4
    if params.clue == "soggy_note":
        note.meters["wet"] = 1.0
        world.say(clue.wetline)
        world.say("The wet paper pointed toward a narrow crack where cold air leaked through.")
    elif params.clue == "wasp_nest":
        nest.meters["buzz"] = 1.0
        world.say(clue.wetline)
        world.say("The wasp kept circling the same beam, as if guarding a secret.")
    else:
        note.meters["wet"] = 1.0
        world.say(clue.wetline)
        world.say("The damp prints led straight toward a cloth cover near the corner.")

    world.say(f"{hero.label} wanted to solve the mystery, even though the shadows made {hero.pronoun('object')} swallow hard.")
    world.para()

    # Act 2: discovery.
    hero.memes["curiosity"] += 1.0
    if params.clue == "soggy_note":
        hidden.hidden = False
        hidden.meters["seen"] = 1.0
        world.say(f"Behind the crack, {hero.label} found {hidden.phrase}.")
        world.say(f"The note's wet edge had hidden the words, but now the message made sense.")
        world.say("It was only a forgotten hunting tool, locked away long ago, not a monster at all.")
    elif params.clue == "wasp_nest":
        hidden.hidden = False
        hidden.meters["seen"] = 1.0
        world.say(f"Following the wasp's path, {hero.label} found {hidden.phrase} behind a dusty curtain.")
        world.say("The wasp had not been guarding danger. It had been living near the warm glass case.")
        world.say("The old shotgun was just an old thing from a long-ago day, sleeping in the dark.")
    else:
        hidden.hidden = False
        hidden.meters["seen"] = 1.0
        world.say(f"The soggy bootprints ended at {hidden.phrase}.")
        world.say("The case was not haunted. It was only stuck shut with rust and age.")
        world.say("The wasp was there because a tiny gap near the latch let it in from outside.")

    # Act 3: resolution.
    world.para()
    hero.memes["fear"] = 0.0
    hero.memes["relief"] = 1.0
    world.say(f"{hero.label} laughed softly, because the mystery had been solved and the room felt less strange.")
    world.say(f"{hero.pronoun('subject').capitalize()} told {parent.label} what {hero.pronoun('subject')} had found.")
    world.say(f"Together they left the old shotgun safely in place, closed the case, and carried the soggy clue into the light.")
    world.say(f"At the door, the wasp hummed past the lantern, and {hero.label} stepped home with a curious smile instead of a shiver.")

    world.facts = {
        "hero": hero,
        "parent": parent,
        "clue": clue,
        "setting": world.setting,
        "mystery": hidden,
        "wasp": nest,
    }
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    clue: Clue = f["clue"]
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"What kind of mystery did {hero.label} try to solve in {world.setting.place}?",
            answer=f"{hero.label} tried to solve a spooky little mystery about {clue.label} and the old shotgun hidden in the dark place.",
        ),
        QAItem(
            question=f"Why did the story feel less scary at the end?",
            answer=f"It felt less scary because {hero.label} learned the strange thing was only an old shotgun and the clues all made sense.",
        ),
        QAItem(
            question=f"Who did {hero.label} tell after the mystery was solved?",
            answer=f"{hero.label} told {parent.label} what {hero.pronoun('subject')} had found, and they left the room together.",
        ),
        QAItem(
            question=f"What was the soggy clue in the story?",
            answer=f"The soggy clue was {clue.phrase}, which helped point toward the hidden old shotgun.",
        ),
        QAItem(
            question=f"What did the wasp have to do with the mystery?",
            answer="The wasp helped lead the child to the secret place, but it was not a monster. It was only part of the clue trail.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does soggy mean?",
            answer="Soggy means wet and soft, like paper or bread that has soaked up too much water.",
        ),
        QAItem(
            question="What is a wasp?",
            answer="A wasp is a small flying insect with a narrow waist and a buzz that people notice quickly.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood at first, so people look for clues to solve it.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone want to look, ask, and learn more about a surprising thing.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue: Clue = f["clue"]
    return [
        f"Write a short ghost-story for a child named {hero.label} about a soggy clue and a wasp.",
        f"Tell a spooky but gentle mystery where {hero.label} solves what the old shotgun in {world.setting.place} means.",
        f"Write a curious child story with a quiet haunted mood, a soggy clue, and a harmless old shotgun mystery.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
mystery_solved(H) :- clue(H), curiosity(H), soggy(H).
eerie(H) :- mystery_solved(H), wasp(H).
resolved_story(H) :- mystery_solved(H), not scary_end(H).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("clue", "soggy"),
        asp.fact("clue", "wasp"),
        asp.fact("clue", "shotgun"),
        asp.fact("curiosity", "soggy"),
        asp.fact("wasp", "wasp"),
        asp.fact("soggy", "soggy"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_world_combo_validity() -> bool:
    return True


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_solved/1."))
    atoms = set(asp.atoms(model, "mystery_solved"))
    ok = ("soggy",) in atoms
    if ok:
        print("OK: ASP model produced the expected mystery_solved(soggy).")
        return 0
    print("MISMATCH: ASP did not produce the expected result.")
    return 1


CURATED = [
    StoryParams(place="attic", clue="soggy_note", hero="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="shed", clue="wasp_nest", hero="Owen", gender="boy", parent="father", trait="quiet"),
    StoryParams(place="barn", clue="soggy_bootprints", hero="Ivy", gender="girl", parent="mother", trait="brave"),
]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show mystery_solved/1."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery_solved/1."))
        print(asp.atoms(model, "mystery_solved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            p = resolve_params(args, rng)
            p.seed = base_seed + i
            samples.append(generate(p))

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
