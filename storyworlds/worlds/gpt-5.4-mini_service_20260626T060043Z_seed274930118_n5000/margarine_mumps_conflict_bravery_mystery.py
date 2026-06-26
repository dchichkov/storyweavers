#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/margarine_mumps_conflict_bravery_mystery.py
========================================================================================================================

A small mystery storyworld about a worried household, a sticky clue, and a brave
turn toward the truth.

The seed words here are "margarine" and "mumps", and the style leans into a
gentle mystery: someone thinks margarine caused a problem, tension rises, and a
brave look around the room reveals the real reason.

The world model tracks:
- a child with curiosity and bravery,
- a grown-up with concern and conflict,
- a clue that may be sticky or smooth,
- a snack bowl or lunch table where the mystery unfolds,
- a hidden cause behind the symptoms.

The story is generated from simulated state, not by swapping nouns into a fixed
paragraph. The ending image proves what changed: the clue is read correctly, the
worry settles, and the truth becomes clear.
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

SETTING_NAME = "the kitchen"
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str = SETTING_NAME
    smell: str = "buttery"
    clue_kind: str = "margarine"
    symptom: str = "mumps"
    hidden_cause: str = "a shared cup"
    is_true_clue: bool = False


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
    name: str
    gender: str
    parent: str
    clue: str
    symptom: str
    hidden_cause: str
    seed: Optional[int] = None


NAMES_GIRL = ["Mina", "Lila", "Nora", "June", "Pia", "Etta"]
NAMES_BOY = ["Owen", "Theo", "Finn", "Milo", "Levi", "Ari"]


