#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

STEP = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"detective", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    suspect: str
    clue: str
    ration: str
    detective: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    log: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.log.append(text)

    def render(self) -> str:
        return "\n\n".join(self.log)

    def copy(self) -> "World":
        return World(self.place, entities=dataclasses.replace if False else {}, log=[])
        # unreachable; replaced below


def _world_copy(world: World) -> World:
    clone = World(world.place)
    clone.entities = {k: dataclasses.replace(v, meters=dict(v.meters), memes=dict(v.memes)) for k, v in world.entities.items()}
    clone.log = []
    clone.facts = dict(world.facts)
    return clone


def clue_repeated(world: World, clue: str) -> bool:
    return world.get(clue).memes.get("repeated", 0.0) >= STEP


def ration_transformed(world: World, ration: str) -> bool:
    return world.get(ration).meters.get("transformed", 0.0) >= STEP


def suspect_spoke(world: World, suspect: Entity) -> None:
    suspect.memes["nervous"] = suspect.memes.get("nervous", 0.0) + STEP
    world.say(f'{suspect.label} looked up and said, "Hello."')


def repeat_clue(world: World, clue: Entity) -> None:
    clue.memes["repeated"] = clue.memes.get("repeated", 0.0) + STEP
    clue.meters["importance"] = clue.meters.get("importance", 0.0) + STEP


def transform_ration(world: World, ration: Entity, kind: str) -> None:
    ration.meters["transformed"] = ration.meters.get("transformed", 0.0) + STEP
    ration.label = kind


def investigate(world: World, detective: Entity, suspect: Entity, clue: Entity, ration: Entity) -> None:
    world.say(f"{detective.label} stepped into {world.place.name} in a small fiat and listened carefully.")
    world.say(f"The first clue was a hello, and then another hello, as if someone had practiced the same word twice.")
    suspect_spoke(world, suspect)
    repeat_clue(world, clue)
    world.say(f"{detective.label} wrote the repeated hello in a notebook because repeated words can hide a trail.")
    world.say(f"Near the bench, the ration looked plain at first, but the detective knew plain things can change.")
    transform_ration(world, ration, f"opened {ration.label}")
    world.say(f"The ration transformed when {detective.label} opened it: inside was the missing note, folded tight.")
    world.say(f"That note named the suspect, and the case stopped being a guess.")


def setup_world(params: StoryParams) -> World:
    place = PLACE_REGISTRY[params.place]
    world = World(place)
    detective = world.add(Entity(id="detective", kind="character", label=params.detective, type="detective"))
    suspect = world.add(Entity(id="suspect", kind="character", label=params.suspect, type="woman"))
    clue = world.add(Entity(id="clue", kind="thing", label=params.clue, type="thing"))
    ration = world.add(Entity(id="ration", kind="thing", label=params.ration, type="thing"))
    fiat = world.add(Entity(id="fiat", kind="thing", label="fiat", type="thing"))
    world.facts = {
        "detective": detective,
        "suspect": suspect,
        "clue": clue,
        "ration": ration,
        "fiat": fiat,
        "place": place,
    }
    world.say(f"{detective.label} was a detective who liked quiet cases and neat answers.")
    world.say(f"At {place.name}, the air smelled like dust, paper, and a little bit of trouble.")
    world.say(f"Someone had left a fiat by the curb, a hello on a scrap of paper, and a ration on the table.")
    world.say(f"{detective.label} knew the case would need patience, because clues sometimes repeat before they reveal anything.")
    world.say(f"{suspect.label} kept her hands folded and watched the ration without blinking.")
    return world


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    world.say("")
    investigate(world, world.get("detective"), world.get("suspect"), world.get("clue"), world.get("ration"))
    world.say("")
    world.say(f"In the end, {world.get('detective').label} parked the fiat, closed the notebook, and smiled.")
    world.say(f"The repeated hello had become a clue, the ration had transformed into the answer, and the suspect was no longer a mystery.")
    world.facts["solved"] = True
    return world


PLACE_REGISTRY = {
    "station": Place("the station", {"walk", "wait", "watch"}),
    "alley": Place("the alley", {"walk", "search"}),
    "office": Place("the office", {"read", "wait", "search"}),
}

SUSPECTS = ["Mrs. Vale", "Nina", "Mara", "June"]
CLUES = ["hello note", "hello scrap", "hello card"]
RATIONS = ["lunch ration", "bread ration", "field ration"]
DETECTIVES = ["Detective Lane", "Detective Sol", "Detective June"]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out = []
    for place in PLACE_REGISTRY:
        for suspect in SUSPECTS:
            for clue in CLUES:
                for ration in RATIONS:
                    for detective in DETECTIVES:
                        out.append((place, suspect, clue, ration, detective))
    return out


@dataclass
class StoryParams:
    place: str
    suspect: str
    clue: str
    ration: str
    detective: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with repeated clues and transforming ration.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--ration", choices=RATIONS)
    ap.add_argument("--detective", choices=DETECTIVES)
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
    place = args.place or rng.choice(list(PLACE_REGISTRY))
    suspect = args.suspect or rng.choice(SUSPECTS)
    clue = args.clue or rng.choice(CLUES)
    ration = args.ration or rng.choice(RATIONS)
    detective = args.detective or rng.choice(DETECTIVES)
    return StoryParams(place=place, suspect=suspect, clue=clue, ration=ration, detective=detective)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story that includes the words "fiat", "hello", and "ration" in a mystery at {f["place"].name}.',
        f"Tell a short mystery where {f['detective'].label} notices a repeated hello and solves what the ration hides.",
        "Write a child-friendly detective tale with one clue that repeats and one ordinary thing that transforms into the answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"].label
    suspect = f["suspect"].label
    place = f["place"].name
    return [
        QAItem(
            question=f"Who solved the mystery at {place}?",
            answer=f"{detective} solved the mystery by following the repeated hello and the transformed ration.",
        ),
        QAItem(
            question="What clue repeated in the story?",
            answer="The hello clue repeated, and that repetition helped the detective notice it was important.",
        ),
        QAItem(
            question="What changed during the investigation?",
            answer="The ration transformed when it was opened, and the detective found the missing note inside.",
        ),
        QAItem(
            question=f"Why did {detective} keep watching {suspect}?",
            answer=f"{suspect} seemed nervous, and the detective thought she might know why the hello and the ration mattered.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective for?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means something happens or is said again, like a word repeated twice.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a different form or becomes different in an important way.",
        ),
    ]


def asp_facts() -> str:
    import asp
    lines = []
    for pname in PLACE_REGISTRY:
        lines.append(asp.fact("place", pname))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
        if "hello" in c:
            lines.append(asp.fact("repeats", c))
    for r in RATIONS:
        lines.append(asp.fact("ration", r))
        lines.append(asp.fact("can_transform", r))
    for d in DETECTIVES:
        lines.append(asp.fact("detective", d))
    return "\n".join(lines)


ASP_RULES = r"""
repeated_clue(C) :- clue(C), repeats(C).
transformed_ration(R) :- ration(R), can_transform(R).
valid_story(P, C, R, D) :- place(P), repeated_clue(C), transformed_ration(R), detective(D).
#show valid_story/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((p, c, r, d) for p, c, r, d in valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and python")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        w = sample.world
        for e in w.entities.values():
            print(f"{e.id}: {e.label} {e.kind} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_stories():
            print(row)
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        combos = valid_combos()
        for i, combo in enumerate(combos[: max(args.n, len(combos))]):
            p = StoryParams(*combo, seed=base + i)
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base + i)
            p = resolve_params(args, rng)
            p.seed = base + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
