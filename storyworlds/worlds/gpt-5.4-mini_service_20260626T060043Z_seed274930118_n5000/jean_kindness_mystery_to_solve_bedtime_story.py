#!/usr/bin/env python3
"""
A small bedtime-story world about Jean, a kindness, and a mystery to solve.

The story model:
- Jean is a child who notices someone sad at bedtime.
- A small mystery appears: a missing glow-star, missing lullaby book, or a creaky sound.
- Kindness is the main tool that solves the mystery.
- The turn comes from looking carefully, asking gently, and sharing.
- The ending proves the change with a calm bedtime image.

This script follows the Storyweavers world contract:
- standalone stdlib script
- StoryParams + parser + resolve_params + generate + emit + main
- lazy ASP import inside helpers
- simulated state with meters and memes
- ASP twin for reasonableness parity
"""

from __future__ import annotations

import argparse
import copy
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["tidy", "lost", "found", "sleepy", "quiet", "helped"]:
            self.meters.setdefault(k, 0.0)
        for k in ["kindness", "worry", "curiosity", "relief", "joy"]:
            self.memes.setdefault(k, 0.0)

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
class Place:
    id: str
    label: str
    indoors: bool = True
    bedtime: bool = True


@dataclass
class Mystery:
    id: str
    label: str
    clue: str
    ask: str
    solve: str
    place: str


@dataclass
class KindnessMove:
    id: str
    label: str
    verb: str
    result: str
    needed_clue: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.clues_found: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.clues_found = list(self.clues_found)
        c.facts = dict(self.facts)
        return c


