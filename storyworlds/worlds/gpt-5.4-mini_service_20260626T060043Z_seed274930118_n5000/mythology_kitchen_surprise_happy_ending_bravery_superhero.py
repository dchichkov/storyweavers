#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mythology_kitchen_surprise_happy_ending_bravery_superhero.py
================================================================================

A standalone storyworld about a small superhero story in a kitchen, with
mythology-flavored surprises, bravery, and a happy ending.

Premise:
- A young hero helps in the kitchen.
- A mythic surprise causes a small problem.
- Bravery and clever teamwork turn the surprise into a happy ending.

This world is intentionally small and constraint-checked: we only generate
stories where the surprising kitchen problem can be solved in a plausible way.
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
    caretaker: Optional[str] = None
    wearing: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "heroine"}
        male = {"boy", "father", "dad", "man", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Kitchen:
    name: str = "the kitchen"
    has_stove: bool = True
    has_sink: bool = True
    has_table: bool = True
    has_pantry: bool = True
    surprise_level: int = 0


@dataclass
class Threat:
    id: str
    label: str
    phrase: str
    mess: str
    cause: str
    fix_item: str
    weakness: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    guards: set[str]
    prep: str
    closing: str
    plural: bool = False


class World:
    def __init__(self, kitchen: Kitchen) -> None:
        self.kitchen = kitchen
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.threat_active: bool = False
        self.mythic_surprise: str = ""

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.kitchen)
        import copy
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.threat_active = self.threat_active
        clone.mythic_surprise = self.mythic_surprise
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
HERO_NAMES = ["Nova", "Milo", "Zara", "Finn", "Luna", "Toby", "Iris", "Arlo"]
SIDEKICK_NAMES = ["Pip", "Dot", "Bean", "Skye", "Mimi", "Juno"]
GUARDIANS = ["mother", "father", "grandmother", "grandfather", "aunt", "uncle"]
TRAITS = ["brave", "curious", "kind", "quick", "gentle", "cheerful"]

THREATS = {
    "giant_jar": Threat(
        id="giant_jar",
        label="a giant jar",
        phrase="a giant jar of starry honey",
        mess="sticky",
        cause="it tipped off the counter",
        fix_item="lid",
        weakness="cold",
        tags={"mythology", "kitchen", "surprise", "sticky"},
    ),
    "spilled_soup": Threat(
        id="spilled_soup",
        label="a soup spill",
        phrase="a splash of glowing soup",
        mess="wet",
        cause="the ladle slipped",
        fix_item="towel",
        weakness="soak",
        tags={"mythology", "kitchen", "surprise", "wet"},
    ),
    "floating_flour": Threat(
        id="floating_flour",
        label="a flour cloud",
        phrase="a puff of enchanted flour",
        mess="dusty",
        cause="a magic sneeze shook the bowl",
        fix_item="cloth",
        weakness="settle",
        tags={"mythology", "kitchen", "surprise", "dusty"},
    ),
}

AIDS = {
    "lid": Aid(
        id="lid",
        label="a tight lid",
        phrase="a tight lid",
        guards={"sticky"},
        prep="put on a tight lid first",
        closing="sealed the jar before it could spill again",
    ),
    "towel": Aid(
        id="towel",
        label="a thick towel",
        phrase="a thick towel",
        guards={"wet"},
        prep="grab a thick towel",
        closing="soaked up the soup",
    ),
    "cloth": Aid(
        id="cloth",
        label="a soft cloth",
        phrase="a soft cloth",
        guards={"dusty"},
        prep="hold a soft cloth ready",
        closing="settled the flour down",
    ),
}

