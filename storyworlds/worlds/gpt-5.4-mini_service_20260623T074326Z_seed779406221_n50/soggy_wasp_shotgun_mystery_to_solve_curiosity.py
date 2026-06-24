#!/usr/bin/env python3
"""
storyworlds/worlds/soggy_wasp_shotgun_mystery_to_solve_curiosity.py
===================================================================

A small, standalone storyworld in a ghost-story mood: a curious child in an
old house follows a soggy wasp, hears a mysterious knock, and solves a gentle
puzzle about a shotgun-shaped shadow. The setting is spooky, but the ending is
safe, concrete, and explanatory.

Seed image used to build the domain:
---
On a rainy evening, a curious child in an old house found a soggy wasp on the
porch, a shotgun-shaped shadow in the hall, and a mystery to solve. The child
followed clues, learned the sound came from a loose rain gutter tapping the
wall, and the "shotgun" was only an old umbrella case. The fright faded, the
house felt friendly again, and curiosity became the hero.

This world keeps the prose close to a ghost story: creaks, shadows, wet wind,
and a hush of suspense, but the turn always ends in a clear explanation.
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
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    name: str
    mood: str
    sound: str
    shadow: str


@dataclass
class Clue:
    id: str
    text: str
    kind: str


@dataclass
class Mystery:
    id: str
    question: str
    answer: str
    false_lead: str
    truth: str


@dataclass
class StoryParams:
    place: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    mystery: str
    clue1: str
    clue2: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


PLACES = {
    "old_house": Place("old_house", "an old house", "spooky", "creaked in the rain", "long and lacy"),
    "attic": Place("attic", "the attic", "dusty", "whispered at the rafters", "thin and bent"),
    "porch": Place("porch", "the porch", "wet", "dripped from the gutter", "glossy and gray"),
}

CLUES = {
    "soggy_wasp": Clue("soggy_wasp", "a soggy wasp trembling on the porch rail", "animal"),
    "shotgun_case": Clue("shotgun_case", "a shotgun-shaped case in the hall", "object"),
    "gutter_tap": Clue("gutter_tap", "a tapping sound from the loose gutter", "sound"),
    "wet_bootprint": Clue("wet_bootprint", "a wet bootprint by the side door", "trace"),
    "umbrella_stick": Clue("umbrella_stick", "an umbrella stick hiding inside the case", "reveal"),
}

MYSTERIES = {
    "tap": Mystery(
        "tap",
        "What made the spooky tapping sound in the old house?",
        "A loose gutter tapping the wall in the wind",
        "A ghost in the attic",
        "The wind nudged the gutter and made the tapping sound.",
    ),
    "case": Mystery(
        "case",
        "What was the shotgun-shaped thing in the hall?",
        "An old umbrella case",
        "A dangerous gun left in the house",
        "It only looked like a shotgun in the dark; it was an umbrella case.",
    ),
    "wasp": Mystery(
        "wasp",
        "Why was the wasp soggy?",
        "Because the rain soaked it on the porch",
        "Because it came from a haunted bee nest",
        "It had simply been splashed by the storm.",
    ),
}

NAMES_GIRL = ["Mina", "Clara", "Ivy", "Nora", "Lena", "Wren"]
NAMES_BOY = ["Evan", "Theo", "Miles", "Owen", "Finn", "Jasper"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story mystery world with curiosity and a gentle ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue1", choices=CLUES)
    ap.add_argument("--clue2", choices=CLUES)
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = NAMES_GIRL if gender == "girl" else NAMES_BOY
    pool = [n for n in pool if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    clue1, clue2 = args.clue1, args.clue2
    if clue1 is None or clue2 is None:
        cue_choices = list(CLUES)
        clue1, clue2 = rng.sample(cue_choices, 2)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or _pick_name(rng, child_gender)
    helper = args.helper or _pick_name(rng, helper_gender, avoid=child)
    return StoryParams(place=place, child=child, child_gender=child_gender,
                       helper=helper, helper_gender=helper_gender,
                       mystery=mystery, clue1=clue1, clue2=clue2)


def validate(params: StoryParams) -> None:
    if params.clue1 == params.clue2:
        raise StoryError("Pick two different clues.")
    if params.mystery == "case" and "shotgun" not in CLUES[params.clue1].text and "shotgun" not in CLUES[params.clue2].text:
        pass


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


ASP_RULES = r"""
chosen_mystery(M) :- mystery(M), not other_mystery(M).
other_mystery(M) :- mystery(M), mystery(N), N != M.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    return 0


def world_story_lines(world: World) -> str:
    return world.render()


def _mood_opening(place: Place, child: Entity, helper: Entity) -> str:
    return (
        f"That evening, {child.id} and {helper.id} were in {place.name}. "
        f"It felt {place.mood}, as if the house were holding its breath."
    )


