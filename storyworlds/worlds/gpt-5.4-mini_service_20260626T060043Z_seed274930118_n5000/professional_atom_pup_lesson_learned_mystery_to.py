#!/usr/bin/env python3
"""
A standalone storyworld: a professional space helper, an atom-sized mystery,
and a pup who learns the lesson by the end.

This world models a tiny "space adventure" domain where a careful professional
pilot, a curious pup, and a strange atom beacon cause a mystery to solve.
The story premise is that the crew needs to inspect a drifting station module,
but a tiny atom-core device is missing. The tension is that the pup follows the
scent, gets into trouble, and the professional must solve the mystery without
breaking the ship. The turn is that the missing atom-core is hiding inside a
small floating cargo latch. The resolution is the lesson learned: careful
checking beats rushing in space.
"""

from __future__ import annotations

import argparse
import copy
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"woman", "girl", "pilot"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"man", "boy", "captain"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if case == "possessive":
            return "its"
        return "it"

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class SpaceSetting:
    place: str = "the star dock"
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    hiding_place: str
    lesson: str
    danger: str


@dataclass
class Guide:
    id: str
    label: str
    solves: str
    prep: str
    end: str


class World:
    def __init__(self, setting: SpaceSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld: lesson learned, mystery to solve.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--name")
    ap.add_argument("--crew", choices=["pilot", "captain"])
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


SETTINGS = {
    "dock": SpaceSetting(place="the star dock", affords={"scan", "float"}),
    "orbital_lab": SpaceSetting(place="the orbital lab", affords={"scan", "float", "repair"}),
    "moon_base": SpaceSetting(place="the moon base", affords={"scan", "float"}),
}

MYSTERIES = {
    "atom_core": Mystery(
        id="atom_core",
        clue="a tiny blue blink",
        hiding_place="inside a cargo latch",
        lesson="careful checking solves small problems before they grow",
        danger="the station lights could fail",
    ),
    "signal_spot": Mystery(
        id="signal_spot",
        clue="a whispering beep",
        hiding_place="behind a solar panel hinge",
        lesson="looking twice is wiser than guessing once",
        danger="the map could stay confusing",
    ),
    "lost_tool": Mystery(
        id="lost_tool",
        clue="a silver clink",
        hiding_place="under a magnet tray",
        lesson="tidy habits make space work safer",
        danger="the repair kit could be incomplete",
    ),
}

GUIDES = {
    "scanner": Guide(
        id="scanner",
        label="a handheld scanner",
        solves="scan",
        prep="held up the scanner and traced the faint clue",
        end="its steady beep pointed the way",
    ),
    "tether": Guide(
        id="tether",
        label="a safety tether",
        solves="float",
        prep="hooked on the tether before drifting closer",
        end="it kept everyone safe while they searched",
    ),
    "repair_kit": Guide(
        id="repair_kit",
        label="a repair kit",
        solves="repair",
        prep="opened the repair kit and checked each piece",
        end="it showed the missing part was only hidden, not gone",
    ),
}

GIRL_NAMES = ["Nova", "Mira", "Luna", "Zuri", "Iris"]
BOY_NAMES = ["Kai", "Rex", "Jett", "Arlo", "Finn"]
TRAITS = ["professional", "calm", "careful", "brave", "patient"]


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_of", mid, m.clue))
        lines.append(asp.fact("danger_of", mid, m.danger))
    for gid, g in GUIDES.items():
        lines.append(asp.fact("guide", gid))
        lines.append(asp.fact("solves", gid, g.solves))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S, M, G) :- setting(S), mystery(M), guide(G), affords(S, scan), solves(G, scan).
compatible(S, M, G) :- setting(S), mystery(M), guide(G), affords(S, float), solves(G, float).
compatible(S, M, G) :- setting(S), mystery(M), guide(G), affords(S, repair), solves(G, repair).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for mid in MYSTERIES:
            for gid, g in GUIDES.items():
                if g.solves in s.affords:
                    combos.append((sid, mid, gid))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if p - a:
        print("  only in python:", sorted(p - a))
    if a - p:
        print("  only in clingo:", sorted(a - p))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random):
    if args.guide and args.mystery:
        if GUIDES[args.guide].solves not in {"scan", "float", "repair"}:
            raise StoryError("Unsupported guide.")
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.guide is None or c[2] == args.guide)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, guide = rng.choice(sorted(combos))
    gender = rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    crew = args.crew or rng.choice(["pilot", "captain"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, guide=guide, name=name, crew=crew, trait=trait)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    guide: str
    name: str
    crew: str
    trait: str
    seed: Optional[int] = None


def introduce(world: World, hero: Entity, pup: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} was a {hero.memes['trait']} {hero.type} and a professional space helper."
        f" {hero.pronoun().capitalize()} worked with a small pup named {pup.label_word}."
    )
    world.say(
        f"One day, they found a mystery: {mystery.clue} near {world.setting.place}, "
        f"and everyone wanted to know where the atom-sized answer had gone."
    )


