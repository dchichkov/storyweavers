#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/vest_flashback_dialogue_mystery.py
===================================================================

A standalone storyworld for a small mystery domain with a vest, flashback
beats, and dialogue.

Premise:
- A child notices a missing vest right before a little mystery unfolds.
- The search moves through concrete world state: places, clues, and ownership.
- A flashback reveals where the vest was seen last.
- Dialogue helps the children and an adult solve the mystery.
- The ending proves the change by showing the vest returned to its owner.

This world keeps the prose child-facing and authored, while the simulation
tracks physical state (meters) and emotional state (memes).
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    role: str = ""
    owner: str = ""
    location: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    mood: str
    rooms: list[str]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Vest:
    id: str
    label: str
    color: str
    pocket_clue: str
    memory_place: str
    found_place: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    location: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTING = Setting(
    id="house",
    place="the little house",
    mood="quiet",
    rooms=["hall", "kitchen", "mudroom", "bedroom"],
)

VESTS = {
    "red_vest": Vest("red_vest", "red vest", "red", "a tiny pencil stub in the pocket", "mudroom hook", "hall bench"),
    "blue_vest": Vest("blue_vest", "blue vest", "blue", "a crumpled ticket in the pocket", "bedroom chair", "laundry basket"),
    "yellow_vest": Vest("yellow_vest", "yellow vest", "yellow", "a marble in the pocket", "back door peg", "playroom shelf"),
}

CLUES = {
    "ticket": Clue("ticket", "a crumpled ticket", "paper", "hall bench"),
    "stub": Clue("stub", "a tiny pencil stub", "paper", "mudroom hook"),
    "marble": Clue("marble", "a blue marble", "toy", "playroom shelf"),
}

GIRL_NAMES = ["Maya", "Lily", "Nora", "Ava", "Mila", "Ella"]
BOY_NAMES = ["Theo", "Ben", "Finn", "Owen", "Leo", "Sam"]
ADULT_NAMES = ["Mom", "Dad"]


@dataclass
@dataclass
class StoryParams:
    vest: str
    child: str
    child_gender: str
    adult: str
    adult_gender: str
    clue: str
    setting: str = "house"
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for vest_id, vest in VESTS.items():
        for clue_id, clue in CLUES.items():
            if vest.pocket_clue.startswith(clue.label):
                combos.append((SETTING.id, vest_id, clue_id))
    return combos


