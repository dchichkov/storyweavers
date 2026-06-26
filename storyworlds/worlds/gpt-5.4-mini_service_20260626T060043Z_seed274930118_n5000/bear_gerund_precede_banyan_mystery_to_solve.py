#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bear_gerund_precede_banyan_mystery_to_solve.py
=================================================================================================

A small, self-contained story world for a gentle ghost-story mystery.

Premise:
- A child and a soft-spoken ghost look for a missing keepsake under a banyan tree.
- Clues come first, then the spooky reveal, then the solution.
- The story stays child-facing and concrete, with a faintly eerie but safe mood.

The seed words are woven into the world:
- bear-gerund -> "bearing" is used as a narrative cue and in prompts
- precede -> clue events precede the reveal
- banyan -> the story takes place beneath a banyan tree
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    shadowy: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    object_label: str
    object_phrase: str
    hiding_place: str
    clue: str
    reveal: str
    solved_reveal: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


PLACES = {
    "banyan_garden": Place(
        id="banyan_garden",
        label="the banyan garden",
        shadowy=True,
        affords={"listen", "search", "follow_clues"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="the courtyard",
        shadowy=False,
        affords={"listen", "search", "follow_clues"},
    ),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        object_label="little silver bell",
        object_phrase="a little silver bell with a ribbon",
        hiding_place="the banyan roots",
        clue="a soft tinkling sound",
        reveal="a shiny bell tucked under the roots",
        solved_reveal="the silver bell the ghost had been guarding for the child",
        mood="spooky",
        tags={"bell", "sound", "banyan", "ghost"},
    ),
    "lantern": Mystery(
        id="lantern",
        object_label="paper lantern",
        object_phrase="a paper lantern with star cutouts",
        hiding_place="a low banyan branch",
        clue="a pale glow in the leaves",
        reveal="a paper lantern hanging from a branch",
        solved_reveal="the lantern that lit the garden path every night",
        mood="quiet",
        tags={"lantern", "light", "banyan", "ghost"},
    ),
    "toy_bear": Mystery(
        id="toy_bear",
        object_label="toy bear",
        object_phrase="a small toy bear with stitched paws",
        hiding_place="a stone bench",
        clue="tiny paw prints in the dust",
        reveal="a toy bear sitting on the bench",
        solved_reveal="the toy bear the child had lost before dusk",
        mood="gentle",
        tags={"bear-gerund", "bear", "toy", "banyan"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Sana", "Ivy", "Nora", "Maya"]
BOY_NAMES = ["Ravi", "Arun", "Timo", "Nico", "Eli", "Noah"]
TRAITS = ["curious", "brave", "quiet", "careful", "gentle", "wary"]


class World:
    def __init__(self, place: Place, mystery: Mystery) -> None:
        self.place = place
        self.mystery = mystery
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


def title_case_name(name: str) -> str:
    return name[:1].upper() + name[1:]


def arrange_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(place, mystery)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    ghost = world.add(Entity(id="Ghost", kind="character", type="ghost", label="the ghost"))
    clue = world.add(Entity(id="Clue", kind="thing", type="clue", label=mystery.clue))
    prize = world.add(Entity(id="Prize", kind="thing", type=mystery.id, label=mystery.object_label, phrase=mystery.object_phrase))

    hero.memes["curiosity"] = 1.0
    ghost.memes["mystery"] = 1.0
    world.facts.update(hero=hero, parent=parent, ghost=ghost, clue=clue, prize=prize)
    return world


def solve_mystery(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    mystery: Mystery = world.mystery

    world.say(f"That night, {hero.id} and {parent.label} walked into {world.place.label}.")
    world.say(f"The banyan branches stood still above them, and the shadows looked like quiet hands.")
    world.say(f"{hero.id} heard {mystery.clue}; the clue came first and the answer came later.")
    world.say(f"Then a soft, pale figure appeared beside the trunk.")
    world.say(f'"Please help me," whispered the ghost. "Something important is missing."')

    world.say(f"{hero.id} searched carefully, following the clue as it preceded the reveal.")
    if mystery.id == "toy_bear":
        world.say(f"At last, {hero.id} found {mystery.reveal}.")
        world.say(f"The little bear had been bearing dust and moonlight, but it was safe.")
    elif mystery.id == "bell":
        world.say(f"At last, {hero.id} found {mystery.reveal}.")
        world.say(f"The bell had been bearing a ribbon and a memory, and it gave one tiny ring.")
    else:
        world.say(f"At last, {hero.id} found {mystery.reveal}.")
        world.say(f"The lantern had been bearing soft light, and the garden looked kind again.")

    world.say(f"The ghost smiled because the mystery was solved, and {mystery.solved_reveal}.")
    world.say(f"{hero.id} smiled too, and the banyan tree no longer felt spooky; it felt like a keeper of secrets.")


def tell_story(params: StoryParams) -> World:
    world = arrange_world(params)
    solve_mystery(world)
    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    m: Mystery = world.mystery
    p: Place = world.place
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f'Write a gentle ghost story about a child solving a mystery under a banyan tree, using the word "banyan".',
        f"Tell a short story where {hero.id} follows a clue that precedes the reveal and discovers {m.object_phrase} at {p.label}.",
        f'Write a spooky-but-kind story that includes a ghost, a banyan tree, and the idea of "bearing" a secret.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    mystery: Mystery = world.mystery
    return [
        QAItem(
            question=f"Who went to {world.place.label} to solve the mystery?",
            answer=f"{hero.id} went with {parent.label} to solve the mystery under the banyan tree.",
        ),
        QAItem(
            question=f"What clue came first before the answer was revealed?",
            answer=f"The clue was {mystery.clue}, and it helped the child find the hidden object.",
        ),
        QAItem(
            question=f"What did the child finally find?",
            answer=f"{hero.id} finally found {mystery.object_phrase} and helped solve the mystery.",
        ),
        QAItem(
            question=f"How did the ghost feel at the end?",
            answer="The ghost felt relieved and happy because the missing thing was found.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a banyan tree?",
            answer="A banyan tree is a large tree with spreading branches and many hanging roots.",
        ),
        QAItem(
            question="Why can shadows look spooky at night?",
            answer="Shadows can look spooky at night because it is harder to see clearly and shapes can seem mysterious.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to find the missing answer by noticing clues and putting them together.",
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
    lines.append(f"place={world.place.id} label={world.place.label} shadowy={world.place.shadowy}")
    lines.append(f"mystery={world.mystery.id} object={world.mystery.object_label}")
    for e in world.entities.values():
        lines.append(f"  {e.id:8} type={e.type} kind={e.kind} memes={dict(e.memes)} meters={dict(e.meters)}")
    return "\n".join(lines)


SETTINGS = {
    "banyan_garden": PLACES["banyan_garden"],
    "courtyard": PLACES["courtyard"],
}

MYSTERY_ORDER = ["bell", "lantern", "toy_bear"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for mystery in MYSTERY_ORDER:
            combos.append((place, mystery))
    return combos


def explain_rejection(place: str, mystery: str) -> str:
    return f"(No story: {place} and {mystery} do not make a fitting mystery.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if p.shadowy:
            lines.append(asp.fact("shadowy", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("reveals", mid, m.reveal))
        for t in sorted(m.tags):
            lines.append(asp.fact("tagged", mid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,M) :- place(P), mystery(M).
shadow_story(P,M) :- valid(P,M), shadowy(P).
solvable(P,M) :- valid(P,M).
#show valid/2.
#show shadow_story/2.
#show solvable/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle banyan-tree ghost mystery storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, parent=parent)


def generation_name(params: StoryParams) -> str:
    return title_case_name(params.name)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


CURATED = [
    StoryParams(place="banyan_garden", mystery="toy_bear", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="banyan_garden", mystery="bell", name="Ravi", gender="boy", parent="father"),
    StoryParams(place="courtyard", mystery="lantern", name="Ivy", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2.\n#show shadow_story/2.\n#show solvable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mystery) combos:\n")
        for place, mystery in combos:
            print(f"  {place:14} {mystery}")
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
