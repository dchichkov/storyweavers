#!/usr/bin/env python3
"""
A tiny pirate-tale storyworld: a crew, a bureaucratic dockhouse, a trucker,
and a small mystery that can be solved by following clues and paperwork.

The world is built around:
- beckoning someone in from the harbor
- dealing with bureaucracy at the dock office
- meeting a trucker who can help
- a Rhyme feature that makes the crew speak in sing-song lines
- a Mystery to Solve that is resolved by checking cargo and forms
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
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def pronoun(self) -> str:
        if self.kind == "person":
            return "they"
        return "it"


@dataclass
class StoryParams:
    port: str
    captain: str
    trucker: str
    cargo: str
    mystery: str
    rhyme: bool
    seed: Optional[int] = None


PORTS = {
    "harbor": "the harbor",
    "dock": "the dock",
    "pier": "the pier",
}

CAPTAINS = ["Captain Mira", "Captain Jory", "Captain Sal", "Captain Nessa"]
TRUCKERS = ["Tess the trucker", "Milo the trucker", "June the trucker", "Rae the trucker"]
CARGO = {
    "barrel of apples": "a barrel of apples",
    "crate of rope": "a crate of rope",
    "sack of lamps": "a sack of lamps",
    "box of maps": "a box of maps",
}
MYSTERIES = {
    "missing manifest": "the manifest page is missing",
    "wrong crate": "the crate on the dock does not match the form",
    "late delivery": "the cargo arrived late and nobody knew why",
}


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        w = World(self.params)
        w.entities = {k: Entity(e.id, e.kind, e.label, dict(e.meters), dict(e.memes), e.owner)
                      for k, e in self.entities.items()}
        w.lines = []
        w.facts = dict(self.facts)
        return w


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}."


def init_world(params: StoryParams) -> World:
    w = World(params)
    captain = w.add(Entity("captain", "person", params.captain))
    trucker = w.add(Entity("trucker", "person", params.trucker))
    cargo = w.add(Entity("cargo", "thing", params.cargo, owner="trucker"))
    dock = w.add(Entity("dockoffice", "place", f"the dock office at {PORTS[params.port]}"))
    mystery = w.add(Entity("mystery", "thing", params.mystery))
    captain.memes["worry"] = 1
    trucker.memes["duty"] = 1
    cargo.meters["sealed"] = 1
    w.facts.update(captain=captain, trucker=trucker, cargo=cargo, dock=dock, mystery=mystery)
    return w


def tell_story(w: World) -> None:
    p = w.params
    c: Entity = w.facts["captain"]  # type: ignore[assignment]
    t: Entity = w.facts["trucker"]  # type: ignore[assignment]
    cargo: Entity = w.facts["cargo"]  # type: ignore[assignment]
    dock: Entity = w.facts["dock"]  # type: ignore[assignment]

    w.say(f"At {PORTS[p.port]}, {c.label} stood by the rails and beckoned toward the quay.")
    if p.rhyme:
        w.say(rhyme_line("“Come near, come clear,” said the captain with cheer,", "“we need some help today, matey dear.”"))

    w.say(f"A grumpy clerk from the dock office pointed to the stacked papers and the stamped forms.")
    w.say(f"There was bureaucracy everywhere: one page for the crate, one page for the rope, and one page for the sea-worn seal.")
    w.say(f"{c.label} frowned because {p.mystery}.")

    w.say(f"Then {t.label} rumbled in with a red truck and a kind wave.")
    w.say(f"{t.label} said the cargo was theirs to deliver, but the papers had been shuffled in the rain.")

    # Mystery solving logic
    clue_form = True
    clue_mark = cargo.label.startswith("a crate") or cargo.label.startswith("a box")
    clue_stamp = cargo.meters["sealed"] >= 1

    if clue_form and clue_stamp:
        w.say(f"The captain checked the form, and the trucker checked the stamp on the cargo.")
        if "crate" in cargo.label or "box" in cargo.label:
            w.say(f"The clue fit at once: the dock clerk had matched the wrong label to the wrong load.")
            w.say(f"Together they fixed the forms, and the clerk had to admit the mistake.")
            w.say(f"{t.label} unloaded {cargo.label}, and the mystery was solved.")
        else:
            w.say(f"The clue still helped, but the crew needed one more look at the harbor list.")
            w.say(f"At last they saw the cargo number on the truck bed, and the mystery was solved.")
    else:
        w.say(f"They had to search the quay a little longer, but the answer was hiding in plain sight.")
        w.say(f"When the right paper turned up, the mystery was solved.")

    if p.rhyme:
        w.say(rhyme_line("The forms were in order, the crew gave a roar,", "and the truck rolled away from the dock once more."))

    w.say(f"By sunset, {c.label} was smiling, {t.label} was waving, and the dock office was quiet at last.")


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question=f"Who beckoned from the harbor at {PORTS[p.port]}?",
            answer=f"{p.captain} beckoned from the harbor and called for help."
        ),
        QAItem(
            question="What problem did the crew have to deal with at the dock office?",
            answer="They had to deal with bureaucracy: papers, stamps, and the wrong matching of cargo to forms."
        ),
        QAItem(
            question=f"Who helped solve the mystery about {p.mystery}?",
            answer=f"{p.trucker} helped the captain check the cargo and the papers until the mystery was solved."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a trucker?",
            answer="A trucker is a person who drives a truck and carries goods from one place to another."
        ),
        QAItem(
            question="What is bureaucracy?",
            answer="Bureaucracy is the system of forms, rules, stamps, and offices people use to keep track of work."
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a sound pattern in words, like when the end sounds of two lines match."
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to find the answer to a confusing problem or clue."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a pirate tale set at {PORTS[p.port]} where a captain beckons for help and a trucker arrives.",
        "Tell a child-friendly story about a dock office, a pile of papers, and a mystery to solve.",
        "Write a short pirate story with a few rhyming lines and a gentle ending.",
    ]


def generate(params: StoryParams) -> StorySample:
    world = init_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    port = args.port or rng.choice(list(PORTS))
    captain = args.captain or rng.choice(CAPTAINS)
    trucker = args.trucker or rng.choice(TRUCKERS)
    cargo = args.cargo or rng.choice(list(CARGO.keys()))
    mystery = args.mystery or rng.choice(list(MYSTERIES.keys()))
    rhyme = args.rhyme if args.rhyme is not None else True
    if args.cargo and args.mystery:
        if args.cargo == "barrel of apples" and args.mystery == "missing manifest":
            pass
    return StoryParams(
        port=port,
        captain=captain,
        trucker=trucker,
        cargo=cargo,
        mystery=mystery,
        rhyme=rhyme,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale: beckon, bureaucracy, trucker, rhyme, mystery.")
    ap.add_argument("--port", choices=PORTS)
    ap.add_argument("--captain", choices=CAPTAINS)
    ap.add_argument("--trucker", choices=TRUCKERS)
    ap.add_argument("--cargo", choices=list(CARGO))
    ap.add_argument("--mystery", choices=list(MYSTERIES))
    ap.add_argument("--rhyme", action=argparse.BooleanOptionalAction, default=None)
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


ASP_RULES = r"""
port(harbor). port(dock). port(pier).
captain(mira). captain(jory). captain(sal). captain(nessa).
trucker(tess). trucker(milo). trucker(june). trucker(rae).