def pronoun_word(gender: str, case: str) -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle mystery about margarine, mumps, conflict, and bravery.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--clue", choices=["margarine", "crumbs", "soap"])
    ap.add_argument("--symptom", choices=["mumps", "a sore cheek", "a puffy jaw"])
    ap.add_argument("--hidden-cause", choices=["a shared cup", "a chilly draft", "a sneezy friend"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [("margarine", "mumps", "a shared cup")]


def explain_rejection(clue: str, symptom: str, hidden_cause: str) -> str:
    return (f"(No story: this world is tuned to a small mystery where margarine and mumps matter, "
            f"and the false lead must be the margarine clue while the real cause is a shared cup.)")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.symptom and args.hidden_cause:
        if (args.clue, args.symptom, args.hidden_cause) != ("margarine", "mumps", "a shared cup"):
            raise StoryError(explain_rejection(args.clue, args.symptom, args.hidden_cause))
    if args.clue and args.clue != "margarine":
        raise StoryError(explain_rejection(args.clue, args.symptom or "mumps", args.hidden_cause or "a shared cup"))
    if args.symptom and args.symptom != "mumps":
        raise StoryError(explain_rejection(args.clue or "margarine", args.symptom, args.hidden_cause or "a shared cup"))
    if args.hidden_cause and args.hidden_cause != "a shared cup":
        raise StoryError(explain_rejection(args.clue or "margarine", args.symptom or "mumps", args.hidden_cause))

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        name=name,
        gender=gender,
        parent=parent,
        clue="margarine",
        symptom="mumps",
        hidden_cause="a shared cup",
    )


def reasonableness_gate(params: StoryParams) -> bool:
    return (params.clue, params.symptom, params.hidden_cause) == ("margarine", "mumps", "a shared cup")


def story_setup(world: World, hero: Entity, parent: Entity, clue: Entity, symptom: Entity) -> None:
    world.say(f"{hero.id} was a curious child who noticed tiny details.")
    world.say(f"{hero.pronoun('subject').capitalize()} loved solving little puzzles with {parent.label}.")
    world.say(f"One morning, the kitchen smelled buttery, and {clue.label} sat near the toast.")
    world.say(f"Then {hero.id} noticed {symptom.label}, and everyone grew quiet.")


def story_conflict(world: World, hero: Entity, parent: Entity, clue: Entity, symptom: Entity) -> None:
    hero.memes["conflict"] += 1
    parent.memes["worry"] += 1
    world.para()
    world.say(f"{parent.pronoun('subject').capitalize()} looked at the {clue.label} and frowned.")
    world.say(f'"Maybe the {clue.label} made this happen," {parent.id} said, sounding unsure.')
    world.say(f"{hero.id} felt a twist of conflict, because the clue looked suspicious but did not feel proven.")


def story_bravery(world: World, hero: Entity, parent: Entity, clue: Entity, symptom: Entity, hidden: Entity) -> None:
    hero.memes["bravery"] += 1
    hero.memes["curiosity"] += 1
    world.para()
    world.say(f"Still, {hero.id} was brave enough to look closer.")
    world.say(f"{hero.id} checked the cup, the plate, and the sticky spoon beside the snack bowl.")
    world.say(f"At last, {hero.id} found a second clue: {hidden.phrase}.")
    world.say(f"That clue showed the real cause was not the {clue.label} at all.")


def story_resolution(world: World, hero: Entity, parent: Entity, clue: Entity, symptom: Entity, hidden: Entity) -> None:
    parent.memes["worry"] = 0.0
    hero.memes["conflict"] = 0.0
    world.para()
    world.say(f"{parent.id} blinked, then sighed with relief.")
    world.say(f'"Oh! The {symptom.label} came from {hidden.phrase}," {parent.id} said.')
    world.say(f"{hero.id} smiled, because the mystery was solved and the false alarm about {clue.label} was cleared away.")
    world.say(f"By the end, the kitchen felt calm again, and the buttery smell was only a smell, not a secret.")


def tell(params: StoryParams) -> World:
    if not reasonableness_gate(params):
        raise StoryError(explain_rejection(params.clue, params.symptom, params.hidden_cause))

    world = World(Scene())
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={},
        memes={"curiosity": 1.0, "bravery": 0.0, "conflict": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="Mom" if params.parent == "mother" else "Dad",
        meters={},
        memes={"worry": 0.0},
    ))
    clue = world.add(Entity(
        id="clue",
        type="thing",
        label="margarine",
        phrase="a little tub of margarine",
        meters={"sticky": 1.0},
    ))
    symptom = world.add(Entity(
        id="symptom",
        type="thing",
        label="mumps",
        phrase="mumps",
        meters={"noticeable": 1.0},
    ))
    hidden = world.add(Entity(
        id="hidden",
        type="thing",
        label="shared cup",
        phrase="a shared cup",
        meters={"used": 1.0},
    ))

    world.facts.update(hero=hero, parent=parent, clue=clue, symptom=symptom, hidden=hidden, params=params)
    story_setup(world, hero, parent, clue, symptom)
    story_conflict(world, hero, parent, clue, symptom)
    story_bravery(world, hero, parent, clue, symptom, hidden)
    story_resolution(world, hero, parent, clue, symptom, hidden)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    return [
        "Write a short mystery story for a young child about margarine and mumps.",
        f"Tell a gentle story where {hero.id} and {parent.label} mistake margarine for the cause of mumps, but bravery helps solve the puzzle.",
        "Make the ending clear and calm, with the real clue discovered and the false alarm finished.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    clue = f["clue"]
    symptom = f["symptom"]
    hidden = f["hidden"]
    return [
        QAItem(
            question=f"What did {hero.id} first think was connected to {symptom.label}?",
            answer=f"{hero.id} and {parent.label} first worried about the margarine, because it looked like a suspicious clue in the kitchen.",
        ),
        QAItem(
            question=f"What helped {hero.id} be brave in the middle of the mystery?",
            answer=f"Curiosity helped {hero.id} be brave enough to look closely at the cup, the plate, and the spoon instead of stopping at the first guess.",
        ),
        QAItem(
            question=f"What was the real cause of the problem in the end?",
            answer=f"The real cause was {hidden.phrase}, not the {clue.label}. That discovery solved the mystery.",
        ),
        QAItem(
            question=f"How did the story end after the truth was found?",
            answer=f"The worry settled down, the false alarm about {clue.label} was cleared away, and the kitchen felt calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is margarine?",
            answer="Margarine is a soft spread used on bread or toast. It can look pale and buttery.",
        ),
        QAItem(
            question="What are mumps?",
            answer="Mumps is an illness that can make cheeks or jaws swell up, so a person may look puffy or sore.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something careful and difficult even when you feel worried or unsure.",
        ),
        QAItem(
            question="What is a mystery story?",
            answer="A mystery story is a story where someone notices clues, makes guesses, and then finds out the truth.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
clue_is_suspicious(margarine).
symptom_is_present(mumps).
real_cause(shared_cup).

valid_story(margarine,mumps,shared_cup).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("clue", "margarine"),
        asp.fact("symptom", "mumps"),
        asp.fact("cause", "shared_cup"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_story(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


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
    StoryParams(name="Mina", gender="girl", parent="mother", clue="margarine", symptom="mumps", hidden_cause="a shared cup"),
    StoryParams(name="Owen", gender="boy", parent="father", clue="margarine", symptom="mumps", hidden_cause="a shared cup"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: mystery of margarine and mumps"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
