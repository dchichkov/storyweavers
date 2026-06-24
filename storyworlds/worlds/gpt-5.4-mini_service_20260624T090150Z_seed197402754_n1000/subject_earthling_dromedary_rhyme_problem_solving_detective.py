#!/usr/bin/env python3
"""
A small detective-story world about an earthling detective, a dromedary helper,
and a rhyme-based mystery that gets solved by careful thinking.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"earthling", "detective", "child"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"dromedary", "camel"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str = "the bazaar"
    clue_kind: str = "rhyme"
    problem: str = "missing key"
    solution: str = "follow the rhyme"
    mood: str = "curious"
    seed_word: str = "subject"


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
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


@dataclass
class StoryParams:
    place: str
    detective_name: str
    dromedary_name: str
    case: str
    clue: str
    seed: Optional[int] = None


PLACES = {
    "bazaar": "the bazaar",
    "train_station": "the train station",
    "museum": "the museum",
    "harbor": "the harbor",
    "library": "the library",
}

CASES = {
    "missing_key": ("missing key", "key"),
    "lost_map": ("lost map", "map"),
    "vanished_hat": ("vanished hat", "hat"),
    "stolen_cookie": ("stolen cookie", "cookie"),
}

RIDDLES = {
    "key": ("A key to the gate does not stay in the crate.", "The answer was to check the grate."),
    "map": ("A map won't nap; it slips from a lap.", "The answer was to look under the flap."),
    "hat": ("A hat that is flat may rest by a mat.", "The answer was to search where it sat."),
    "cookie": ("A cookie can hide where a pocket is wide.", "The answer was to peek at the side."),
}

DETECTIVE_NAMES = ["Mina", "Toby", "June", "Nico", "Rae", "Pip", "Luna", "Owen"]
DROMEDARY_NAMES = ["Bump", "Sandy", "Juno", "Khalil", "Mochi", "Patches"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with rhyme clues and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--clue", choices=RIDDLES)
    ap.add_argument("--name")
    ap.add_argument("--dromedary")
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
    case = args.case or rng.choice(list(CASES))
    clue = args.clue or CASES[case][1]
    if clue not in RIDDLES:
        raise StoryError("That clue does not fit this detective world.")
    place = args.place or rng.choice(list(PLACES))
    name = args.name or rng.choice(DETECTIVE_NAMES)
    dromedary = args.dromedary or rng.choice(DROMEDARY_NAMES)
    return StoryParams(place=place, detective_name=name, dromedary_name=dromedary, case=case, clue=clue)


def tell(scene: Scene, params: StoryParams) -> World:
    world = World(scene)
    detective = world.add(Entity(id=params.detective_name, kind="character", type="detective", label="detective"))
    helper = world.add(Entity(id=params.dromedary_name, kind="character", type="dromedary", label="dromedary"))
    missing = world.add(Entity(id="mystery", type=params.case, label=CASES[params.case][0]))

    detective.memes["curious"] = 1
    helper.memes["calm"] = 1

    world.say(f"At {PLACES[params.place]}, {detective.id} was a little earthling detective with bright eyes and a notebook.")
    world.say(f"Beside {detective.pronoun('object')}, {helper.id} the dromedary padded along, ready to help.")
    world.say(f"Then a small problem arrived: someone had a {missing.label}.")

    world.para()
    rhyme, answer = RIDDLES[params.clue]
    detective.memes["thinking"] = 1
    world.say(f"{detective.id} found a rhyme clue and read it aloud: “{rhyme}”")
    world.say(f"{helper.id} listened closely, because good problem solving starts with a careful ear.")

    world.para()
    world.say(f"{detective.id} looked at the clue, looked at the room, and tried one smart place first.")
    if params.clue == "key":
        world.say(f"They checked the grate by the gate, and there it was: the missing key.")
    elif params.clue == "map":
        world.say(f"They lifted the flap on a little travel desk, and under it lay the lost map.")
    elif params.clue == "hat":
        world.say(f"They searched by the mat near the chair, and the vanished hat was resting there.")
    else:
        world.say(f"They peeked by the side of the basket, and the stolen cookie was tucked away safely.")

    world.say(f"{helper.id} nodded and said, “That rhyme really helped us think!”")
    world.say(f"{detective.id} smiled. “We solved it by listening, looking, and not giving up.”")

    world.facts.update(
        detective=detective,
        helper=helper,
        missing=missing,
        rhyme=rhyme,
        answer=answer,
        params=params,
        scene=scene,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a short detective story for a child about an earthling and a dromedary at {PLACES[p.place]} using the word "subject".',
        f"Tell a mystery story where {p.detective_name} and {p.dromedary_name} solve a {CASES[p.case][0]} by using a rhyme clue.",
        f"Write a gentle detective tale with problem solving, a rhyme, and a happy ending at {PLACES[p.place]}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {p.detective_name}, a little earthling detective, and {p.dromedary_name}, the dromedary helper.",
        ),
        QAItem(
            question=f"What problem did they try to solve at {PLACES[p.place]}?",
            answer=f"They tried to solve the {CASES[p.case][0]}.",
        ),
        QAItem(
            question=f"How did they solve the mystery?",
            answer=f"They solved it by listening to the rhyme clue and then checking the right place first.",
        ),
        QAItem(
            question=f"What did the rhyme clue help them do?",
            answer=f"It helped them think about where the missing {CASES[p.case][1]} was hiding.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a dromedary?", answer="A dromedary is a camel with one hump."),
        QAItem(question="What is a rhyme?", answer="A rhyme is when words sound alike at the end, like cat and hat."),
        QAItem(question="What is problem solving?", answer="Problem solving means thinking carefully and trying good ideas to fix a problem."),
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
        lines.append(f"  {e.id:12} ({e.type:10}) meters={e.meters} memes={e.memes}")
    lines.append(f"  facts: solved={world.facts.get('solved')}, clue={world.facts.get('params').clue}")
    return "\n".join(lines)


ASP_RULES = r"""
place(bazaar). place(train_station). place(museum). place(harbor). place(library).
case(missing_key,key). case(lost_map,map). case(vanished_hat,hat). case(stolen_cookie,cookie).
rhyme(key,gate,grate).
rhyme(map,lap,flap).
rhyme(hat,mat,sat).
rhyme(cookie,wide,side).

valid_place(P) :- place(P).
valid_case(C) :- case(C,_).
valid_clue(K) :- rhyme(K,_,_).
valid_story(P,C,K) :- place(P), case(C,K), rhyme(K,_,_).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", pid) for pid in PLACES
    ] + [
        asp.fact("case", cid, clue) for cid, (label, clue) in CASES.items()
    ] + [
        asp.fact("rhyme", clue, a, b) for clue, (a, b) in RIDDLES.items()
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set((p, c, k) for p in PLACES for c in CASES for k in RIDDLES if CASES[c][1] == k)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("Only in clingo:", sorted(clingo_set - python_set))
    print("Only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    scene = Scene(place=PLACES[params.place], clue_kind=params.clue, problem=CASES[params.case][0], solution=RIDDLES[params.clue][1], seed_word="subject")
    world = tell(scene, params)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES:
            for case in CASES:
                params = StoryParams(place=place, detective_name="Mina", dromedary_name="Bump", case=case, clue=CASES[case][1])
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
