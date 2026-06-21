#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/discipline_continue_brook_sharing_happy_ending_mystery.py
=========================================================================================

A standalone story world for a small mystery about a brook, shared clues, calm
discipline, continuing the search, and a happy ending.

Premise:
- A child notices strange signs near a brook.
- A careful friend helps them share clues instead of guessing wildly.
- The children keep their discipline and continue the search.
- They solve the mystery with a kind share and end safely and happily.

The world is intentionally small and state-driven: meters track physical changes,
memes track emotions, and the story comes from the simulated sequence of events.

Run:
    python storyworlds/worlds/gpt-5.4-mini/discipline_continue_brook_sharing_happy_ending_mystery.py
    python storyworlds/worlds/gpt-5.4-mini/discipline_continue_brook_sharing_happy_ending_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/discipline_continue_brook_sharing_happy_ending_mystery.py --verify
"""

from __future__ import annotations

import argparse
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
BRAVERY_INIT = 4.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    near: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    type: str
    helpful: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for ent in world.entities.values():
            if ent.meters["worry"] >= THRESHOLD and ("worry", ent.id) not in world.fired:
                world.fired.add(("worry", ent.id))
                ent.memes["focus"] += 1
                changed = True
            if ent.meters["shared"] >= THRESHOLD and ("shared", ent.id) not in world.fired:
                world.fired.add(("shared", ent.id))
                ent.memes["trust"] += 1
                changed = True


def mystery_hint(world: World, child: Entity, place: Place, clue: Clue) -> None:
    child.memes["curiosity"] += 1
    child.meters["worry"] += 1
    world.say(
        f"At the edge of the brook, {child.id} found a small mystery. "
        f"{place.label} looked quiet, but {clue.label} was tucked near {place.near}."
    )
    world.say(
        f'{child.id} frowned. "That is odd," {child.pronoun()} said. '
        f'"I want to continue, but I need to understand it first."'
    )
    propagate(world)


def discipline_beat(world: World, child: Entity, friend: Entity, clue: Clue) -> None:
    child.memes["discipline"] += 1
    friend.memes["calm"] += 1
    world.say(
        f"{friend.id} pointed at the clue and spoke softly. "
        f'"Let us not rush," {friend.id} said. "We will stay careful and keep going."'
    )
    world.say(
        f"{child.id} took a slow breath. {child.pronoun().capitalize()} kept {child.pronoun('possessive')} hands still "
        f"and followed the path by the brook instead of darting ahead."
    )


def share_clue(world: World, child: Entity, friend: Entity, clue: Clue) -> None:
    child.meters["shared"] += 1
    friend.meters["shared"] += 1
    clue.meters["handled"] += 1
    world.say(
        f"{child.id} and {friend.id} shared the clue between them. "
        f"They held {clue.label} up together so both could see the same thing."
    )


def continue_search(world: World, child: Entity, friend: Entity, place: Place) -> None:
    child.memes["resolve"] += 1
    friend.memes["resolve"] += 1
    world.say(
        f"They continued along {place.label}, past the reeds and the stones, "
        f"looking for the answer instead of guessing."
    )


def reveal_and_fix(world: World, child: Entity, friend: Entity, clue: Clue, place: Place) -> None:
    clue.meters["solved"] += 1
    world.say(
        f"Then they saw the answer: the little mystery was only a lost note that had blown near the brook."
    )
    world.say(
        f"{friend.id} laughed first, and {child.id} smiled. "
        f"They placed the note on a dry rock, and the worry slipped away."
    )
    child.memes["joy"] += 2
    friend.memes["joy"] += 2
    world.say(
        f"By the time they left {place.label}, the brook shimmered in the sun and the whole day felt bright again."
    )


def tell(place: Place, clue: Clue, response: Response, child_name: str, child_type: str,
         friend_name: str, friend_type: str, parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))

    child.memes["curiosity"] = 1
    child.memes["discipline"] = BRAVERY_INIT
    friend.memes["calm"] = 1

    world.facts.update(place=place, clue=clue, response=response, child=child, friend=friend, parent=parent)

    world.say(
        f"One afternoon, {child.id} walked to {place.label} with {friend.id}."
    )
    mystery_hint(world, child, place, clue)
    world.para()
    discipline_beat(world, child, friend, clue)
    share_clue(world, child, friend, clue)
    continue_search(world, child, friend, place)
    world.para()
    reveal_and_fix(world, child, friend, clue, place)

    world.facts.update(
        solved=True,
        shared=child.meters["shared"] >= THRESHOLD,
        disciplined=child.memes["discipline"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    clue: str
    response: str
    child: str
    child_gender: str
    friend: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


PLACES = {
    "brook": Place(id="brook", label="the brook", near="a mossy stone", tags={"brook", "mystery"}),
    "bridge": Place(id="bridge", label="the little bridge", near="a cracked plank", tags={"mystery"}),
    "garden": Place(id="garden", label="the garden path", near="a flowerbed", tags={"mystery"}),
}

CLUES = {
    "ribbon": Clue(id="ribbon", label="a blue ribbon", type="ribbon", helpful=True, tags={"sharing"}),
    "note": Clue(id="note", label="a folded note", type="note", helpful=True, tags={"mystery", "sharing"}),
    "shell": Clue(id="shell", label="a shiny shell", type="shell", helpful=True, tags={"mystery"}),
}

RESPONSES = {
    "careful": Response(id="careful", sense=3, text="kept looking carefully and spoke kindly", tags={"discipline"}),
    "ask": Response(id="ask", sense=3, text="asked one another gentle questions", tags={"sharing"}),
    "wait": Response(id="wait", sense=2, text="waited and listened for the next clue", tags={"discipline"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Noah", "Leo", "Theo", "Finn", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for c in CLUES:
            for r in RESPONSES:
                if p == "brook" and c in {"note", "ribbon"}:
                    combos.append((p, c, r))
                elif p != "brook" and c == "note":
                    combos.append((p, c, r))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery story world with sharing and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, response = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (BOY_NAMES if friend_gender == "boy" else GIRL_NAMES) if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place, clue=clue, response=response,
        child=child, child_gender=child_gender,
        friend=friend, friend_gender=friend_gender,
        parent=parent,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story that includes the words "{f["place"].label}", "{f["clue"].label}", and "continue".',
        f"Tell a story where {f['child'].id} and {f['friend'].id} share a clue, keep their discipline, and solve a mystery near the brook.",
        f'Write a happy-ending mystery with sharing, calm thinking, and the word "brook".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, friend, place, clue = f["child"], f["friend"], f["place"], f["clue"]
    return [
        QAItem(
            question=f"What did {child.id} find near the brook?",
            answer=f"{child.id} found {clue.label} near {place.near}. It turned out to be the clue that started the mystery."
        ),
        QAItem(
            question=f"How did {child.id} and {friend.id} solve the mystery?",
            answer=f"They shared the clue, stayed disciplined, and continued searching together. That careful teamwork helped them find the answer instead of panicking."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily. The children solved the mystery, put the clue where it belonged, and walked away smiling beside the brook."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a brook?",
            answer="A brook is a small stream of water. It often makes a soft, flowing sound."
        ),
        QAItem(
            question="What does discipline mean in a story like this?",
            answer="Discipline means staying calm, following a careful plan, and not rushing when something is confusing."
        ),
        QAItem(
            question="Why is sharing helpful?",
            answer="Sharing helps because more than one person can look at the same clue and think about it together. That often makes a mystery easier to solve."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="brook", clue="note", response="careful", child="Mia", child_gender="girl", friend="Theo", friend_gender="boy", parent="mother"),
    StoryParams(place="bridge", clue="ribbon", response="ask", child="Noah", child_gender="boy", friend="Lily", friend_gender="girl", parent="father"),
    StoryParams(place="garden", clue="shell", response="wait", child="Ava", child_gender="girl", friend="Eli", friend_gender="boy", parent="mother"),
]


def explain_rejection(place: Place, clue: Clue) -> str:
    if place.id != "brook" and clue.id in {"ribbon"}:
        return "(No story: this clue fits the brook mystery best. Pick the brook, or choose a folded note for another place.)"
    return "(No story: that combination does not fit the small mystery world.)"


ASP_RULES = r"""
valid(P,C,R) :- place(P), clue(C), response(R), compatible(P,C).
compatible(brook,note).
compatible(brook,ribbon).
compatible(bridge,note).
compatible(garden,note).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for r in RESPONSES:
        lines.append(asp.fact("response", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH between ASP and Python.")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, clue=None, response=None, child=None, child_gender=None, friend=None, friend_gender=None, parent=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.response not in RESPONSES:
        raise StoryError("Invalid parameters.")
    if (params.place, params.clue, params.response) not in valid_combos():
        raise StoryError(explain_rejection(PLACES[params.place], CLUES[params.clue]))
    world = tell(
        PLACES[params.place],
        CLUES[params.clue],
        RESPONSES[params.response],
        params.child,
        params.child_gender,
        params.friend,
        params.friend_gender,
        params.parent,
    )
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
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