KITCHEN_SPOTS = ["counter", "sink", "table", "pantry", "stove"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    threat: str
    name: str
    sidekick: str
    guardian: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def threat_is_reasonable(threat: Threat) -> bool:
    return "mythology" in threat.tags and "kitchen" in threat.tags and "surprise" in threat.tags


def select_aid(threat: Threat) -> Optional[Aid]:
    return AIDS.get(threat.fix_item)


def valid_combos() -> list[tuple[str, str]]:
    return [(tid, aid.id) for tid, t in THREATS.items() if threat_is_reasonable(t) and (aid := select_aid(t))]


def explain_rejection(threat: Threat) -> str:
    return (
        f"(No story: the kitchen surprise '{threat.label}' does not have a plausible fix "
        f"that fits its mess. The happy ending needs an aid that truly works.)"
    )


def explain_gender(name: str) -> str:
    return f"(No story: '{name}' is not a supported hero name for this world.)"


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, guardian: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.pronoun('subject')} with a bright cape and a brave heart. "
        f"{hero.pronoun().capitalize()} liked helping {guardian.label} in {world.kitchen.name}."
    )


def mention_mythology(world: World, hero: Entity, threat: Threat) -> None:
    world.say(
        f"One afternoon, while the pots gleamed and the spoons shone, "
        f"{hero.id} heard a story about old mythology and a treasure that could surprise anyone."
    )
    world.say(
        f"Then, right there in {world.kitchen.name}, the surprise came true: {threat.phrase}."
    )


def predict_mess(world: World, threat: Threat, aid: Aid) -> bool:
    return threat.mess not in aid.guards


def warn(world: World, guardian: Entity, hero: Entity, threat: Threat) -> None:
    world.say(
        f'"Careful," {guardian.label} said. "If we are not brave and quick, {threat.cause} and the kitchen will get {threat.mess}."'
    )


def brave_move(world: World, hero: Entity, sidekick: Entity, threat: Threat) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    sidekick.memes["bravery"] = sidekick.memes.get("bravery", 0) + 1
    world.say(
        f"{hero.id} took a deep breath. {hero.pronoun().capitalize()} did not run away. "
        f"Instead, {hero.id} and {sidekick.id} stepped closer with brave little superhero feet."
    )