def _r_found_clue(world: World) -> list[str]:
    out: list[str] = []
    for clue in world.clues_found:
        sig = ("clue", clue)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"A clue was already waiting: {clue}.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("solved") and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        for e in world.characters():
            e.memes["relief"] += 1
        out.append("The room grew quiet and soft again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_r_found_clue, _r_relief):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def bedtime_detail(place: Place) -> str:
    if place.indoors:
        return f"At {place.label}, the lamp made a little circle of gold on the floor."
    return f"At {place.label}, the evening felt hushed and wrapped in blankets."


def tell(place: Place, mystery: Mystery, kindness: KindnessMove, name: str = "Jean",
         hero_type: str = "girl", parent_type: str = "mother") -> World:
    world = World(place)
    jean = world.add(Entity(id=name, kind="character", type=hero_type))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent"))
    puzzler = world.add(Entity(id="mystery", type="mystery", label=mystery.label, phrase=mystery.label))
    world.facts.update(jean=jean, parent=parent, mystery=puzzler, kind=kindness, place=place)

    world.say(f"{jean.id} was a little {jean.type} who loved bedtime because bedtime felt safe.")
    world.say(f"{jean.id} also loved being kind, especially when someone needed a gentle hand.")
    world.say(bedtime_detail(place))

    world.para()
    world.say(f"One night, a small mystery popped up: {mystery.label}.")
    world.say(f"{mystery.clue.capitalize()}")

    world.para()
    jean.memes["curiosity"] += 1
    world.say(f"{jean.id} did not laugh or rush. {jean.pronoun().capitalize()} looked carefully and asked, “{mystery.ask}”")
    world.say(f"{parent.pronoun().capitalize()} listened and smiled at the gentle question.")

    world.para()
    world.say(f"{jean.id} tried kindness. {kindness.verb.capitalize()} {kindness.result}.")
    world.clues_found.append(mystery.clue)
    jean.meters["helped"] += 1
    jean.memes["kindness"] += 1
    parent.memes["joy"] += 1
    world.say(f"The clue led them straight to the answer: {mystery.solve}.")
    world.facts["solved"] = True
    propagate(world, narrate=True)

    world.para()
    jean.memes["relief"] += 1
    world.say(f"{jean.id} smiled a sleepy smile. The mystery was solved, and bedtime felt calm again.")
    world.say(f"{parent.pronoun().capitalize()} tucked {jean.pronoun('object')} in, and soon {jean.id} was breathing softly under the blankets.")
    return world


PLACES = {
    "nursery": Place(id="nursery", label="the nursery", indoors=True, bedtime=True),
    "bedroom": Place(id="bedroom", label="the bedroom", indoors=True, bedtime=True),
    "cottage": Place(id="cottage", label="the little cottage room", indoors=True, bedtime=True),
}

MYSTERIES = {
    "star": Mystery(
        id="star",
        label="the missing paper star",
        clue="A paper star had slipped behind the pillow.",
        ask="Did the star hide behind the pillow?",
        solve="the paper star was tucked behind the pillow all along",
        place="bedroom",
    ),
    "book": Mystery(
        id="book",
        label="the missing lullaby book",
        clue="A soft book edge was peeking from under the blanket.",
        ask="Could the book be under the blanket?",
        solve="the lullaby book was hiding under the blanket",
        place="nursery",
    ),
    "toy": Mystery(
        id="toy",
        label="the missing little bunny toy",
        clue="A floppy ear was sticking out from the curtain.",
        ask="Is the bunny toy by the curtain?",
        solve="the bunny toy was resting by the curtain",
        place="cottage",
    ),
}

KINDNESS = {
    "gentle_question": KindnessMove(
        id="gentle_question",
        label="a gentle question",
        verb="Jean asked kindly",
        result="made the room feel safe enough to look",
        needed_clue="question",
    ),
    "sharing_light": KindnessMove(
        id="sharing_light",
        label="sharing the lamp light",
        verb="Jean carried the lamp closer",
        result="helped the shadows shrink",
        needed_clue="light",
    ),
    "soft_search": KindnessMove(
        id="soft_search",
        label="a soft search",
        verb="Jean lifted the blanket carefully",
        result="revealed the hiding place",
        needed_clue="search",
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for mystery_id, mystery in MYSTERIES.items():
            if mystery.place == place_id:
                for kind_id in KINDNESS:
                    combos.append((place_id, mystery_id, kind_id))
    return combos


@dataclass
class StoryParams:
    place: str
    mystery: str
    kindness: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    jean = f["jean"]
    mystery = f["mystery"]
    kind = f["kind"]
    return [
        f'Write a bedtime story for a young child about {jean.id}, kindness, and a mystery to solve.',
        f"Tell a soft story where {jean.id} notices {mystery.label} and uses {kind.label} to help.",
        f'Write a cozy bedtime tale that includes the name "{jean.id}" and ends with a solved mystery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    jean = f["jean"]
    parent = f["parent"]
    mystery = f["mystery"]
    kind = f["kind"]
    return [
        QAItem(
            question=f"What was the bedtime mystery in the story?",
            answer=f"The bedtime mystery was {mystery.label}, and Jean solved it by being careful and kind.",
        ),
        QAItem(
            question=f"How did {jean.id} try to solve the mystery?",
            answer=f"{jean.id} used {kind.label}. That meant {kind.verb.lower()}, which helped everyone look gently.",
        ),
        QAItem(
            question=f"Who stayed with {jean.id} while the mystery was being solved?",
            answer=f"{parent.pronoun().capitalize()} stayed close and listened while {jean.id} looked for the answer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring to others.",
        ),
        QAItem(
            question="Why do people look carefully when something is missing?",
            answer="People look carefully so they can find clues and understand where the missing thing might be.",
        ),
        QAItem(
            question="Why is bedtime often quiet?",
            answer="Bedtime is often quiet because people are getting ready to rest and sleep.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  clues found: {world.clues_found}")
    return "\n".join(lines)


ASP_RULES = r"""
solvable(P, M, K) :- place(P), mystery(M), kindness(K), place_for(M, P), kind_ok(K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        if place.bedtime:
            lines.append(asp.fact("bedtime", pid))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("place_for", mid, mystery.place))
    for kid in KINDNESS:
        lines.append(asp.fact("kindness", kid))
        lines.append(asp.fact("kind_ok", kid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/3."))
    return sorted(set(asp.atoms(model, "solvable")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: Jean, kindness, and a mystery to solve.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--kindness", choices=KINDNESS)
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


def explain_rejection() -> str:
    return "(No story: the requested bedtime-mystery combination is not reasonable for this world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if args.kindness:
        combos = [c for c in combos if c[2] == args.kindness]
    if not combos:
        raise StoryError(explain_rejection())
    place, mystery, kindness = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or "Jean"
    return StoryParams(place=place, mystery=mystery, kindness=kindness, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MYSTERIES[params.mystery], KINDNESS[params.kindness],
                 params.name, params.gender, params.parent)
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
    StoryParams(place="bedroom", mystery="star", kindness="gentle_question", name="Jean", gender="girl", parent="mother"),
    StoryParams(place="nursery", mystery="book", kindness="sharing_light", name="Jean", gender="boy", parent="father"),
    StoryParams(place="cottage", mystery="toy", kindness="soft_search", name="Jean", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solvable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} solvable bedtime-story combos:\n")
        for p, m, k in combos:
            print(f"  {p:8} {m:8} {k:16}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.mystery} with {p.kindness} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
