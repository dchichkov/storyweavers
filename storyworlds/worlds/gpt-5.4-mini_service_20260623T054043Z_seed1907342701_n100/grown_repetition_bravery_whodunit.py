#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/grown_repetition_bravery_whodunit.py
===============================================================================================================

A small whodunit storyworld about a child finding a missing grown-up object by
following repeated clues and a brave choice.
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
    owner: str = ""
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    key: str
    name: str
    dark: str
    hide_spots: list[str]
    clue_line: str


@dataclass
class Mystery:
    key: str
    missing: str
    label: str
    repeated_sound: str
    search_method: str
    ending_image: str


@dataclass
class Helper:
    key: str
    name: str
    type: str
    brave_line: str
    clue_hint: str


class World:
    def __init__(self, place: Place, mystery: Mystery) -> None:
        self.place = place
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
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

    def copy(self) -> "World":
        import copy
        w = World(self.place, self.mystery)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_repeat(world: World) -> list[str]:
    out = []
    clue = world.facts["clue"]
    if world.facts.get("heard_twice") and "repeat" not in world.fired:
        world.fired.add("repeat")
        world.get("hero").memes["certainty"] = world.get("hero").memes.get("certainty", 0) + 1
        out.append(clue)
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out = _r_repeat(world)
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


PLACES = {
    "hall": Place("hall", "the old hall", "dark corners", ["under the bench", "behind the curtain"], "tap, tap, tap"),
    "kitchen": Place("kitchen", "the quiet kitchen", "dim shelves", ["by the sink", "inside the cupboard"], "drip, drip, drip"),
    "garden": Place("garden", "the back garden", "shadowy bushes", ["under the hedge", "behind the flower pot"], "rustle, rustle, rustle"),
    "attic": Place("attic", "the dusty attic", "long shadows", ["under the trunk", "behind the crate"], "creak, creak, creak"),
}

MYSTERIES = {
    "spoon": Mystery("spoon", "a silver spoon", "the silver spoon", "clink, clink", "look low and listen carefully", "The silver spoon sat on the table again, shining by a bowl."),
    "key": Mystery("key", "the brass key", "the brass key", "jingle, jingle", "check the little hiding spots", "The brass key hung from its hook, right where it belonged."),
    "book": Mystery("book", "the picture book", "the picture book", "thump, thump", "follow the repeated sound", "The picture book rested on the shelf, its corner still folded."),
    "hat": Mystery("hat", "the blue hat", "the blue hat", "plop, plop", "search the darkest corner", "The blue hat was back on the peg, looking neat and grown."),
}

HERO_NAMES = ["Mia", "Noah", "Lily", "Eli", "Nora", "Theo", "Ava", "Ben"]
HELPERS = {
    "mother": Helper("mother", "Mother", "mother", "Mother said, 'Be brave and try the clue again.'", "she keeps the house calm"),
    "father": Helper("father", "Father", "father", "Father said, 'Be brave and look once more.'", "he knows the rooms well"),
    "grandma": Helper("grandma", "Grandma", "woman", "Grandma said, 'Brave eyes notice small things.'", "she notices little things"),
    "grownup": Helper("grownup", "the grown-up", "woman", "The grown-up smiled and said, 'You can do it.'", "the grown-up stays steady"),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p, m, h, g) for p in PLACES for m in MYSTERIES for h in HELPERS for g in ["girl", "boy"]]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld about a missing thing, repetition, and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.helper is None or c[2] == args.helper)
              and (args.gender is None or c[3] == args.gender)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, helper, gender = rng.choice(combos)
    name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(place=place, mystery=mystery, hero=name, hero_gender=gender, helper=helper, helper_gender=gender)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    helper = HELPERS[params.helper]
    world = World(place, mystery)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, label=params.hero, meters={"meters": 0.0}, memes={"bravery": 0.0, "certainty": 0.0}, attrs={"role": "hero"}))
    grown = world.add(Entity(id="grown", kind="character", type=helper.type, label=helper.name, meters={"meters": 0.0}, memes={"bravery": 0.0}, attrs={"role": "helper"}))
    world.facts.update(hero=hero, grown=grown, place=place, mystery=mystery, helper=helper, clue=f'The clue kept saying "{mystery.repeated_sound}."', heard_twice=False)

    world.say(f"{hero.id} and {grown.label} were in {place.name}. Something was missing: {mystery.label}.")
    world.say(f"{place.clue_line}. {hero.id} heard it once, then again: {mystery.repeated_sound}.")
    world.para()
    hero.memes["bravery"] += 1
    world.say(f"{hero.id} took a breath and said, 'I'll look where it sounds the loudest.'")
    world.say(helper.brave_line)
    world.facts["heard_twice"] = True
    propagate(world)
    world.para()
    world.say(f"{hero.id} checked {place.hide_spots[0]}, then {place.hide_spots[1]}.")
    world.say(f"At last, {mystery.ending_image}")
    world.say(f"{grown.label} smiled, and {hero.id} stood a little taller, as grown as the room felt.")
    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a 3-to-5-year-old set in {f["place"].name} where a child hears "{f["mystery"].repeated_sound}" more than once and uses bravery to solve the little mystery.',
        f"Tell a gentle mystery story where {f['hero'].id} and {f['helper'].name} search for {f['mystery'].label} in {f['place'].name}.",
        f'Write a child-friendly mystery that includes the word "grown" and ends with {f["mystery"].label} found again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, grown, mystery, place = f["hero"], f["grown"], f["mystery"], f["place"]
    return [
        QAItem(
            question=f"What was missing in {place.name}?",
            answer=f"{mystery.label} was missing. {hero.id} and {grown.label} looked for it because it was not where it should be.",
        ),
        QAItem(
            question=f"Why did {hero.id} keep listening for the clue?",
            answer=f"The clue repeated itself, so {hero.id} knew it might point to the hiding place. Repetition helped the search feel clear and brave.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery in the mystery?",
            answer=f"{hero.id} took a breath and checked the hiding spots anyway. That brave choice helped the story move from a worry to an answer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does repeated mean?", "Repeated means something happens again and again. In a mystery, a repeated clue can help someone notice a pattern."),
        QAItem("What is bravery?", "Bravery means doing something scary or unsure anyway. A brave person keeps going even when the room feels dark or puzzly."),
        QAItem("What does grown mean?", "Grown means someone is not little anymore. A grown-up can help, and a child can feel more grown after solving a problem."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)} attrs={e.attrs}")
    lines.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
heard_twice :- clue(_).
solved :- heard_twice.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show place/1."))
        _ = asp.atoms(model, "place")
    except Exception as e:
        print(f"ASP unavailable or failed: {e}")
        return 1
    sample = generate(resolve_params(argparse.Namespace(place=None, mystery=None, helper=None, gender=None, name=None), random.Random(0)))
    if not sample.story:
        print("Story generation failed.")
        return 1
    print("OK: ASP loaded and a story generated.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.mystery not in MYSTERIES or params.helper not in HELPERS:
        raise StoryError("Invalid params.")
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
        print(asp_program("#show place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, mystery=m, hero="Mia", hero_gender="girl", helper=h, helper_gender="girl")) for p, m, h, _ in valid_combos()[:5]]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