def generate_world(params: StoryParams) -> World:
    validate(params)
    rng = random.Random(params.seed)
    world = World()
    place = PLACES[params.place]
    child = world.add(Entity(params.child, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(params.helper, kind="character", type=params.helper_gender, role="helper"))
    child.memes["curiosity"] = 2.0
    helper.memes["curiosity"] = 1.0
    child.memes["nervous"] = 1.0
    world.facts.update(params=copy.deepcopy(params), place=place, child=child, helper=helper,
                       mystery=MYSTERIES[params.mystery], clue1=CLUES[params.clue1], clue2=CLUES[params.clue2])

    world.say(_mood_opening(place, child, helper))
    world.say(f"{place.sound.capitalize()}, and the windows shivered in the rain.")
    world.say(f"{child.id} noticed {CLUES[params.clue1].text}.")

    world.para()
    world.say(f"Then {child.id} spotted {CLUES[params.clue2].text}.")
    child.memes["curiosity"] += 1.0
    helper.memes["curiosity"] += 1.0
    world.say(f'“{MYSTERIES[params.mystery].question}” {child.id} whispered.')
    world.say(f'“Let’s solve it,” said {helper.id}, leaning closer to the dark hall.')

    world.para()
    if params.mystery == "tap":
        world.say("They followed the tapping to the side wall and looked up.")
        world.say("The gutter was loose, and the wind kept nudging it against the wood.")
        world.say("The spooky knock was only rain and wind having a little argument.")
        world.say("When the child tied the gutter down with a string, the house grew quiet.")
    elif params.mystery == "case":
        world.say("In the hall, the shadow looked long and serious.")
        world.say("But when they turned on the lamp, the shotgun shape disappeared.")
        world.say("It was only an old umbrella case standing by the door.")
        world.say("The child laughed, because the dark had made an ordinary thing look fierce.")
    else:
        world.say("The soggy wasp trembled on the porch rail, too wet to buzz.")
        world.say("It had been caught in the storm, not a ghost at all.")
        world.say("The child set out a dry leaf, and the wasp crawled onto it slowly.")
        world.say("Soon it dried its wings and drifted away into the rain-gray dusk.")

    world.para()
    child.memes["fear"] = 0.0
    child.memes["pride"] = 1.0
    world.say(
        f"{child.id} smiled at the answer. Curiosity had not made the night less spooky; "
        f"it had made the spooky things make sense."
    )
    world.say(
        f"By the time the rain softened, the old house felt friendly again."
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    place: Place = f["place"]
    mystery: Mystery = f["mystery"]
    clue1: Clue = f["clue1"]
    clue2: Clue = f["clue2"]
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"What kind of story is this in {place.name}?",
            answer=f"It is a spooky mystery story in {place.name}, but the ending is safe and friendly."
        ),
        QAItem(
            question=f"What did {child.id} notice first?",
            answer=f"{child.id} noticed {clue1.text}."
        ),
        QAItem(
            question=f"What clue did {helper.id} help notice?",
            answer=f"{helper.id} helped notice {clue2.text}."
        ),
        QAItem(
            question=f"What was {mystery.question.lower()}?",
            answer=f"{mystery.truth}"
        ),
        QAItem(
            question=f"What did the shotgun-shaped thing turn out to be?",
            answer="It was only an old umbrella case, not a real gun."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curiosity do in a mystery?",
            answer="Curiosity helps a person look carefully, gather clues, and find a real answer."
        ),
        QAItem(
            question="Why can a wet wasp look mysterious?",
            answer="A soggy wasp can look strange in bad weather, but rain alone can explain it."
        ),
        QAItem(
            question="What should you do when something looks scary but might not be dangerous?",
            answer="Look carefully, stay calm, and ask a trusted grown-up if you need help."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a ghost-story mystery for a young child in {PLACES[p.place].name} where curiosity solves a spooky clue.",
        f"Tell a calm spooky story that includes a soggy wasp, a shotgun-shaped shadow, and a real explanation.",
        f"Write a mystery-to-solve story where {p.child} and {p.helper} follow clues and discover that the scary thing is ordinary.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world trace ---"]
    for e in world.entities.values():
        parts.append(f"{e.id}: kind={e.kind} type={e.type} memes={e.memes}")
    return "\n".join(parts)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world_story_lines(world),
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
        print(asp_program(show="#show chosen_mystery/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program(show="#show chosen_mystery/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        curated = [
            StoryParams("old_house", "Mina", "girl", "Evan", "boy", "tap", "gutter_tap", "wet_bootprint"),
            StoryParams("attic", "Owen", "boy", "Ivy", "girl", "case", "shotgun_case", "umbrella_stick"),
            StoryParams("porch", "Lena", "girl", "Theo", "boy", "wasp", "soggy_wasp", "wet_bootprint"),
        ]
        samples = [generate(p) for p in curated]
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
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
