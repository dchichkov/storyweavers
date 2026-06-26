#!/usr/bin/env python3
"""
storyworlds/worlds/search_flashback_repetition_fable.py
=======================================================

A small fable-style storyworld about a character searching for a lost thing,
with flashback and repetition as the main narrative instruments.

Premise:
A small animal loses something important and searches for it across a few
places. The search becomes uncertain, so the story briefly flashes back to the
moment the item was lost. Repeated lines mark persistence. The ending proves
the search changed the character: the lost thing is found, and the character
learns a gentle lesson about paying attention.
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
    value: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    found: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "bear", "lion", "rabbit", "mouse"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str
    hiding_score: int
    clues: set[str] = field(default_factory=set)


@dataclass
class LostItem:
    id: str
    label: str
    phrase: str
    kind: str
    importance: str
    value: int
    likely_places: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    seeker: str
    item: str
    starting_place: str
    ending_place: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.places: dict[str, Place] = {}
        self.item_location: str = ""
        self.searched: list[str] = []
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_place(self, place: Place) -> Place:
        self.places[place.id] = place
        return place

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
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.places = _copy.deepcopy(self.places)
        w.item_location = self.item_location
        w.searched = list(self.searched)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SEEKERS = [
    ("fox", "fox"),
    ("rabbit", "rabbit"),
    ("mouse", "mouse"),
    ("bear", "bear"),
]

ITEMS = {
    "acorn": LostItem(
        id="acorn",
        label="acorn",
        phrase="a small acorn",
        kind="food",
        importance="tiny but precious",
        value=1,
        likely_places={"path", "roots", "tree"},
    ),
    "bell": LostItem(
        id="bell",
        label="bell",
        phrase="a bright brass bell",
        kind="token",
        importance="important and bright",
        value=2,
        likely_places={"path", "nest", "well"},
    ),
    "book": LostItem(
        id="book",
        label="book",
        phrase="a little blue book",
        kind="book",
        importance="full of stories",
        value=2,
        likely_places={"bench", "tree", "home"},
    ),
}

PLACES = {
    "path": Place("path", "the forest path", "outdoor", 2, {"footprints", "dust"}),
    "tree": Place("tree", "the oak tree", "outdoor", 3, {"branches", "leaves"}),
    "nest": Place("nest", "the bird nest", "high", 4, {"twigs", "feathers"}),
    "roots": Place("roots", "the roots of the old tree", "low", 2, {"dirt", "shade"}),
    "well": Place("well", "the stone well", "deep", 4, {"water", "echo"}),
    "bench": Place("bench", "the mossy bench", "quiet", 1, {"moss", "shade"}),
    "home": Place("home", "the little home", "inside", 1, {"door", "table"}),
}

CURATED = [
    StoryParams("fox", "acorn", "path", "roots"),
    StoryParams("rabbit", "bell", "tree", "nest"),
    StoryParams("mouse", "book", "bench", "home"),
]


def choose_name(kind: str) -> str:
    return {
        "fox": "Fenn",
        "rabbit": "Nim",
        "mouse": "Milo",
        "bear": "Bram",
    }.get(kind, kind.title())


def reasonableness_gate(seeker: str, item: LostItem, start: str, end: str) -> bool:
    if start == end:
        return False
    if start not in item.likely_places and end not in item.likely_places:
        return False
    return True


def select_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = []
    for seeker, _stype in SEEKERS:
        for item_id, item in ITEMS.items():
            for start in PLACES:
                for end in PLACES:
                    if start == end:
                        continue
                    if not reasonableness_gate(seeker, item, start, end):
                        continue
                    if args.seeker and args.seeker != seeker:
                        continue
                    if args.item and args.item != item_id:
                        continue
                    if args.starting_place and args.starting_place != start:
                        continue
                    if args.ending_place and args.ending_place != end:
                        continue
                    combos.append((seeker, item_id, start, end))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    seeker, item, start, end = rng.choice(sorted(combos))
    return StoryParams(seeker=seeker, item=item, starting_place=start, ending_place=end)


def flashback_line(seeker: Entity, item: LostItem, place: Place) -> str:
    return (
        f"Then came a flashback: earlier that day, {seeker.id} had set {seeker.pronoun('possessive')} "
        f"{item.label} near {place.label}, only to turn away when a sudden breeze lifted the leaves."
    )


def repeated_search_line(seeker: Entity, place: Place) -> str:
    return f"{seeker.id} searched here, and searched again, because hope was a patient little thing."


def build_world(params: StoryParams) -> World:
    world = World()
    seeker_kind = params.seeker
    seeker_name = choose_name(seeker_kind)
    seeker = world.add_entity(Entity(id=seeker_name, kind="character", type=seeker_kind))
    item = ITEMS[params.item]
    world.add_place(PLACES[params.starting_place])
    world.add_place(PLACES[params.ending_place])
    world.item_location = params.starting_place
    world.facts["seeker"] = seeker
    world.facts["item"] = item
    world.facts["start"] = params.starting_place
    world.facts["end"] = params.ending_place
    world.facts["item_found"] = False
    return world


def search_place(world: World, seeker: Entity, item: LostItem, place: Place, narrate: bool = True) -> bool:
    sig = ("search", seeker.id, place.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.searched.append(place.id)
    seeker.memes["hope"] = seeker.memes.get("hope", 0.0) + 1
    if narrate:
        world.say(f"{seeker.id} went to {place.label} and looked under the quiet corners.")
        world.say(repeated_search_line(seeker, place))
    if world.item_location == place.id:
        seeker.memes["joy"] = seeker.memes.get("joy", 0.0) + 1
        item_found(world, seeker, item, place, narrate=narrate)
        return True
    return False


def item_found(world: World, seeker: Entity, item: LostItem, place: Place, narrate: bool = True) -> None:
    sig = ("found", seeker.id, place.id, item.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    world.facts["item_found"] = True
    seeker.memes["relief"] = seeker.memes.get("relief", 0.0) + 1
    if narrate:
        world.say(
            f"At last, {seeker.id} found {seeker.pronoun('possessive')} {item.label} where the {place.label} had kept it safe."
        )


def lesson_line(seeker: Entity, item: LostItem) -> str:
    return (
        f"{seeker.id} smiled and learned that when something matters, it helps to pause, remember, and search with care."
    )


def tell_story(world: World) -> None:
    seeker: Entity = world.facts["seeker"]
    item: LostItem = world.facts["item"]
    start = world.places[world.facts["start"]]
    end = world.places[world.facts["end"]]

    world.say(
        f"Once in a small forest, {seeker.id} loved {item.phrase}, for it was {item.importance}."
    )
    world.say(
        f"But one windy morning, {seeker.id} lost the {item.label} and felt a little worried."
    )
    world.para()

    if search_place(world, seeker, item, start, narrate=True):
        world.para()
        world.say(lesson_line(seeker, item))
        return

    world.say(f"So {seeker.id} searched the {start.label}, but the {item.label} was not there.")
    world.say(repeated_search_line(seeker, start))
    world.para()

    world.say(f"Then came a flashback: earlier that day, {seeker.id} remembered walking past {end.label}.")
    world.say(f"That memory gave {seeker.id} a new clue, and the search began again.")
    world.para()

    if search_place(world, seeker, item, end, narrate=True):
        world.para()
        world.say(lesson_line(seeker, item))
    else:
        world.say(f"{seeker.id} searched and searched, but the forest kept its secret. At dusk, the lesson was to look more carefully tomorrow.")


def build_story_params_from_namespace(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.seeker and args.seeker not in {s for s, _ in SEEKERS}:
        raise StoryError("Invalid seeker.")
    if args.item and args.item not in ITEMS:
        raise StoryError("Invalid item.")
    if args.starting_place and args.starting_place not in PLACES:
        raise StoryError("Invalid starting place.")
    if args.ending_place and args.ending_place not in PLACES:
        raise StoryError("Invalid ending place.")
    params = select_combo(args, rng)
    return params


def generation_prompts(world: World) -> list[str]:
    seeker: Entity = world.facts["seeker"]
    item: LostItem = world.facts["item"]
    start = world.places[world.facts["start"]]
    end = world.places[world.facts["end"]]
    return [
        f"Write a short fable about {seeker.id} searching for a lost {item.label}.",
        f"Tell a gentle story where {seeker.id} remembers {start.label} and then searches {end.label} for the missing {item.label}.",
        "Use a flashback and a repeated search line to show how patience helps."
    ]


def story_qa(world: World) -> list[QAItem]:
    seeker: Entity = world.facts["seeker"]
    item: LostItem = world.facts["item"]
    start = world.places[world.facts["start"]]
    end = world.places[world.facts["end"]]
    found = world.facts["item_found"]
    qa = [
        QAItem(
            question=f"What was {seeker.id} looking for?",
            answer=f"{seeker.id} was looking for {seeker.pronoun('possessive')} {item.label}.",
        ),
        QAItem(
            question=f"Where did the search begin?",
            answer=f"The search began at {start.label}.",
        ),
        QAItem(
            question="What story trick helped the search feel important?",
            answer="A flashback reminded the character where the item had last been seen, and repetition showed that the searching continued.",
        ),
    ]
    if found:
        qa.append(
            QAItem(
                question=f"Where was the {item.label} found in the end?",
                answer=f"The {item.label} was found at {end.label}.",
            )
        )
        qa.append(
            QAItem(
                question=f"What did {seeker.id} learn by the end?",
                answer=f"{seeker.id} learned to remember carefully and search with patience.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    item: LostItem = world.facts["item"]
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a short look back at something that happened earlier.",
        ),
        QAItem(
            question="What does repetition do in a fable?",
            answer="Repetition repeats words or actions to make a lesson feel stronger and easier to remember.",
        ),
        QAItem(
            question=f"What kind of thing is a {item.label}?",
            answer=f"A {item.label} is a {item.kind} in this storyworld.",
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
        lines.append(f"  entity {e.id}: type={e.type} memes={dict(e.memes)}")
    lines.append(f"  item_location={world.item_location}")
    lines.append(f"  searched={world.searched}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
seeker(S) :- seeker_fact(S).
item(I) :- item_fact(I).
place(P) :- place_fact(P).

can_search(S,P) :- seeker(S), place(P).
found(S,I,P) :- can_search(S,P), item_likely(I,P), start_location(S,P).

found(S,I,P) :- can_search(S,P), item_likely(I,P), end_location(S,P).

valid_story(S,I,Start,End) :- seeker(S), item(I), place(Start), place(End), Start != End,
                              (item_likely(I, Start); item_likely(I, End)).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sk, _ in SEEKERS:
        lines.append(asp.fact("seeker_fact", sk))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item_fact", iid))
        for p in sorted(item.likely_places):
            lines.append(asp.fact("item_likely", iid, p))
    for pid in PLACES:
        lines.append(asp.fact("place_fact", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set()
    for s, _ in SEEKERS:
        for iid, item in ITEMS.items():
            for start in PLACES:
                for end in PLACES:
                    if start == end:
                        continue
                    if end in item.likely_places or start in item.likely_places:
                        py_set.add((s, iid, start, end))
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like storyworld of search, flashback, and repetition.")
    ap.add_argument("--seeker", choices=[s for s, _ in SEEKERS])
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--starting-place", choices=sorted(PLACES))
    ap.add_argument("--ending-place", choices=sorted(PLACES))
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
    return build_story_params_from_namespace(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
        print(f"{len(combos)} compatible story combos:")
        for combo in combos:
            print(" ", combo)
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
            except StoryError as err:
                print(err)
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
            header = f"### {p.seeker} searching for {p.item} from {p.starting_place} to {p.ending_place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
