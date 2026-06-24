#!/usr/bin/env python3
"""
storyworlds/worlds/soggy_wasp_shotgun_mystery_to_solve_curiosity.py
===================================================================

A standalone story world about a curious child, a soggy clue, a wasp, and a
shotgun-shaped red herring in a ghost-story mystery. The world is small, typed,
state-driven, and constraint checked.

Seed-tale inspiration:
---
On a foggy night, a curious kid found a soggy note on the porch, a wasp circling
the back step, and an old shotgun in the shed. Something strange was hiding in
the house, and the kid wanted to solve the mystery. A brave grown-up listened,
followed the clues, and found the real problem before anyone used the shotgun.
---

The domain keeps the tone eerie but child-friendly: a mystery to solve, curiosity
as the engine, and a calm resolution that proves what changed.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    eerie: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    damp: bool
    points_to: str
    phrase: str


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    risky: bool
    noise: str
    oddness: str


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    method: str
    calm: str


class World:
    def __init__(self, place: Place) -> None:
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

    def people(self) -> list[Entity]:
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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_soggy_hint(world: World) -> list[str]:
    out = []
    kid = world.get("kid")
    if kid.memes["curiosity"] < THRESHOLD:
        return out
    clue = world.get("clue")
    if clue.meters["seen"] >= THRESHOLD and ("hint", clue.id) not in world.fired:
        world.fired.add(("hint", clue.id))
        kid.memes["mystery"] += 1
        out.append("The soggy clue made the mystery feel real.")
    return out


def _r_wasp_alarm(world: World) -> list[str]:
    out = []
    wasp = world.get("wasp")
    if wasp.meters["buzzing"] < THRESHOLD or ("alarm", wasp.id) in world.fired:
        return out
    world.fired.add(("alarm", wasp.id))
    for person in world.people():
        person.memes["unease"] += 1
    out.append("The wasp made the porch feel too strange to ignore.")
    return out


def _r_uncleaned(world: World) -> list[str]:
    out = []
    clue = world.get("clue")
    if clue.meters["wet"] < THRESHOLD or ("trace", clue.id) in world.fired:
        return out
    world.fired.add(("trace", clue.id))
    out.append("The damp paper left a trail toward the shed.")
    return out


CAUSAL_RULES = [
    _r_soggy_hint,
    _r_wasp_alarm,
    _r_uncleaned,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule(world)
            if produced:
                changed = True
                lines.extend(produced)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def ghosty_begin(world: World, kid: Entity, adult: Entity, place: Place) -> None:
    kid.memes["curiosity"] += 1
    world.say(
        f"On a pale evening, {kid.id} stood at {place.label} and listened to the hush. "
        f"{place.eerie}"
    )
    world.say(
        f"{kid.id} was a curious {kid.type} who loved solving little mysteries, "
        f"and {adult.id} promised to listen."
    )


def find_clue(world: World, kid: Entity, clue: Clue) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["seen"] += 1
    if clue.damp:
        clue_ent.meters["wet"] += 1
    world.say(
        f"{kid.id} found {clue.phrase}. It felt soggy in the fingers, as if it had "
        f"been waiting in the dark for help."
    )
    propagate(world)


def see_wasp(world: World, wasp: Entity) -> None:
    wasp.meters["buzzing"] += 1
    world.say(
        f"A wasp looped over the step, tiny and stern, as if it were guarding the porch."
    )
    propagate(world)


def suspect_red_herring(world: World, kid: Entity, hazard: Hazard) -> None:
    kid.memes["mystery"] += 1
    world.say(
        f"In the shed, {kid.id} spotted {hazard.phrase}. It looked frightening, "
        f"but also lonely, like something left behind by a story nobody finished."
    )
    if hazard.risky:
        world.say(
            f"{kid.id} wondered if it was the answer, yet something about it felt like a trap."
        )
    else:
        world.say(
            f"{kid.id} guessed it was not the real answer, just a shadowy object in the wrong place."
        )


def ask_for_help(world: World, kid: Entity, adult: Entity) -> None:
    kid.memes["trust"] += 1
    world.say(
        f"{kid.id} tugged {kid.pronoun('possessive')} sleeve and told {adult.id} about the soggy clue, "
        f"the wasp, and the strange thing in the shed."
    )
    world.say(
        f"{adult.id} did not laugh. {adult.pronoun().capitalize()} followed the clues with calm steps."
    )


def solve(world: World, adult: Entity, clue: Clue, hazard: Hazard, remedy: Remedy) -> None:
    world.get("case").meters["solved"] += 1
    world.say(
        f"Together they followed the damp trail. It led not to the old {hazard.label}, "
        f"but to a loose board and a hidden nest of wet leaves."
    )
    world.say(
        f"{adult.id} used {remedy.phrase} to clear the way, {remedy.method}, and the porch grew quiet."
    )
    world.say(
        f"The wasp drifted off, the soggy clue finally made sense, and the mystery was solved."
    )
    world.say(
        f"By the end, {kid.id} smiled because curiosity had led to the truth, not trouble."
    )


PLACEs = {
    "porch": Place(
        id="porch",
        label="the porch",
        eerie="The boards creaked, and the screen door whispered in the wind.",
        affords={"clue", "wasp", "shotgun"},
    ),
    "shed": Place(
        id="shed",
        label="the shed",
        eerie="Inside, the rafters sighed, and the air smelled like rain and old wood.",
        affords={"clue", "wasp", "shotgun"},
    ),
    "hallway": Place(
        id="hallway",
        label="the hallway",
        eerie="A long draft slid under the door like a shy ghost.",
        affords={"clue", "wasp"},
    ),
}

CLUES = {
    "note": Clue(
        id="note",
        label="note",
        damp=True,
        points_to="shed",
        phrase="a soggy note",
    ),
    "sock": Clue(
        id="sock",
        label="sock",
        damp=True,
        points_to="porch",
        phrase="a soggy sock",
    ),
    "map": Clue(
        id="map",
        label="map",
        damp=False,
        points_to="hallway",
        phrase="a creased map",
    ),
}

HAZARDS = {
    "shotgun": Hazard(
        id="shotgun",
        label="shotgun",
        phrase="an old shotgun in the shed",
        risky=True,
        noise="a loud bang",
        oddness="too stern for a kid's game",
    ),
    "umbrella": Hazard(
        id="umbrella",
        label="umbrella",
        phrase="a bent umbrella",
        risky=False,
        noise="a soft flap",
        oddness="too ordinary to be the answer",
    ),
}

REMEDIES = {
    "lantern": Remedy(
        id="lantern",
        label="lantern",
        phrase="a small lantern",
        method="so they could see without fear",
        calm="warm light",
    ),
    "broom": Remedy(
        id="broom",
        label="broom",
        phrase="a broom",
        method="to sweep the wet leaves aside",
        calm="clean boards",
    ),
}

GIRL_NAMES = ["Mina", "June", "Ivy", "Nora", "Lena"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Owen", "Milo"]
TRAITS = ["curious", "careful", "brave", "gentle"]


@dataclass
class StoryParams:
    place: str
    clue: str
    hazard: str
    remedy: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACEs:
        for c in CLUES:
            for h in HAZARDS:
                if CLUES[c].damp and HAZARDS[h].risky:
                    combos.append((p, c, h))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story mystery world with a curious child.")
    ap.add_argument("--place", choices=PLACEs)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.hazard is None or c[2] == args.hazard)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, hazard = rng.choice(sorted(combos))
    remedy = args.remedy or "lantern"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = args.trait if hasattr(args, "trait") and getattr(args, "trait") else rng.choice(TRAITS)
    return StoryParams(place=place, clue=clue, hazard=hazard, remedy=remedy, name=name, gender=gender, adult=adult, trait=trait)


def _make_world(params: StoryParams) -> World:
    place = PLACEs[params.place]
    world = World(place)
    kid = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[params.trait]))
    adult = world.add(Entity(id="Adult", kind="character", type=params.adult))
    world.add(Entity(id="clue", label=CLUES[params.clue].label))
    world.add(Entity(id="wasp", label="wasp"))
    world.add(Entity(id="case", label="mystery case"))
    world.add(Entity(id=params.hazard, label=HAZARDS[params.hazard].label))
    world.facts.update(kid=kid, adult=adult, clue=CLUES[params.clue], hazard=HAZARDS[params.hazard], remedy=REMEDIES[params.remedy])
    ghosty_begin(world, kid, adult, place)
    world.para()
    find_clue(world, kid, CLUES[params.clue])
    see_wasp(world, world.get("wasp"))
    world.para()
    suspect_red_herring(world, kid, HAZARDS[params.hazard])
    ask_for_help(world, kid, adult)
    world.para()
    solve(world, adult, CLUES[params.clue], HAZARDS[params.hazard], REMEDIES[params.remedy])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost-story mystery for a young child about {f["kid"].id}, a soggy clue, and a wasp. Include the word "soggy".',
        f"Tell a gentle spooky story where {f['kid'].id} wants to solve a mystery, but a weird old shotgun in the shed is not the real answer.",
        f"Write a child-friendly mystery with curiosity, a damp clue, and a calm grown-up who helps solve the case without using the shotgun.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid, adult, clue, hazard, remedy = f["kid"], f["adult"], f["clue"], f["hazard"], f["remedy"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {kid.id}, a curious child who wanted to solve a mystery with {adult.id}.",
        ),
        QAItem(
            question=f"What did {kid.id} find that was soggy?",
            answer=f"{kid.id} found {clue.phrase}, and it felt damp like it had been out in the rain.",
        ),
        QAItem(
            question=f"What strange creature buzzed near the porch?",
            answer=f"A wasp buzzed near the porch and made the evening feel eerie.",
        ),
        QAItem(
            question=f"What did {kid.id} see in the shed?",
            answer=f"{kid.id} saw {hazard.phrase}, but it turned out not to be the real answer to the mystery.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{adult.id} and {kid.id} followed the soggy clue and used {remedy.phrase} to clear the way, which solved the mystery.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does soggy mean?",
            answer="Soggy means wet and soft, like paper or socks after rain.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to know more, ask questions, and look for clues.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that you can solve by following clues and thinking carefully.",
        ),
        QAItem(
            question="What should you do when a scary thing looks like a clue?",
            answer="You should stay calm and ask a grown-up for help so you can figure it out safely.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


ASP_RULES = r"""
valid(P,C,H) :- place(P), clue(C), hazard(H), soggy(C), risky(H).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACEs:
        lines.append(asp.fact("place", p))
    for c, clue in CLUES.items():
        lines.append(asp.fact("clue", c))
        if clue.damp:
            lines.append(asp.fact("soggy", c))
    for h, hz in HAZARDS.items():
        lines.append(asp.fact("hazard", h))
        if hz.risky:
            lines.append(asp.fact("risky", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, combo in enumerate([
            StoryParams("porch", "note", "shotgun", "lantern", "Mina", "girl", "mother", "curious"),
            StoryParams("shed", "sock", "shotgun", "broom", "Eli", "boy", "father", "careful"),
        ]):
            combo.seed = base_seed + i
            samples.append(generate(combo))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