ASP_RULES = r"""
matching(vest(V), clue(C)) :- vest_clue(V, C).
valid_story(S, V, C) :- setting(S), matching(vest(V), clue(C)).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", SETTING.id)]
    for vid, vest in VESTS.items():
        lines.append(asp.fact("vest", vid))
        lines.append(asp.fact("vest_clue", vid, vest.pocket_clue.split()[1]))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH between ASP and Python valid combos")
        print("only in ASP:", sorted(clingo_set - python_set))
        print("only in Python:", sorted(python_set - clingo_set))
        return 1
    sample = generate(resolve_params(argparse.Namespace(vest=None, clue=None), random.Random(7)))
    if not sample.story.strip():
        print("Smoke test failed: story empty")
        return 1
    print(f"OK: {len(clingo_set)} valid combo(s); smoke test story generated.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery world built around a missing vest.")
    ap.add_argument("--vest", choices=VESTS)
    ap.add_argument("--clue", choices=CLUES)
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
    combos = [c for c in valid_combos()
              if (args.vest is None or c[1] == args.vest)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    _, vest_id, clue_id = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    child = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    adult_gender = rng.choice(["female", "male"])
    adult = rng.choice(ADULT_NAMES)
    return StoryParams(vest=vest_id, child=child, child_gender=child_gender,
                       adult=adult, adult_gender=adult_gender, clue=clue_id)


def _setup(world: World, child: Entity, adult: Entity, vest: Vest, clue: Clue) -> None:
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    world.say(f"It was a quiet afternoon in {SETTING.place}. {child.id} noticed that {vest.label} was missing.")
    world.say(f'"{adult.id}, have you seen my {vest.label}?" {child.id} asked.')
    world.say(f'"Not since morning," {adult.id} said. "But I remember {vest.pocket_clue}."')


def _flashback(world: World, child: Entity, vest: Vest) -> None:
    child.memes["memory"] += 1
    world.say(f"That made {child.id} blink, and a little flashback came back to {her(child)}.")
    world.say(f"In the flashback, {child.id} had left {vest.label} on {vest.memory_place} after coming inside from play.")


def her(child: Entity) -> str:
    return "her" if child.type == "girl" else "him"


def _search(world: World, child: Entity, adult: Entity, vest: Vest, clue: Clue) -> None:
    world.para()
    world.say(f'"Then let us look," {adult.id} said. {child.id} checked {clue.location}, then the hall bench, then the mudroom.')
    if clue.location == vest.found_place:
        world.say(f'"I found it!" {child.id} called. The {vest.label} was right where the clue pointed.')
    else:
        world.say(f'"That clue was real," {child.id} whispered, "but the vest is not here."')
        world.say(f'"Keep going," {adult.id} said. "Mysteries like to hide in plain sight."')
    world.say(f'At last, {child.id} reached {vest.found_place}.')


def _resolve(world: World, child: Entity, adult: Entity, vest: Vest) -> None:
    world.para()
    vest_ent = world.get("vest")
    vest_ent.location = child.id
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    world.say(f'"There you are," {child.id} said, lifting the {vest.label}.')
    world.say(f'"I knew the pocket clue would help," {adult.id} said. "You solved the mystery."')
    world.say(f"{child.id} put on the {vest.label} again, and the day felt less strange at once.")


def _ending(world: World, child: Entity, adult: Entity, vest: Vest) -> None:
    world.para()
    world.say(f"By evening, {child.id} was wearing the {vest.label} and {adult.id} was smiling at the tidy little room.")
    world.say(f"The missing thing had been found, the clues made sense, and the house was quiet again.")


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="detective"))
    adult = world.add(Entity(id=params.adult, kind="character", type=params.adult_gender, role="helper"))
    vest = VESTS[params.vest]
    clue = CLUES[params.clue]
    world.add(Entity(id="vest", kind="thing", type="vest", label=vest.label, owner=child.id, location=vest.memory_place))
    world.add(Entity(id="clue", kind="thing", type=clue.kind, label=clue.label, location=clue.location))

    _setup(world, child, adult, vest, clue)
    _flashback(world, child, vest)
    _search(world, child, adult, vest, clue)
    _resolve(world, child, adult, vest)
    _ending(world, child, adult, vest)

    world.facts.update(child=child, adult=adult, vest=vest, clue=clue, outcome="found")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child that includes the word "vest".',
        f"Tell a gentle mystery where {f['child'].id} loses a {f['vest'].label} and remembers a clue in a flashback.",
        f'Write a story with dialogue and a flashback about a missing vest that gets found again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    vest = f["vest"]
    clue = f["clue"]
    return [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"The missing thing was the {vest.label}. {child.id} noticed it was gone and asked {adult.id} about it."
        ),
        QAItem(
            question=f"What did the flashback help {child.id} remember?",
            answer=f"The flashback helped {child.id} remember leaving the {vest.label} on {vest.memory_place}. That memory gave the search a real place to start."
        ),
        QAItem(
            question=f"How did the mystery get solved?",
            answer=f"They followed the clue about {clue.label} and looked carefully until the {vest.label} was found at {vest.found_place}. The clue and the search worked together."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vest?",
            answer="A vest is a piece of clothing that covers the middle part of your body and is worn over a shirt."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story shows something that happened earlier. It helps explain what a character remembers."
        ),
        QAItem(
            question="Why do detectives look for clues?",
            answer="Detectives look for clues because clues help them figure out what happened and where to look next."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)],
             "", "== (2) Story questions =="]
    for q in sample.story_qa:
        lines += [f"Q: {q.question}", f"A: {q.answer}"]
    lines += ["", "== (3) World knowledge =="]
    for q in sample.world_qa:
        lines += [f"Q: {q.question}", f"A: {q.answer}"]
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams("red_vest", "Maya", "girl", "Mom", "female", "ticket"),
    StoryParams("blue_vest", "Theo", "boy", "Dad", "male", "stub"),
    StoryParams("yellow_vest", "Nora", "girl", "Mom", "female", "marble"),
]


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid combos:")
        for row in asp_valid_rows():
            print(" ", row)
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


def asp_valid_rows() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


if __name__ == "__main__":
    main()
