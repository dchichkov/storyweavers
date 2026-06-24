#!/usr/bin/env python3
"""
A small whodunit-style storyworld about a misplaced cone, a scolding, and a
child who solves the mystery by listening to an inner monologue and following
the clues.
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
class Person:
    id: str
    kind: str = "character"
    type: str = "child"
    name: str = ""
    role: str = ""
    is_suspect: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Object:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden_in: Optional[str] = None
    moved_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    clues: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    scolder: str
    scolder_type: str
    suspect: str
    suspect_type: str
    cone_color: str
    seed: Optional[int] = None


PLACES = {
    "schoolyard": Place(id="schoolyard", label="the schoolyard", clues=["footprints", "a chalk line", "a shiny scuff"]),
    "playground": Place(id="playground", label="the playground", clues=["sand", "a swing chain", "a bent leaf"]),
    "porch": Place(id="porch", label="the porch", clues=["mud", "a doormat", "a drip trail"]),
}

HEROES = {
    "Mia": ("girl", "Mia"),
    "Noah": ("boy", "Noah"),
    "Ava": ("girl", "Ava"),
    "Eli": ("boy", "Eli"),
}

SCOURERS = {
    "Mrs. Lane": ("woman", "Mrs. Lane"),
    "Mr. Reed": ("man", "Mr. Reed"),
    "Coach Bell": ("man", "Coach Bell"),
}

SUSPECTS = {
    "Rin": ("girl", "Rin"),
    "Tate": ("boy", "Tate"),
    "June": ("girl", "June"),
    "Owen": ("boy", "Owen"),
}

COLORS = ["orange", "yellow", "blue", "red"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.people: dict[str, Person] = {}
        self.objects: dict[str, Object] = {}
        self.story: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add_person(self, p: Person) -> Person:
        self.people[p.id] = p
        return p

    def add_object(self, o: Object) -> Object:
        self.objects[o.id] = o
        return o

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def person(self, pid: str) -> Person:
        return self.people[pid]

    def obj(self, oid: str) -> Object:
        return self.objects[oid]


def setup_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    hero = world.add_person(Person(id=params.hero, type=params.hero_type, name=params.hero, role="detective"))
    scolder = world.add_person(Person(id=params.scolder, type=params.scolder_type, name=params.scolder, role="scolder"))
    suspect = world.add_person(Person(id=params.suspect, type=params.suspect_type, name=params.suspect, role="suspect", is_suspect=True))
    cone = world.add_object(Object(id="cone", label="cone", phrase=f"a {params.cone_color} cone", owner=suspect.id))
    missing = world.add_object(Object(id="missing_sign", label="sign", phrase="the missing sign", owner="school"))
    world.facts.update(hero=hero, scolder=scolder, suspect=suspect, cone=cone, missing=missing)
    return world


def clue_chain(world: World) -> str:
    return ", ".join(world.place.clues)


def inner_monologue(hero: Person, suspicion: str) -> str:
    return f"{hero.name} thought, {suspicion}"


def tell_story(params: StoryParams) -> World:
    world = setup_world(params)
    hero = world.facts["hero"]
    scolder = world.facts["scolder"]
    suspect = world.facts["suspect"]
    cone = world.facts["cone"]
    place = world.place

    world.say(f"{hero.name} was a small helper who loved quiet mysteries.")
    world.say(f"One morning at {place.label}, everyone stared at a missing sign and a lonely cone.")
    world.say(f"{scolder.name} gave {suspect.name} a sharp scold. \"Who moved the cone?\" {scolder.pronoun().capitalize()} asked.")
    world.say(inner_monologue(hero, "That scold sounded too quick. A real clue should come first."))
    world.para()
    world.say(f"{hero.name} knelt beside the ground and looked carefully. {clue_chain(world)} were all nearby.")
    world.say(f"The cone had a tiny smear of paint on one side, and {suspect.name}'s sleeves were clean.")
    world.say(inner_monologue(hero, "If the cone were dragged, it would leave a trail. The trail points somewhere else."))
    world.say(f"{hero.name} followed a thin streak by the wall and found the missing sign behind a crate.")
    world.para()
    world.say(f"{suspect.name} blinked. \"I only picked up the cone because I saw it tip over,\" {suspect.pronoun()} said.")
    world.say(f"{scolder.name} looked embarrassed and softened the scold. \"I spoke too soon,\" {scolder.pronoun()} said.")
    world.say(f"Then {hero.name} explained that the cone had been moved by the wind, not by {suspect.name}.")
    world.say(f"By the end, the cone was back where it belonged, the sign was found, and the whole place felt tidy again.")
    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.place.label
    return [
        f"Write a short whodunit story about a cone and a scold at {p}.",
        "Tell a child-friendly mystery where the detective listens to an inner monologue and follows clues.",
        f"Write a gentle story that includes a cone, a scold, and a solved mystery at {p}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Person = world.facts["hero"]
    scolder: Person = world.facts["scolder"]
    suspect: Person = world.facts["suspect"]
    cone: Object = world.facts["cone"]
    place = world.place.label
    return [
        QAItem(
            question=f"Who listened closely instead of trusting the scold right away?",
            answer=f"{hero.name} listened closely and looked for clues instead of trusting the scold right away.",
        ),
        QAItem(
            question=f"What color was the cone in the mystery at {place}?",
            answer=f"It was a {cone.phrase.split()[1]} cone.",
        ),
        QAItem(
            question=f"Why did {scolder.name} feel embarrassed at the end?",
            answer=f"{scolder.name} felt embarrassed because {scolder.pronoun()} scolded too quickly before the clues were checked.",
        ),
        QAItem(
            question=f"Who was first blamed for moving the cone?",
            answer=f"{suspect.name} was first blamed, but the mystery later showed that {suspect.pronoun()} had not done it.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cone used for?",
            answer="A cone is often used to mark a place, guide people around danger, or show that something is being worked on.",
        ),
        QAItem(
            question="What is a scold?",
            answer="A scold is a sharp warning or reprimand, usually said when someone thinks a mistake has been made.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in a character's head that shows what they are thinking.",
        ),
        QAItem(
            question="What does a detective do in a mystery?",
            answer="A detective looks for clues, thinks carefully, and tries to find out what really happened.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for p in world.people.values():
        lines.append(f"{p.id}: type={p.type} role={p.role} suspect={p.is_suspect}")
    for o in world.objects.values():
        extra = []
        if o.owner:
            extra.append(f"owner={o.owner}")
        if o.hidden_in:
            extra.append(f"hidden_in={o.hidden_in}")
        if o.moved_by:
            extra.append(f"moved_by={o.moved_by}")
        lines.append(f"{o.id}: label={o.label} {' '.join(extra)}")
    lines.append(f"place={world.place.label}")
    lines.append(f"solved={world.facts.get('solved', False)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def story_params_registry() -> dict:
    return {
        "places": list(PLACES),
        "heroes": list(HEROES),
        "scolders": list(SCOURERS),
        "suspects": list(SUSPECTS),
        "colors": list(COLORS),
    }


def valid_combo(place: str, hero_type: str, scolder_type: str, suspect_type: str) -> bool:
    return place in PLACES and hero_type in {"girl", "boy"} and scolder_type in {"woman", "man"} and suspect_type in {"girl", "boy"}


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in PLACES:
        for h in ("girl", "boy"):
            for s in ("woman", "man"):
                for x in ("girl", "boy"):
                    out.append((place, h, s, x))
    return out


def explain_invalid(msg: str) -> str:
    return f"(No story: {msg})"


@dataclass
class ASPFacts:
    place: str
    hero_type: str
    scolder_type: str
    suspect_type: str
    cone: str


ASP_RULES = r"""
place(P) :- setting(P).
person_role(hero, T) :- hero_type(T).
person_role(scolder, T) :- scolder_type(T).
person_role(suspect, T) :- suspect_type(T).

