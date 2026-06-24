#!/usr/bin/env python3
"""
storyworlds/worlds/wise_mutant_bronze_repetition_transformation_inner_monologue.py
===================================================================================

A small detective-story storyworld built from the seed words:
wise, mutant, bronze.

Premise:
- A wise little detective notices repeated clues in a quiet museum city.
- A mutant bronze figurine keeps changing form under moonlight.
- The detective follows repetition, transformation, and inner monologue to solve
  the case and restore the missing exhibit.

This world is designed as a tiny classical simulation with physical meters and
emotional memes. The plot is state-driven: repeated clues raise suspicion,
transformations change what object is actually being tracked, and the hero's
inner monologue advances the investigation and the resolution.

The script is standalone and uses only stdlib plus the shared storyworld
containers. ASP helpers are imported lazily only when needed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    place: str = ""
    movable: bool = True
    bronze: bool = False
    mutant: bool = False
    wears: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"woman", "girl", "detective"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the museum"
    indoors: bool = True
    quiet: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    repeat_word: str
    transform_word: str
    place: str
    topic: str
    reveal: str


@dataclass
class StoryParams:
    setting: str
    clue: str
    hero_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.entities.values() if e.kind == "character"), None)
    clue = world.facts.get("clue_entity")
    if not hero or not clue:
        return out
    if clue.meters.get("repeated", 0) < THRESHOLD:
        return out
    sig = ("repetition", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0.0) + 1
    out.append(f"The same clue kept showing up, and that made the case feel deliberate.")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("clue_entity")
    if not clue:
        return out
    if clue.meters.get("changed", 0) < THRESHOLD:
        return out
    sig = ("transformation", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.bronze = True
    clue.mutant = True
    out.append(f"Under the lamp, the clue changed shape and turned out to be more than it seemed.")
    return out


def _r_inner_monologue(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.entities.values() if e.kind == "character"), None)
    clue = world.facts.get("clue_entity")
    if not hero or not clue:
        return out
    if hero.memes.get("resolve", 0) < THRESHOLD:
        return out
    sig = ("monologue", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(
        f"{hero.name_or_label()} thought, I know what the clue is trying to hide, and I know where it leads."
    )
    return out


CAUSAL_RULES = [
    Rule("repetition", _r_repetition),
    Rule("transformation", _r_transformation),
    Rule("inner_monologue", _r_inner_monologue),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "museum": Setting(place="the museum", indoors=True, quiet=True, affords={"search"}),
    "dock": Setting(place="the old dock", indoors=False, quiet=False, affords={"search"}),
    "library": Setting(place="the library", indoors=True, quiet=True, affords={"search"}),
}

CLUES = {
    "bronze_statue": Clue(
        id="bronze_statue",
        label="a bronze statuette",
        repeat_word="again",
        transform_word="changed",
        place="gallery",
        topic="bronze",
        reveal="a tiny bronze key hidden in its base",
    ),
    "footprint": Clue(
        id="footprint",
        label="a repeated footprint",
        repeat_word="again",
        transform_word="shifted",
        place="hallway",
        topic="repetition",
        reveal="a path toward the back room",
    ),
    "mirror_note": Clue(
        id="mirror_note",
        label="a note in the mirror",
        repeat_word="again",
        transform_word="flipped",
        place="reading room",
        topic="inner monologue",
        reveal="a code only the detective noticed",
    ),
}

NAMES = ["Mara", "June", "Iris", "Noah", "Eli", "Nina", "Theo", "Ada"]
TRAITS = ["wise", "patient", "careful", "quiet", "sharp"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CLUES:
            combos.append((s, c))
    return combos


@dataclass
class StoryParams:
    setting: str
    clue: str
    hero_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with wise, mutant bronze clues.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue = rng.choice(combos)
    return StoryParams(setting=setting, clue=clue, hero_name=args.name or rng.choice(NAMES))


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.hero_name, kind="character", type="detective", traits=["wise"]))
    clue_cfg = CLUES[params.clue]
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="object",
        label=clue_cfg.label,
        phrase=clue_cfg.label,
        place=world.setting.place,
        bronze=False,
        mutant=False,
        meters={"repeated": 0.0, "changed": 0.0},
    ))
    world.facts["hero"] = hero
    world.facts["clue_entity"] = clue
    world.facts["clue_cfg"] = clue_cfg

    world.say(f"{hero.name_or_label()} was a wise detective who liked cases that felt small but strange.")
    world.say(f"In {world.setting.place}, one clue kept showing up: {clue_cfg.label}.")
    world.say(f"{hero.name_or_label()} noticed the clue {clue_cfg.repeat_word} and {clue_cfg.repeat_word}.")

    world.para()
    clue.meters["repeated"] += 2
    hero.memes["suspicion"] = 1.0
    world.say(
        f"That repetition made {hero.name_or_label()} narrow {hero.pronoun('possessive')} eyes and think hard."
    )
    world.say(
        f"Inside {hero.name_or_label()}'s head, a small voice said the clue was trying to point somewhere on purpose."
    )

    world.para()
    clue.meters["changed"] += 1
    propagate(world, narrate=True)
    world.say(
        f"When the lamp touched it, {clue.label} was no longer only a clue; it had become mutant bronze."
    )
    world.say(f"That transformation turned the search from a simple look-around into a real investigation.")

    world.para()
    hero.memes["resolve"] = 1.0
    propagate(world, narrate=True)
    world.say(
        f"{hero.name_or_label()} followed the bronze shine to a hidden drawer and found {clue_cfg.reveal}."
    )
    world.say(
        f"The case ended with the clue set safely on a shelf, quiet again, while {hero.name_or_label()} smiled at the solved mystery."
    )

    world.facts["resolved"] = True
    return world


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


def generation_prompts(world: World) -> list[str]:
    cfg = world.facts["clue_cfg"]
    hero = world.facts["hero"]
    return [
        f"Write a short detective story about {hero.name_or_label()} and {cfg.topic}.",
        f"Tell a child-friendly mystery that features repetition, transformation, and inner monologue.",
        f"Write a story where a wise detective follows {cfg.label} until it becomes bronze.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    clue = world.facts["clue_cfg"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.name_or_label()}, a wise detective who solves a strange little case.",
        ),
        QAItem(
            question=f"What kept happening with {clue.label}?",
            answer=f"{clue.label.capitalize()} kept repeating itself, which made the mystery feel important.",
        ),
        QAItem(
            question="What changed when the lamp touched the clue?",
            answer="The clue transformed and became mutant bronze, so the detective knew it was hiding something real.",
        ),
        QAItem(
            question="What did the detective think to himself or herself near the end?",
            answer="The detective thought that the clue was pointing to a hidden place, and that thought helped finish the case.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bronze?",
            answer="Bronze is a strong metal that has a warm brown-gold color and is often used for statues and tools.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means something happens again and again, which can make people notice it.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the quiet voice in your head when you think things through.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a different form or becomes different in an important way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} label={e.label or '-'} "
            f"bronze={e.bronze} mutant={e.mutant} meters={e.meters} memes={e.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
repeated_clue(C) :- clue(C), repeats(C, N), N >= 2.
changed_clue(C) :- clue(C), changed(C).
wise_detective(D) :- detective(D), wise(D).
solved(D, C) :- wise_detective(D), repeated_clue(C), changed_clue(C), inner_monologue(D).
#show repeated_clue/1.
#show changed_clue/1.
#show wise_detective/1.
#show solved/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("detective", "hero"))
    lines.append(asp.fact("wise", "hero"))
    lines.append(asp.fact("inner_monologue", "hero"))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("repeats", cid, 2))
        lines.append(asp.fact("changed", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/2."))
    atoms = set(asp.atoms(model, "solved"))
    py = {("hero", cid) for cid in CLUES}
    if atoms == py:
        print(f"OK: clingo gate matches python expectations ({len(py)} clues).")
        return 0
    print("MISMATCH between clingo and python expectations.")
    print("clingo:", sorted(atoms))
    print("python:", sorted(py))
    return 1


def valid_story_combos() -> list[tuple[str, str]]:
    return valid_combos()


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
        print(asp_program("#show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting, clue in valid_combos():
            params = StoryParams(setting=setting, clue=clue, hero_name="Mara")
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