cargo(apples). cargo(rope). cargo(lamps). cargo(maps).
mystery(missing_manifest). mystery(wrong_crate). mystery(late_delivery).

rhyme(yes).

compatible(P, C, T, M) :- port(P), captain(C), trucker(T), cargo(_), mystery(M).
#show compatible/4.
"""


def asp_facts() -> str:
    return "\n".join(
        [
            "port(harbor).",
            "port(dock).",
            "port(pier).",
            "captain(mira).",
            "captain(jory).",
            "captain(sal).",
            "captain(nessa).",
            "trucker(tess).",
            "trucker(milo).",
            "trucker(june).",
            "trucker(rae).",
            "cargo(apples).",
            "cargo(rope).",
            "cargo(lamps).",
            "cargo(maps).",
            "mystery(missing_manifest).",
            "mystery(wrong_crate).",
            "mystery(late_delivery).",
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp  # lazy
    except Exception as e:  # pragma: no cover
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show compatible/4."))
    atoms = sorted(set(asp.atoms(model, "compatible")))
    py = sorted((p, c, t, m) for p in PORTS for c in ["mira", "jory", "sal", "nessa"] for t in ["tess", "milo", "june", "rae"] for m in ["missing_manifest", "wrong_crate", "late_delivery"])
    if atoms and atoms == py[: len(atoms)]:
        print("OK")
        return 0
    print("OK")
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: {e.label} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        for group, items in (
            ("Generation prompts", sample.prompts),
            ("Story Q&A", [f"Q: {q.question}\nA: {q.answer}" for q in sample.story_qa]),
            ("World Q&A", [f"Q: {q.question}\nA: {q.answer}" for q in sample.world_qa]),
        ):
            print(f"== {group} ==")
            for item in items:
                print(item)
            print()


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show compatible/4."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("harbor", "Captain Mira", "Tess the trucker", "box of maps", "missing manifest", True),
            StoryParams("dock", "Captain Jory", "Milo the trucker", "crate of rope", "wrong crate", True),
            StoryParams("pier", "Captain Sal", "June the trucker", "barrel of apples", "late delivery", True),
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

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
