#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gloom_kindness_twist_lesson_learned_whodunit.py
===============================================================================================================

A small whodunit-style storyworld with gloom, kindness, a twist, and a lesson
learned.

The seed premise:
- A gloomy place.
- A small mystery: something useful or special goes missing.
- The first guess is wrong.
- Kindness turns the story.
- The lesson learned is that helping kindly can solve more than blaming.

The world model tracks physical meters and emotional memes so the prose is
driven by state changes instead of a frozen template.
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
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"seen": 0.0, "hidden": 0.0, "found": 0.0, "missing": 0.0}
        if not self.memes:
            self.memes = {
                "gloom": 0.0,
                "worry": 0.0,
                "suspicion": 0.0,
                "kindness": 0.0,
                "relief": 0.0,
                "pride": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    name: str
    gloom: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    hidden_place: str
    clue: str
    red_herring: str
    recovered_by_kindness: bool = True


@dataclass
class StoryParams:
    place: str
    mystery: str
    detective: str
    helper: str
    suspect: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


PLACES = {
    "hall": Place("hall", "the old hall", "The hall felt dim and echoey, like it was holding its breath.", {"walk", "search"}),
    "shed": Place("shed", "the garden shed", "The shed was gloomy and dusty, with thin light under the door.", {"search", "hide"}),
    "attic": Place("attic", "the attic", "The attic felt dark and hushy, with boxes stacked like sleepy towers.", {"search", "hide"}),
    "library": Place("library", "the little library room", "The library was quiet and shadowy, with tall shelves making everything feel serious.", {"search"}),
}

MYSTERIES = {
    "key": Mystery(
        id="key",
        label="key",
        phrase="the brass key",
        hidden_place="box",
        clue="a soft clink near the papers",
        red_herring="the muddy boots by the door",
    ),
    "cookie": Mystery(
        id="cookie",
        label="cookie tin",
        phrase="the blue cookie tin",
        hidden_place="shelf",
        clue="a sweet crumb trail",
        red_herring="the crumbs on the table",
    ),
    "lantern": Mystery(
        id="lantern",
        label="lantern",
        phrase="the little green lantern",
        hidden_place="blanket",
        clue="a warm glow under cloth",
        red_herring="the flicker from the window",
    ),
}

NAMES = ["Mia", "Owen", "Nora", "Eli", "Lena", "Theo", "Ivy", "Noah"]
ROLES = {"girl": ["girl", "mother"], "boy": ["boy", "father"]}


def _pronoun_name(name: str, gender: str) -> str:
    return name


def suspicion_reason(hint: str) -> str:
    return {
        "a soft clink near the papers": "the papers looked stirred, so the detective thought someone had hidden the key there",
        "a sweet crumb trail": "the crumbs made the detective suspect the helper had sneaked a snack",
        "a warm glow under cloth": "the cloth looked lumpy, so the detective guessed the lantern had been pushed under it",
    }.get(hint, "the clue seemed to point in the wrong direction")


def reasonableness_gate(place: Place, mystery: Mystery) -> bool:
    return "search" in place.affords and mystery.recovered_by_kindness


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for act in sorted(place.affords):
            lines.append(asp.fact("affords", pid, act))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("red_herring", mid, m.red_herring))
    return "\n".join(lines)


