#!/usr/bin/env python3
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
class Character:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    remembers: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]


@dataclass
class Thing:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    location: str = ""
    hidden: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    places: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    hero: str
    clue: str
    suspect: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HEROES = [
    ("Mina", "curious", "girl"),
    ("Ivy", "small", "girl"),
    ("Noah", "careful", "boy"),
    ("Leo", "quiet", "boy"),
]
HELPS = ["best friend", "older sister", "grandpa", "neighbor"]
SUSPECTS = ["missing key", "muddy paw print", "broken clock", "open window"]
PLACES = {
    "attic": Setting(place="the attic", places=["the attic", "the stairs", "the hall"]),
    "library": Setting(place="the library", places=["the library", "the desk", "the shelf"]),
    "garden": Setting(place="the garden", places=["the garden", "the gate", "the shed"]),
}


ASP_RULES = r"""
hero(H) :- hero_name(H).
clue(C) :- clue_name(C).
place(P) :- place_name(P).

forgot(H,C) :- hero(H), clue(C), lose_memory(H,C).
remembers(H,C) :- hero(H), clue(C), found_again(H,C).
mystery(H,C) :- forgot(H,C), not remembers(H,C).
solved(H,C) :- forgot(H,C), remembers(H,C), clue(C), hero(H).
#show mystery/2.
#show solved/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for h, _, _ in HEROES:
        lines.append(asp.fact("hero_name", h))
    for c in SUSPECTS:
        lines.append(asp.fact("clue_name", c))
    for p in PLACES:
        lines.append(asp.fact("place_name", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A forgetful inner-monologue mystery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=[h for h, _, _ in HEROES])
    ap.add_argument("--clue", choices=SUSPECTS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--helper", choices=HELPS)
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


def valid_combo(place: str, clue: str) -> bool:
    if place == "attic":
        return clue in {"missing key", "broken clock"}
    if place == "library":
        return clue in {"missing key", "open window"}
    return clue in {"muddy paw print", "open window"}


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    places = list(PLACES)
    heroes = [h for h, _, _ in HEROES]
    clues = list(SUSPECTS)
    helpers = list(HELPS)
    combos = []
    for p in places:
        for c in clues:
            if valid_combo(p, c):
                combos.append((p, c))
    if args.place and args.clue and not valid_combo(args.place, args.clue):
        raise StoryError("That place and clue do not make a good mystery together.")
    combos = [c for c in combos if args.place is None or c[0] == args.place]
    combos = [c for c in combos if args.clue is None or c[1] == args.clue]
    if not combos:
        raise StoryError("No valid mystery matches the given options.")
    place, clue = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(heroes)
    suspect = args.suspect or clue
    helper = args.helper or rng.choice(helpers)
    return StoryParams(place=place, hero=hero, clue=clue, suspect=suspect, helper=helper)


def _hero_record(name: str) -> tuple[str, str, str]:
    for h, trait, gender in HEROES:
        if h == name:
            return h, trait, gender
    return name, "curious", "girl"


def generate(params: StoryParams) -> StorySample:
    setting = PLACES[params.place]
    world = World(setting)
    hero_name, trait, gender = _hero_record(params.hero)
    hero = world.add(Character(id=hero_name, type=gender, label=hero_name, traits=["forgetful", trait]))
    clue = world.add(Thing(id="clue", type="clue", label=params.clue, phrase=params.clue, location=params.place))
    suspect = world.add(Thing(id="suspect", type="suspect", label=params.suspect, phrase=params.suspect, location=params.place))
    helper = world.add(Character(id=params.helper, type="adult", label=params.helper, traits=["kind"]))

    clue.hidden = True
    hero.memes["worry"] = 1
    hero.meters["confusion"] = 1

    world.say(f"{hero.id} was a forgetful little {trait} detective who liked quiet mysteries.")
    world.say(f"One day, {hero.id} noticed a {params.clue} and tried to remember why it mattered.")
    world.say(f"'{hero.id}.' {hero.pronoun('subject').capitalize()} thought, 'stay calm. Look at the room. Start from the last thing you saw.'")
    world.para()

    world.say(f"In {setting.place}, something felt off. {params.suspect} was the first thing that looked strange.")
    world.say(f"{hero.id} looked at the corners, the floor, and the door. 'If I were careful, where would I have put it?' {hero.pronoun('subject').capitalize()} wondered.")
    hero.memes["inner_monologue"] = 1
    if params.place == "attic":
        clue.location = "under a box"
        world.say(f"The answer hid under a dusty box near the stairs.")
    elif params.place == "library":
        clue.location = "behind a book"
        world.say(f"The answer waited behind a big book on a tall shelf.")
    else:
        clue.location = "by the shed"
        world.say(f"The answer was by the shed, where the shadow made a neat little line.")
    world.para()

    world.say(f"{params.helper} came over and said, 'Let's check the clues one by one.'")
    world.say(f"{hero.id} nodded. 'Right,' {hero.pronoun('subject')} thought. 'I forgot, but I can trace my steps.'")
    clue.hidden = False
    hero.remembers.add(clue.id)
    hero.meters["confusion"] = 0
    hero.memes["worry"] = 0
    hero.memes["relief"] = 1
    world.say(f"Then {hero.id} found the {params.clue} and smiled. It had been there all along.")
    world.say(f"{hero.id} told {params.helper}, 'I was looking too hard. The answer was hiding in a plain place.'")
    world.say(f"At the end, the room felt calm again, and the little detective had a clearer mind.")

    world.facts.update(
        hero=hero,
        clue=clue,
        suspect=suspect,
        helper=helper,
        setting=setting,
        solved=True,
    )
    story = world.render()
    prompts = [
        f"Write a short mystery story for children about a forgetful detective in {setting.place}.",
        f"Tell a gentle story where {hero.id} keeps thinking to {hero.pronoun('object')}self until the clue makes sense.",
        f"Write a simple mystery with inner monologue, a missing clue, and a calm ending image.",
    ]
    story_qa = [
        QAItem(
            question=f"Why was {hero.id} worried at the start?",
            answer=f"{hero.id} was worried because {hero.id} was forgetful and could not remember what the {params.clue} meant at first.",
        ),
        QAItem(
            question=f"What did {hero.id} think to {hero.pronoun('object')}self to solve the mystery?",
            answer=f"{hero.id} thought to {hero.pronoun('object')}self to stay calm, look at the room, and trace the last steps again.",
        ),
        QAItem(
            question=f"Where did the answer turn out to be?",
            answer=f"The answer was in {clue.location}, which made the mystery feel simple once {hero.id} looked carefully.",
        ),
        QAItem(
            question=f"How did {params.helper} help?",
            answer=f"{params.helper} helped by checking the clues one by one and reminding {hero.id} not to give up.",
        ),
    ]
    world_qa = [
        QAItem(question="What is a clue?", answer="A clue is a small piece of information that helps solve a mystery."),
        QAItem(question="What does it mean to be forgetful?", answer="Being forgetful means you do not remember something right away."),
        QAItem(question="Why can thinking quietly help in a mystery?", answer="Thinking quietly can help you notice details and put the clues together."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: {getattr(e, 'label', '')} {getattr(e, 'location', '')}")
    if qa:
        print("\nQ&A:")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def verify() -> int:
    import storyworlds.asp as asp
    py = {(p, c) for p in PLACES for c in SUSPECTS if valid_combo(p, c)}
    model = asp.one_model(asp_program("#show mystery/2.\n"))
    atoms = set(asp.atoms(model, "mystery"))
    asp_pairs = {(p, c) for p, c in atoms}
    if py != asp_pairs:
        print("MISMATCH")
        print("python only:", sorted(py - asp_pairs))
        print("asp only:", sorted(asp_pairs - py))
        return 1
    sample = generate(resolve_params(argparse.Namespace(place=None, hero=None, clue=None, suspect=None, helper=None), random.Random(1)))
    if not sample.story.strip():
        print("empty story")
        return 1
    print(f"OK: ASP matches Python over {len(py)} combos and sample generation works.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show mystery/2.\n#show solved/2."))
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show mystery/2.\n#show solved/2."))
        print(sorted(asp.atoms(model, "mystery")))
        print(sorted(asp.atoms(model, "solved")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in PLACES:
            for clue in SUSPECTS:
                if valid_combo(place, clue):
                    samples.append(generate(StoryParams(place=place, hero="Mina", clue=clue, suspect=clue, helper="best friend")))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
