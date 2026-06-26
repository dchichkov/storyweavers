#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from collections import defaultdict
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
    owner: Optional[str] = None
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "lady"}
        male = {"boy", "father", "man", "king", "lord"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    dark: bool = False
    props: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    place: str
    can_write: bool = False
    can_hide: bool = False
    can_move: bool = False


@dataclass
class StoryParams:
    place: str
    clue: str
    culprit: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "council_room": Place("council_room", "the council room", dark=False, props={"table", "lamp", "chairs", "notice_board"}),
    "garden": Place("garden", "the garden", dark=False, props={"hedge", "stone_path", "flowers"}),
    "shed": Place("shed", "the shed", dark=True, props={"rope", "boxes", "bucket"}),
}

CLUES = {
    "ink_note": Clue("ink_note", "an ink note", "note", "council_room", can_write=True),
    "mud_track": Clue("mud_track", "muddy tracks", "track", "garden", can_hide=True),
    "lost_key": Clue("lost_key", "the lost key", "key", "shed", can_move=True),
}

CULPRITS = {
    "mouse": "mouse",
    "squirrel": "squirrel",
    "hedgehog": "hedgehog",
}

NAMES = ["Mina", "Toby", "Pip", "Nora", "Lark", "Finn", "Mabel", "Otto"]
HELPER_NAMES = ["Rue", "Wren", "Dot", "Ivy", "Jules", "Bram"]

TRAITS = ["brave", "careful", "curious", "quiet", "steady", "gentle"]