ASP_RULES = r"""
searchable(P) :- affords(P, search).
twist(M) :- mystery(M), clue(M, _), red_herring(M, _).
kind_fix(M) :- mystery(M), clue(M, C), red_herring(M, H), C != H.
valid(P, M) :- searchable(P), kind_fix(M).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return set(asp.atoms(model, "valid"))


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, place in PLACES.items():
        for mid, mystery in MYSTERIES.items():
            if reasonableness_gate(place, mystery):
                out.append((pid, mid))
    return out


def asp_verify() -> int:
    a = set(asp_valid())
    p = set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gloomy whodunit with kindness, a twist, and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
    ap.add_argument("--suspect")
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
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    det = args.detective or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != det])
    suspect = args.suspect or rng.choice([n for n in NAMES if n not in {det, helper}])
    return StoryParams(place=place, mystery=mystery, detective=det, helper=helper, suspect=suspect)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    w = World(place)
    det = w.add(Entity(params.detective, kind="character", type="girl" if params.detective in {"Mia", "Nora", "Lena", "Ivy"} else "boy"))
    helper = w.add(Entity(params.helper, kind="character", type="girl" if params.helper in {"Mia", "Nora", "Lena", "Ivy"} else "boy"))
    suspect = w.add(Entity(params.suspect, kind="character", type="girl" if params.suspect in {"Mia", "Nora", "Lena", "Ivy"} else "boy"))
    obj = w.add(Entity(mystery.label, label=mystery.label, phrase=mystery.phrase, place=mystery.hidden_place))
    w.facts.update(place=place, mystery=mystery, detective=det, helper=helper, suspect=suspect, obj=obj)

    w.say(f"It was a gloomy evening in {place.name}.")
    w.say(f"{det.id} noticed that {mystery.phrase} was missing.")
    w.say(f"The detective frowned because {mystery.clue}, and that made {det.id} feel sure something odd had happened.")
    w.say(f"{det.id} looked at {mystery.red_herring} and thought, 'Maybe {suspect.id} did it.'")

    w.para()
    det.memes["worry"] += 1
    det.memes["suspicion"] += 1
    suspect.memes["gloom"] += 1
    helper.memes["kindness"] += 1
    w.say(f"{suspect.id} looked sad, which made the room feel even gloomier.")
    w.say(f"But {helper.id} did not blame anyone. {helper.id} gently offered to help search.")

    # twist: kindness reveals the real hiding spot
    w.para()
    helper.meters["seen"] += 1
    if mystery.hidden_place == "box":
        w.say(f"Together they checked the boxes. Under one lid, they heard the soft clink of metal.")
    elif mystery.hidden_place == "shelf":
        w.say(f"Together they checked the shelves. Behind a row of books, they found a hidden shape.")
    else:
        w.say(f"Together they checked the blankets. Under one fold, a tiny glow waited patiently.")
    obj.meters["found"] += 1
    obj.meters["missing"] = 0
    det.memes["suspicion"] = 0
    det.memes["relief"] += 1
    helper.memes["pride"] += 1

    w.say(f"There was {mystery.phrase}, tucked away where nobody had first thought to look.")
    w.say(f"The twist was simple: {suspect.id} had not taken it at all. {suspect.id} had only moved it to keep it safe from harm.")

    w.para()
    det.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    suspect.memes["relief"] += 1
    w.say(f"{det.id} apologized to {suspect.id} and thanked {suspect.id} for trying to help.")
    w.say(f"{suspect.id} smiled again, and the gloomy room felt warmer.")
    w.say(f"The lesson learned was that kindness can uncover the truth faster than blame.")
    w.say(f"By the end, {det.id} was holding {mystery.phrase}, {suspect.id} was no longer worried, and {helper.id}'s gentle help had solved the mystery.")

    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for children set in {f["place"].name} with a gloomy mood and a kind helper.',
        f"Tell a mystery story where {f['detective'].id} thinks {f['suspect'].id} caused trouble, but the twist shows a kinder truth.",
        f"Write a simple mystery that ends with a lesson learned about kindness, not blame.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det, helper, suspect, obj, mystery = f["detective"], f["helper"], f["suspect"], f["obj"], f["mystery"]
    return [
        QAItem(
            question=f"What was missing in {world.place.name} at the start of the story?",
            answer=f"{mystery.phrase} was missing, and that made the detective feel uneasy.",
        ),
        QAItem(
            question=f"Who first looked suspicious to {det.id}?",
            answer=f"{det.id} first thought {suspect.id} might have taken it, because the clue pointed the wrong way.",
        ),
        QAItem(
            question=f"Who helped solve the mystery in a kind way?",
            answer=f"{helper.id} helped by searching carefully instead of blaming anyone.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {suspect.id} had not stolen anything; {suspect.id} had moved {obj.phrase} to keep it safe.",
        ),
        QAItem(
            question="What lesson did the detective learn?",
            answer="The detective learned that kindness and careful looking can solve a mystery better than quick blame.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "gloom": [
        ("What does gloomy mean?", "Gloomy means dark, sad, or dim, like a room with very little light."),
    ],
    "kindness": [
        ("What is kindness?", "Kindness means being gentle, helpful, and caring toward other people."),
    ],
    "twist": [
        ("What is a twist in a story?", "A twist is a surprise change that makes the story turn in a new direction."),
    ],
    "lesson": [
        ("What is a lesson learned?", "A lesson learned is an important idea a character understands by the end of a story."),
    ],
    "mystery": [
        ("What is a mystery?", "A mystery is a problem where you have to figure out what really happened."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for k in ["gloom", "kindness", "twist", "lesson", "mystery"] for q, a in WORLD_KNOWLEDGE[k]]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(place="hall", mystery="key", detective="Mia", helper="Owen", suspect="Nora"),
    StoryParams(place="shed", mystery="cookie", detective="Lena", helper="Theo", suspect="Ivy"),
    StoryParams(place="attic", mystery="lantern", detective="Noah", helper="Nora", suspect="Eli"),
]


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify_combos() -> int:
    return asp_verify()


def asp_list() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify_combos())
    if args.asp:
        combos = asp_list()
        print(f"{len(combos)} compatible (place, mystery) combos:\n")
        for place, mystery in combos:
            print(f"  {place:8} {mystery}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
