#!/usr/bin/env python3
"""
storyworlds/worlds/tortilla_dog_dim_cheetah_moral_value_inner.py
===============================================================

A small adventure storyworld about a tortilla, a dog-dim mystery, a cheetah,
a moral choice, and a private inner monologue.

The seed idea:
- A child/adventurer finds a tortilla missing from a picnic basket.
- A dog-like shadow ("dog-dim") seems to have taken it.
- A cheetah appears as a fast helper in the search.
- The mystery is solved by careful tracking and a kind moral choice:
  share, return, or rescue rather than blame.

This file is standalone, stdlib-only, and uses the shared Storyweavers result
containers plus the shared ASP helper lazily.
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
    label: str
    vibe: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    discover: str
    meaning: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelpAction:
    id: str
    label: str
    speed: int
    care: int
    method: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


@dataclass
class StoryParams:
    place: str
    clue: str
    helper: str
    action: str
    name: str
    gender: str
    sidekick: str
    sidekick_gender: str
    seed: Optional[int] = None


PLACES = {
    "picnic": Place(id="picnic", label="the picnic blanket", vibe="sunlit and breezy", afford={"search"}),
    "trail": Place(id="trail", label="the forest trail", vibe="leafy and quiet", afford={"search"}),
    "camp": Place(id="camp", label="the little camp", vibe="crackly and bright", afford={"search"}),
}

CLUES = {
    "crumbs": Clue(id="crumbs", label="crumbs", discover="spotted a trail of crumbs", meaning="someone carried food there", tags={"food"}),
    "pawprints": Clue(id="pawprints", label="pawprints", discover="found soft pawprints in the dirt", meaning="a small animal had passed by", tags={"animal"}),
    "napkin": Clue(id="napkin", label="napkin", discover="noticed a napkin tucked under a stone", meaning="something had been wrapped carefully", tags={"cloth"}),
}

HELP = {
    "track": HelpAction(id="track", label="track the mystery", speed=3, care=4, method="follow the clue step by step", tags={"search"}),
    "listen": HelpAction(id="listen", label="listen closely", speed=2, care=5, method="pause and listen for tiny sounds", tags={"search"}),
    "share": HelpAction(id="share", label="share the tortilla", speed=1, care=6, method="offer food kindly instead of scolding", tags={"moral"}),
}

GIRL_NAMES = ["Mia", "Nora", "Ava", "Zoe", "Lena", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Tomas", "Eli", "Finn", "Noah"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for clue in CLUES:
            for helper in HELP:
                if clue == "pawprints" or helper != "listen":
                    combos.append((place, clue, helper))
    return combos


def explain_rejection(place: str, clue: str, helper: str) -> str:
    if clue == "pawprints" and helper == "share":
        return "(No story: pawprints already point to an animal mystery, so 'share' alone would not solve it.)"
    return "(No story: this choice does not give a clear mystery or a fair ending.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: tortilla, dog-dim mystery, cheetah helper.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=HELP)
    ap.add_argument("--action", choices=["search", "return", "share"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
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
              and (args.clue is None or c[1] == args.clue)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, helper = rng.choice(sorted(combos))
    action = args.action or rng.choice(["search", "return", "share"])
    if action == "share" and helper != "share":
        action = "search"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sidekick_gender = args.sidekick_gender or ("boy" if gender == "girl" else "girl")
    sidekick = args.sidekick or rng.choice(GIRL_NAMES if sidekick_gender == "girl" else BOY_NAMES)
    if sidekick == name:
        sidekick = sidekick + "y"
    return StoryParams(place=place, clue=clue, helper=helper, action=action, name=name, gender=gender, sidekick=sidekick, sidekick_gender=sidekick_gender)


def tell(place: Place, clue: Clue, helper: HelpAction, params: StoryParams) -> World:
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name,
                            meters={"meters": 0.0}, memes={"curiosity": 1.0, "worry": 0.0}))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type=params.sidekick_gender, label=params.sidekick,
                                meters={"meters": 0.0}, memes={"curiosity": 1.0, "worry": 0.0}))
    tortilla = world.add(Entity(id="tortilla", kind="thing", type="food", label="the tortilla",
                                attrs={"owner": hero.id}, meters={"hidden": 1.0}, memes={"value": 1.0},
                                tags={"tortilla", "food"}))
    dog_dim = world.add(Entity(id="dog_dim", kind="thing", type="shadow", label="the dog-dim shadow",
                               attrs={"mystery": True}, meters={"seen": 0.0}, memes={"mystery": 1.0},
                               tags={"dog-dim", "mystery"}))
    cheetah = world.add(Entity(id="cheetah", kind="character", type="cheetah", label="the cheetah",
                               meters={"speed": 5.0}, memes={"help": 1.0}, tags={"cheetah"}))

    hero.memes["curiosity"] += 1
    world.say(f"{hero.id} stood on {place.label}, where the air felt {place.vibe}.")
    world.say(f"{hero.id} noticed that {tortilla.label} was missing from the basket, and {hero.pronoun().capitalize()} wondered who could have taken it.")
    world.say(f"Inside {hero.pronoun('possessive')} head, {hero.id} thought, 'If I rush, I might blame the wrong one. I should look first.'")

    world.para()
    world.say(f"Then {hero.id} {clue.discover}. That clue meant {clue.meaning}.")
    world.say(f"A small shape flickered near the edge of the path: {dog_dim.label}. It looked like a dog, but not quite. The mystery grew deeper.")
    world.say(f"{sidekick.id} pointed and whispered, 'Maybe it hid near the trees.'")

    world.para()
    if helper.id == "share" and action == "share":
        hero.memes["moral"] = 1.0
        world.say(f"{hero.id} took a breath and chose kindness over blame. {hero.pronoun().capitalize()} broke the tortilla in half and offered one piece to the shy little shape.")
        world.say(f"That gentle act changed everything: {dog_dim.label} relaxed, and the missing tortilla had only been borrowed by a hungry trail friend.")
        world.say(f"At the bushes, {cheetah.label} darted back with the other piece, fast as a flash, and everyone laughed.")
        hero.memes["worry"] = 0.0
        world.facts["solved"] = True
        world.facts["moral"] = "kindness"
    else:
        world.say(f"{hero.id} decided to solve the mystery by following the clue carefully.")
        world.say(f"{cheetah.label} offered to help, racing ahead to scan the ground in a blink.")
        world.say(f"At last, {cheetah.label} found {tortilla.label} tucked safely under a leaf pile, where a small wind had nudged it after lunch.")
        world.say(f"{hero.id} felt relief flood the chest, because the answer was simple and nobody had been to blame.")
        world.facts["solved"] = True
        world.facts["moral"] = "patience"
    world.facts.update(hero=hero, sidekick=sidekick, tortilla=tortilla, dog_dim=dog_dim, cheetah=cheetah, clue=clue, helper=helper, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child where a tortilla goes missing at {f["place"].label} and a dog-dim mystery must be solved.',
        f"Tell a gentle mystery story where {f['hero'].id} uses a clue, thinks privately about what is fair, and gets help from a cheetah.",
        f'Write a child-friendly adventure about "{f["clue"].label}", the tortilla, and a kind choice instead of blame.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    tortilla = f["tortilla"]
    clue = f["clue"]
    helper = f["helper"]
    cheetah = f["cheetah"]
    qa = [
        QAItem(question=f"What mystery did {hero.id} need to solve?", answer=f"{hero.id} needed to solve the mystery of where {tortilla.label} had gone. The clues showed that the answer was hiding in a careful little trail."),
        QAItem(question=f"What clue helped {hero.id} search?", answer=f"{clue.discover.capitalize()}, and that clue meant {clue.meaning}. It pointed {hero.id} toward the place where the tortilla had been left."),
        QAItem(question=f"How did the cheetah help?", answer=f"{cheetah.label} helped by moving very fast and checking the path ahead. That speed let the mystery be solved without wasting time."),
    ]
    if f["moral"] == "kindness":
        qa.append(QAItem(question=f"What moral choice did {hero.id} make?", answer=f"{hero.id} chose kindness instead of blame. {hero.pronoun().capitalize()} shared the tortilla, and that gentle choice calmed the mystery right away."))
    else:
        qa.append(QAItem(question=f"What did {hero.id} learn while solving the mystery?", answer=f"{hero.id} learned to be patient and look closely before deciding. That careful choice kept the adventure fair and ended the search well."))
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a tortilla?", answer="A tortilla is a soft flat bread, often used for wrapping or sharing food."),
        QAItem(question="What is a cheetah?", answer="A cheetah is a very fast animal. It can help by reaching a place quickly."),
        QAItem(question="What does it mean to solve a mystery?", answer="To solve a mystery means to gather clues and find the real answer."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes} attrs={e.attrs}")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="picnic", clue="crumbs", helper="track", action="search", name="Mia", gender="girl", sidekick="Leo", sidekick_gender="boy"),
    StoryParams(place="trail", clue="pawprints", helper="listen", action="search", name="Noah", gender="boy", sidekick="Ava", sidekick_gender="girl"),
    StoryParams(place="camp", clue="napkin", helper="share", action="share", name="Lena", gender="girl", sidekick="Finn", sidekick_gender="boy"),
]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for hid in HELP:
        lines.append(asp.fact("helper", hid))
    lines.append(asp.fact("solvable", "yes"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, C, H) :- place(P), clue(C), helper(H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if asp_set != py_set:
        print("MISMATCH between ASP and Python valid combos")
        return 1
    sample = generate(resolve_params(argparse.Namespace(place=None, clue=None, helper=None, action=None, name=None, gender=None, sidekick=None, sidekick_gender=None), random.Random(3)))
    if not sample.story:
        print("Empty story")
        return 1
    print("OK")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.helper not in HELP:
        raise StoryError("Invalid params")
    world = tell(PLACES[params.place], CLUES[params.clue], HELP[params.helper], params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_combos(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params_impl(args, rng)


def resolve_params_impl(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return _resolve(args, rng)


def _resolve(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params_core(args, rng)


def resolve_params_core(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, helper = rng.choice(sorted(combos))
    action = args.action or ("share" if helper == "share" else "search")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sidekick_gender = args.sidekick_gender or ("boy" if gender == "girl" else "girl")
    sidekick = args.sidekick or rng.choice(GIRL_NAMES if sidekick_gender == "girl" else BOY_NAMES)
    if sidekick == name:
        sidekick = sidekick + "n"
    return StoryParams(place=place, clue=clue, helper=helper, action=action, name=name, gender=gender, sidekick=sidekick, sidekick_gender=sidekick_gender)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, c, h) for p in PLACES for c in CLUES for h in HELP if not (c == "pawprints" and h == "share")]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(asp.atoms(model, "valid"))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params_core(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()
