#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/treasury_hem_column_kindness_conflict_sharing_whodunit.py
============================================================================================================

A small whodunit-style storyworld set in a treasury with a stone column and a
troublesome hem. The domain keeps the focus on kindness, conflict, and sharing:
a child detective notices a clue, a mistaken suspicion causes tension, and a
shared search reveals the truth.

The story is built from a short simulated world:
- a treasury room with a column
- a banner or cloak hem that can snag
- a missing object that creates a mystery
- a child detective, a worried guard, and a helpful companion

The narrative turn comes from a clue hidden in plain sight: a hem caught on a
column points to the real culprit. The resolution comes from kindness and
sharing: the detective shares a lantern and the group solves the mystery
together.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle", "guard"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the treasury"
    column: str = "the stone column"


@dataclass
class Mystery:
    id: str
    missing: str
    missing_phrase: str
    clue: str
    culprit: str
    culprit_phrase: str
    revelation: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    mystery: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
SETTING = Setting()

MYSTERIES = {
    "key": Mystery(
        id="key",
        missing="key",
        missing_phrase="a small silver key",
        clue="a thin thread of blue cloth caught on the column",
        culprit="mouse",
        culprit_phrase="a tiny mouse with a nest behind the column",
        revelation="The mouse had dragged the key to line its nest, and the key glittered under a pebble.",
        tags={"treasury", "column", "hem", "kindness", "sharing"},
    ),
    "seal": Mystery(
        id="seal",
        missing="seal",
        missing_phrase="the brass seal for the chest",
        clue="a loose gold thread hanging from the hem of the banner",
        culprit="bird",
        culprit_phrase="a little bird hiding in the rafters",
        revelation="The bird had tucked the seal into a nest above the column, where it shone like a toy coin.",
        tags={"treasury", "column", "hem", "kindness", "sharing"},
    ),
    "coin": Mystery(
        id="coin",
        missing="coin",
        missing_phrase="one bright copper coin",
        clue="a snag in the hem of the old cloak near the column",
        culprit="kitten",
        culprit_phrase="a sleepy kitten curled in a box beside the column",
        revelation="The kitten had batted the coin into the box, where it rolled under a soft blanket.",
        tags={"treasury", "column", "hem", "kindness", "sharing"},
    ),
}


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for mid in MYSTERIES:
        out.append(("treasury", mid, "child"))
    return out


def explain_rejection(mystery: str) -> str:
    if mystery not in MYSTERIES:
        return "(No story: that mystery is not part of this treasury world.)"
    return "(No story: this treasury mystery needs a child detective.)"


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved whodunits and quiet clues."
    )
    world.say(
        f"One morning, {hero.pronoun('possessive')} {helper.label} brought {hero.pronoun('object')} to the treasury, "
        f"where a stone column stood beside a hanging banner."
    )
    world.say(
        f"Then someone noticed that {mystery.missing_phrase} had gone missing."
    )


def clue(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} looked closely and found {mystery.clue}."
    )
    world.say(
        f"That clue made {hero.pronoun('possessive')} eyes narrow with thought."
    )


def conflict(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    helper.memes["suspicion"] = helper.memes.get("suspicion", 0) + 1
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {helper.label} frowned and said, "
        f'"Maybe {mystery.culprit_phrase} took it."'
    )
    world.say(
        f"{hero.id} did not like the blaming feeling in the air."
    )


