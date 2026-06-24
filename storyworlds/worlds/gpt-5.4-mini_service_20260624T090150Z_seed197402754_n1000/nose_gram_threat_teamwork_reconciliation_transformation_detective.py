#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    place: str
    detective: str
    partner: str
    threat: str
    clue: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    detail: str


@dataclass
class Mystery:
    clue: str
    threat: str
    transformation: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        clone.entities = {k: Entity(e.id, e.kind, e.type, e.label, dict(e.meters), dict(e.memes))
                          for k, e in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


PLACES = {
    "dock": Place("the dock", "The dock smelled like salt and old ropes."),
    "market": Place("the market", "The market was busy with carts, baskets, and whispers."),
    "museum": Place("the museum", "The museum had quiet halls and shiny glass cases."),
    "station": Place("the train station", "The train station echoed with footsteps and rolling bags."),
}

DETECTIVES = [
    ("Mina", "girl", "curious"),
    ("Theo", "boy", "careful"),
    ("Pip", "boy", "brave"),
    ("Ivy", "girl", "sharp-eyed"),
]

PARTNERS = [
    ("Nia", "girl"),
    ("Bo", "boy"),
    ("Rae", "girl"),
    ("Owen", "boy"),
]

THREATS = {
    "storm": "a storm cloud that threatened to flood the clues",
    "thief": "a sneaky thief in a dark coat",
    "fox": "a fox that kept circling the path",
    "fire": "a small fire that smoked near the crates",
}

CLUES = {
    "nose": "a dusting of cinnamon on the detective's nose",
    "gram": "a missing gram from the cookie tin",
    "threat": "a torn note that said THREAT in big letters",
}

ASP_RULES = r"""
place(dock;market;museum;station).
detective(mina;theo;pip;ivy).
partner(nia;bo;rae;owen).
threat(storm;thief;fox;fire).
clue(nose;gram;threat).

needs_teamwork(C) :- clue(C), C != nose.
needs_reconciliation(T) :- threat(T).
transforms(C,T) :- clue(C), threat(T).
valid(P,D,Pa,T,C) :- place(P), detective(D), partner(Pa), threat(T), clue(C).
#show valid/5.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for d, _, _ in DETECTIVES:
        lines.append(asp.fact("detective", d.lower()))
    for p, _ in PARTNERS:
        lines.append(asp.fact("partner", p.lower()))
    for t in THREATS:
        lines.append(asp.fact("threat", t))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for p in PLACES:
        for d, _, _ in DETECTIVES:
            for pa, _ in PARTNERS:
                for t in THREATS:
                    for c in CLUES:
                        combos.append((p, d, pa, t, c))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective story world about nose clues, a gram, and a threat.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--detective", choices=[d for d, _, _ in DETECTIVES])
    ap.add_argument("--partner", choices=[p for p, _ in PARTNERS])
    ap.add_argument("--threat", choices=THREATS)
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
    choices = valid_combos()
    if args.place:
        choices = [c for c in choices if c[0] == args.place]
    if args.detective:
        choices = [c for c in choices if c[1] == args.detective]
    if args.partner:
        choices = [c for c in choices if c[2] == args.partner]
    if args.threat:
        choices = [c for c in choices if c[3] == args.threat]
    if args.clue:
        choices = [c for c in choices if c[4] == args.clue]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, detective, partner, threat, clue = rng.choice(sorted(choices))
    return StoryParams(place=place, detective=detective, partner=partner, threat=threat, clue=clue)


def make_story(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    det_name, det_type, det_trait = next(d for d in DETECTIVES if d[0] == params.detective)
    par_name, par_type = next(p for p in PARTNERS if p[0] == params.partner)
    det = world.add(Entity(params.detective, "character", det_type, det_name, memes={"duty": 1.0}))
    par = world.add(Entity(params.partner, "character", par_type, par_name))
    m = Mystery(clue=params.clue, threat=params.threat, transformation="reconciliation")
    world.facts.update(detective=det, partner=par, mystery=m, params=params)

    world.say(f"{det.label} was a {det_trait} detective who loved using {det.pronoun('possessive')} nose to hunt for clues.")
    if params.clue == "nose":
        world.say(f"One morning, a faint smell tickled {det.pronoun('possessive')} nose, and that smell led {det.pronoun('object')} toward the case.")
    elif params.clue == "gram":
        world.say(f"On the table, {det.label} found a tiny gram missing from the cookie tin.")
    else:
        world.say(f"Inside the folder, {det.label} found a note that spelled out a threat.")
    world.para()
    world.say(f"{world.place.detail}")
    world.say(f"{par.label} hurried over to help, because the case was too tricky for one detective alone.")
    world.say(f"Together, they followed the clue until it pointed at {THREATS[params.threat]}.")
    world.para()
    world.say(f"The threat made {par.label} scared for a moment, and {det.label} was scared too.")
    world.say(f"Then {det.label} and {par.label} worked as a team: one watched the door while the other checked the clue.")
    world.say(f"That teamwork turned the trouble into a safer path, and the detective remembered that sharing the job made both of them braver.")
    world.para()
    world.say(f"At last, the scary suspicion changed into reconciliation.")
    world.say(f"{det.label} apologized for jumping to conclusions, and {par.label} smiled and forgave {det.pronoun('object')}.")
    world.say(f"The tiny clue transformed the whole case: the missing gram was found, the threat was gone, and the friends walked home side by side.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a short detective story for a young child that includes the words "{p.clue}", "{p.threat}", and "teamwork".',
        f"Tell a gentle mystery where {p.detective} and {p.partner} solve a case at {p.place} by using a nose clue.",
        f"Write a story in which a small threat leads to reconciliation and a surprising transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    det: Entity = world.facts["detective"]
    par: Entity = world.facts["partner"]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {det.label}, who used {det.pronoun('possessive')} nose to look for clues.",
        ),
        QAItem(
            question=f"What clue did {det.label} find?",
            answer=f"{det.label} found {CLUES[p.clue]}. That clue helped point the case in the right direction.",
        ),
        QAItem(
            question=f"How did {det.label} and {par.label} solve the problem?",
            answer=f"They used teamwork, stayed calm, and followed the clue together until the threat no longer mattered.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The worry changed into reconciliation, and the clue transformed the case from scary to safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a nose used for?", answer="A nose helps you breathe and smell things."),
        QAItem(question="What does teamwork mean?", answer="Teamwork means people help each other do something together."),
        QAItem(question="What is a threat?", answer="A threat is something that might cause danger or worry."),
        QAItem(question="What does reconciliation mean?", answer="Reconciliation is when people make up after a disagreement."),
        QAItem(question="What is transformation?", answer="Transformation means something changes into a new form or feeling."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} {e.kind:8} {e.type:8} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_story(params)
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
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        print()
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} compatible combos.")
        for row in vals[:20]:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p, d, pa, t, c in valid_combos()[:5]:
            params = StoryParams(p, d, pa, t, c, seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx+1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
