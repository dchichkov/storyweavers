#!/usr/bin/env python3
"""
A standalone storyworld for a tall-tale mystery with repetition and flashback.

Seed image:
---
A child hears a repeated clink in an old wall niche, where a tiny syringe
keeps vanishing. A bogey may be behind it, but the truth is hidden in a
flashback and solved by careful looking.
"""

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

NAMES = ["Milo", "Nell", "Rosa", "Toby", "Ivy", "Hank", "June", "Bea"]
ADULTS = ["grandpa", "ma", "pa", "aunt", "uncle", "doctor"]
PLACES = [
    "the old cabin",
    "the lantern room",
    "the barn loft",
    "the front hall",
    "the clinic porch",
]
NICHES = [
    "a stone niche",
    "a small wall niche",
    "a deep wooden niche",
    "a tiny plaster niche",
]
BOGEYS = [
    "a little bogey",
    "a shaggy bogey",
    "a moon-faced bogey",
    "a pocket-sized bogey",
]
SYRINGES = [
    "a tiny syringe",
    "a bright syringe",
    "a little medicine syringe",
    "a clean little syringe",
]

FLASHBACK_CLUES = [
    "a medicine bottle label",
    "a bandage box",
    "a note tied with twine",
    "a chalk mark near the niche",
]

# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "ma", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "pa", "uncle", "grandpa", "doctor"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    place: str
    niche: str
    bogey: str
    syringe: str
    hero_name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def tell(params: StoryParams) -> World:
    world = World(params.place)

    hero_type = params.hero_type
    helper_type = params.helper_type

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=hero_type,
        label=params.hero_name,
        meters={"curiosity": 0.0, "resolve": 0.0},
        memes={"worry": 0.0, "wonder": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label=params.helper_type,
        meters={"memory": 0.0},
        memes={"calm": 0.0},
    ))
    bogey = world.add(Entity(
        id="Bogey",
        kind="creature",
        type="bogey",
        label=params.bogey,
        phrase=params.bogey,
        meters={"sneak": 0.0, "mischief": 0.0},
        memes={"secret": 0.0},
    ))
    niche = world.add(Entity(
        id="Niche",
        kind="thing",
        type="niche",
        label=params.niche,
        phrase=params.niche,
        meters={"hide": 0.0},
    ))
    syringe = world.add(Entity(
        id="Syringe",
        kind="thing",
        type="syringe",
        label=params.syringe,
        phrase=params.syringe,
        owner="Helper",
        hidden_in="Niche",
        meters={"shined": 0.0},
    ))

    # Act 1: repetition and unease.
    world.say(
        f"On a windy evening in {params.place}, {hero.id} kept hearing a little clink, clink, clink."
    )
    world.say(
        f"It came from {params.niche}, where {params.bogey} liked to fuss around like a thimble with feet."
    )
    hero.memes["worry"] += 1
    hero.meters["curiosity"] += 1

    world.para()
    world.say(
        f"Every time {hero.id} looked, the sound came again: clink, clink, clink."
    )
    world.say(
        f"And every time, the tiny {params.syringe.split()[-1]} was gone from the niche."
    )
    bogey.meters["mischief"] += 1
    bogey.memes["secret"] += 1

    # Act 2: mystery to solve.
    world.para()
    world.say(
        f"{hero.id} asked, \"Who is moving the syringe?\""
    )
    world.say(
        f"{helper.id} said, \"Look close, child. A mystery is just a story with its boots on.\""
    )
    hero.meters["resolve"] += 1
    hero.memes["wonder"] += 1

    # Flashback clue.
    world.para()
    world.say(
        f"Then {hero.id} remembered a flashback from earlier that day."
    )
    world.say(
        f"{helper.id} had opened {params.niche} to find {params.syringe} beside {FLASHBACK_CLUES[0]}."
    )
    world.say(
        f"{helper.id} had said the syringe was for medicine, and that it must stay safe, clean, and easy to reach."
    )
    helper.meters["memory"] += 1

    # Solve: bogey wasn't stealing; it was returning and protecting it.
    world.para()
    world.say(
        f"That was the trick. {params.bogey} was not stealing the syringe at all."
    )
    world.say(
        f"It had been tucking the little tool deeper into {params.niche} so dust would not settle on it."
    )
    bogey.meters["mischief"] = 0.0
    bogey.memes["secret"] = 0.0
    syringe.meters["shined"] += 1
    hero.memes["relief"] += 1

    world.say(
        f"{hero.id} laughed, because the bogey's odd habit was only a tall-tale way of keeping medicine ready."
    )
    world.say(
        f"Together they left the syringe where it could be found fast, and the clink never came back."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        bogey=bogey,
        niche=niche,
        syringe=syringe,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a tall-tale style story about {p.hero_name}, a mystery in {p.place}, and a repeated clinking sound.',
        f"Tell a child-friendly mystery where a bogey, a niche, and a syringe all matter, and the answer comes from a flashback.",
        f"Write a short story with repetition, a mystery to solve, and an ending that explains why the syringe kept vanishing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    bogey = f["bogey"]
    niche = f["niche"]
    syringe = f["syringe"]
    p = f["params"]

    return [
        QAItem(
            question=f"What sound did {hero.id} keep hearing in {p.place}?",
            answer="{} kept hearing a little clink, clink, clink.".format(hero.id),
        ),
        QAItem(
            question=f"What was the mystery in the story?",
            answer=f"The mystery was who kept moving {syringe.label} in {niche.label}.",
        ),
        QAItem(
            question=f"What did the flashback help {hero.id} remember?",
            answer=f"The flashback helped {hero.id} remember that {helper.id} had placed {syringe.label} near the niche for medicine and safety.",
        ),
        QAItem(
            question=f"What was really going on with {bogey.label}?",
            answer=f"{bogey.label.capitalize()} was not stealing the syringe. It was tucking it deeper into the niche to keep it clean and safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="The mystery got solved, the clinking stopped, and the syringe stayed easy to find.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a niche?",
        answer="A niche is a small hollow space in a wall or shelf where a little object can rest.",
    ),
    QAItem(
        question="What is a syringe used for?",
        answer="A syringe is a tool that helps give or measure medicine carefully.",
    ),
    QAItem(
        question="What is a flashback in a story?",
        answer="A flashback is a scene that goes back to something that happened earlier so the reader can learn more.",
    ),
    QAItem(
        question="Why can repeating a sound matter in a mystery?",
        answer="Repeating a sound can be a clue, because it helps people notice that something keeps happening for a reason.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"{e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reasonableness / parameters
# ---------------------------------------------------------------------------

@dataclass
class ParamsRegistry:
    places: list[str] = field(default_factory=lambda: list(PLACES))
    niches: list[str] = field(default_factory=lambda: list(NICHES))
    bogeys: list[str] = field(default_factory=lambda: list(BOGEYS))
    syringes: list[str] = field(default_factory=lambda: list(SYRINGES))


REGISTRY = ParamsRegistry()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale mystery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--niche", choices=NICHES)
    ap.add_argument("--bogey", choices=BOGEYS)
    ap.add_argument("--syringe", choices=SYRINGES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=ADULTS)
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
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        niche=args.niche or rng.choice(NICHES),
        bogey=args.bogey or rng.choice(BOGEYS),
        syringe=args.syringe or rng.choice(SYRINGES),
        hero_name=args.name or rng.choice(NAMES),
        hero_type=args.hero_type or rng.choice(["girl", "boy"]),
        helper_type=args.helper_type or rng.choice(ADULTS),
    )


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is reasonable when a bogey, a niche, and a syringe are all present.
story_ok(P) :- place(P), niche(_), bogey(_), syringe(_).

% The mystery is solved when the syringe is found in the niche and the bogey
% is revealed to be protective rather than stealing.
solved(P) :- story_ok(P), found_in_niche(P), protects(P).

#show story_ok/1.
#show solved/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for n in NICHES:
        lines.append(asp.fact("niche", n))
    for b in BOGEYS:
        lines.append(asp.fact("bogey", b))
    for s in SYRINGES:
        lines.append(asp.fact("syringe", s))
    lines.append(asp.fact("found_in_niche", PLACES[0]))
    lines.append(asp.fact("protects", PLACES[0]))
    return "\n".join(lines)


def asp_program(show: str = "#show story_ok/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show story_ok/1. #show solved/1."))
    atoms = {(sym.name, tuple(a.string if a.type == type(sym).String else getattr(a, 'number', getattr(a, 'name', None)) for a in sym.arguments)) for sym in model}
    if model is None:
        print("ASP produced no model.")
        return 1
    print("OK: ASP program solved one model.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="the old cabin", niche="a stone niche", bogey="a little bogey", syringe="a tiny syringe", hero_name="Milo", hero_type="boy", helper_type="grandpa"),
    StoryParams(place="the lantern room", niche="a deep wooden niche", bogey="a moon-faced bogey", syringe="a bright syringe", hero_name="Ivy", hero_type="girl", helper_type="aunt"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp
        except Exception as exc:
            raise SystemExit(f"ASP unavailable: {exc}")
        model = asp.one_model(asp_program("#show story_ok/1. #show solved/1."))
        print("ASP model atoms:", [str(s) for s in model])
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(seed + i))
            params.seed = seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
