#!/usr/bin/env python3
"""
storyworlds/worlds/worded_warrant_flashback_comedy.py
======================================================

A small comedy storyworld about a badly worded warrant, a flashback, and a
lighthearted fix.

Premise:
- Someone receives a warrant that is worded too strangely.
- A flashback shows why everyone is nervous.
- The confusion is resolved with a clearer reading and a harmless comedy beat.

World model:
- A person can hold a warrant, worry about a search, remember a flashback, and
  react with embarrassment or relief.
- Physical meters model paper, pockets, doors, and snack messes.
- Emotional memes model worry, embarrassment, relief, and laughter.

The world is intentionally tiny and constraint-checked: stories are only
generated when the warrant's wording could plausibly trigger a comedy of errors,
and the resolution must make sense in the simulated state.
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

PEOPLE = [
    ("Milo", "boy"),
    ("Nia", "girl"),
    ("Ivy", "girl"),
    ("Owen", "boy"),
    ("Pia", "girl"),
    ("Theo", "boy"),
]

LOCATIONS = [
    "the bakery",
    "the library",
    "the tiny museum",
    "the shoe shop",
    "the corner cafe",
]

OBJECTS = [
    ("cookies", "a tin of cookies"),
    ("balloons", "a box of balloons"),
    ("stamps", "a sheet of rare stamps"),
    ("muffins", "a tray of muffins"),
    ("marbles", "a jar of marbles"),
]

MISWORDS = [
    "worded too fast",
    "worded in a silly way",
    "worded like a riddle",
    "worded with one missing word",
    "worded with a funny typo",
]

FLASHBACK_REASONS = [
    "the clerk had been sneezing while writing",
    "someone spilled juice on the desk",
    "a cat walked across the paper",
    "the printer kept eating the bottom line",
    "the pen skipped and left a gap",
]

FIXES = [
    "read the warrant out loud again",
    "point to the missing word and laugh",
    "ask the clerk to write a clearer copy",
    "compare it with the original note",
    "say the whole thing slowly, like a stage actor",
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    person_name: str
    person_type: str
    location: str
    object_key: str
    wording: str
    flashback_reason: str
    fix: str
    seed: Optional[int] = None


@dataclass
class World:
    person: Entity
    officer: Entity
    warrant: Entity
    item: Entity
    location: str
    wording: str
    flashback_reason: str
    fix: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        clone = World(
            person=copy.deepcopy(self.person),
            officer=copy.deepcopy(self.officer),
            warrant=copy.deepcopy(self.warrant),
            item=copy.deepcopy(self.item),
            location=self.location,
            wording=self.wording,
            flashback_reason=self.flashback_reason,
            fix=self.fix,
        )
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def _lower_title(text: str) -> str:
    return text[:1].lower() + text[1:] if text else text


def _make_world(params: StoryParams) -> World:
    person = Entity(
        id=params.person_name,
        kind="character",
        type=params.person_type,
        meters={"worry": 0.0, "relief": 0.0, "embarrassment": 0.0},
        memes={"worry": 0.0, "relief": 0.0, "laughter": 0.0},
    )
    officer = Entity(
        id="Officer",
        kind="character",
        type="adult",
        label="the officer",
        meters={"patience": 1.0},
        memes={"seriousness": 1.0},
    )
    warrant = Entity(
        id="Warrant",
        kind="thing",
        type="paper",
        label="warrant",
        phrase=params.wording,
        owner=officer.id,
        carried_by=officer.id,
    )
    item_label, item_phrase = next(v for k, v in OBJECTS if k == params.object_key)
    item = Entity(
        id="Item",
        kind="thing",
        type=params.object_key,
        label=item_label,
        phrase=item_phrase,
        owner=params.person_name,
        carried_by=params.person_name,
        plural=params.object_key in {"cookies", "balloons", "stamps", "muffins", "marbles"},
        meters={"mess": 0.0},
    )
    return World(
        person=person,
        officer=officer,
        warrant=warrant,
        item=item,
        location=params.location,
        wording=params.wording,
        flashback_reason=params.flashback_reason,
        fix=params.fix,
    )


def warrant_is_confusing(world: World) -> bool:
    return any(key in world.wording for key in ("silly", "riddle", "typo", "missing"))


def warrants_story(params: StoryParams) -> bool:
    return params.location in LOCATIONS and params.object_key in {k for k, _ in OBJECTS} and (
        "worded" in params.wording or warrant_is_confusing(_make_world(params))
    )


def predict_flashback(world: World) -> bool:
    sim = world.copy()
    sim.person.memes["worry"] += 1.0
    sim.person.meters["worry"] += 1.0
    return sim.person.memes["worry"] >= THRESHOLD


def setup(world: World) -> None:
    world.say(
        f"{world.person.id} was at {world.location}, trying to enjoy the day, when the officer arrived with a warrant."
    )
    world.say(
        f"The paper was {world.wording}, and that made the room feel one tiny step away from a joke."
    )


def flashback(world: World) -> None:
    world.person.memes["worry"] += 1.0
    world.person.meters["worry"] += 1.0
    world.person.memes["embarrassment"] += 1.0
    world.person.meters["embarrassment"] += 1.0
    world.say(
        f"That made {world.person.id} freeze, because a flashback popped up: {world.flashback_reason}."
    )
    world.say(
        f"Suddenly {world.person.id} remembered how the last confusing note had sent everyone into a silly scramble."
    )


def tension(world: World) -> None:
    world.say(
        f"{world.person.id} clutched {world.person.pronoun('possessive')} {world.item.label} and asked, "
        f'"Do we have to panic about {world.item.phrase}?"'
    )
    world.officer.memes["seriousness"] += 1.0
    world.say(
        f"The officer tried to look official, but even {world.officer.pronoun('possessive')} own face said this warrant was badly phrased."
    )


def turn(world: World) -> None:
    world.say(
        f"Then {world.person.id} noticed the odd part: the warrant was not about taking {world.item.phrase} at all."
    )
    world.say(
        f"It was supposed to let the officer {world.fix}, which was much less scary and much more funny."
    )
    world.person.memes["laughter"] += 1.0
    world.person.meters["embarrassment"] = max(0.0, world.person.meters["embarrassment"] - 1.0)
    world.person.meters["relief"] += 1.0
    world.person.memes["relief"] += 1.0


def resolution(world: World) -> None:
    world.say(
        f"{world.person.id} laughed so hard that {world.person.pronoun()} had to lean on the counter."
    )
    world.say(
        f"Together they {world.fix}, and the joke of the day became how one tiny wording problem had caused all that drama."
    )
    world.say(
        f"In the end, {world.item.phrase} stayed right where it was, and {world.person.id} was smiling instead of worrying."
    )


def tell(params: StoryParams) -> World:
    world = _make_world(params)
    if not warrants_story(params):
        raise StoryError("The selected story ingredients do not form a plausible warrant comedy.")
    setup(world)
    world.para()
    if predict_flashback(world):
        flashback(world)
    tension(world)
    world.para()
    turn(world)
    resolution(world)
    world.facts.update(
        person=world.person,
        officer=world.officer,
        warrant=world.warrant,
        item=world.item,
        location=world.location,
        wording=world.wording,
        flashback_reason=world.flashback_reason,
        fix=world.fix,
    )
    return world


def build_prompts(world: World) -> list[str]:
    return [
        f'Write a short comedy story for a child about a warrant that is {world.wording}.',
        f"Tell a funny story where {world.person.id} remembers a flashback while reading a warrant at {world.location}.",
        f'Write a playful story that uses the word "warrant" and ends with a harmless misunderstanding being cleared up.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.person
    return [
        QAItem(
            question=f"Why did {p.id} get nervous when the officer showed the warrant?",
            answer=f"{p.id} got nervous because the warrant was {world.wording}, so it sounded confusing and made a search feel more dramatic than it really was.",
        ),
        QAItem(
            question=f"What did {p.id} remember in the flashback?",
            answer=f"{p.id} remembered that {world.flashback_reason}, which had caused a previous mix-up and made everyone scramble around in a silly way.",
        ),
        QAItem(
            question=f"What fixed the misunderstanding in the end?",
            answer=f"They {world.fix}, and that showed the warrant meant something harmless and much less scary than it first seemed.",
        ),
        QAItem(
            question=f"What happened to {world.item.phrase}?",
            answer=f"{world.item.phrase.capitalize()} stayed right where it was, because nobody was really there to take it away.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a warrant?",
            answer="A warrant is an official paper that gives someone permission to do a specific job, like searching a place or bringing a document.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when the story briefly remembers something that happened before the present scene.",
        ),
        QAItem(
            question="Why can word choice matter?",
            answer="Word choice matters because a sentence can sound clear, serious, silly, or confusing depending on how it is worded.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in [world.person, world.officer, world.warrant, world.item]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.phrase:
            bits.append(f'phrase="{e.phrase}"')
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for loc in LOCATIONS:
        lines.append(asp.fact("location", loc))
    for key, _ in OBJECTS:
        lines.append(asp.fact("object", key))
    for w in MISWORDS:
        lines.append(asp.fact("wording", w))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx))
    return "\n".join(lines)


ASP_RULES = r"""
confusing(W) :- wording(W), (W = "worded in a silly way"; W = "worded like a riddle"; W = "worded with a funny typo"; W = "worded with one missing word").
plausible(L,O,W) :- location(L), object(O), wording(W), confusing(W).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show plausible/3."))
    return sorted(set(asp.atoms(model, "plausible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} plausible combos.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for loc in LOCATIONS:
        for obj, _ in OBJECTS:
            for wording in MISWORDS:
                if "worded" in wording:
                    out.append((loc, obj, wording))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a worded warrant and a flashback.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--object", dest="object_key", choices=[k for k, _ in OBJECTS])
    ap.add_argument("--wording", choices=MISWORDS)
    ap.add_argument("--name", choices=[n for n, _ in PEOPLE])
    ap.add_argument("--type", dest="person_type", choices=["boy", "girl"])
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    person_name, person_type = rng.choice(PEOPLE)
    if args.name:
        person_name = args.name
        person_type = next(t for n, t in PEOPLE if n == person_name)
    if args.person_type:
        person_type = args.person_type
        choices = [n for n, t in PEOPLE if t == person_type]
        if args.name is None:
            person_name = rng.choice(choices)
    location = args.place or rng.choice(LOCATIONS)
    object_key = args.object_key or rng.choice([k for k, _ in OBJECTS])
    wording = args.wording or rng.choice(MISWORDS)
    fix = args.fix or rng.choice(FIXES)
    flashback_reason = rng.choice(FLASHBACK_REASONS)

    if "worded" not in wording:
        raise StoryError("The warrant must be worded in a way that can actually cause a comedy mix-up.")

    return StoryParams(
        person_name=person_name,
        person_type=person_type,
        location=location,
        object_key=object_key,
        wording=wording,
        flashback_reason=flashback_reason,
        fix=fix,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=build_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show plausible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} plausible (location, object, wording) combos:")
        for c in combos[:50]:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [
        StoryParams("Milo", "boy", "the bakery", "cookies", "worded with a funny typo", "the clerk had been sneezing while writing", "read the warrant out loud again"),
        StoryParams("Nia", "girl", "the library", "stamps", "worded like a riddle", "the printer kept eating the bottom line", "ask the clerk to write a clearer copy"),
        StoryParams("Ivy", "girl", "the tiny museum", "marbles", "worded with one missing word", "a cat walked across the paper", "compare it with the original note"),
    ]

    if args.all:
        samples = [generate(p) for p in curated]
    else:
        seen = set()
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
            header = f"### {p.person_name}: {p.location} / {p.object_key} / {p.wording}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