def solve_mystery(world: World, hero: Entity, pup: Entity, mystery: Mystery, guide: Guide) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} {guide.prep} because the clue might be hiding close by."
        f" {pup.pronoun().capitalize()} sniffed around the panel with a wagging tail."
    )
    world.say(
        f"At last, the missing atom-core was found {mystery.hiding_place}. "
        f"The tiny piece had not vanished at all; it had only slipped out of sight."
    )
    hero.memes["relief"] += 1
    pup.memes["joy"] += 1
    world.say(
        f"{hero.id} smiled and said the lesson learned was simple: {mystery.lesson}."
        f" {pup.label_word} bounced happily beside the glowing station lights."
    )
    world.say(
        f"{guide.end.capitalize()}, and the crew could travel on through the quiet stars."
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    mystery = MYSTERIES[params.mystery]
    guide = GUIDES[params.guide]

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.crew,
        label=params.name,
        memes={"trait": params.trait, "curiosity": 1.0},
    ))
    pup = world.add(Entity(
        id="pup",
        kind="character",
        type="pup",
        label="Pip",
        label_word="Pip",
        memes={"joy": 0.0, "curiosity": 1.0},
    ))
    atom = world.add(Entity(
        id="atom",
        type="atom",
        label="atom-core",
        phrase="a tiny atom-core",
        owner=hero.id,
        caretaker=hero.id,
    ))
    world.facts.update(hero=hero, pup=pup, atom=atom, mystery=mystery, guide=guide, setting=world.setting)

    world.say(
        f"{hero.id} checked the instruments at {world.setting.place} before the next flight."
        f" {pup.label_word} trotted along, eager for adventure among the silver panels."
    )
    world.para()
    introduce(world, hero, pup, mystery)
    world.para()
    solve_mystery(world, hero, pup, mystery, guide)

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short space adventure for a young child about a professional helper, a pup, and a tiny atom mystery.',
        f"Tell a gentle story where {f['hero'].id} and a pup solve a clue about an atom-core at {world.setting.place}.",
        "Write a story with a clear lesson learned and a mystery to solve, ending with a happy space image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    guide = f["guide"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a professional space helper, and a pup who solved a mystery together.",
        ),
        QAItem(
            question=f"What was the mystery in the story?",
            answer=f"The mystery was a missing atom-core that only seemed gone; it was hiding {mystery.hiding_place}.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that {mystery.lesson}.",
        ),
        QAItem(
            question=f"How did the guide help?",
            answer=f"{guide.label.capitalize()} helped by leading the search and pointing the crew toward the clue.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pup?",
            answer="A pup is a young dog, full of energy and curiosity.",
        ),
        QAItem(
            question="What is an atom?",
            answer="An atom is a tiny piece of matter, smaller than what people can see with their eyes.",
        ),
        QAItem(
            question="What does a professional mean?",
            answer="A professional is someone who does a job carefully and seriously.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="dock", mystery="atom_core", guide="scanner", name="Nova", crew="pilot", trait="professional"),
    StoryParams(setting="orbital_lab", mystery="signal_spot", guide="tether", name="Kai", crew="captain", trait="careful"),
    StoryParams(setting="moon_base", mystery="lost_tool", guide="repair_kit", name="Mira", crew="pilot", trait="calm"),
]


def asp_valid_stories() -> list[tuple]:
    return asp_valid_combos()


def story_qa_for_all(sample: StorySample) -> None:
    return None


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mystery, guide) combos:\n")
        for s, m, g in combos:
            print(f"  {s:12} {m:12} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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


def _infer_label_word(self: Entity) -> str:
    return self.label or self.type


Entity.label_word = property(_infer_label_word)  # type: ignore[attr-defined]


if __name__ == "__main__":
    main()
