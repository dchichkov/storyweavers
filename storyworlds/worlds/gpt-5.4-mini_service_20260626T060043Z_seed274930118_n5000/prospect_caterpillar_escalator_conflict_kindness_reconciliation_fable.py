#!/usr/bin/env python3
"""
A small fable-like storyworld about a prospect, a caterpillar, and an
escalator conflict that resolves through kindness and reconciliation.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the escalator"
    moving: bool = True


@dataclass
class StoryParams:
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        return clone


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
NAMES = ["Prosper", "Milo", "Nina", "Ada", "Tess", "Arlo", "Ivy", "Owen"]

CHARITY_WORDS = ["gentle", "kind", "patient", "careful", "humble", "brave"]


@dataclass(frozen=True)
class Catalyst:
    id: str
    label: str
    weight: str
    movement: str
    risk: str


CATALYST = Catalyst(
    id="caterpillar",
    label="caterpillar",
    weight="small",
    movement="crawling slowly along the moving step",
    risk="slipping close to the edge",
)


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------
def _bump(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _mood(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def reasonableness_gate() -> None:
    # Only one narrow, coherent story shape in this world.
    return None


# ---------------------------------------------------------------------------
# Fable screenplay
# ---------------------------------------------------------------------------
def tell(name: str) -> World:
    world = World(Setting())
    hero = world.add(
        Entity(
            id=name,
            kind="character",
            type="girl" if name in {"Nina", "Ada", "Tess", "Ivy"} else "boy",
            label=name,
            traits=["young", "thoughtful"],
        )
    )
    caterpillar = world.add(
        Entity(
            id="caterpillar",
            kind="character",
            type="caterpillar",
            label="caterpillar",
            traits=["small", "quiet"],
        )
    )
    guide = world.add(
        Entity(
            id="guide",
            kind="character",
            type="adult",
            label="old guide",
            traits=["patient", "wise"],
        )
    )

    # Act I: the prospect spots the caterpillar.
    _mood(hero, "curiosity", 1)
    world.say(
        f"{hero.id} was a young prospect who liked to watch people and notices small "
        f"things on the way home."
    )
    world.say(
        f"One day on the escalator, {hero.id} saw a {CATALYST.label} "
        f"{CATALYST.movement}."
    )
    world.say(
        f"The little creature looked in danger, because the moving steps carried it "
        f"toward the edge."
    )

    # Act II: conflict.
    world.para()
    _mood(hero, "alarm", 1)
    _mood(hero, "conflict", 1)
    _bump(caterpillar, "risk", 1)
    world.say(
        f"{hero.id} wanted to help at once, but the people behind were hurrying and "
        f"the escalator kept moving."
    )
    world.say(
        f"Some voices said to leave the caterpillar alone, and the voices made "
        f"{hero.id} feel torn between fear and duty."
    )
    world.say(
        f"The caterpillar wiggled nervously, and the small trouble became a true conflict."
    )

    # Act III: kindness and reconciliation.
    world.para()
    _mood(guide, "kindness", 1)
    _mood(hero, "kindness", 1)
    _mood(hero, "reconciliation", 1)
    _mood(caterpillar, "safe", 1)
    hero.memes["conflict"] = 0
    world.say(
        f"Then the old guide smiled and said, 'Kindness is fastest when it is calm.'"
    )
    world.say(
        f"{hero.id} knelt carefully, shielded the caterpillar with two hands, and asked "
        f"the people to wait for a moment."
    )
    world.say(
        f"Together they carried the caterpillar to a safer step, where it could rest."
    )
    world.say(
        f"The hurrying crowd softened, and the conflict melted into reconciliation."
    )
    world.say(
        f"{hero.id} learned that a gentle act can steady a whole day, and the "
        f"caterpillar went on safely, tiny and brave."
    )

    world.facts = {
        "hero": hero,
        "caterpillar": caterpillar,
        "guide": guide,
        "setting": world.setting,
        "conflict": True,
        "resolved": True,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    return [
        "Write a short fable about a prospect and a caterpillar on an escalator.",
        f"Tell a child-friendly story where {hero.id} notices a caterpillar and chooses kindness.",
        "Write a fable with conflict, kindness, and reconciliation on an escalator.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a young prospect who learns to be kind.",
        ),
        QAItem(
            question="What caused the conflict?",
            answer="The conflict started when the caterpillar was in danger on the moving escalator, and people were hurrying past.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer="It was solved by kindness: {0} and the old guide helped the caterpillar to a safer step, and everyone reconciled.".format(hero.id),
        ),
        QAItem(
            question="What did the hero learn?",
            answer="The hero learned that calm kindness can help more than fear or rushing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an escalator?",
            answer="An escalator is a moving staircase that carries people up or down slowly.",
        ),
        QAItem(
            question="What is a caterpillar?",
            answer="A caterpillar is the soft, crawling young form of a butterfly or moth.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a disagreement or hurt feelings.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, care, or be gentle with someone else.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== prompts ==")
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
present(caterpillar).
present(guide).
conflict(H) :- hero(H), sees_caterpillar(H), danger(caterpillar), hurrying_people.
kind(H) :- hero(H), chooses_help(H).
resolved :- conflict(H), kind(H), safe(caterpillar).
show_hero(H) :- hero(H).
show_conflict(H) :- conflict(H).
show_kind(H) :- kind(H).
show_resolved :- resolved.
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero_name", "prospect"),
        asp.fact("sees_caterpillar", "prospect"),
        asp.fact("danger", "caterpillar"),
        asp.fact("hurrying_people"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_parity_check() -> int:
    import asp
    model = asp.one_model(asp_program("#show show_hero/1.\n#show show_conflict/1.\n#show show_kind/1.\n#show show_resolved/0."))
    names = set(a.name for a in model)
    expected = {"show_hero", "show_conflict", "show_kind", "show_resolved"}
    if names == expected:
        print("OK: ASP rules align with Python story shape.")
        return 0
    print("MISMATCH: ASP rules did not produce the expected shape.")
    print(sorted(names))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    return StoryParams(name=name, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world about a prospect, a caterpillar, and an escalator.")
    ap.add_argument("--name", choices=NAMES)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show show_hero/1.\n#show show_conflict/1.\n#show show_kind/1.\n#show show_resolved/0."))
        return
    if args.verify:
        sys.exit(asp_parity_check())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show show_hero/1.\n#show show_conflict/1.\n#show show_kind/1.\n#show show_resolved/0."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        for nm in NAMES:
            params = StoryParams(name=nm, seed=base_seed)
            samples.append(generate(params))
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

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### story {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