def _r_search(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["bravery"] < THRESHOLD:
        return out
    clue = world.get("clue")
    if clue.meters["found"] >= THRESHOLD:
        return out
    clue.meters["found"] += 1
    hero.memes["confidence"] += 1
    out.append(f"{hero.id} found the clue.")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    culprit = world.get("culprit")
    if clue.meters["found"] < THRESHOLD:
        return out
    if world.fired and ("reveal", culprit.id) in world.fired:
        return out
    world.fired.add(("reveal", culprit.id))
    culprit.memes["worry"] += 1
    out.append("The secret came out.")
    return out


def _r_happy_end(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.get("culprit")
    hero = world.get("hero")
    helper = world.get("helper")
    if culprit.memes["worry"] < THRESHOLD:
        return out
    sig = ("ending",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    culprit.memes["guilt"] = 0
    out.append("The council forgave the mistake.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_r_search, _r_reveal, _r_happy_end):
            lines = fn(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def build_story_places() -> list[Place]:
    return list(PLACES.values())


def choose_culprit(rng: random.Random) -> str:
    return rng.choice(list(CULPRITS))


def valid_combo(place: str, clue: str, culprit: str) -> bool:
    return place in PLACES and clue in CLUES and culprit in CULPRITS


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for c in CLUES:
            for k in CULPRITS:
                if valid_combo(p, c, k):
                    combos.append((p, c, k))
    return combos


@dataclass
class StoryParams:
    place: str
    clue: str
    culprit: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit story world about a council, a clue, and a brave reveal.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--hero-type", default="mouse", choices=["mouse", "bird", "fox", "rabbit", "cat"])
    ap.add_argument("--helper-type", default="sparrow", choices=["mouse", "bird", "fox", "rabbit", "cat", "otter"])
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
    place = args.place or rng.choice(list(PLACES))
    clue = args.clue or rng.choice(list(CLUES))
    culprit = args.culprit or choose_culprit(rng)
    if not valid_combo(place, clue, culprit):
        raise StoryError("No valid council mystery matches those choices.")
    hero_name = args.name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        place=place,
        clue=clue,
        culprit=culprit,
        hero_name=hero_name,
        hero_type=args.hero_type,
        helper_name=helper_name,
        helper_type=args.helper_type,
    )


def tell(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity("hero", kind="character", type=params.hero_type, label=params.hero_name, traits=["brave", "curious"]))
    helper = world.add(Entity("helper", kind="character", type=params.helper_type, label=params.helper_name, traits=["kind"]))
    culprit = world.add(Entity("culprit", kind="character", type=CULPRITS[params.culprit], label=params.culprit))
    clue = world.add(Entity("clue", kind="thing", type=CLUES[params.clue].kind, label=CLUES[params.clue].label, place=CLUES[params.clue].place))

    world.facts.update(hero=hero, helper=helper, culprit=culprit, clue=clue, params=params)

    world.say(f"{hero.label} came to the council room because the council had a problem.")
    world.say(f"The council kept a small seat open for {hero.label}, who liked to write careful notes.")
    world.say(f"That day, the council was upset because {clue.label} had gone missing.")

    world.para()
    world.say(f"{helper.label} pointed at the floor and whispered, 'Someone left a clue.'")
    hero.memes["bravery"] += 1
    hero.memes["worry"] += 1
    world.say(f"{hero.label} was brave enough to search the dark corners, even though the room felt strange.")
    propagate(world, narrate=True)

    world.para()
    world.say(f"Near {PLACES[params.place].label}, {hero.label} found the first hint: {clue.label}.")
    clue.meters["found"] += 1
    culprit.memes["worry"] += 1
    world.say(f"Then came a surprise: the clue matched {culprit.label}, who had borrowed it to write a secret note for the council.")
    world.say(f"{culprit.label} had not meant harm; {culprit.label} only wanted to help the council remember the meeting.")
    world.say(f"{helper.label} said the note should have been shared, not hidden.")
    propagate(world, narrate=True)

    world.para()
    world.say(f"{hero.label} took a deep breath and asked the hard question kindly.")
    hero.memes["bravery"] += 1
    culprit.memes["guilt"] += 1
    world.say(f"{culprit.label} apologized and brought back the missing thing.")
    world.say(f"The council laughed softly, because the mystery was solved and nobody was lost or hurt.")
    world.say(f"In the end, {hero.label} wrote the new council note, {helper.label} held the lamp, and everyone went home to a happy ending.")
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    culprit.memes["joy"] += 1
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].label
    clue = f["clue"].label
    culprit = f["culprit"].label
    place = world.place.label
    return [
        f"Write a child-friendly whodunit about {hero}, a council room, and {clue}.",
        f"Tell a short mystery story where someone in {place} has to be brave, follow a clue, and find out what {culprit} did.",
        f"Write a story that includes the words stickle, write, and council, with a surprise and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    helper = f["helper"].label
    culprit = f["culprit"].label
    clue = f["clue"].label
    place = world.place.label
    return [
        QAItem(
            question=f"Who was brave enough to search in the council room?",
            answer=f"{hero} was brave enough to search in {place}, because the council needed help solving the mystery.",
        ),
        QAItem(
            question=f"What clue was missing from the council?",
            answer=f"The missing clue was {clue}, and it helped lead the search to the truth.",
        ),
        QAItem(
            question=f"Who turned out to be behind the surprise in the story?",
            answer=f"{culprit} was behind the surprise, but only because {culprit} had borrowed the clue to write a secret note.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero} writing the new council note, {helper} helping, and everyone enjoying a happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a council?",
            answer="A council is a group of people or animals who meet to talk about a shared problem and decide what to do.",
        ),
        QAItem(
            question="What does it mean to be brave?",
            answer="Being brave means doing something hard or scary when you need to help someone or solve a problem.",
        ),
        QAItem(
            question="What is a surprise in a mystery story?",
            answer="A surprise is something unexpected that changes what the characters think is happening.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters finish feeling safe, glad, or peaceful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
place(council_room). place(garden). place(shed).
clue(ink_note). clue(mud_track). clue(lost_key).
culprit(mouse). culprit(squirrel). culprit(hedgehog).

valid(P, C, K) :- place(P), clue(C), culprit(K).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for k in CULPRITS:
        lines.append(asp.fact("culprit", k))
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
    print("MISMATCH between clingo and python valid_combos().")
    if py - cl:
        print("Only in python:", sorted(py - cl))
    if cl - py:
        print("Only in clingo:", sorted(cl - py))
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
        print("\n--- trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid mystery combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("council_room", "ink_note", "mouse", "Stickle", "mouse", "Wren", "bird"),
            StoryParams("garden", "mud_track", "squirrel", "Pip", "mouse", "Dot", "mouse"),
            StoryParams("shed", "lost_key", "hedgehog", "Mina", "cat", "Bram", "otter"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