valid(P, H, S, X) :- setting(P), hero_type(H), scolder_type(S), suspect_type(X).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("setting", p))
    lines.append(asp.fact("hero_type", "girl"))
    lines.append(asp.fact("hero_type", "boy"))
    lines.append(asp.fact("scolder_type", "woman"))
    lines.append(asp.fact("scolder_type", "man"))
    lines.append(asp.fact("suspect_type", "girl"))
    lines.append(asp.fact("suspect_type", "boy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches python valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python valid_combos():")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld: a cone, a scold, and a mystery to solve.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--scolder")
    ap.add_argument("--scolder-type", choices=["woman", "man"])
    ap.add_argument("--suspect")
    ap.add_argument("--suspect-type", choices=["girl", "boy"])
    ap.add_argument("--cone-color", choices=COLORS)
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
    hero, hero_type = args.hero, args.hero_type
    if hero is None or hero_type is None:
        hero, hero_type = rng.choice(list(HEROES.items()))
        hero_type = hero_type[0]
    scolder, scolder_type = args.scolder, args.scolder_type
    if scolder is None or scolder_type is None:
        scolder, scolder_type = rng.choice(list(SCOURERS.items()))
        scolder_type = scolder_type[0]
    suspect, suspect_type = args.suspect, args.suspect_type
    if suspect is None or suspect_type is None:
        suspect, suspect_type = rng.choice(list(SUSPECTS.items()))
        suspect_type = suspect_type[0]
    cone_color = args.cone_color or rng.choice(COLORS)
    if not valid_combo(place, hero_type, scolder_type, suspect_type):
        raise StoryError(explain_invalid("invalid combination"))
    return StoryParams(
        place=place,
        hero=hero,
        hero_type=hero_type,
        scolder=scolder,
        scolder_type=scolder_type,
        suspect=suspect,
        suspect_type=suspect_type,
        cone_color=cone_color,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, place in enumerate(PLACES):
            params = StoryParams(
                place=place,
                hero="Mia" if i % 2 == 0 else "Noah",
                hero_type="girl" if i % 2 == 0 else "boy",
                scolder="Mrs. Lane",
                scolder_type="woman",
                suspect="Rin",
                suspect_type="girl",
                cone_color=COLORS[i % len(COLORS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