def resolve(world: World, guardian: Entity, hero: Entity, sidekick: Entity, threat: Threat, aid: Aid) -> None:
    world.say(
        f"{guardian.label} smiled and said, \"Good thinking. {aid.prep}.\""
    )
    world.say(
        f"Together they used {aid.label}. It {aid.closing}, and the surprise stayed under control."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    sidekick.memes["joy"] = sidekick.memes.get("joy", 0) + 1
    guardian.memes["pride"] = guardian.memes.get("pride", 0) + 1
    world.say(
        f"At the end, {hero.id} stood a little taller, {sidekick.id} clapped, and the kitchen looked neat again. "
        f"It was a happy ending, and the brave hero had helped save the day."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    if params.threat not in THREATS:
        raise StoryError("Unknown threat.")
    threat = THREATS[params.threat]
    if not threat_is_reasonable(threat):
        raise StoryError(explain_rejection(threat))
    aid = select_aid(threat)
    if aid is None:
        raise StoryError(explain_rejection(threat))

    kitchen = Kitchen()
    world = World(kitchen)

    hero = world.add(Entity(id=params.name, kind="character", type="hero", label=params.name))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="sidekick", label=params.sidekick))
    guardian = world.add(Entity(id=params.guardian, kind="character", type=params.guardian, label=f"the {params.guardian}"))
    treasure = world.add(Entity(id="treasure", type="thing", label=threat.label, phrase=threat.phrase, caretaker=guardian.id))

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        guardian=guardian,
        treasure=treasure,
        threat=threat,
        aid=aid,
    )

    introduce(world, hero, guardian)
    world.para()
    mention_mythology(world, hero, threat)
    warn(world, guardian, hero, threat)
    brave_move(world, hero, sidekick, threat)
    world.para()
    resolve(world, guardian, hero, sidekick, threat, aid)

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    threat = f["threat"]
    aid = f["aid"]
    guardian = f["guardian"]
    return [
        "Write a short superhero story for a young child set in a kitchen, with a surprising mythological problem and a happy ending.",
        f"Tell a brave kitchen story where {hero.id} faces {threat.phrase} and uses {aid.label} to help {guardian.label}.",
        f"Write a gentle superhero tale with mythology, a surprise, and bravery that ends happily in the kitchen.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    guardian = f["guardian"]
    threat = f["threat"]
    aid = f["aid"]

    return [
        QAItem(
            question=f"Who was the brave hero in the kitchen story?",
            answer=f"The brave hero was {hero.id}, who helped in the kitchen and faced a surprising mythological problem.",
        ),
        QAItem(
            question=f"What surprising thing happened in the kitchen?",
            answer=f"The surprising thing was {threat.phrase}. It appeared in {world.kitchen.name} and made a small mess risk.",
        ),
        QAItem(
            question=f"How did {hero.id} and {sidekick.id} fix the problem?",
            answer=f"They used {aid.label} to handle the surprise safely, and {guardian.label} guided them toward the happy ending.",
        ),
        QAItem(
            question=f"Why was {hero.id} brave?",
            answer=f"{hero.id} was brave because {hero.pronoun().capitalize()} stayed calm, stepped forward, and helped instead of hiding from the surprise.",
        ),
        QAItem(
            question=f"What kind of ending did the story have?",
            answer="It had a happy ending, because the surprise was solved and the kitchen became neat again.",
        ),
    ]


WORLD_QA = [
    QAItem(
        question="What is mythology?",
        answer="Mythology is a collection of old stories about magical beings, heroes, and special events people have told for a long time.",
    ),
    QAItem(
        question="Why can a kitchen surprise be messy?",
        answer="A kitchen surprise can be messy because food, water, flour, or sticky things can spill, puff up, or slide onto the floor and counters.",
    ),
    QAItem(
        question="What does bravery mean?",
        answer="Bravery means doing the right thing even when you feel a little scared.",
    ),
    QAItem(
        question="What makes a happy ending?",
        answer="A happy ending is when the problem gets fixed and the characters end the story feeling safe and glad.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when a mythology-themed surprise belongs in the kitchen and
% has a matching aid that can handle the mess kind.
threat_ok(T) :- threat(T), myth(T), kitchen_surprise(T).
fix_ok(T, A) :- threat_ok(T), threat_fix(T, A), aid(A), guards(A, M), threat_mess(T, M).
valid_story(T, A) :- fix_ok(T, A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid, t in THREATS.items():
        lines.append(asp.fact("threat", tid))
        lines.append(asp.fact("threat_fix", tid, t.fix_item))
        lines.append(asp.fact("threat_mess", tid, t.mess))
        if "mythology" in t.tags:
            lines.append(asp.fact("myth", tid))
        if "kitchen" in t.tags:
            lines.append(asp.fact("kitchen_surprise", tid))
    for aid in AIDS.values():
        lines.append(asp.fact("aid", aid.id))
        for g in sorted(aid.guards):
            lines.append(asp.fact("guards", aid.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return valid_combos_impl()


def valid_combos_impl() -> list[tuple[str, str]]:
    combos = []
    for tid, threat in THREATS.items():
        if not threat_is_reasonable(threat):
            continue
        aid = select_aid(threat)
        if aid is not None and not predict_miss_aid(threat, aid):
            combos.append((tid, aid.id))
    return combos


def predict_miss_aid(threat: Threat, aid: Aid) -> bool:
    return threat.mess not in aid.guards


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero kitchen storyworld with mythology, surprise, bravery, and a happy ending.")
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICK_NAMES)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.threat is not None:
        threat = THREATS[args.threat]
        if not threat_is_reasonable(threat):
            raise StoryError(explain_rejection(threat))
    else:
        threat = THREATS[rng.choice(sorted(THREATS))]

    name = args.name or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICK_NAMES)
    guardian = args.guardian or rng.choice(GUARDIANS)
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(threat=threat.id, name=name, sidekick=sidekick, guardian=guardian, trait=trait)


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
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  surprise: {world.mythic_surprise!r}")
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(threat="giant_jar", name="Nova", sidekick="Pip", guardian="mother", trait="brave"),
    StoryParams(threat="spilled_soup", name="Milo", sidekick="Dot", guardian="father", trait="kind"),
    StoryParams(threat="floating_flour", name="Luna", sidekick="Bean", guardian="grandmother", trait="quick"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible story combos:")
        for tid, aid in vals:
            print(f"  {tid:15} {aid}")
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
            try:
                params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.threat}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