def share_lantern(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    hero.memes["sharing"] = hero.memes.get("sharing", 0) + 1
    helper.memes["relief"] = helper.memes.get("relief", 0) + 1
    world.say(
        f"{hero.id} shared the lantern with {helper.label} and said, "
        f'"Let’s look together."'
    )
    world.say(
        f"That kind offer made the room feel less sharp and more calm."
    )


def resolve(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"They followed the clue around the column and found the truth: {mystery.revelation}"
    )
    world.say(
        f"{helper.label} apologized for the blame, and {hero.id} smiled because the mystery was solved kindly."
    )
    world.say(
        f"In the end, the treasury was quiet again, the hem was fixed, and the lantern shone on a safe, solved room."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
mystery(M) :- valid_mystery(_, M, _).
valid_story(P, M, G) :- place(P), mystery(M), gender(G), valid_mystery(P, M, G).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    lines.append(asp.fact("place", "treasury"))
    lines.append(asp.fact("setting", "treasury"))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
        lines.append(asp.fact("culprit", mid, m.culprit))
        lines.append(asp.fact("valid_mystery", "treasury", mid, "child"))
        for tag in sorted(m.tags):
            lines.append(asp.fact("tag", mid, tag))
    lines.append(asp.fact("gender", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE_QA = {
    "treasury": [
        QAItem(
            question="What is a treasury?",
            answer="A treasury is a place where valuable things are kept safe."
        )
    ],
    "hem": [
        QAItem(
            question="What is a hem?",
            answer="A hem is the edge of cloth on a skirt, cloak, banner, or shirt."
        )
    ],
    "column": [
        QAItem(
            question="What is a column?",
            answer="A column is a tall upright stone or wood support that helps hold up a building."
        )
    ],
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when you are gentle, helpful, and caring toward someone else."
        )
    ],
    "sharing": [
        QAItem(
            question="What is sharing?",
            answer="Sharing is letting someone else use or enjoy something with you."
        )
    ],
    "conflict": [
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a problem or disagreement that makes the story tense for a while."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery_obj"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    return [
        f'Write a short whodunit for a young child set in a treasury with a column and a hem clue.',
        f"Tell a gentle mystery where {hero.id} and {helper.label} search the treasury for {mystery.missing_phrase}.",
        f"Write a story about kindness, conflict, and sharing that solves a small mystery in a treasury.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery_obj"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a curious little {hero.type}, and {helper.label}, who helped in the treasury."
        ),
        QAItem(
            question=f"What went missing in the treasury?",
            answer=f"{mystery.missing_phrase} went missing."
        ),
        QAItem(
            question="What clue did the detective notice?",
            answer=f"{mystery.clue.capitalize()} was the clue that pointed the way."
        ),
        QAItem(
            question="Why did the story feel tense for a moment?",
            answer=f"It felt tense because {helper.label} blamed {mystery.culprit_phrase}, and {hero.id} did not want the wrong person blamed."
        ),
        QAItem(
            question="How did the child detective help solve the mystery?",
            answer=f"{hero.id} shared the lantern, kept looking kindly, and followed the clue around the column until the truth was found."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The mystery ended happily when the missing thing was found and everyone apologized and felt calmer."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery_obj"].tags)
    out: list[QAItem] = []
    for tag in ["treasury", "hem", "column", "kindness", "conflict", "sharing"]:
        if tag in tags:
            out.extend(KNOWLEDGE_QA[tag])
    return out


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id=params.helper, kind="character", type="guard", label=params.helper))
    mystery = MYSTERIES[params.mystery]
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=mystery.clue))
    missing = world.add(Entity(id="missing", kind="thing", type=mystery.missing, label=mystery.missing_phrase))
    world.facts.update(hero=hero, helper=helper, mystery_obj=mystery, clue=clue, missing=missing)
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    mystery = world.facts["mystery_obj"]

    intro(world, hero, helper, mystery)
    world.para()
    clue(world, hero, helper, mystery)
    conflict(world, hero, helper, mystery)
    world.para()
    share_lantern(world, hero, helper)
    resolve(world, hero, helper, mystery)

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
NAMES = ["Mina", "Noor", "Ivy", "Owen", "Tess", "Milo", "Luna", "Ezra"]
HELPERS = ["Guard Rook", "Aunt Pip", "Keeper Bram", "Guard Nia"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A treasury whodunit about a hem clue, a column, and kind sharing.")
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy", "child"])
    ap.add_argument("--helper", choices=HELPERS)
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
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    if mystery not in MYSTERIES:
        raise StoryError(explain_rejection(mystery))
    gender = args.gender or "child"
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(mystery=mystery, name=name, gender=gender, helper=helper)


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
    StoryParams(mystery="key", name="Mina", gender="girl", helper="Guard Rook"),
    StoryParams(mystery="seal", name="Noor", gender="girl", helper="Aunt Pip"),
    StoryParams(mystery="coin", name="Owen", gender="boy", helper="Keeper Bram"),
]


def asp_verify_wrapper() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify_wrapper())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for place, mid, gender in combos:
            print(f"  {place:9} {mid:8} {gender}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
