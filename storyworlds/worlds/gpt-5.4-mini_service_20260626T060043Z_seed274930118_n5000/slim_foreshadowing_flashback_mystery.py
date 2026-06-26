#!/usr/bin/env python3
"""
storyworlds/worlds/slim_foreshadowing_flashback_mystery.py
===========================================================

A small mystery story world built from the seed word "slim", with
foreshadowing and flashback as the main narrative instruments.

Premise:
- A child notices a slim clue.
- Something small goes missing.
- Tiny foreshadowed details and a brief flashback point to the answer.
- The story ends with a clear reveal and a changed emotional state.

The world is deliberately compact: one setting, a handful of entities, and a
single causal arc from curiosity to discovery.
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
    phrase: str = ""
    owner: Optional[str] = None
    hidden_in: Optional[str] = None
    found_by: Optional[str] = None
    slim: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["curiosity", "worry", "relief", "suspicion", "clue", "memory"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the library"
    hidden_spaces: tuple[str, ...] = ("shelf gap", "reading nook", "desk drawer")


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    hiding_place: str
    reveal_hint: str


@dataclass
class StoryParams:
    place: str
    clue: str
    hero_name: str
    hero_type: str
    parent_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "library": Setting(place="the library"),
    "attic": Setting(place="the attic"),
    "garden": Setting(place="the garden"),
    "kitchen": Setting(place="the kitchen"),
}

CLUES = {
    "key": Clue(
        id="key",
        label="key",
        phrase="a slim silver key",
        hiding_place="slim crack under the bench",
        reveal_hint="a tiny shine in the dust",
    ),
    "note": Clue(
        id="note",
        label="note",
        phrase="a slim folded note",
        hiding_place="slim book pocket",
        reveal_hint="a corner of paper under a stack of books",
    ),
    "ribbon": Clue(
        id="ribbon",
        label="ribbon",
        phrase="a slim blue ribbon",
        hiding_place="slim box lid",
        reveal_hint="a blue thread by the chair leg",
    ),
}

HERO_NAMES = ["Mina", "Owen", "Lila", "Noah", "Pia", "Eli"]
TRAITS = ["quiet", "curious", "careful", "brave", "patient"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world with slim clues, foreshadowing, and flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    hero_type = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, clue=clue, hero_name=hero_name, hero_type=hero_type, parent_type=parent_type)


def predict_reveal(world: World, hero: Entity, clue: Clue) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["curiosity"] += 1
    return clue.hiding_place in sim.facts.get("search_path", [])


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, label="the parent"))
    clue = CLUES[params.clue]
    item = world.add(Entity(
        id="clue",
        type="thing",
        label=clue.label,
        phrase=clue.phrase,
        owner=hero.id,
        hidden_in=clue.hiding_place,
        slim=True,
    ))

    world.facts["search_path"] = [clue.hiding_place]

    hero.meters["curiosity"] += 1
    world.say(f"{hero.id} was a {rng_trait(hero.id)} child who noticed small things right away.")
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.type} were in {world.setting.place}.")
    world.say(f"{hero.id} loved looking for answers, especially when something felt wrong.")

    world.para()
    hero.meters["worry"] += 1
    world.say(f"Something was missing, and the room felt too quiet.")
    world.say(f"Then {hero.id} saw a slim clue: {item.phrase}.")
    world.say(f"It looked ordinary, but {clue.reveal_hint} made {hero.pronoun('object')} stop and stare.")

    world.para()
    hero.meters["suspicion"] += 1
    world.say(f"At first, {hero.id} wondered if the clue meant someone had taken the missing thing.")
    world.say(f"But then a flashback came back to {hero.pronoun('object')}: yesterday, {hero.id} had heard a tiny click near the {clue.hiding_place.split(' under ')[0]}.")
    world.say(f"That memory made the mystery feel smaller and clearer.")

    world.para()
    hero.meters["clue"] += 1
    hero.meters["relief"] += 1
    hero.meters["worry"] = 0
    world.say(f"{hero.id} knelt down and searched the {world.setting.place}.")
    world.say(f"Right where the flashback pointed, {hero.id} found the missing {clue.label} tucked in the {clue.hiding_place}.")
    world.say(f"It had not been stolen at all; it had simply slipped into a tiny place where slim things could hide.")
    world.say(f"{hero.id} smiled, and the room felt calm again.")

    world.facts.update(hero=hero, parent=parent, clue=item, clue_cfg=clue)
    return world


def rng_trait(name: str) -> str:
    return random.choice(TRAITS)


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
    f = world.facts
    hero = f["hero"]
    clue = f["clue_cfg"]
    return [
        f"Write a short mystery story for a child where {hero.id} notices a slim clue in {world.setting.place}.",
        f"Tell a gentle mystery with foreshadowing and a flashback that helps solve the case of the missing {clue.label}.",
        f"Write a small, child-friendly story where a slim clue leads to a clear answer and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue_cfg"]
    parent = f["parent"]
    return [
        QAItem(
            question=f"What kind of clue did {hero.id} notice in {world.setting.place}?",
            answer=f"{hero.id} noticed a slim clue: {clue.phrase}. It was small, careful-looking, and easy to miss.",
        ),
        QAItem(
            question=f"What helped {hero.id} solve the mystery?",
            answer=f"A flashback helped {hero.id} remember a tiny click near the {clue.hiding_place.split(' under ')[0]}, and that pointed to the hiding place.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {parent.type}?",
            answer=f"The missing {clue.label} was found in the {clue.hiding_place}, so the mystery was solved and everyone felt calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery story?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="What does foreshadowing do?",
            answer="Foreshadowing gives a small hint early in a story about what may matter later.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory that shows something from earlier and can help explain the present.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.slim:
            bits.append("slim=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A clue is slim if it is marked slim.
slim_clue(C) :- clue(C), slim(C).

% Foreshadowing: a hint appears before the reveal.
foreshadowing(C) :- slim_clue(C), hint(C).

% Flashback: a remembered sound or detail points to the hiding place.
flashback(C) :- slim_clue(C), memory(C).

% The case is solved when the clue is slim and the hiding place is identified.
solved(C) :- slim_clue(C), hidden(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for h in s.hidden_spaces:
            lines.append(asp.fact("hidden_space", pid, h))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("label", cid, c.label))
        lines.append(asp.fact("phrase", cid, c.phrase))
        lines.append(asp.fact("hidden", cid))
        lines.append(asp.fact("slim", cid))
        lines.append(asp.fact("hint", cid))
        lines.append(asp.fact("memory", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        raise StoryError(f"ASP verification needs clingo/asp helper support: {exc}")
    model = asp.one_model(asp_program("#show solved/1."))
    solved = sorted(set(asp.atoms(model, "solved")))
    python_set = [(cid,) for cid in CLUES]
    if len(solved) == len(python_set):
        print(f"OK: ASP twin lists {len(solved)} slim clues as solvable.")
        return 0
    print("MISMATCH between ASP and Python registry interpretation.")
    print("ASP:", solved)
    print("Python:", python_set)
    return 1


def build_reasonable_story(params: StoryParams) -> StorySample:
    return generate(params)


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(list(SETTINGS)),
        clue=args.clue or rng.choice(list(CLUES)),
        hero_name=args.name or rng.choice(HERO_NAMES),
        hero_type=args.gender or rng.choice(["girl", "boy"]),
        parent_type=args.parent or rng.choice(["mother", "father"]),
    )


CURATED = [
    StoryParams(place="library", clue="key", hero_name="Mina", hero_type="girl", parent_type="mother"),
    StoryParams(place="attic", clue="note", hero_name="Owen", hero_type="boy", parent_type="father"),
    StoryParams(place="garden", clue="ribbon", hero_name="Lila", hero_type="girl", parent_type="mother"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solved/1."))
    return sorted(set(asp.atoms(model, "solved")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/1."))
        solved = sorted(set(asp.atoms(model, "solved")))
        print(f"{len(solved)} solvable slim clues:\n")
        for cid, in solved:
            print(f"  {cid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: slim mystery in {p.place} ({p.clue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
